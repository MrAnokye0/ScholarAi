"""
Private API backend for ScholarAI generation.
Keeps provider keys on the server side and exposes a single generation endpoint.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from reviewer import generate_review

load_dotenv()

app = FastAPI(title="ScholarAI Private API", version="1.0.0")


class ArticleIn(BaseModel):
    filename: str
    text: str


class GenerateRequest(BaseModel):
    topic: str
    articles: list[ArticleIn]
    citation_style: str
    provider: str = "google"


def _check_token(x_api_token: Optional[str]) -> None:
    expected = os.getenv("PRIVATE_API_TOKEN", "").strip()
    if expected and (x_api_token or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid API token")


def _make_client(provider: str):
    provider = (provider or "google").lower()
    if provider == "openai":
        from openai import OpenAI

        key = os.getenv("OPENAI_API_KEY", "").strip()
        if not key:
            raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not configured on server")
        return OpenAI(api_key=key), "openai"

    import google.generativeai as genai

    key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="GOOGLE_API_KEY is not configured on server")
    genai.configure(api_key=key)
    return genai.GenerativeModel("gemini-1.5-flash"), "google"


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/api/generate-review")
def api_generate_review(payload: GenerateRequest, x_api_token: Optional[str] = Header(default=None)):
    _check_token(x_api_token)
    client, provider = _make_client(payload.provider)
    try:
        review = generate_review(
            client=client,
            topic=payload.topic,
            articles=[a.model_dump() for a in payload.articles],
            citation_style=payload.citation_style,
            provider=provider,
        )
        return {"ok": True, "review": review}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

