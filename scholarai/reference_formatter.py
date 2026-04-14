"""
reference_formatter.py — Format references and in-text citations in 6 academic styles.
APA 7th · Harvard · MLA 9th · Chicago 17th · Vancouver · IEEE
"""

from typing import Optional


STYLES = ["APA 7th", "Harvard", "MLA 9th", "Chicago 17th", "Vancouver", "IEEE"]


def format_authors_apa(authors: list[str]) -> str:
    """Smith, J., & Jones, M. B."""
    if not authors:
        return "Unknown Author"
    formatted = []
    for a in authors:
        parts = a.strip().split(",", 1)
        if len(parts) == 2:
            last, first = parts[0].strip(), parts[1].strip()
            initials = "".join(f"{w[0]}." for w in first.split() if w)
            formatted.append(f"{last}, {initials}")
        else:
            name_parts = a.strip().split()
            if len(name_parts) >= 2:
                last = name_parts[-1]
                initials = "".join(f"{w[0]}." for w in name_parts[:-1])
                formatted.append(f"{last}, {initials}")
            else:
                formatted.append(a.strip())
    if len(formatted) == 1:
        return formatted[0]
    elif len(formatted) == 2:
        return f"{formatted[0]}, & {formatted[1]}"
    else:
        return ", ".join(formatted[:-1]) + f", & {formatted[-1]}"


def format_authors_harvard(authors: list[str]) -> str:
    """Smith, J.A. and Jones, M.B."""
    if not authors:
        return "Unknown Author"
    formatted = []
    for a in authors:
        parts = a.strip().split(",", 1)
        if len(parts) == 2:
            last, first = parts[0].strip(), parts[1].strip()
            initials = "".join(f"{w[0]}." for w in first.split() if w)
            formatted.append(f"{last}, {initials}")
        else:
            name_parts = a.strip().split()
            if len(name_parts) >= 2:
                last = name_parts[-1]
                initials = "".join(f"{w[0]}." for w in name_parts[:-1])
                formatted.append(f"{last}, {initials}")
            else:
                formatted.append(a.strip())
    if len(formatted) == 1:
        return formatted[0]
    elif len(formatted) == 2:
        return f"{formatted[0]} and {formatted[1]}"
    else:
        return ", ".join(formatted[:-1]) + f" and {formatted[-1]}"


def format_authors_mla(authors: list[str]) -> str:
    """Smith, John, and Mary Jones."""
    if not authors:
        return "Unknown Author"
    def expand(a):
        parts = a.strip().split(",", 1)
        if len(parts) == 2:
            return f"{parts[0].strip()}, {parts[1].strip()}"
        return a.strip()
    if len(authors) == 1:
        return expand(authors[0])
    return f"{expand(authors[0])}, and {expand(authors[1])}" + \
           (", et al." if len(authors) > 2 else "")


def format_authors_chicago(authors: list[str]) -> str:
    """Smith, John, and Mary Jones."""
    return format_authors_mla(authors)


def format_authors_vancouver(authors: list[str]) -> str:
    """Smith JA, Jones MB."""
    if not authors:
        return "Unknown Author"
    formatted = []
    for a in authors:
        parts = a.strip().split(",", 1)
        if len(parts) == 2:
            last, first = parts[0].strip(), parts[1].strip()
            initials = "".join(w[0] for w in first.split() if w)
            formatted.append(f"{last} {initials}")
        else:
            name_parts = a.strip().split()
            if len(name_parts) >= 2:
                last = name_parts[-1]
                initials = "".join(w[0] for w in name_parts[:-1])
                formatted.append(f"{last} {initials}")
            else:
                formatted.append(a.strip())
    return ", ".join(formatted)


def format_authors_ieee(authors: list[str]) -> str:
    """A. Smith and M. Jones."""
    if not authors:
        return "Unknown Author"
    formatted = []
    for a in authors:
        parts = a.strip().split(",", 1)
        if len(parts) == 2:
            last, first = parts[0].strip(), parts[1].strip()
            initials = " ".join(f"{w[0]}." for w in first.split() if w)
            formatted.append(f"{initials} {last}")
        else:
            name_parts = a.strip().split()
            if len(name_parts) >= 2:
                last = name_parts[-1]
                initials = " ".join(f"{w[0]}." for w in name_parts[:-1])
                formatted.append(f"{initials} {last}")
            else:
                formatted.append(a.strip())
    if len(formatted) == 1:
        return formatted[0]
    elif len(formatted) == 2:
        return f"{formatted[0]} and {formatted[1]}"
    else:
        return ", ".join(formatted[:-1]) + f", and {formatted[-1]}"


# ── Full reference formatters ────────────────────────────────────

