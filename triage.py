"""
triage.py  ▸  Convert chief concern → visit length (minutes)
Uses the dental_services pgvector table for exact durations.
"""
import re
from rag.vector_store import search

def _parse_minutes(duration_text: str) -> int:
    """
    Extract the *largest* numeric value in the Duration string.
    • “45 minutes”           → 45
    • “90–120 minutes”       → 120
    • “2 visits (60 min)”    → 60
    • “Varies” / blank       → 30  (fallback)
    • “1 hour”               → 60
    """
    txt = duration_text.lower()
    # convert “hour(s)” to minutes for easier math
    txt = re.sub(r"(\d+)\s*hour", lambda m: str(int(m.group(1)) * 60), txt)
    nums = [int(n) for n in re.findall(r"\d+", txt)]
    return max(nums) if nums else 30

def duration_for(chief_concern: str) -> int:
    """
    Look up the most similar service description and return its duration in minutes.
    Defaults to 30 if nothing found.
    """
    hit = search(chief_concern, k=1)
    if not hit:
        return 30
    _name, _desc, _price, duration_txt = hit[0]
    return _parse_minutes(duration_txt or "")
