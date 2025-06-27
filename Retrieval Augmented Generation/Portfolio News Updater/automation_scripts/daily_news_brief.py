import os
import json
import time
import feedparser
from dotenv import load_dotenv
from datetime import datetime
from openai import OpenAI
from pathlib import Path

# LangChain & OpenAI imports
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import yfinance as yf

# Email
import smtplib
from email.message import EmailMessage
import markdown as md

here = Path(__file__)
rss_feeds_path = here.parent.parent / 'news_rss.json'

def load_rss_feeds(path: str = rss_feeds_path) -> list:
    with open(path, 'r') as f:
        return json.load(f)


def pull_feeds(rss_list):
    feeds = []
    for rss in rss_list:
        parsed = feedparser.parse(rss['rss'])
        feeds.append({
            'source': rss['source'],
            'type': rss['type'],
            'entries': parsed.entries,
            'time_pulled': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        })
    return feeds


def build_documents(feeds):
    docs = []
    for feed in feeds:
        for entry in feed['entries']:
            docs.append({
                'content': str(entry),
                'metadata': {
                    'title': entry.get('title'),
                    'source': feed['source'],
                    'time_pulled': feed['time_pulled'],
                    'news_type': feed['type']
                }
            })
    return docs


def batch_docs(documents, model='text-embedding-3-small', token_limit=300000):
    import tiktoken
    enc = tiktoken.encoding_for_model(model)
    batches, current, count = [], [], 0
    for d in documents:
        tokens = len(enc.encode(d['content']))
        if count + tokens > token_limit and current:
            batches.append(current)
            current, count = [], 0
        current.append(d)
        count += tokens
    if current: batches.append(current)
    return batches


def init_vector_store():
    embedding = OpenAIEmbeddings(model='text-embedding-3-small')
    return Chroma(collection_name='rss_news_feeds', embedding_function=embedding)


def ingest_vector_store(store, batches):
    for batch in batches:
        texts = [d['content'] for d in batch]
        metas = [d['metadata'] for d in batch]
        store.add_texts(texts, metadatas=metas)


def make_system_prompt():
    return (
    "You are an assistant designed to search through news feeds and find the most relevant news based on a prompt. "
    "Use the following pieces of retrieved context to answer "
    "the question. If you don't have enough information to infer an answer, say that you dont have enough information to answer the question."
    "Each document contains the meta data which has the source, news type and pulled date. If you have two stories from different sources that appear to be about the same story prioritize the one with the ealier published time."
    "Keep the answer concise."
    "\n\n"
    "{context}"
    )


def summarize_ticker(rag_chain, ticker: str) -> str:
    today = datetime.today().strftime('%Y-%m-%d')
    name, desc = ticker, ''
    try:
        fast = yf.Ticker(ticker).fast_info      # <- fast_info not quoteSummary
        name = fast.get('shortName') or ticker
    except Exception as e:
        print(f"⚠️  fast_info failed for {ticker}: {e}")
    
    query = (
        f"Today's date is {today}. You MUST only reference news published either today or yesterday. News published any other day is unacceptable!\n\n"
        f"Here is a description of {name}: {desc}\n\n"
        f"Which news stories published either today or yesterday are most likely to have a material impact on {name}'s stock? If there isnt anything material, say so.\n\n"
        "Include citations. Remember news published any other day is unacceptable!"
    )
    resp = rag_chain.invoke({'input': query})
    return f"{ticker} – {name}:\n{resp}\n"


def build_rag_chain(store):
    llm = ChatOpenAI(model='gpt-4.1')
    prompt = ChatPromptTemplate.from_messages([
        ('system', make_system_prompt()),
        ('human', '{input}')
    ])
    retr = store.as_retriever(search_kwargs={'k': 20})
    stuff = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retr, stuff)


def create_portfolio_brief(summaries: list, client) -> str:
    from langchain_core.documents import Document
    docs = [Document(page_content=s, metadata={'ticker': s.split('–')[0]}) for s in summaries]
    prompt = (
        f"""You are a financial analyst and expert Markdown formatter.

        Your task is to synthesize the following stock-specific news briefs into a structured, markdown-formatted report. Focus only on **material information** relevant to the portfolio.

        **Instructions:**
        - Structure the output using **headings** for each portfolio stock (e.g., ## AAPL).
        - Under each stock, use **bullet points** for each insight.
        - Use your expert financial skill to determine what actually has a high probability to be material and only highlight those stories. Be selective!
        - Povide a clear explaination below the news on why the news could materially affect the stock - what are the potential outcomes? 
        - Add **in-context citations** (e.g., (Source: Bloomberg, June 14)) to back up each point.
        - Do **not** wrap the output in code blocks.
        - Do **not** include commentary or filler—just structured insights.

        Here are the news briefs: {str(docs)}"""
    )
    comp = client.chat.completions.create(
        model='gpt-4.1',
        messages=[{'role': 'system', 'content': 'You are an expert financial analyst.'},
                  {'role': 'user', 'content': prompt}]
    )
    return comp.choices[0].message.content


def send_email(subject: str, body_md: str):
    load_dotenv()
    user = os.getenv('GMAIL_EMAIL')
    pwd = os.getenv('GMAIL_APP_PASSWORD')
    to   = os.getenv('TO_EMAIL')

    msg = EmailMessage()
    msg['Subject'], msg['From'], msg['To'] = subject, user, to
    html = md.markdown(body_md)
    msg.set_content('HTML only', subtype='plain')
    msg.add_alternative(html, subtype='html')

    with smtplib.SMTP('smtp.gmail.com', 587) as s:
        s.starttls()
        s.login(user, pwd)
        s.send_message(msg)

    print(f"✅ Email sent to {to}")


def main():
    load_dotenv()
    rss = load_rss_feeds()
    feeds = pull_feeds(rss)
    docs = build_documents(feeds)
    batches = batch_docs(docs)
    store = init_vector_store()
    ingest_vector_store(store, batches)
    rag = build_rag_chain(store)
    tickers = os.getenv('PORTFOLIO').split(',')
    summaries = []
    for t in tickers:
        try:
            summaries.append(summarize_ticker(rag, t))
        except Exception as e:
            print(f"⚠️  Warning: skipped {t} due to error: {e}")
    client = OpenAI()
    brief = create_portfolio_brief(summaries, client)

    send_email('Morning Brief', brief)

if __name__ == '__main__':
    main()