def format_reference(meta: dict, style: str, number: int = 1) -> str:
    """
    Format a full reference entry.
    meta = {authors, year, title, journal, volume, issue, pages, doi}
    """
    authors  = meta.get("authors") or []
    year     = meta.get("year") or "n.d."
    title    = meta.get("title") or "Untitled"
    journal  = meta.get("journal") or ""
    volume   = meta.get("volume") or ""
    issue    = meta.get("issue") or ""
    pages    = meta.get("pages") or ""
    doi      = meta.get("doi") or ""

    doi_str = f" https://doi.org/{doi}" if doi else ""
    pp_str  = f"pp. {pages}" if pages else ""

    if style == "APA 7th":
        auth = format_authors_apa(authors)
        yr   = f"({year})."
        ttl  = f"{title}."
        jour = f"*{journal}*," if journal else ""
        vol  = f" *{volume}*" if volume else ""
        iss  = f"({issue})" if issue else ""
        pgs  = f", {pages}." if pages else "."
        return f"{auth} {yr} {ttl} {jour}{vol}{iss}{pgs}{doi_str}".strip()

    elif style == "Harvard":
        auth = format_authors_harvard(authors)
        yr   = f"({year})"
        ttl  = f"'{title}'"
        jour = f"*{journal}*" if journal else ""
        vol  = f", {volume}" if volume else ""
        iss  = f"({issue})" if issue else ""
        pgs  = f", {pp_str}." if pages else "."
        return f"{auth} {yr} {ttl}, {jour}{vol}{iss}{pgs}".strip()

    elif style == "MLA 9th":
        auth = format_authors_mla(authors)
        ttl  = f'"{title}."'
        jour = f"*{journal}*" if journal else ""
        vol  = f", vol. {volume}" if volume else ""
        iss  = f", no. {issue}" if issue else ""
        yr   = f", {year}"
        pgs  = f", {pp_str}." if pages else "."
        return f"{auth} {ttl} {jour}{vol}{iss}{yr}{pgs}".strip()

    elif style == "Chicago 17th":
        auth = format_authors_chicago(authors)
        ttl  = f'"{title}."'
        jour = f"*{journal}*" if journal else ""
        vol  = f" {volume}" if volume else ""
        iss  = f", no. {issue}" if issue else ""
        yr   = f" ({year})"
        pgs  = f": {pages}." if pages else "."
        return f"{auth} {ttl} {jour}{vol}{iss}{yr}{pgs}".strip()

    elif style == "Vancouver":
        auth = format_authors_vancouver(authors)
        ttl  = f"{title}."
        jour = f"{journal}." if journal else ""
        yr   = f" {year}"
        vol  = f";{volume}" if volume else ""
        iss  = f"({issue})" if issue else ""
        pgs  = f":{pages}." if pages else ""
        return f"{number}. {auth}. {ttl} {jour}{yr}{vol}{iss}{pgs}".strip()

    elif style == "IEEE":
        auth = format_authors_ieee(authors)
        ttl  = f'"{title},"'
        jour = f"*{journal}*" if journal else ""
        vol  = f", vol. {volume}" if volume else ""
        iss  = f", no. {issue}" if issue else ""
        pgs  = f", pp. {pages}" if pages else ""
        yr   = f", {year}." if year != "n.d." else "."
        return f"[{number}] {auth}, {ttl} {jour}{vol}{iss}{pgs}{yr}".strip()

    return f"{', '.join(authors)} ({year}). {title}. {journal}."


# ── In-text citation formatters ───────────────────────────────────

def format_intext(meta: dict, style: str, number: int = 1,
                  page: Optional[str] = None) -> str:
    """Return the in-text citation string for a given style."""
    authors = meta.get("authors") or []
    year    = meta.get("year") or "n.d."

    def first_author_last(auths):
        if not auths:
            return "Unknown"
        a = auths[0].strip()
        parts = a.split(",", 1)
        if parts:
            return parts[0].strip()
        return a.split()[-1] if a.split() else "Unknown"

    last = first_author_last(authors)
    et_al = " et al." if len(authors) > 2 else ""
    second = ""
    if len(authors) == 2:
        second = " & " + first_author_last(authors[1:])

    if style == "APA 7th":
        pg = f", p. {page}" if page else ""
        return f"({last}{second}{et_al}, {year}{pg})"

    elif style == "Harvard":
        pg = f", p. {page}" if page else ""
        return f"({last}{second}{et_al} {year}{pg})"

    elif style == "MLA 9th":
        pg = f" {page}" if page else ""
        return f"({last}{pg})"

    elif style == "Chicago 17th":
        pg = f", {page}" if page else ""
        return f"({last}{second}{et_al} {year}{pg})"

    elif style == "Vancouver":
        return f"[{number}]"

    elif style == "IEEE":
        return f"[{number}]"

    return f"({last}, {year})"


def format_all_references(articles_meta: list[dict], style: str) -> list[str]:
    """Format reference list for all articles in chosen style."""
    refs = []
    for i, meta in enumerate(articles_meta, 1):
        refs.append(format_reference(meta, style, number=i))
    return refs
