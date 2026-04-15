"""
reviewer.py — Core AI pipeline: metadata extraction → review generation → citation formatting.
Supports both OpenAI and Google Gemini.
"""

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable, Any

from openai import OpenAI
import google.generativeai as genai

from extractor import truncate_text, get_first_chars
from prompts import build_metadata_prompt, build_review_prompt
from reference_formatter import format_all_references, format_intext

GEMINI_FALLBACK_MODELS = [
    "gemini-pro",  # Most stable and widely available
    "gemini-1.5-pro-latest",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]


def _generate_with_gemini_fallback(client: Any, prompt: str) -> str:
    """Try provided Gemini client, then fall back across common model IDs."""
    errors = []
    try:
        response = client.generate_content(prompt)
        text = getattr(response, "text", "") or ""
        if text.strip():
            return text.strip()
        raise RuntimeError("Empty response text from Gemini.")
    except Exception as e:
        errors.append(str(e))

    for model_name in GEMINI_FALLBACK_MODELS:
        try:
            fallback_client = genai.GenerativeModel(model_name)
            response = fallback_client.generate_content(prompt)
            text = getattr(response, "text", "") or ""
            if text.strip():
                return text.strip()
            errors.append(f"{model_name}: Empty response")
        except Exception as e:
            errors.append(f"{model_name}: {e}")

    # Last resort: discover models available to this API key/project and try those.
    try:
        discovered = []
        for m in genai.list_models():
            name = getattr(m, "name", "")
            methods = getattr(m, "supported_generation_methods", []) or []
            if "generateContent" in methods and "gemini" in name.lower():
                # names from list_models come as "models/<id>"
                discovered.append(name.replace("models/", ""))
        for model_name in discovered:
            try:
                dynamic_client = genai.GenerativeModel(model_name)
                response = dynamic_client.generate_content(prompt)
                text = getattr(response, "text", "") or ""
                if text.strip():
                    return text.strip()
                errors.append(f"{model_name}: Empty response")
            except Exception as e:
                errors.append(f"{model_name}: {e}")
    except Exception as e:
        errors.append(f"list_models: {e}")

    raise RuntimeError("Gemini fallback failed: " + " | ".join(errors[:4]))


def extract_metadata(client: Any, text: str, provider: str = "openai") -> dict:
    """Extract author/year/title/journal using AI."""
    # Keep metadata extraction concise to reduce latency.
    excerpt_len = 5000 if provider == "google" else 1200
    excerpt = get_first_chars(text, excerpt_len)
    prompt = build_metadata_prompt(excerpt)
    
    try:
        if provider == "google":
            raw = _generate_with_gemini_fallback(client, prompt)
        else:
            # client is OpenAI()
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.1,
            )
            raw = resp.choices[0].message.content.strip()

        # Clean JSON: Find the most outer curly braces to extract raw JSON from chatter
        json_match = re.search(r"({.*})", raw, re.DOTALL)
        if json_match:
            raw = json_match.group(1)
        else:
            # Fallback if no braces found
            raw = re.sub(r"```json\s*|\s*```", "", raw).strip()
            
        meta = json.loads(raw)
        
        if isinstance(meta.get("authors"), str):
            meta["authors"] = [meta["authors"]]
        return meta
    except Exception as e:
        return {"authors": [], "year": "n.d.", "title": "Unknown Article",
                "journal": None, "volume": None, "issue": None,
                "pages": None, "doi": None}


def generate_review(
    client: Any,
    topic: str,
    articles: list[dict],
    citation_style: str,
    provider: str = "openai",
    progress_cb: Optional[Callable[[str], None]] = None,
) -> dict:
    def cb(msg):
        if progress_cb: progress_cb(msg)

    engine_name = "Gemini 1.5 Flash" if provider == "google" else "GPT-4o"
    cb(f"🚀 Using Engine: {engine_name}")

    cb("🔍 Extracting metadata from articles...")
    articles_meta = [None] * len(articles)

    def _extract_one(idx_and_article):
        idx, art = idx_and_article
        meta = extract_metadata(client, art["text"], provider=provider)
        if not meta.get("title") or meta["title"] == "Unknown Article":
            meta["title"] = art["filename"]
        return idx, meta

    max_workers = min(4, max(1, len(articles)))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for idx, meta in executor.map(_extract_one, list(enumerate(articles))):
            articles_meta[idx] = meta
            cb(f"  ✓ Processed: {meta['title'][:40]}...")

    cb("📝 Preparing analysis models...")
    prompt_articles = []
    for i, (art, meta) in enumerate(zip(articles, articles_meta)):
        # Keep prompt context lean for faster generation.
        txt_limit = 14000 if provider == "google" else 7000
        truncated = truncate_text(art["text"], txt_limit)
        prompt_articles.append({
            "metadata": meta,
            "excerpt": truncated,
            "text": truncated,
        })

    cb(f"✍️  Synthesizing literature review...")
    prompt = build_review_prompt(topic, citation_style, prompt_articles)
    
    try:
        if provider == "google":
            review_text = _generate_with_gemini_fallback(client, prompt)
        else:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert academic research assistant specializing in systematic literature reviews and academic synthesis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            review_text = response.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"{provider.capitalize()} Generation Error: {str(e)}")

    cb("📚 Formatting scientific references...")
    refs_list = format_all_references(articles_meta, citation_style)
    refs_text = "\n\n".join([r.strip() for r in refs_list if r and r.strip()])

    cb("🔗 Building source attribution map...")
    attribution = _build_attribution(review_text, articles_meta, citation_style)

    cb("✅ Literature review generated successfully!")

    return {
        "review_text": review_text,
        "references_list": refs_list,
        "references_text": refs_text,
        "articles_meta": articles_meta,
        "word_count": len(review_text.split()),
        "attribution": attribution,
    }


def _build_attribution(review_text: str, meta_list: list[dict],
                        style: str) -> list[dict]:
    """
    For each article, count how many times its citation key appears
    in the review text. Returns list of {title, intext_key, count}.
    """
    result = []
    for i, meta in enumerate(meta_list, 1):
        key = format_intext(meta, style, number=i)
        # Count approximate occurrences (strip brackets for numbered styles)
        search = key.strip("[]() ")
        count = review_text.count(search) if len(search) > 1 else 0
        result.append({
            "title":     meta.get("title", f"Article {i}")[:80],
            "authors":   meta.get("authors", []),
            "year":      meta.get("year", "n.d."),
            "intext_key":key,
            "count":     count,
        })
    return result


def count_tokens(text: str, provider: str = "openai") -> int:
    """Estimate token count (1 token ≈ 4 chars)."""
    if provider == "google":
        return len(text) // 4 # Rough estimate
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except Exception:
        return len(text) // 4
