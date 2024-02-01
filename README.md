---
title: Arxiv Plagiarism Checker LLM
emoji: 🚀
colorFrom: pink
colorTo: pink
sdk: docker
app_port: 7860
pinned: true
---

# Arxiv Plagiarism Checker LLM

**Demo** - [Link](https://huggingface.co/spaces/asach/arxiv-plagiarism-checker-Ilm)

**Dataset** - [Link](https://huggingface.co/datasets/asach/arxiv-2023-4-months-openai-embeddings)

[![Sync to Hugging Face hub](https://github.com/gamingflexer/arxiv-plagiarism-checker-llm/actions/workflows/main.yml/badge.svg)](https://github.com/gamingflexer/arxiv-plagiarism-checker-llm/actions/workflows/main.yml)

Arxiv author's plagiarism check just by entering the arxiv author

## Docs & Working

INPUT - Authors Name
OUTPUT - Plagiarism Check Results

You can get MIT authors List from here - [Link](https://dspace.mit.edu/handle/1721.1/7582/browse?rpp=100&sort_by=-1&type=author&offset=100&etal=-1&order=ASC)

### Tech Stack

- Gradio
- ChromaDB
- SERP API
- OpenAI GPT Embeddings & LLM Models

1. We have collected the data from arxiv GCP cloud for the year of 2023 & 2024 and then we have used the text-embedding-3-large to generate the embeddings for the documents. This amount to about 10GB.

2. Document Text Extraction is done in 2 formats with metdata

- Document Level
- Paragraph Level
- MetaData

Meta data example

```json
{
  "id": "2106.09680",
  "title": "Accuracy, Interpretability, and Differential Privacy via Explainable Boosting",
  "summary": "We show that adding differential privacy to Explainable Boosting Machines\n(EBMs), a recent method for training interpretable ML models, yields\nstate-of-the-art accuracy while protecting privacy. Our experiments on multiple\nclassification and regression datasets show that DP-EBM models suffer\nsurprisingly little accuracy loss even with strong differential privacy\nguarantees. In addition to high accuracy, two other benefits of applying DP to\nEBMs are: a) trained models provide exact global and local interpretability,\nwhich is often important in settings where differential privacy is needed; and\nb) the models can be edited after training without loss of privacy to correct\nerrors which DP noise may have introduced.",
  "source": "http://arxiv.org/pdf/2106.09680",
  "authors": "Harsha Nori Rich Caruana Zhiqi Bu Judy Hanwen Shen Janardhan Kulkarni",
  "references": ""
}
```
3. Embeddings are generated for the documents and paragraphs using OpenAI Models

4. Authors are then searched on the Google SERP API and the documents (Top 10) are then compared individually with the embeddings of the documents.

5. Retreived documents & Top 3 simialar papers from Google SERP API on the topic
    - Metadata and text is extracted 

6. Once Extracted Unique Lines and Paragraphs are extracted and then compared by using LLM - GPT 4 Preview Model - 128K

7. Unique Lines are then compared with the document embeddings and the paragraphs are compared with the paragraph embeddings.

8. Top 3 Similar Text and respective documents are then returned to the user as Plagiarised Content.


### Research Points

- Miro RoadMap [Link](https://miro.com/app/board/uXjVN8HgXk8=/)
- Notion [Link](https://gamingflexer.notion.site/Arxiv-983d173f46c1426caa9dab319f4ddb3d?pvs=4)

### Top Plagiarism Checkers API

- **[ProWritingAid API V2](https://cloud.prowritingaid.com/analysis/swagger/ui/index) - Free Plan**
- **[Unicheck](https://unicheck.com/plagiarism-checker-api) - Request Demo**
- **[Copyleaks]() - Request Demo** 
- **[EDEN AI](https://www.edenai.co/feature/plagiarism-detection) - Free Plan**
----

## Requirements

- Python 3.9+
- Gradio
- GPT Keys

## Installation

```bash
pip install -r requirements.txt
```

## Usage

We are using a gradio app to implement the plagiarism checker

```python
python app.py or gradio app.py
```