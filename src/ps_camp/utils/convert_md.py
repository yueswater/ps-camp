import re
from bs4 import BeautifulSoup
import markdown

def downgrade_headings(text: str) -> str:
    # 把 # 變成 ###，## 變成 ####
    text = re.sub(r"^#### (.*)", r"##### \1", text, flags=re.MULTILINE)
    text = re.sub(r"^### (.*)", r"#### \1", text, flags=re.MULTILINE)
    text = re.sub(r"^## (.*)", r"### \1", text, flags=re.MULTILINE)
    text = re.sub(r"^# (.*)", r"## \1", text, flags=re.MULTILINE)
    return text

def generate_preview(md_text: str, limit: int = 100) -> dict:
    html = markdown.markdown(
        downgrade_headings(md_text),
        extensions=["nl2br", "fenced_code", "codehilite"],
    )
    plain_text = strip_html_tags(html)

    if len(plain_text) <= 120 and "<a " in html:
        return {"html": html, "is_truncated": False}

    truncated = md_text[:limit] + "..."
    truncated_html = markdown.markdown(
        downgrade_headings(truncated),
        extensions=["nl2br", "fenced_code", "codehilite"],
    )
    return {"html": truncated_html, "is_truncated": True}


def strip_html_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html).strip()
