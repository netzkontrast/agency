"""Configurable Hugging Face Space demo for a model, paper, or local folder."""

from __future__ import annotations

import html
import os
import re
from pathlib import Path
from typing import Any

import gradio as gr
import requests
from huggingface_hub import model_info

DEFAULT_TARGET_TYPE = os.getenv("DEMO_TARGET_TYPE", "model")
DEFAULT_TARGET = os.getenv(
    "DEMO_TARGET", "distilbert-base-uncased-finetuned-sst-2-english"
)
DEFAULT_SAMPLE_INPUT = os.getenv(
    "DEMO_SAMPLE_INPUT", "I love how simple this demo is to customize."
)
MAX_README_CHARS = 2_000
MAX_LISTED_FILES = 40


def _markdown_escape(value: object) -> str:
    return html.escape(str(value), quote=False)


def _normalise_arxiv_id(target: str) -> str | None:
    target = target.strip()
    patterns = [
        r"arxiv\.org/(?:abs|pdf)/([^?#/]+)",
        r"^arXiv:(.+)$",
        r"^(\d{4}\.\d{4,5})(?:v\d+)?$",
        r"^([a-z\-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?$",
    ]
    for pattern in patterns:
        match = re.search(pattern, target, flags=re.IGNORECASE)
        if match:
            return match.group(1).removesuffix(".pdf")
    return None


def describe_model(model_id: str, sample_input: str) -> str:
    """Return metadata and optional inference output for a Hugging Face model."""
    lines = [f"## 🤗 Model demo: `{_markdown_escape(model_id)}`"]
    try:
        info = model_info(model_id)
        tags = ", ".join(info.tags or []) or "No tags published"
        pipeline_tag = info.pipeline_tag or "unknown"
        downloads = getattr(info, "downloads", None)
        likes = getattr(info, "likes", None)
        lines.extend(
            [
                "### Model card snapshot",
                f"- Pipeline: `{_markdown_escape(pipeline_tag)}`",
                f"- Tags: {_markdown_escape(tags)}",
                f"- Downloads: `{_markdown_escape(downloads)}`" if downloads is not None else "- Downloads: not reported",
                f"- Likes: `{_markdown_escape(likes)}`" if likes is not None else "- Likes: not reported",
                f"- Hub: https://huggingface.co/{model_id}",
            ]
        )
    except Exception as exc:  # network/model metadata may be unavailable in duplicated Spaces
        lines.extend(
            [
                "### Model card snapshot",
                f"Could not load Hub metadata right now: `{_markdown_escape(exc)}`",
            ]
        )
        pipeline_tag = "unknown"

    if sample_input.strip():
        lines.append("### Sample inference")
        try:
            from transformers import pipeline

            task = pipeline_tag if pipeline_tag != "unknown" else "text-classification"
            demo_pipeline = pipeline(task=task, model=model_id)
            result: Any = demo_pipeline(sample_input)
            lines.extend(
                [
                    f"Input: `{_markdown_escape(sample_input)}`",
                    "```json",
                    _markdown_escape(result),
                    "```",
                ]
            )
        except Exception as exc:
            lines.append(
                "Inference was skipped or failed gracefully. "
                f"Reason: `{_markdown_escape(exc)}`"
            )
    return "\n".join(lines)


