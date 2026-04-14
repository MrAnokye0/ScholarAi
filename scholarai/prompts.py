"""
prompts.py — System prompt templates for ScholarAI's AI pipeline.
"""


METADATA_PROMPT = """Extract bibliographic metadata from this academic article text.
Return ONLY a valid JSON object with these exact fields:
{{
  "authors": ["Last, First Middle", "Last2, First2"],
  "year": "2022",
  "title": "Full article title here",
  "journal": "Journal Name or null",
  "volume": "14 or null",
  "issue": "3 or null",
  "pages": "45-62 or null",
  "doi": "10.xxxx/xxxx or null"
}}

Rules:
- authors: list of strings in "Last, First" format. Use [] if not found.
- year: 4-digit year string, or "n.d." if not found.
- title: the article title. Use the filename description if genuinely not found.
- All other fields: use null (not "null") if not found.
- Return ONLY the JSON. No explanation, no markdown, no code fences.

Article text (first 1200 characters):
{text}
"""


REVIEW_PROMPT = """You are an expert academic writer specialising in literature reviews for university research papers.

TASK: Write a complete literature review based EXCLUSIVELY on the source article excerpts provided below.

RESEARCH TOPIC: {topic}
CITATION STYLE: {style}
NUMBER OF ARTICLES: {article_count}

STRICT RULES — FOLLOW ALL OF THEM:
1. Use ONLY information from the provided articles. Do not add outside knowledge, invent facts, or cite sources not provided.
2. Every factual claim MUST include an in-text citation in {style} format. Use the citation markers exactly as specified.
3. Paraphrase ALL source material. Do NOT copy sentences verbatim from the articles.
4. No sequence of more than 6 consecutive words may match the source text.
5. Structure: Introduction (1-2 paragraphs) → Thematic body (2-4 sections, each with a heading) → Conclusion (1 paragraph).
6. Each thematic section MUST draw from at least 2 different articles.
7. Section headings should reflect themes found across the articles (not just restate the topic).
8. Introduction: contextualise the topic, explain why it matters, state what this review covers.
9. Conclusion: summarise key themes, identify at least one research gap based on the literature provided.
10. Academic register: formal English, third person, objective tone.
11. Target length: approximately {word_target} words of body text.

CITATION FORMAT REMINDER for {style}:
{citation_reminder}

SOURCE ARTICLES WITH CITATION KEYS:
{articles_formatted}

OUTPUT INSTRUCTIONS:
- Output ONLY the literature review text.
- Use ## for thematic section headings (e.g., ## Impact of Climate Change on Crop Yields).
- Do NOT include a title, abstract, or reference list (added separately).
- Do NOT add any preamble, explanation, or concluding note outside the review itself.
- Start directly with the Introduction paragraph.
"""


CITATION_REMINDERS = {
    "APA 7th":    "In-text: (Author, Year) or Author (Year) found that... — e.g. (Smith & Jones, 2022) or Smith and Jones (2022) found that...",
    "Harvard":    "In-text: (Author Year) — note NO comma — e.g. (Smith and Jones 2022) or As Smith and Jones (2022) argued...",
    "MLA 9th":    "In-text: (Author Page) — no year — e.g. (Smith 45) or As Smith argues (45)...",
    "Chicago 17th":"In-text: (Author, Year, Page) — e.g. (Smith 2022, 45) or Smith (2022, 45) found...",
    "Vancouver":  "In-text: [N] superscript number — e.g. 'This was demonstrated [1].' or 'Research shows [2,3] that...'",
    "IEEE":       "In-text: [N] in brackets — e.g. 'As shown in [1],' or 'This approach [2] demonstrates...'",
}


def build_review_prompt(topic: str, style: str, articles: list[dict]) -> str:
    """Build the full review generation prompt."""
    word_target = min(900 + len(articles) * 200, 1800)
    citation_reminder = CITATION_REMINDERS.get(style, "")

    lines = []
    for i, art in enumerate(articles, 1):
        meta = art.get("metadata", {})
        authors = meta.get("authors", [])
        year    = meta.get("year", "n.d.")
        title   = meta.get("title", f"Article {i}")

        # Build the intext key for the AI to use
        from reference_formatter import format_intext
        intext_key = format_intext(meta, style, number=i)

        author_str = authors[0].split(",")[0] if authors else "Unknown"
        lines.append(
            f"--- ARTICLE {i} | CITE AS: {intext_key} ---\n"
            f"Title: {title}\n"
            f"Authors: {', '.join(authors) or 'Unknown'} | Year: {year}\n\n"
            f"{art.get('excerpt', art.get('text', '')[:4000])}\n"
        )

    articles_formatted = "\n".join(lines)

    return REVIEW_PROMPT.format(
        topic=topic,
        style=style,
        article_count=len(articles),
        word_target=word_target,
        citation_reminder=citation_reminder,
        articles_formatted=articles_formatted,
    )


def build_metadata_prompt(text_excerpt: str) -> str:
    # Use token replacement (not str.format) to avoid accidental brace parsing
    # from JSON examples in prompt text.
    return METADATA_PROMPT.replace("{text}", text_excerpt)
