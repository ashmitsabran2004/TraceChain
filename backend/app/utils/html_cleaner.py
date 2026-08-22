import html
import re
from typing import Optional

def clean_text(text: Optional[str]) -> str:
    """
    Decodes HTML entities (&#039; -> ', &quot; -> ", &amp; -> &, etc.), replaces special unicode dashes, and removes raw HTML tags.
    Returns clean, human-readable text string.
    """
    if not text:
        return ""
    
    # Unescape HTML entities
    decoded = html.unescape(text)
    # Replace unicode dashes and quotes
    decoded = decoded.replace('\u2013', '-').replace('\u2014', '-').replace('\u2018', "'").replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
    # Remove HTML tags if present
    clean = re.sub(r'<[^>]+>', '', decoded)
    # Collapse multiple whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean
