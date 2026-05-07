import React, { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { novels as novelsApi, quiz as quizApi } from "@api/client";

const LEVEL_COLORS = { B1: "#4caf91", B2: "#4c8faf", C1: "#8f4caf" };

export default function NovelDetailPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [novel, setNovel] = useState(null);
    const [progress, setProgress] = useState(null);
    const [quizzes, setQuizzes] = useState([]);
    const [error, setError] = useState(null);
    const [resetting, setResetting] = useState(false);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const [novelData, progressData, quizData] = await Promise.all([
                    novelsApi.get(id),
                    novelsApi.progress(id),
                    quizApi.listForNovel(id).catch(() => []),
                ]);
                if (!cancelled) {
                    setNovel(novelData);
                    setProgress(progressData);
                    setQuizzes(quizData);
                }
            } catch (_) {
                if (!cancelled) setError("Failed to load novel.");
            }
        })();
        return () => { cancelled = true; };
    }, [id]);

    if (error) return <p className="page-status">{error}</p>;
    if (!novel) return <p className="page-status">Loading…</p>;

    const isCompleted = Boolean(progress?.is_completed);
    const hasProgress = (progress?.progress_percent || 0) > 0;

    const handleReset = async () => {
        setResetting(true);
        try {
            await novelsApi.resetProgress(id);
            const fresh = await novelsApi.progress(id);
            setProgress(fresh);
        } finally {
            setResetting(false);
        }
    };

    return (
        <main className="novel-detail">
            <Link to="/" className="back-link">← Back to library</Link>

            <article className="novel-detail-article">
                <div className="novel-detail-cover">
                    {novel.cover_image ? (
                        <img
                            src={novel.cover_image}
                            alt={novel.title}
                            className="novel-cover"
                        />
                    ) : (
                        <div className="novel-cover novel-cover-placeholder">
                            {novel.title}
                        </div>
                    )}
                    <div className="novel-cover-badges">
                        {novel.language_level ? (
                            <span
                                className="level-badge"
                                style={{ background: LEVEL_COLORS[novel.language_level] }}
                            >
                                {novel.language_level}
                            </span>
                        ) : null}
                        {novel.genre ? (
                            <span className="genre-badge">{novel.genre}</span>
                        ) : null}
                    </div>
                </div>

                <div className="novel-detail-body">
                    <h1>{novel.title}</h1>
                    <p className="novel-detail-description">{novel.description}</p>

                    <div className="novel-detail-stats">
                        {novel.estimated_minutes ? (
                            <div className="detail-stat">
                                <span className="detail-stat-value">
                                    ~{novel.estimated_minutes}
                                </span>
                                <span className="detail-stat-label">min</span>
                            </div>
                        ) : null}
                        {novel.vocabulary_count > 0 ? (
                            <div className="detail-stat">
                                <span className="detail-stat-value">
                                    {novel.vocabulary_count}
                                </span>
                                <span className="detail-stat-label">words</span>
                            </div>
                        ) : null}
                        {quizzes.length > 0 ? (
                            <div className="detail-stat">
                                <span className="detail-stat-value">{quizzes.length}</span>
                                <span className="detail-stat-label">quizzes</span>
                            </div>
                        ) : null}
                    </div>

                    {progress && hasProgress ? (
                        <div className="novel-detail-progress">
                            <div className="progress-bar-wrap">
                                <div
                                    className="progress-bar-fill"
                                    style={{ width: `${Math.round(progress.progress_percent)}%` }}
                                />
                            </div>
                            <span className="progress-label">
                                {Math.round(progress.progress_percent)}%
                                {isCompleted ? " · Completed" : " · In progress"}
                            </span>
                        </div>
                    ) : null}

                    <div className="novel-actions">
                        <button
                            type="button"
                            className="btn-primary"
                            onClick={() => navigate(`/novel/${id}/play`)}
                        >
                            {hasProgress && !isCompleted ? "Continue reading" : "Start reading"}
                        </button>

                        {novel.vocabulary_count > 0 ? (
                            <Link
                                to={`/novel/${id}/vocabulary`}
                                className="btn-secondary"
                            >
                                Vocabulary
                            </Link>
                        ) : null}

                        {quizzes.length > 0 ? (
                            <Link
                                to={`/quiz/${quizzes[0].id}`}
                                className="btn-secondary"
                            >
                                Take quiz
                            </Link>
                        ) : null}

                        {hasProgress ? (
                            <button
                                type="button"
                                className="btn-ghost"
                                onClick={handleReset}
                                disabled={resetting}
                            >
                                {resetting ? "Resetting…" : "Reset progress"}
                            </button>
                        ) : null}
                    </div>
                </div>
            </article>
        </main>
    );
}
