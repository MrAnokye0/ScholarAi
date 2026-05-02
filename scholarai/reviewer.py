"""
reviewer.py — Core AI pipeline: metadata extraction → review generation → citation formatting.
Supports both OpenAI and Google Gemini (new google-genai SDK).
"""

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable, Any

from openai import OpenAI

from extractor import truncate_text, get_first_chars
from prompts import build_metadata_prompt, build_review_prompt
from reference_formatter import format_all_references, format_intext

# New Gemini SDK (google-genai)
try:
    from google import genai as _new_genai
    _NEW_SDK = True
except ImportError:
    _NEW_SDK = False

# Fallback: old SDK
try:
    import google.generativeai as _old_genai
    _OLD_SDK = True
except ImportError:
    _OLD_SDK = False

# Preferred model order — newest/fastest first
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro",
]


def _call_gemini(api_key: str, prompt: str) -> str:
    """Call Gemini using the new SDK, falling back to old SDK if needed."""
    errors = []

    # ── New SDK (google-genai) ─────────────────────────────────────
    if _NEW_SDK:
        try:
            client = _new_genai.Client(api_key=api_key)
            for model in GEMINI_MODELS:
                try:
                    resp = client.models.generate_content(
                        model=model, contents=prompt
                    )
                    text = resp.text or ""
                    if text.strip():
                        return text.strip()
                except Exception as e:
                    err = str(e)
                    errors.append(f"{model}: {err}")
                    # Stop trying if quota exhausted
                    if "429" in err or "RESOURCE_EXHAUSTED" in err:
                        raise RuntimeError(
                            "Gemini API quota exhausted. "
                            "Please wait a minute and try again, or check your quota at "
                            "https://ai.dev/rate-limit"
                        )
                    continue
        except RuntimeError:
            raise
        except Exception as e:
            errors.append(f"new_sdk: {e}")

    # ── Old SDK fallback (google-generativeai) ─────────────────────
    if _OLD_SDK:
        try:
            _old_genai.configure(api_key=api_key)
            for model in GEMINI_MODELS:
                try:
                    m = _old_genai.GenerativeModel(model)
                    resp = m.generate_content(prompt)
                    text = getattr(resp, "text", "") or ""
                    if text.strip():
                        return text.strip()
                except Exception as e:
                    errors.append(f"old/{model}: {e}")
                    continue
        except Exception as e:
            errors.append(f"old_sdk: {e}")

    raise RuntimeError("Gemini failed: " + " | ".join(errors[:3]))


def _generate_with_gemini_fallback(client: Any, prompt: str) -> str:
    """
    Compatibility wrapper — client can be:
    - a string (API key) → use _call_gemini directly
    - old GenerativeModel instance → call generate_content
    - new genai.Client → call models.generate_content
    """
    # If client is an API key string
    if isinstance(client, str):
        return _call_gemini(client, prompt)

    # New SDK client
    if _NEW_SDK and isinstance(client, _new_genai.Client):
        for model in GEMINI_MODELS:
            try:
                resp = client.models.generate_content(model=model, contents=prompt)
                text = resp.text or ""
                if text.strip():
                    return text.strip()
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    raise RuntimeError(
                        "Gemini API quota exhausted. Wait a minute and try again."
                    )
                continue

    # Old SDK GenerativeModel instance
    try:
        resp = client.generate_content(prompt)
        text = getattr(resp, "text", "") or ""
        if text.strip():
            return text.strip()
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            raise RuntimeError(
                "Gemini API quota exhausted. Wait a minute and try again."
            )

    raise RuntimeError("Gemini returned empty response")


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
