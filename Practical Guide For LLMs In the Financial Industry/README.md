# How to use this repo
This repo contains tutorials on how to run small and large language models in Huggingface for various financial related tasks. The repo contains the following:

>>Run_LLM_on_local_machine: This is a Jupyter Notebook tutorial guide through ways in which you can run language models locally using HuggingFace if you have a GPU and using lamma.cpp if you do not have a GPU. We suggest downloading this notebook or cloning this repo if you wish to run this locally. 

>>Run_LLM_on_the_cloud: This is the same guide but set up for running LLMs in Google Colab or Kaggle where you have free access to limited GPU resources. We suggest running this throug a shared version on google colab here: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1cbOGsTa96las7bT0bG4cCKWPNzIRdQtb?usp=sharing)

>>FinLLM Comparison Table: This is a table comparing financial language models against general purpose language models. Please refer to the Article - [Practical Guide For LLMs in the Finance Industry for more information](https://rpc.cfainstitute.org/research/the-automation-ahead-content-series/practical-guide-for-llms).

We suggest you follow the the notebook tutorial and refer back to here for any further information.

# Run an LLM with llama.cpp locally. 

llama.cpp is a an open-source project that allows running LLMs efficiently with the use of only a CPU on a local laptop, without the need for a powerful GPU.  

Here's a step by step approach:

1. Download a HuggingFace model
2. There are various ways to download models, but in my experience the huggingface_hub library has been the most reliable. 

# Install the huggingface_hub library:

!pip install huggingface_hub 

# Create a Python script named download.py with the following content:

```
import sys
from huggingface_hub import snapshot_download

if len(sys.argv) != 2:
    print("Usage: python download.py required two arguments")
    sys.exit(1)

model_id = sys.argv[1]
local_dir = model_id.replace("/", "-")
snapshot_download(repo_id=model_id, local_dir=local_dir, local_dir_use_symlinks=False, revision="main")
```


# Run the Python script:

```python download.py <huggingface-model-name>```  The model_name can be found and copied from the HuggingFace models section.

Let's say we want to download this model: meta-llama/Llama-2-7b-chat-hf


# Converting the model

Now it's time to convert the downloaded HuggingFace model to a GGUF model.
Llama.cpp comes with a converter script to do this.

Get the script by cloning the llama.cpp repo. Run this in the terminal.

```git clone https://github.com/ggerganov/llama.cpp.git```

# Install the required python libraries by running the following in the terminal.

```pip install -r llama.cpp/requirements.txt```


# Add the model and tokenizer you wish to convert from hf to gguf on the below python file in the models dict and then run: 

```convert-hf-to-gguf-update.py <huggingface_token>``` 
 
# To generate the model vocabulary

python3 convert_hf_to_gguf.py models/tokenizers/meta-llama/Llama-2-7b-chat-hf/ --outfile models/ggml-vocab-lmsys-vicuna-13b-v1.5.gguf --vocab-only


You can now refer back to the Jupyter Notebook to run the model. 


# Requirements. 
You should have created a virtual enviroment of your choice with the following packages and versions for this implementation to run without errors.

brotli                    1.0.7                hc377ac9_0

brotli-bin                1.1.0                hd74edd7_2    conda-forge
brotli-python             1.0.9           py311h313beb8_8

datasets                  3.0.2                    pypi_0    pypi

flax                      0.7.0                    pypi_0    pypi

llama-cloud               0.1.5                    pypi_0    pypi
llama-cpp-python          0.3.2                    pypi_0    pypi
llama-index               0.12.1                   pypi_0    pypi
llama-index-agent-openai  0.4.0                    pypi_0    pypi
llama-index-cli           0.4.0                    pypi_0    pypi
llama-index-core          0.12.1                   pypi_0    pypi
llama-index-embeddings-openai 0.3.0                    pypi_0    pypi
llama-index-indices-managed-llama-cloud 0.6.2                    pypi_0    pypi
llama-index-legacy        0.9.48.post4             pypi_0    pypi
llama-index-llms-openai   0.3.1                    pypi_0    pypi
llama-index-multi-modal-llms-openai 0.3.0                    pypi_0    pypi
llama-index-program-openai 0.3.0                    pypi_0    pypi
llama-index-question-gen-openai 0.3.0                    pypi_0    pypi
llama-index-readers-file  0.4.0                    pypi_0    pypi
llama-index-readers-llama-parse 0.4.0                    pypi_0    pypi
llama-parse               0.5.14                   pypi_0    pypi

pip                       24.2            py311hca03da5_0

pipeline                  0.1.0                    pypi_0    pypi

pyarrow                   17.0.0                   pypi_0    pypi

python                    3.11.10         hc51fdd5_3_cpython    conda-forge

tensorflow                2.16.2                   pypi_0    pypi
tensorflow-estimator      2.17.0          cpu_py311h0c0a56a_0    conda-forge
tensorflow-io-gcs-filesystem 0.37.1                   pypi_0    pypi
tensorflow-macos          2.16.2                   pypi_0    pypi
tensorflow-metal          1.1.0                    pypi_0    pypi
tensorstore               0.1.66                   pypi_0    pypi

torch                     2.5.0                    pypi_0    pypi
torchaudio                2.5.0                    pypi_0    pypi
torchvision               0.20.0                   pypi_0    pypi

transformers              4.46.0             pyhd8ed1ab_0    conda-forge