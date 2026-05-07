/**
 * Visual-novel runtime.
 *
 * Pure data, no DOM. The runtime walks a scenario graph (see the
 * builders in vn-builder/) and exposes the current "frame" plus a
 * minimal set of commands: advance() and pickChoice(index).
 *
 * The runtime is fully serialisable: getState() / loadState(state)
 * round-trip through JSON, which is what the backend stores in
 * UserProgress.state_snapshot.
 */

export const NODE_TYPES = Object.freeze({
    SAY: "say",
    CHOICE: "choice",
    SET: "set",
    IF: "if",
    JUMP: "jump",
    END: "end",
});

export class ScenarioError extends Error {}

export class VisualNovelRuntime {
    constructor(scenario) {
        this._scenario = validateScenario(scenario);
        this._byId = new Map(scenario.nodes.map((n) => [n.id, n]));
        this._currentId = scenario.start;
        this._vars = {};
        this._visited = [];
        this._totalNodes = scenario.nodes.length;

        this._currentId = this._fastForward(this._currentId);
        this._touch(this._currentId);
    }

    get scenario() { return this._scenario; }
    get currentNode() { return this._byId.get(this._currentId) || null; }
    get isFinished() {
        const node = this.currentNode;
        return !node || node.type === NODE_TYPES.END;
    }
    get progressPercent() {
        if (this.isFinished) return 100;
        if (this._totalNodes === 0) return 0;
        const seen = new Set(this._visited).size;
        return Math.min(99, Math.round((seen / this._totalNodes) * 100));
    }
    get vars() { return { ...this._vars }; }
    get visitedNodes() { return [...this._visited]; }

    get currentFrame() {
        const node = this.currentNode;
        if (!node) return null;
        const assets = this._scenario.assets || {};
        const characters = assets.characters || {};
        const backgrounds = assets.backgrounds || {};
        const music = assets.music || {};

        const character = node.character ? characters[node.character] : null;
        const background = node.background ? backgrounds[node.background] : null;
        const track = node.music ? music[node.music] : null;

        return {
            id: node.id,
            type: node.type,
            text: node.text || null,
            prompt: node.prompt || null,
            position: node.position || "center",
            character: character ? { id: node.character, ...character } : null,
            background: background ? { id: node.background, ...background } : null,
            music: track ? { id: node.music, ...track } : null,
            choices: node.type === NODE_TYPES.CHOICE
                ? (node.choices || []).map((c, idx) => ({ index: idx, text: c.text }))
                : [],
            isFinished: node.type === NODE_TYPES.END,
        };
    }

    advance() {
        const node = this.currentNode;
        if (!node) throw new ScenarioError("No current node.");
        if (node.type === NODE_TYPES.CHOICE) {
            throw new ScenarioError("Cannot advance: current node expects a choice.");
        }
        if (node.type === NODE_TYPES.END) return;

        const nextId = node.next;
        if (!nextId) { this._currentId = null; return; }
        this._currentId = this._fastForward(nextId);
        this._touch(this._currentId);
    }

    pickChoice(index) {
        const node = this.currentNode;
        if (!node || node.type !== NODE_TYPES.CHOICE) {
            throw new ScenarioError("No choice at the current node.");
        }
        const choice = (node.choices || [])[index];
        if (!choice) throw new ScenarioError(`Invalid choice index: ${index}`);
        if (choice.set) Object.assign(this._vars, choice.set);
        this._currentId = this._fastForward(choice.next);
        this._touch(this._currentId);
    }

    reset() {
        this._currentId = this._scenario.start;
        this._vars = {};
        this._visited = [];
        this._currentId = this._fastForward(this._currentId);
        this._touch(this._currentId);
    }

    getState() {
        return {
            current_node_id: this._currentId,
            state_snapshot: { vars: { ...this._vars } },
            visited_nodes: [...this._visited],
            is_completed: this.isFinished,
            progress_percent: this.progressPercent,
        };
    }

    loadState(state) {
        if (!state || typeof state !== "object") return;
        if (state.current_node_id && this._byId.has(state.current_node_id)) {
            this._currentId = state.current_node_id;
        }
        if (Array.isArray(state.visited_nodes)) {
            this._visited = state.visited_nodes.filter((id) => this._byId.has(id));
        }
        const snap = state.state_snapshot;
        if (snap && typeof snap === "object" && snap.vars && typeof snap.vars === "object") {
            this._vars = { ...snap.vars };
        }
    }

    _touch(id) {
        if (id && !this._visited.includes(id)) this._visited.push(id);
    }

    _fastForward(id) {
        const guard = new Set();
        while (id) {
            if (guard.has(id)) {
                throw new ScenarioError(`Detected a cycle in passive nodes near ${id}`);
            }
            guard.add(id);
            const node = this._byId.get(id);
            if (!node) {
                throw new ScenarioError(`Unknown node id: ${id}`);
            }
            this._touch(id);
            switch (node.type) {
                case NODE_TYPES.SET:
                    if (node.vars) Object.assign(this._vars, node.vars);
                    if (!node.next) return id;
                    id = node.next;
                    break;
                case NODE_TYPES.JUMP:
                    if (!node.next) return id;
                    id = node.next;
                    break;
                case NODE_TYPES.IF: {
                    const left = this._vars[node.var];
                    const branch = left === node.equals ? node.then : node.else;
                    if (!branch) return id;
                    id = branch;
                    break;
                }
                default:
                    return id;
            }
        }
        return id;
    }
}

function validateScenario(scenario) {
    if (!scenario || typeof scenario !== "object") {
        throw new ScenarioError("Scenario must be an object.");
    }
    if (!Array.isArray(scenario.nodes) || scenario.nodes.length === 0) {
        throw new ScenarioError("Scenario must contain a non-empty `nodes` array.");
    }
    if (!scenario.start || typeof scenario.start !== "string") {
        throw new ScenarioError("Scenario must declare a `start` node id.");
    }
    const ids = new Set();
    for (const n of scenario.nodes) {
        if (!n || typeof n !== "object") {
            throw new ScenarioError("Every node must be an object.");
        }
        if (!n.id || typeof n.id !== "string") {
            throw new ScenarioError("Every node must have a string `id`.");
        }
        if (ids.has(n.id)) {
            throw new ScenarioError(`Duplicate node id: ${n.id}`);
        }
        ids.add(n.id);
    }
    if (!ids.has(scenario.start)) {
        throw new ScenarioError(`Start node ${scenario.start} not found.`);
    }
    return scenario;
}
