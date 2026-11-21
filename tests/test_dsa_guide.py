"""Run the Python solutions and edge cases exactly as they appear in the guide."""

from html.parser import HTMLParser
from pathlib import Path

import pytest


class LessonReader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lessons = {}
        self.lesson = None
        self.block = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "article":
            self.lesson = self.lessons.setdefault(attrs["id"], {})
        if tag == "pre" and self.lesson is not None:
            self.block = attrs.get("class")
            self.lesson[self.block] = ""

    def handle_data(self, data):
        if self.block is not None:
            self.lesson[self.block] += data

    def handle_endtag(self, tag):
        if tag == "pre":
            self.block = None
        if tag == "article":
            self.lesson = None


guide = Path(__file__).resolve().parents[1] / "docs/dsa/index.html"
reader = LessonReader()
reader.feed(guide.read_text(encoding="utf-8"))
reader.close()


@pytest.mark.parametrize("lesson_id", reader.lessons)
def test_worked_example(lesson_id):
    blocks = reader.lessons[lesson_id]
    assert "assert " in blocks["checks"]
    source = blocks["solution"] + "\n" + blocks["checks"]
    exec(compile(source, f"{guide.name}#{lesson_id}", "exec"), {})
