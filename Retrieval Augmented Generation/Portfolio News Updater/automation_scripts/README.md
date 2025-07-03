# ⚙️ Automate Your Daily News Brief with GitHub Actions

This repository contains everything you need to set up a fully automated daily portfolio news briefing—no local installs required beyond initially forking. It is recommended that you go through the News Updater Jupyter Notebook before attempting this automated workflow.

## 1️⃣ Fork the Repo

Click **Fork** in the top-right corner of the [main repo](https://github.com/CFA-Institute-RPC/The-Automation-Ahead/tree/main) to create your own copy under your GitHub account.

## 2️⃣ Add Your Secrets

In **Settings → Secrets and variables → Actions**, add the following repository secrets:

* **OPENAI_API_KEY**: Your OpenAI API key.
* **GMAIL_EMAIL**: A dedicated Gmail address that will send the brief.
* **GMAIL_APP_PASSWORD**: The app-specific password generated for that Gmail account.
* **TO_EMAIL**: Recipient address for the daily brief.

On the variables tab on the same page add your portfolio companies.

* **PORTFOLIO**: Comma-separated list of tickers (e.g. `AAPL,MSFT,NVDA`).

⚠️ **Warning:** We strongly recommend creating a **junk Gmail account** just for this project, not your personal address.

To set it up:
1. [Create a Gmail account](https://accounts.google.com/signup)
2. [Enable 2-Step Verification](https://myaccount.google.com/security)
3. [Generate an App Password](https://myaccount.google.com/apppasswords)

Use that app password instead of your Gmail login when setting `GMAIL_APP_PASSWORD`.

## 3️⃣ Configure RSS Feeds (Optional)

Edit `news_rss.json` in your fork if you want to customize which news sources are pulled in.

## 4️⃣ Review the Workflow

Open `.github/workflows/daily_brief.yml` in the root directory to see the schedule (runs daily at 07:00 UTC) and the steps it performs:

1. Install dependencies (`Retrieval Augmented Generation/Portfolio News Updater/automation_scripts/requirements.txt`).
2. Run `Retrieval Augmented Generation/Portfolio News Updater/automation_scripts/daily_news_brief.py` to fetch, summarize, and email the briefing.

## 5️⃣ Push & Automate

Any push to your fork’s default branch will trigger the workflow on schedule. No further action required—your inbox will receive a markdown-formatted news brief each morning.

### ⚡ Manual Trigger

You can also run the job on demand via **Actions → Daily Brief → Run workflow**.

---

> **Note:** If you'd like to test locally, you can clone your fork and run:
>
> ```bash
> pip install -r Retrieval Augmented Generation/Portfolio News Updater/automation_scripts/requirements.txt
> cp .env.example .env
> # fill in your credentials in .env
> python Retrieval Augmented Generation/Portfolio News Updater/automation_scripts/daily_news_brief.py
> ```
>
> But for pure automation, steps 1–5 above are all you need.

## 📝 License

This project is MIT-licensed. See [LICENSE](LICENSE).