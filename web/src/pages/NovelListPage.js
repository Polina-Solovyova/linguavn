import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { novels as novelsApi } from "@api/client";
import { useUser } from "@providers/UserProvider";

const LEVEL_COLORS = { B1: "#4caf91", B2: "#4c8faf", C1: "#8f4caf" };

export default function NovelListPage() {
    const { user } = useUser();
    const [items, setItems] = useState([]);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);
    const [filterLevel, setFilterLevel] = useState("");
    const [filterGenre, setFilterGenre] = useState("");

    useEffect(() => {
        let cancelled = false;
        (async () => {
            setLoading(true);
            try {
                const params = {};
                if (filterLevel) params.level = filterLevel;
                if (filterGenre) params.genre = filterGenre;
                const data = await novelsApi.list(params);
                if (!cancelled) setItems(data);
            } catch (_) {
                if (!cancelled) setError("Failed to load novels.");
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => { cancelled = true; };
    }, [filterLevel, filterGenre]);

    const userLevel = user?.profile?.language_level;

    const genres = [...new Set(items.map((n) => n.genre).filter(Boolean))];

    return (
        <main className="library">
            <div className="library-header">
                <h1>Library</h1>
                {userLevel ? (
                    <span
                        className="level-badge"
                        style={{ background: LEVEL_COLORS[userLevel] }}
                    >
                        Your level: {userLevel}
                    </span>
                ) : null}
            </div>

            <div className="library-filters">
                <div className="filter-group">
                    <span className="filter-label">Level</span>
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
                </div>
                {genres.length > 0 ? (
                    <div className="filter-group">
                        <span className="filter-label">Genre</span>
                        <div className="filter-chips">
                            <button
                                type="button"
                                className={`filter-chip ${filterGenre === "" ? "active" : ""}`}
                                onClick={() => setFilterGenre("")}
                            >
                                All
                            </button>
                            {genres.map((g) => (
                                <button
                                    key={g}
                                    type="button"
                                    className={`filter-chip ${filterGenre === g ? "active" : ""}`}
                                    onClick={() => setFilterGenre(g)}
                                >
                                    {g}
                                </button>
                            ))}
                        </div>
                    </div>
                ) : null}
            </div>

            {loading ? (
                <p className="page-status">Loading…</p>
            ) : error ? (
                <p className="page-status">{error}</p>
            ) : items.length === 0 ? (
                <p className="page-status empty-state">No novels found.</p>
            ) : (
                <div className="novel-grid">
                    {items.map((novel) => (
                        <Link
                            key={novel.id}
                            to={`/novel/${novel.id}`}
                            className="novel-card"
                        >
                            {novel.cover_image ? (
                                <img src={novel.cover_image} alt={novel.title} />
                            ) : (
                                <div className="novel-cover-placeholder">
                                    {novel.title}
                                </div>
                            )}
                            <div className="novel-card-body">
                                <div className="novel-card-badges">
                                    {novel.language_level ? (
                                        <span
                                            className="level-badge-sm"
                                            style={{
                                                background:
                                                    LEVEL_COLORS[novel.language_level],
                                            }}
                                        >
                                            {novel.language_level}
                                        </span>
                                    ) : null}
                                    {novel.genre ? (
                                        <span className="genre-badge">{novel.genre}</span>
                                    ) : null}
                                </div>
                                <h3>{novel.title}</h3>
                                <p>{novel.description}</p>
                                <div className="novel-card-meta">
                                    {novel.estimated_minutes ? (
                                        <span>~{novel.estimated_minutes} min</span>
                                    ) : null}
                                    {novel.vocabulary_count > 0 ? (
                                        <span>{novel.vocabulary_count} words</span>
                                    ) : null}
                                    {novel.quiz_count > 0 ? (
                                        <span>{novel.quiz_count} quiz</span>
                                    ) : null}
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </main>
    );
}
