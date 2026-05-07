/* eslint-disable no-console */
const assert = require("assert");
const { Scenario } = require("./vn-builder");

function testLinear() {
    const s = new Scenario({ title: "t" });
    const sc = s.scene();
    sc.say("a", { nodeId: "a" });
    sc.say("b", { nodeId: "b" });
    sc.end({ nodeId: "end" });
    const data = s.toJSON();
    const m = Object.fromEntries(data.nodes.map((n) => [n.id, n]));
    assert.equal(m.a.next, "b");
    assert.equal(m.b.next, "end");
}

function testChoice() {
    const s = new Scenario({ title: "t" });
    const sc = s.scene();
    sc.say("Q", { nodeId: "q" });
    sc.choice(
        [
            { text: "A", next: "a" },
            { text: "B", next: "b" },
        ],
        { nodeId: "pick" },
    );
    sc.say("after", { nodeId: "a" });
    sc.jump("end");
    s.scene().say("alt", { nodeId: "b" }).b; // chain access valid
    s.scene().jump("end");
    s.scene().end({ nodeId: "end" });

    const d = s.toJSON();
    const m = Object.fromEntries(d.nodes.map((n) => [n.id, n]));
    assert.equal(d.start, "q");
    assert.equal(m.pick.choices[0].next, "a");
    assert.equal(m.pick.choices[1].next, "b");
}

function testValidation() {
    const s = new Scenario({ title: "t" });
    const sc = s.scene();
    sc.say("hi");
    sc.jump("nowhere");
    let threw = false;
    try {
        s.toJSON();
    } catch (e) {
        threw = true;
    }
    assert.ok(threw, "expected validation to fail");
}

testLinear();
testChoice();
testValidation();
console.log("vn-builder.js: all tests OK");
