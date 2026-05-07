"""Programmatic builder for visual-novel scenarios.

The builder produces a JSON document that the web runtime understands.
The output format intentionally mirrors the data model in
``web/src/vn/runtime.js`` and is also compatible with the documentation
of the tuesday.js engine (it can be used as a "kinetic novel" script
by ignoring the choice nodes).

Schema (top level)::

    {
      "version": "1.0",
      "meta":   {"title": str, "language": str, "level": "B1|B2|C1"?},
      "assets": {
        "characters":  {char_id: {"name": str, "image": url}},
        "backgrounds": {bg_id:   {"image": url}},
        "music":       {m_id:    {"file":  url}}
      },
      "start": node_id,
      "nodes": [Node, ...]
    }

Node types::

    {"id": ..., "type": "say",      "character": char_id?,
     "text": str, "position": "left|right|center"?,
     "background": bg_id?, "music": m_id?, "next": node_id}

    {"id": ..., "type": "choice",   "prompt": str?,
     "choices": [{"text": str, "next": node_id, "set": {var: val}?}]}

    {"id": ..., "type": "set",      "vars": {var: val}, "next": node_id}

    {"id": ..., "type": "if",       "var": str,
     "equals": value, "then": node_id, "else": node_id}

    {"id": ..., "type": "jump",     "next": node_id}

    {"id": ..., "type": "end"}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

NodeDict = dict[str, Any]


@dataclass
class Scene:
    """Lightweight grouping helper used by the fluent API."""

    builder: "Scenario"
    last_node_id: str | None = None
    background: str | None = None
    music: str | None = None

    def say(
        self,
        text: str,
        *,
        character: str | None = None,
        position: str | None = None,
        node_id: str | None = None,
    ) -> "Scene":
        node = self.builder._mk_node("say", node_id)
        node.update({"text": text})
        if character:
            node["character"] = character
        if position:
            node["position"] = position
        if self.background:
            node["background"] = self.background
        if self.music:
            node["music"] = self.music
        self.builder._append(node, prev_node_id=self.last_node_id)
        self.last_node_id = node["id"]
        return self

    def choice(
        self,
        choices: Iterable["Choice"],
        *,
        prompt: str | None = None,
        node_id: str | None = None,
    ) -> str:
        node = self.builder._mk_node("choice", node_id)
        if prompt:
            node["prompt"] = prompt
        node["choices"] = [c.to_dict() for c in choices]
        self.builder._append(node, prev_node_id=self.last_node_id)
        self.last_node_id = node["id"]
        return node["id"]

    def set_var(self, vars: dict[str, Any], *, node_id: str | None = None) -> "Scene":
        node = self.builder._mk_node("set", node_id)
        node["vars"] = vars
        self.builder._append(node, prev_node_id=self.last_node_id)
        self.last_node_id = node["id"]
        return self

    def jump(self, target: str) -> None:
        node = self.builder._mk_node("jump")
        node["next"] = target
        self.builder._append(node, prev_node_id=self.last_node_id)
        self.last_node_id = node["id"]

    def end(self, *, node_id: str | None = None) -> None:
        node = self.builder._mk_node("end", node_id)
        self.builder._append(node, prev_node_id=self.last_node_id)
        self.last_node_id = node["id"]


@dataclass
class Choice:
    text: str
    next: str
    set: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"text": self.text, "next": self.next}
        if self.set:
            result["set"] = self.set
        return result


@dataclass
class Scenario:
    title: str
    language: str = "en"
    level: str | None = None
    _nodes: list[NodeDict] = field(default_factory=list)
    _by_id: dict[str, NodeDict] = field(default_factory=dict)
    _id_counter: int = 0
    _start: str | None = None
    characters: dict[str, dict[str, str]] = field(default_factory=dict)
    backgrounds: dict[str, dict[str, str]] = field(default_factory=dict)
    music: dict[str, dict[str, str]] = field(default_factory=dict)

    # ----- assets -------------------------------------------------------
    def character(self, char_id: str, *, name: str, image: str) -> str:
        self.characters[char_id] = {"name": name, "image": image}
        return char_id

    def background(self, bg_id: str, *, image: str) -> str:
        self.backgrounds[bg_id] = {"image": image}
        return bg_id

    def track(self, music_id: str, *, file: str) -> str:
        self.music[music_id] = {"file": file}
        return music_id

    # ----- node construction -------------------------------------------
    def _mk_node(self, node_type: str, node_id: str | None = None) -> NodeDict:
        if node_id is None:
            self._id_counter += 1
            node_id = f"n{self._id_counter}"
        if node_id in self._by_id:
            raise ValueError(f"Duplicate node id: {node_id!r}")
        node: NodeDict = {"id": node_id, "type": node_type}
        return node

    def _append(self, node: NodeDict, *, prev_node_id: str | None) -> None:
        self._nodes.append(node)
        self._by_id[node["id"]] = node
        if self._start is None:
            self._start = node["id"]
        if prev_node_id is not None:
            prev = self._by_id[prev_node_id]
            # Linear nodes get an implicit "next" pointer.
            if prev["type"] in {"say", "set"} and "next" not in prev:
                prev["next"] = node["id"]

    def scene(
        self, *, background: str | None = None, music: str | None = None
    ) -> Scene:
        if background is not None and background not in self.backgrounds:
            raise KeyError(f"Unknown background: {background!r}")
        if music is not None and music not in self.music:
            raise KeyError(f"Unknown music track: {music!r}")
        return Scene(
            builder=self,
            last_node_id=self._nodes[-1]["id"] if self._nodes else None,
            background=background,
            music=music,
        )

    # ----- export & validation -----------------------------------------
    def to_dict(self) -> dict[str, Any]:
        if self._start is None:
            raise ValueError("Scenario has no nodes; nothing to export.")
        self.validate()
        meta: dict[str, Any] = {"title": self.title, "language": self.language}
        if self.level:
            meta["level"] = self.level
        return {
            "version": "1.0",
            "meta": meta,
            "assets": {
                "characters": self.characters,
                "backgrounds": self.backgrounds,
                "music": self.music,
            },
            "start": self._start,
            "nodes": self._nodes,
        }

    def validate(self) -> None:
        ids = self._by_id
        for node in self._nodes:
            t = node["type"]
            for ref_field in ("next", "then", "else"):
                if ref_field in node and node[ref_field] not in ids:
                    raise ValueError(
                        f"Node {node['id']!r} references unknown id "
                        f"{node[ref_field]!r}"
                    )
            if t == "choice":
                for ch in node.get("choices", []):
                    if ch["next"] not in ids:
                        raise ValueError(
                            f"Choice in {node['id']!r} points to unknown id "
                            f"{ch['next']!r}"
                        )
            char = node.get("character")
            if char and char not in self.characters:
                raise ValueError(f"Unknown character {char!r} in {node['id']!r}")
            bg = node.get("background")
            if bg and bg not in self.backgrounds:
                raise ValueError(f"Unknown background {bg!r} in {node['id']!r}")
            mus = node.get("music")
            if mus and mus not in self.music:
                raise ValueError(f"Unknown music {mus!r} in {node['id']!r}")


# ---------------------------------------------------------------------------
# Demo scenario used by `manage.py seed_demo` and the JS docs example.
# ---------------------------------------------------------------------------
def build_demo_scenario() -> dict[str, Any]:
    s = Scenario(title="A Walk Through Tokyo", language="en", level="B1")

    s.character("yuki", name="Yuki", image="/static/demo/yuki.png")
    s.character("ren", name="Ren", image="/static/demo/ren.png")
    s.background("street", image="/static/demo/street.jpg")
    s.background("cafe", image="/static/demo/cafe.jpg")
    s.track("calm", file="/static/demo/calm.mp3")

    intro = s.scene(background="street", music="calm")
    intro.say("It is a bright Saturday morning in Akihabara.", node_id="intro")
    intro.say("Hi! Are you new here?", character="yuki", position="left")
    pick = intro.choice(
        prompt="How do you reply?",
        choices=[
            Choice(text="Yes, just arrived.", next="say_yes"),
            Choice(text="No, I live nearby.", next="say_no"),
        ],
        node_id="first_choice",
    )

    yes_branch = s.scene(background="cafe", music="calm")
    yes_branch.say(
        "Welcome! Let me show you a small cafe I love.",
        character="yuki",
        position="left",
        node_id="say_yes",
    )
    yes_branch.say("Ren joins them at the table.", node_id="say_yes_2")
    yes_branch.say("Nice to meet you both.", character="ren", position="right")
    yes_branch.jump("ending")

    no_branch = s.scene(background="street")
    no_branch.say(
        "Oh, then maybe you can recommend a cafe!",
        character="yuki",
        position="left",
        node_id="say_no",
    )
    no_branch.jump("ending")

    end_scene = s.scene(background="cafe", music="calm")
    end_scene.say("They share a quiet afternoon together.", node_id="ending")
    end_scene.end(node_id="end")

    # Reference variables to silence unused warnings.
    _ = pick
    return s.to_dict()


if __name__ == "__main__":
    import json
    print(json.dumps(build_demo_scenario(), indent=2, ensure_ascii=False))
