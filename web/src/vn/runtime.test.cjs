/* Tiny CommonJS test (runs with `node runtime.test.cjs`).
 * Translates the ESM runtime into CJS via a temporary .cjs file. */
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const os = require("os");

const src = fs
    .readFileSync(path.join(__dirname, "runtime.js"), "utf-8")
    .replace(/export const NODE_TYPES/g, "const NODE_TYPES")
    .replace(/export class ScenarioError/g, "class ScenarioError")
    .replace(/export class VisualNovelRuntime/g, "class VisualNovelRuntime");

const tmp = path.join(os.tmpdir(), `vn_runtime_${process.pid}.cjs`);
fs.writeFileSync(
    tmp,
    `${src}\nmodule.exports = { NODE_TYPES, ScenarioError, VisualNovelRuntime };\n`,
);
const { VisualNovelRuntime } = require(tmp);
fs.unlinkSync(tmp);

function makeScenario() {
    return {
        version: "1.0",
        meta: { title: "T" },
        assets: {
            characters: { y: { name: "Yuki", image: "/y.png" } },
            backgrounds: { s: { image: "/s.jpg" } },
            music: {},
        },
        start: "intro",
        nodes: [
            { id: "intro", type: "say", text: "Hi", character: "y", background: "s", next: "pick" },
            {
                id: "pick",
                type: "choice",
                choices: [
                    { text: "Yes", next: "yes" },
                    { text: "No", next: "no", set: { polite: false } },
                ],
            },
            { id: "yes", type: "say", text: "Great", next: "end" },
            { id: "no", type: "say", text: "Okay", next: "end" },
            { id: "end", type: "end" },
        ],
    };
}

// Linear advance.
{
    const r = new VisualNovelRuntime(makeScenario());
    assert.equal(r.currentFrame.text, "Hi");
    assert.equal(r.currentFrame.character.name, "Yuki");
    assert.equal(r.currentFrame.background.image, "/s.jpg");
    r.advance();
    assert.equal(r.currentFrame.type, "choice");
    assert.equal(r.currentFrame.choices.length, 2);
}

// Choice + variable side effect.
{
    const r = new VisualNovelRuntime(makeScenario());
    r.advance();
    r.pickChoice(1);
    assert.equal(r.vars.polite, false);
    assert.equal(r.currentFrame.text, "Okay");
    r.advance();
    assert.equal(r.isFinished, true);
    assert.equal(r.progressPercent, 100);
}

// Persistence round-trip.
{
    const r = new VisualNovelRuntime(makeScenario());
    r.advance();
    r.pickChoice(0);
    const snap = r.getState();
    const r2 = new VisualNovelRuntime(makeScenario());
    r2.loadState(snap);
    assert.equal(r2.currentFrame.text, "Great");
    assert.deepEqual(r2.visitedNodes, snap.visited_nodes);
}

console.log("runtime.js: all tests OK");
