"""Tests for the programmatic builder."""
from __future__ import annotations

import json
import unittest

from vn_builder import Choice, Scenario, build_demo_scenario


class BuilderTests(unittest.TestCase):
    def test_linear_links(self):
        s = Scenario(title="t")
        scene = s.scene()
        scene.say("a", node_id="a")
        scene.say("b", node_id="b")
        scene.end(node_id="end")

        nodes = {n["id"]: n for n in s.to_dict()["nodes"]}
        self.assertEqual(nodes["a"]["next"], "b")
        self.assertEqual(nodes["b"]["next"], "end")

    def test_choice_branching(self):
        s = Scenario(title="t")
        sc = s.scene()
        sc.say("Q", node_id="q")
        sc.choice(
            choices=[Choice("A", next="a"), Choice("B", next="b")],
            node_id="pick",
        )
        sc.say("after", node_id="a")
        sc.jump("end")
        side = s.scene()
        side.say("alt", node_id="b")
        side.jump("end")
        sc2 = s.scene()
        sc2.end(node_id="end")

        d = s.to_dict()
        nodes = {n["id"]: n for n in d["nodes"]}
        self.assertEqual(d["start"], "q")
        self.assertEqual(nodes["pick"]["choices"][0]["next"], "a")
        self.assertEqual(nodes["pick"]["choices"][1]["next"], "b")

    def test_validation_unknown_target(self):
        s = Scenario(title="t")
        sc = s.scene()
        sc.say("hi")
        sc.jump("nowhere")
        with self.assertRaises(ValueError):
            s.to_dict()

    def test_validation_unknown_character(self):
        s = Scenario(title="t")
        sc = s.scene()
        sc.say("hi", character="ghost")
        sc.end()
        with self.assertRaises(ValueError):
            s.to_dict()

    def test_demo_serialises(self):
        d = build_demo_scenario()
        # Must be json-serialisable and valid.
        s = json.dumps(d)
        self.assertIn("nodes", s)
        self.assertEqual(d["version"], "1.0")
        ids = {n["id"] for n in d["nodes"]}
        self.assertIn(d["start"], ids)


if __name__ == "__main__":
    unittest.main()
