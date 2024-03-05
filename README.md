# Prompt Data Extraction
Python module and scripts to run automated data extraction pipelines built using MaterialsBERT, GPT-3.5 and LlaMa 2 models.

Developed for data extraction method described in:
> S. Gupta, A. Mahmood, P. Shetty, A. Adeboye and R. Ramprasad.
> *Data Extraction from Polymer Literature using Large Language Models*,
> **Nature Machine Intelligence**, 2024 (Submitted)
> [doi:10.1021](https://doi.org/10.1021 "DOI")

The extracted data can be visualized freely at [https://polymerscholar.org](https://polymerscholar.org)

## Installation
1. Make sure you have [conda](https://docs.anaconda.com/free/miniconda/index.html) installed.
2. Clone the git repository: `git clone https://github.com/Ramprasad-Group/PromptDataExtraction && cd PromptDataExtraction`.
3. Source the `env.sh` script. It will setup a new conda environment and install the required python packages, C++ compilers and CUDA libraries.
4. If the environment is already installed, source the `env.sh` script to activate it.

This package depends on connecting to a PostgreSQL server to store and manage literature extracted data.

The database connection details (including SSH tunnel configuration, if required) can be specified in the `settings.yaml` file.

The MaterialsBERT model should be downloaded from huggingfacehub and the path to
the model should be updated in the settings.

## Usage
Edit the newly created `settings.yaml` file to update required paths, usernames, passwords, database connection details, API keys etc.

The following scripts are available:

`run_heuristic_filters.sh`: Filter the paragraphs using property specific heuristic filters.

`run_ner_filters.sh`: Perform filtering of the hueristically filtered paragraphs
using NER filter of MaterialsBERT.

`run_methods.sh`: Add new extraction method to the database.

`run_ner_pipeline.sh`: Perform data extraction on the NER-filtered paragraphs
using NER-based MaterialsBERT pipeline.

`run_gpt_pipeline.sh`: Perform data extraction on the NER-filtered paragraphs
using LLM pipeline.

`run_post_process_ner.sh`: Run post-processing validatation and filtering on the
NER pipeline extracted data.

`run_post_process_llm.sh`: Run post-processing validatation and filtering on the
LLM pipeline extracted data.

## About
Developed by: Ramprasad Research Group, MSE, Goergia Institute of Technology.\
Copyright 2024, Georgia Tech Research Corporation.\
All Rights Reserved. See the [LICENSE](blob/main/LICENSE) file for details.