def describe_paper(target: str, sample_input: str) -> str:
    """Return a compact arXiv paper demo card."""
    arxiv_id = _normalise_arxiv_id(target)
    lines = [f"## 📄 Paper demo: `{_markdown_escape(target)}`"]
    if not arxiv_id:
        return "\n".join(
            lines
            + [
                "Could not recognise this as an arXiv ID/URL.",
                "Try a value like `1706.03762` or `https://arxiv.org/abs/1706.03762`.",
            ]
        )

    api_url = "https://export.arxiv.org/api/query"
    try:
        response = requests.get(api_url, params={"id_list": arxiv_id}, timeout=20)
        response.raise_for_status()
        text = response.text
        title = re.search(r"<title>(.*?)</title>", text, flags=re.DOTALL)
        summary = re.search(r"<summary>(.*?)</summary>", text, flags=re.DOTALL)
        published = re.search(r"<published>(.*?)</published>", text)
        title_text = title.group(1).strip() if title else arxiv_id
        summary_text = re.sub(r"\s+", " ", summary.group(1).strip()) if summary else "No abstract found."
        lines.extend(
            [
                "### Paper snapshot",
                f"- arXiv ID: `{_markdown_escape(arxiv_id)}`",
                f"- Published: `{_markdown_escape(published.group(1) if published else 'unknown')}`",
                f"- Link: https://arxiv.org/abs/{arxiv_id}",
                "### Abstract preview",
                _markdown_escape(summary_text[:1_200]),
            ]
        )
    except Exception as exc:
        lines.append(f"Could not fetch arXiv metadata right now: `{_markdown_escape(exc)}`")

    if sample_input.strip():
        lines.extend(["### Demo prompt", _markdown_escape(sample_input)])
    return "\n".join(lines)


def describe_folder(folder: str, sample_input: str) -> str:
    """Return a safe preview of a local folder inside the Space repository."""
    root = Path.cwd().resolve()
    target = (root / folder).resolve()
    lines = [f"## 📁 Local folder demo: `{_markdown_escape(folder)}`"]
    try:
        target.relative_to(root)
    except ValueError:
        return "\n".join(lines + ["Folder must be inside the Space repository."])
    if not target.exists() or not target.is_dir():
        return "\n".join(lines + ["Folder does not exist yet. Add it to the Space repository."])

    files = [p.relative_to(target) for p in target.rglob("*") if p.is_file()]
    lines.extend(["### Files", *[f"- `{_markdown_escape(path)}`" for path in files[:MAX_LISTED_FILES]]])
    if len(files) > MAX_LISTED_FILES:
        lines.append(f"- …and {len(files) - MAX_LISTED_FILES} more files")

    for readme_name in ("README.md", "readme.md"):
        readme = target / readme_name
        if readme.exists():
            lines.extend(
                [
                    "### README preview",
                    readme.read_text(encoding="utf-8", errors="replace")[:MAX_README_CHARS],
                ]
            )
            break
    if sample_input.strip():
        lines.extend(["### Demo note", _markdown_escape(sample_input)])
    return "\n".join(lines)


def run_demo(target_type: str, target: str, sample_input: str) -> str:
    target = target.strip()
    if not target:
        return "Please provide a model ID, paper URL/ID, or local folder path."
    if target_type == "model":
        return describe_model(target, sample_input)
    if target_type == "paper":
        return describe_paper(target, sample_input)
    if target_type == "folder":
        return describe_folder(target, sample_input)
    return "Unknown target type."


with gr.Blocks(title="Model / Paper / Folder Demo") as demo:
    gr.Markdown(
        """
# 🚀 Model / Paper / Local Folder Demo

Paste a Hugging Face model ID, an arXiv paper URL/ID, or a local folder path to generate a quick demo card.
Customize `DEMO_TARGET_TYPE`, `DEMO_TARGET`, and `DEMO_SAMPLE_INPUT` in your Space settings to make it yours.
"""
    )
    with gr.Row():
        target_type = gr.Radio(
            choices=["model", "paper", "folder"],
            value=DEFAULT_TARGET_TYPE if DEFAULT_TARGET_TYPE in {"model", "paper", "folder"} else "model",
            label="Demo target type",
        )
        target = gr.Textbox(value=DEFAULT_TARGET, label="Target")
    sample_input = gr.Textbox(value=DEFAULT_SAMPLE_INPUT, label="Sample input / note", lines=3)
    run = gr.Button("Build demo", variant="primary")
    output = gr.Markdown(label="Demo")
    run.click(run_demo, inputs=[target_type, target, sample_input], outputs=output)
    demo.load(run_demo, inputs=[target_type, target, sample_input], outputs=output)

if __name__ == "__main__":
    demo.launch()
