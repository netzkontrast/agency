---
title: Model Paper Folder Demo
emoji: 🚀
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 4.44.1
app_file: app.py
pinned: false
license: mit
---

# Model / Paper / Local Folder Demo Space

This Hugging Face Space is a configurable demo shell for presenting **a model, a paper, or a local folder**.

## What it does

- Accepts one of three demo targets:
  - a Hugging Face model ID, such as `distilbert-base-uncased-finetuned-sst-2-english`
  - an arXiv paper URL or ID, such as `1706.03762`
  - a local folder path inside the Space repository, such as `sample_project`
- Produces a concise, human-readable demo card.
- For text-classification models, optionally runs inference through `transformers.pipeline`.
- For local folders, lists a small, safe preview of files and README content.

## Configure for your own target

Set these Space variables to pre-fill the UI:

- `DEMO_TARGET_TYPE`: `model`, `paper`, or `folder`
- `DEMO_TARGET`: model ID, paper URL/ID, or local folder path
- `DEMO_SAMPLE_INPUT`: sample text for model inference

The app intentionally degrades gracefully if optional runtime dependencies or model weights are unavailable.
