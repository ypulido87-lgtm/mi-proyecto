#!/usr/bin/env python3
"""Analyse semantic structure and JavaScript dependency of an HTML document.

Works on the HTML a non-executing agent receives, so every conclusion is about
the served markup, never about a browser-rendered DOM.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

LANDMARKS = ("main", "article", "section", "nav", "header", "footer", "aside")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
SKIP_TEXT = {"script", "style", "template", "noscript", "svg"}


class SemanticParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: dict[str, int] = {}
        self.headings: list[dict[str, Any]] = []
        self.links: list[dict[str, Any]] = []
        self.buttons_without_name = 0
        self.inputs = 0
        self.labelled_inputs = 0
        self.labels_for: set[str] = set()
        self.input_ids: list[str] = []
        self.input_records: list[tuple[bool, str | None]] = []
        self.images = 0
        self.images_without_alt = 0
        self.tables = 0
        self.tables_with_header = 0
        self.lists = 0
        self.scripts = 0
        self.executable_scripts = 0
        self.data_scripts = 0
        self.inline_script_bytes = 0
        self.text_chars = 0
        self.body_text_chars = 0
        self._stack: list[str] = []
        self._current_heading: dict[str, Any] | None = None
        self._current_link: dict[str, Any] | None = None
        self._current_button: str | None = None
        self._button_text = ""
        self._table_depth = 0
        self._table_has_header: list[bool] = []

    # -- helpers -------------------------------------------------------
    def _in_skip(self) -> bool:
        return any(tag in SKIP_TEXT for tag in self._stack)

    def _in_body(self) -> bool:
        return "body" in self._stack or not self._stack

    # -- parsing -------------------------------------------------------
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {k.lower(): (v or "") for k, v in attrs}
        self.tags[tag] = self.tags.get(tag, 0) + 1
        if tag not in VOID:
            self._stack.append(tag)
        if re.fullmatch(r"h[1-6]", tag):
            self._current_heading = {"level": int(tag[1]), "text": ""}
        elif tag == "a":
            self._current_link = {
                "href": attributes.get("href", ""),
                "text": "",
                "aria_label": attributes.get("aria-label", ""),
            }
        elif tag == "button":
            self._current_button = attributes.get("aria-label", "")
            self._button_text = ""
        elif tag == "input":
            self.inputs += 1
            if attributes.get("id"):
                self.input_ids.append(attributes["id"])
            # A wrapping <label> is a valid implicit association, exactly like
            # aria-label or label[for]. Ignoring it reports correct markup as broken.
            directly_labelled = bool(
                attributes.get("aria-label")
                or attributes.get("title")
                or attributes.get("aria-labelledby")
                or "label" in self._stack
            )
            if directly_labelled:
                self.labelled_inputs += 1
            # Hidden and submit controls need no visible label.
            if attributes.get("type", "").lower() not in ("hidden", "submit", "button", "reset", "image"):
                self.input_records.append((directly_labelled, attributes.get("id") or None))
        elif tag == "label" and attributes.get("for"):
            self.labels_for.add(attributes["for"])
        elif tag == "img":
            self.images += 1
            if "alt" not in attributes:
                self.images_without_alt += 1
        elif tag == "table":
            self._table_depth += 1
            self._table_has_header.append(False)
            self.tables += 1
        elif tag == "th" and self._table_has_header:
            self._table_has_header[-1] = True
        elif tag in ("ul", "ol", "dl"):
            self.lists += 1
        elif tag == "script":
            self.scripts += 1
            script_type = attributes.get("type", "").lower()
            # Data blocks (JSON-LD, JSON, importmap, templates) are not executed
            # by the page and must not count as a JavaScript dependency.
            if script_type and ("json" in script_type or "template" in script_type):
                self.data_scripts += 1
            else:
                self.executable_scripts += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if re.fullmatch(r"h[1-6]", tag) and self._current_heading:
            self.headings.append(self._current_heading)
            self._current_heading = None
        elif tag == "a" and self._current_link:
            self.links.append(self._current_link)
            self._current_link = None
        elif tag == "button":
            if not (self._current_button or self._button_text.strip()):
                self.buttons_without_name += 1
            self._current_button = None
        elif tag == "table" and self._table_depth:
            self._table_depth -= 1
            if self._table_has_header and self._table_has_header.pop():
                self.tables_with_header += 1
        if tag in self._stack:
            while self._stack and self._stack.pop() != tag:
                continue

    def handle_data(self, data: str) -> None:
        if self._stack and self._stack[-1] == "script":
            self.inline_script_bytes += len(data)
            return
        if self._in_skip():
            return
        stripped = data.strip()
        if not stripped:
            return
        self.text_chars += len(stripped)
        if self._in_body():
            self.body_text_chars += len(stripped)
        if self._current_heading is not None:
            self._current_heading["text"] += stripped
        if self._current_link is not None:
            self._current_link["text"] += stripped
        if self._current_button is not None:
            self._button_text += stripped


def analyse(html: str) -> dict[str, Any]:
    parser = SemanticParser()
    parse_error = None
    try:
        parser.feed(html)
        parser.close()
    except Exception as exc:
        parse_error = str(exc)

    headings = parser.headings
    h1_count = sum(1 for h in headings if h["level"] == 1)
    skipped = []
    previous = 0
    for heading in headings:
        if previous and heading["level"] > previous + 1:
            skipped.append({"from": "h" + str(previous), "to": "h" + str(heading["level"]), "text": heading["text"][:60]})
        previous = heading["level"]

    empty_headings = [h for h in headings if not h["text"].strip()]
    generic = {"click here", "here", "read more", "more", "link", "this", "learn more"}
    non_descriptive = [
        link for link in parser.links
        if link["href"] and not link["aria_label"] and link["text"].strip().lower() in generic
    ]
    javascript_links = [link for link in parser.links if link["href"].startswith(("javascript:", "#")) and not link["text"].strip()]
    # Exact per-input resolution: a control is labelled by aria-label/title/
    # aria-labelledby, by a wrapping <label>, or by a label[for] pointing at its id.
    unlabelled_inputs = sum(
        1 for labelled, input_id in parser.input_records
        if not labelled and (input_id is None or input_id not in parser.labels_for)
    )

    markup_bytes = len(html)
    text_ratio = round(parser.text_chars / markup_bytes, 3) if markup_bytes else 0.0
    landmarks = {name: parser.tags.get(name, 0) for name in LANDMARKS}
    # A shell page: executable script present, almost no served text, and either
    # no heading structure at all or markup overwhelmingly dominated by script.
    js_dependent = (
        parser.executable_scripts > 0
        and parser.body_text_chars < 500
        and (len(headings) == 0 or text_ratio < 0.02)
    )

    issues = []
    if h1_count == 0:
        issues.append({"severity": "P1", "issue": "No h1 heading in the served HTML"})
    elif h1_count > 1:
        issues.append({"severity": "P2", "issue": str(h1_count) + " h1 headings; the primary topic is ambiguous"})
    if not landmarks["main"]:
        issues.append({"severity": "P2", "issue": "No <main> landmark to delimit primary content"})
    if skipped:
        issues.append({"severity": "P2", "issue": "Heading levels skip: " + ", ".join(s["from"] + "->" + s["to"] for s in skipped[:3])})
    if empty_headings:
        issues.append({"severity": "P2", "issue": str(len(empty_headings)) + " empty heading elements"})
    if js_dependent:
        issues.append({"severity": "P0", "issue": "Primary content appears to require JavaScript; agents that do not execute JS see an empty page"})
    if parser.images_without_alt:
        issues.append({"severity": "P2", "issue": str(parser.images_without_alt) + " images without an alt attribute"})
    if unlabelled_inputs:
        issues.append({"severity": "P2", "issue": str(unlabelled_inputs) + " form inputs without an associated label"})
    if parser.buttons_without_name:
        issues.append({"severity": "P2", "issue": str(parser.buttons_without_name) + " buttons without an accessible name"})
    if non_descriptive:
        issues.append({"severity": "P2", "issue": str(len(non_descriptive)) + " links with non-descriptive text"})
    if parser.tables and parser.tables > parser.tables_with_header:
        issues.append({"severity": "P3", "issue": "Tables without <th> header cells"})

    return {
        "parse_error": parse_error,
        "landmarks": landmarks,
        "heading_count": len(headings),
        "h1_count": h1_count,
        "heading_outline": [{"level": h["level"], "text": h["text"][:80]} for h in headings[:40]],
        "skipped_levels": skipped,
        "empty_headings": len(empty_headings),
        "links_total": len(parser.links),
        "links_non_descriptive": len(non_descriptive),
        "links_javascript_only": len(javascript_links),
        "images": parser.images,
        "images_without_alt": parser.images_without_alt,
        "inputs": parser.inputs,
        "inputs_without_label": unlabelled_inputs,
        "buttons_without_accessible_name": parser.buttons_without_name,
        "tables": parser.tables,
        "tables_with_header": parser.tables_with_header,
        "lists": parser.lists,
        "scripts": parser.scripts,
        "executable_scripts": parser.executable_scripts,
        "data_scripts": parser.data_scripts,
        "served_text_chars": parser.body_text_chars,
        "text_to_markup_ratio": text_ratio,
        "javascript_dependent_content": js_dependent,
        "issues": issues,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyse semantic HTML structure of a file or URL")
    parser.add_argument("source", help="Path to an HTML file or a URL")
    args = parser.parse_args()
    if args.source.startswith(("http://", "https://")):
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "aeo-agent-readiness" / "scripts"))
        from aeolib.fetch import fetch

        response = fetch(args.source)
        if not response.ok:
            raise SystemExit("Cannot fetch: HTTP " + str(response.status) + " " + (response.error or ""))
        html = response.text
    else:
        html = Path(args.source).read_text(encoding="utf-8", errors="replace")
    print(json.dumps(analyse(html), indent=2))


if __name__ == "__main__":
    main()
