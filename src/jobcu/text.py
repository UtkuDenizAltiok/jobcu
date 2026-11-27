"""Turning job ad HTML into clean plain text."""

import html
import re
import unicodedata

from lxml import html as lxml_html
from lxml.etree import ParserError

_BLOCK_TAGS = ("p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr",
               "section", "article", "header", "footer", "table")


# A tag left in the text after converting: the site sent its HTML escaped ("&lt;p&gt;").
_LEFTOVER_TAG = re.compile(
    r"</?(?:p|div|br|li|ul|ol|h[1-6]|strong|b|em|i|u|span|a|table|tr|td|section)\b[^<>]*>",
    re.IGNORECASE,
)

# Characters no text needs and lxml refuses to hold (control characters other than tab and line
# breaks, unpaired surrogates, non-characters): one in a single Arbeitnow ad (2026-11-27)
# stopped the reading of that whole source for the search.
_UNUSABLE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\ud800-\udfff￾￿]")


# A character reference: "&amp;", "&#038;", "&#x2013;". Only whole ones, with their ";": in
# plain text "R&D" or "AT&T" is written as it is meant.
_REFERENCE = re.compile(r"&(?:#[0-9]{1,7}|#[xX][0-9a-fA-F]{1,6}|[A-Za-z][A-Za-z0-9]{1,31});")


def decode_references(text: str) -> str:
    """Plain text with its character references decoded, also when a site escaped it twice
    ("&amp;amp;" → "&"). An unknown name ("&foo;") stays as it is."""
    for _ in range(3):
        if "&" not in text:
            break
        decoded = _REFERENCE.sub(lambda reference: html.unescape(reference.group(0)), text)
        if decoded == text:
            break
        text = decoded
    return text


def html_to_text(markup: str | None) -> str:
    if not markup:
        return ""
    if "<" not in markup:
        # Text without tags can still be escaped: HTML sent as "&lt;p&gt;", or plain text with
        # "&amp;" in it (Reed's and JSearch's ads, Daimler Truck's titles).
        markup = decode_references(markup)
    text = _to_text(markup)
    if "&" in text:
        # A site that escapes its text twice leaves "&amp;" or "&#8211;" (BAE Systems' titles)
        # after the HTML is read: shown as such, and a different title to match copies by.
        text = tidy(decode_references(text))
    # HTML escaped inside HTML (Arbeitnow sometimes): the first pass leaves the inner tags.
    return _to_text(text) if _LEFTOVER_TAG.search(text) else text


def _to_text(markup: str) -> str:
    markup = _UNUSABLE.sub(" ", markup)
    if "<" not in markup:
        return tidy(markup)
    try:
        root = lxml_html.fragment_fromstring(markup, create_parent="div")
    except (ParserError, ValueError):
        return tidy(re.sub(r"<[^>]+>", " ", markup))
    for bad in root.xpath("//script|//style|//noscript"):
        bad.drop_tree()
    for element in root.iter(*_BLOCK_TAGS):
        element.tail = "\n" + (element.tail or "")
        if element.tag == "li":
            element.text = "• " + (element.text or "")
    return tidy(root.text_content())


def tidy(text: str) -> str:
    text = _UNUSABLE.sub(" ", text).replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalise(text: str | None) -> str:
    """For comparing words: lower case, accents removed ("München" → "munchen"), punctuation as
    spaces."""
    text = unicodedata.normalize("NFKD", (text or "").replace("ß", "ss"))
    text = "".join(c for c in text if not unicodedata.combining(c)).casefold()
    return " ".join(re.sub(r"[^\w]+", " ", text).split())
