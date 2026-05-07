"""End-to-end example: build a small branching novel with Python and
write the JSON file the runtime understands.

Run from repository root::

    python examples/my_first_novel.py > examples/my_first_novel.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vn-builder" / "python"))

from vn_builder import Choice, Scenario  # noqa: E402


def build() -> dict:
    s = Scenario(title="My First Novel", language="en", level="B1")

    s.character("ann", name="Ann", image="/media/demo/ann.png")
    s.background("park", image="/media/demo/park.jpg")
    s.background("home", image="/media/demo/home.jpg")

    intro = s.scene(background="park")
    intro.say("A quiet afternoon in the park.", node_id="intro")
    intro.say("Hi, are you waiting for someone?", character="ann", position="left")
    intro.choice(
        prompt="What do you say?",
        choices=[
            Choice("Yes, my friend.", next="path_yes"),
            Choice("No, just resting.", next="path_no"),
        ],
        node_id="pick",
    )

    s.scene(background="park").say(
        "Then I will leave you to it.", character="ann", node_id="path_yes"
    ).jump("end")

    s.scene(background="home").say(
        "May I sit here for a moment?", character="ann", node_id="path_no"
    ).jump("end")

    s.scene().end(node_id="end")
    return s.to_dict()


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
