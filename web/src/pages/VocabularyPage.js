import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { novels as novelsApi, vocabulary as vocabApi } from "@api/client";

const LEVEL_COLORS = { B1: "#4caf91", B2: "#4c8faf", C1: "#8f4caf" };

export default function VocabularyPage() {
    const { id } = useParams();
    const [novel, setNovel] = useState(null);
    const [words, setWords] = useState([]);
    const [filterLevel, setFilterLevel] = useState("");
    const [filterLearned, setFilterLearned] = useState("all"); // all | learned | unlearned
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            setLoading(true);
            try {
                const [novelData, vocabData] = await Promise.all([
                    novelsApi.get(id),
                    vocabApi.list(id),
                ]);
                if (!cancelled) {
                    setNovel(novelData);
                    setWords(vocabData);
                }
            } catch (_) {
                if (!cancelled) setError("Failed to load vocabulary.");
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => { cancelled = true; };
    }, [id]);

    const handleLearn = async (wordId) => {
        try {
            await vocabApi.learn(wordId);
            setWords((prev) =>
                prev.map((w) => (w.id === wordId ? { ...w, is_learned: true } : w))
            );
        } catch (_) {}
    };

    const handleForget = async (wordId) => {
        try {
            await vocabApi.forget(wordId);
            setWords((prev) =>
                prev.map((w) => (w.id === wordId ? { ...w, is_learned: false } : w))
            );
        } catch (_) {}
    };

    const filtered = words.filter((w) => {
        if (filterLevel && w.level !== filterLevel) return false;
        if (filterLearned === "learned" && !w.is_learned) return false;
        if (filterLearned === "unlearned" && w.is_learned) return false;
        if (search) {
            const q = search.toLowerCase();
            return (
                w.word.toLowerCase().includes(q) ||
                w.translation.toLowerCase().includes(q)
            );
        }
        return true;
    });

    const learnedCount = words.filter((w) => w.is_learned).length;

    if (loading) return <div className="page-status">Loading…</div>;
    if (error) return <p className="page-status">{error}</p>;

    return (
        <main className="vocab-page">
            <div className="vocab-page-header">
                <Link to={`/novel/${id}`} className="back-link">
                    ← {novel?.title || "Novel"}
                </Link>
                <h1>Vocabulary</h1>
                <p className="vocab-progress-summary muted">
                    {learnedCount} / {words.length} words learned
                </p>
            </div>

            {words.length > 0 ? (
                <div className="vocab-progress-bar-wrap">
                    <div
                        className="progress-bar-fill"
                        style={{
                            width: `${words.length ? (learnedCount / words.length) * 100 : 0}%`,
                        }}
                    />
                </div>
            ) : null}

            <div className="vocab-filters">
                <input
                    type="search"
                    className="vocab-search"
                    placeholder="Search words…"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
                <div className="filter-chips">
                    {["", "B1", "B2", "C1"].map((lvl) => (
                        <button
                            key={lvl || "all"}
                            type="button"
                            className={`filter-chip ${filterLevel === lvl ? "active" : ""}`}
                            onClick={() => setFilterLevel(lvl)}
                        >
                            {lvl || "All"}
                        </button>
                    ))}
                </div>
                <div className="filter-chips">
                    {[
                        { key: "all", label: "All" },
                        { key: "unlearned", label: "To learn" },
                        { key: "learned", label: "Learned" },
                    ].map((f) => (
                        <button
                            key={f.key}
                            type="button"
                            className={`filter-chip ${filterLearned === f.key ? "active" : ""}`}
                            onClick={() => setFilterLearned(f.key)}
                        >
                            {f.label}
                        </button>
                    ))}
                </div>
            </div>

            {filtered.length === 0 ? (
                <p className="page-status empty-state">No words match your filters.</p>
            ) : (
                <ul className="vocab-list">
                    {filtered.map((w) => (
                        <li
                            key={w.id}
                            className={`vocab-item ${w.is_learned ? "learned" : ""}`}
                        >
                            <div className="vocab-item-main">
                                <div className="vocab-item-word">
                                    {w.word}
                                    {w.transcription ? (
                                        <span className="vocab-transcription">
                                            [{w.transcription}]
                                        </span>
                                    ) : null}
                                    <span
                                        className="level-badge-sm"
                                        style={{ background: LEVEL_COLORS[w.level] }}
                                    >
                                        {w.level}
                                    </span>
                                </div>
                                <div className="vocab-item-translation">
                                    {w.translation}
                                </div>
                                {w.definition ? (
                                    <div className="vocab-item-definition muted">
                                        {w.definition}
                                    </div>
                                ) : null}
                                {w.example ? (
                                    <div className="vocab-item-example">
                                        <em>{w.example}</em>
                                    </div>
                                ) : null}
                            </div>
                            <div className="vocab-item-actions">
                                {w.is_learned ? (
                                    <button
                                        type="button"
                                        className="vocab-learned-btn active"
                                        onClick={() => handleForget(w.id)}
                                        title="Mark as unlearned"
                                    >
                                        ✓ Learned
                                    </button>
                                ) : (
                                    <button
                                        type="button"
                                        className="vocab-learn-btn"
                                        onClick={() => handleLearn(w.id)}
                                    >
                                        + Learn
                                    </button>
                                )}
                            </div>
                        </li>
                    ))}
                </ul>
            )}
        </main>
    );
}
