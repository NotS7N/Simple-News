import html
import webbrowser
from pathlib import Path

import requests
import xml.etree.ElementTree as ET

FEED_URL = "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"
MEDIA_NS = "{http://search.yahoo.com/mrss/}"
OUTPUT = Path(__file__).resolve().parent / "news.html"


def text_of(element):
    """Return an element's text, or an empty string if the element is missing."""
    if element is not None and element.text:
        return element.text.strip()
    return ""


def get_stories():
    response = requests.get(FEED_URL, timeout=10)
    response.raise_for_status()
    root = ET.fromstring(response.content)

    stories = []
    for item in root.findall("channel/item"):
        picture = item.find(MEDIA_NS + "content")
        stories.append({
            "title": text_of(item.find("title")),
            "description": text_of(item.find("description")),
            "image": picture.attrib.get("url") if picture is not None else None,
            "caption": text_of(item.find(MEDIA_NS + "description")),
        })
    return stories


PAGE_START = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>News</title>
<style>
  body {
    background: #ffffff;
    color: #000000;
    font-family: Arial, sans-serif;
    text-align: center;
  }
  .source { position: absolute; top: 10px; left: 14px; margin: 0; font-size: 12px; color: #555555; }
  main { max-width: 600px; margin: 0 auto; padding: 48px 16px 24px; }
  article { margin-bottom: 56px; }
  img { max-width: 100%; height: auto; }
</style>
</head>
<body>
<p class="source">All info gathered from the New York Times (NYT)</p>
<main>
"""

PAGE_END = """</main>
</body>
</html>
"""


def build_page(stories=None, error=None):
    parts = [PAGE_START]
    if error:
        parts.append(f"<p>Couldn't load the feed: {html.escape(error)}</p>\n")
    else:
        for story in stories:
            parts.append("<article>\n")
            parts.append(f"<h2>{html.escape(story['title'])}</h2>\n")
            parts.append(f"<p>{html.escape(story['description'])}</p>\n")
            if story["image"]:
                parts.append(f'<img src="{html.escape(story["image"], quote=True)}" alt="">\n')
            if story["caption"]:
                parts.append(f"<p><small>{html.escape(story['caption'])}</small></p>\n")
            parts.append("</article>\n")
    parts.append(PAGE_END)
    return "".join(parts)


if __name__ == "__main__":
    try:
        page = build_page(stories=get_stories())
    except (requests.RequestException, ET.ParseError) as problem:
        page = build_page(error=str(problem))

    OUTPUT.write_text(page, encoding="utf-8")
    webbrowser.open(OUTPUT.as_uri())