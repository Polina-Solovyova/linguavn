/**
 * JavaScript mirror of the Python builder.
 *
 * Same scenario schema, same node types. Use this when authoring novels
 * directly in the web client (e.g. for in-browser playgrounds) or in
 * Node.js build pipelines that emit JSON files for the runtime.
 */

const SAY = "say";
const CHOICE = "choice";
const SET = "set";
const IF = "if";
const JUMP = "jump";
const END = "end";

class Scenario {
    constructor({ title, language = "en", level } = {}) {
        if (!title) throw new Error("Scenario requires a title.");
        this.title = title;
        this.language = language;
        this.level = level || null;
        this.nodes = [];
        this.byId = new Map();
        this.idCounter = 0;
        this.startId = null;
        this.characters = {};
        this.backgrounds = {};
        this.music = {};
    }

    character(id, { name, image }) {
        this.characters[id] = { name, image };
        return id;
    }

    background(id, { image }) {
        this.backgrounds[id] = { image };
        return id;
    }

    track(id, { file }) {
        this.music[id] = { file };
        return id;
    }

    scene({ background = null, music = null } = {}) {
        if (background !== null && !(background in this.backgrounds)) {
            throw new Error(`Unknown background: ${background}`);
        }
        if (music !== null && !(music in this.music)) {
            throw new Error(`Unknown music: ${music}`);
        }
        return new Scene(this, { background, music });
    }

    _allocId(explicit) {
        if (explicit) {
            if (this.byId.has(explicit)) {
                throw new Error(`Duplicate node id: ${explicit}`);
            }
            return explicit;
        }
        this.idCounter += 1;
        let id;
        do {
            id = `n${this.idCounter}`;
            this.idCounter += 1;
        } while (this.byId.has(id));
        return id;
    }

    _append(node, prevId) {
        this.nodes.push(node);
        this.byId.set(node.id, node);
        if (this.startId === null) this.startId = node.id;
        if (prevId !== null && prevId !== undefined) {
            const prev = this.byId.get(prevId);
            if (prev && (prev.type === SAY || prev.type === SET) && !("next" in prev)) {
                prev.next = node.id;
            }
        }
    }

    validate() {
        for (const node of this.nodes) {
            for (const f of ["next", "then", "else"]) {
                if (f in node && !this.byId.has(node[f])) {
                    throw new Error(`Node ${node.id} references unknown id ${node[f]}`);
                }
            }
            if (node.type === CHOICE) {
                for (const c of node.choices || []) {
                    if (!this.byId.has(c.next)) {
                        throw new Error(`Choice in ${node.id} points to unknown id ${c.next}`);
                    }
                }
            }
            if (node.character && !(node.character in this.characters)) {
                throw new Error(`Unknown character ${node.character} in ${node.id}`);
            }
            if (node.background && !(node.background in this.backgrounds)) {
                throw new Error(`Unknown background ${node.background} in ${node.id}`);
            }
            if (node.music && !(node.music in this.music)) {
                throw new Error(`Unknown music ${node.music} in ${node.id}`);
            }
        }
    }

    toJSON() {
        if (!this.startId) throw new Error("Scenario has no nodes.");
        this.validate();
        const meta = { title: this.title, language: this.language };
        if (this.level) meta.level = this.level;
        return {
            version: "1.0",
            meta,
            assets: {
                characters: this.characters,
                backgrounds: this.backgrounds,
                music: this.music,
            },
            start: this.startId,
            nodes: this.nodes,
        };
    }
}

class Scene {
    constructor(builder, { background, music }) {
        this.b = builder;
        this.last = builder.nodes.length
            ? builder.nodes[builder.nodes.length - 1].id
            : null;
        this.background = background;
        this.music = music;
    }

    say(text, opts = {}) {
        const { character = null, position = null, nodeId = null } = opts;
        const node = { id: this.b._allocId(nodeId), type: SAY, text };
        if (character) node.character = character;
        if (position) node.position = position;
        if (this.background) node.background = this.background;
        if (this.music) node.music = this.music;
        this.b._append(node, this.last);
        this.last = node.id;
        return this;
    }

    choice(choices, opts = {}) {
        const { prompt = null, nodeId = null } = opts;
        const node = { id: this.b._allocId(nodeId), type: CHOICE };
        if (prompt) node.prompt = prompt;
        node.choices = choices.map((c) => ({
            text: c.text,
            next: c.next,
            ...(c.set ? { set: c.set } : {}),
        }));
        this.b._append(node, this.last);
        this.last = node.id;
        return node.id;
    }

    setVar(vars, opts = {}) {
        const { nodeId = null } = opts;
        const node = { id: this.b._allocId(nodeId), type: SET, vars };
        this.b._append(node, this.last);
        this.last = node.id;
        return this;
    }

    jump(target) {
        const node = { id: this.b._allocId(null), type: JUMP, next: target };
        this.b._append(node, this.last);
        this.last = node.id;
    }

    end(opts = {}) {
        const { nodeId = null } = opts;
        const node = { id: this.b._allocId(nodeId), type: END };
        this.b._append(node, this.last);
        this.last = node.id;
    }
}

module.exports = { Scenario, Scene };
