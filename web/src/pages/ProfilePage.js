import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { profile as profileApi } from "@api/client";
import { useUser } from "@providers/UserProvider";

const LEVEL_LABELS = { B1: "Intermediate", B2: "Upper-Intermediate", C1: "Advanced" };
const LEVEL_COLORS = { B1: "#4caf91", B2: "#4c8faf", C1: "#8f4caf" };

export default function ProfilePage() {
    const { user, refresh } = useUser();
    const fileInput = useRef(null);
    const [stats, setStats] = useState(null);
    const [error, setError] = useState(null);
    const [busy, setBusy] = useState(false);
    const [levelSaving, setLevelSaving] = useState(false);
    const [activeTab, setActiveTab] = useState("progress");

    useEffect(() => {
        profileApi.stats().then(setStats).catch(() => {});
    }, []);

    if (!user) return <p className="page-status">Loading…</p>;

    const progressEntries = user.progress || [];
    const achievements = user.achievements || [];
    const quizAttempts = user.quiz_attempts || [];
    const learnedCount = user.learned_words_count || 0;

    const handleUpload = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setBusy(true);
        setError(null);
        try {
            await profileApi.uploadAvatar(file);
            await refresh();
        } catch (_) {
            setError("Failed to upload avatar.");
        } finally {
            setBusy(false);
            if (fileInput.current) fileInput.current.value = "";
        }
    };

    const handleLevelChange = async (level) => {
        setLevelSaving(true);
        try {
            await profileApi.update({ language_level: level });
            await refresh();
        } catch (_) {
            setError("Failed to update level.");
        } finally {
            setLevelSaving(false);
        }
    };

    const currentLevel = user.profile.language_level || "B1";

    return (
        <main className="profile-page">
            <div className="profile-layout">
                {/* Sidebar */}
                <aside className="profile-sidebar">
                    <div className="profile-avatar-wrap">
                        {user.profile.avatar ? (
                            <img
                                src={user.profile.avatar}
                                alt="avatar"
                                className="avatar"
                            />
                        ) : (
                            <div className="avatar avatar-placeholder">
                                {(user.profile.username || "?")[0].toUpperCase()}
                            </div>
                        )}
                        <label className="upload-label">
                            <input
                                ref={fileInput}
                                type="file"
                                accept="image/*"
                                onChange={handleUpload}
                                disabled={busy}
                            />
                            {busy ? "Uploading…" : "Change avatar"}
                        </label>
                    </div>

                    <h2 className="profile-username">{user.profile.username}</h2>
                    <p className="muted profile-email">{user.profile.email}</p>

                    {error ? <p className="auth-error">{error}</p> : null}

                    {/* Stats summary */}
                    {stats ? (
                        <div className="profile-stats-grid">
                            <div className="stat-chip">
                                <span className="stat-value">{stats.total_score}</span>
                                <span className="stat-label">Score</span>
                            </div>
                            <div className="stat-chip">
                                <span className="stat-value">{stats.streak_days}</span>
                                <span className="stat-label">Streak</span>
                            </div>
                            <div className="stat-chip">
                                <span className="stat-value">{stats.novels_completed}</span>
                                <span className="stat-label">Completed</span>
                            </div>
                            <div className="stat-chip">
                                <span className="stat-value">{learnedCount}</span>
                                <span className="stat-label">Words</span>
                            </div>
                        </div>
                    ) : null}

                    {/* Language level selector */}
                    <div className="level-selector">
                        <p className="level-selector-label">Language level</p>
                        <div className="level-buttons">
                            {["B1", "B2", "C1"].map((lvl) => (
                                <button
                                    key={lvl}
                                    type="button"
                                    className={`level-btn ${currentLevel === lvl ? "active" : ""}`}
                                    style={
                                        currentLevel === lvl
                                            ? { background: LEVEL_COLORS[lvl] }
                                            : {}
                                    }
                                    onClick={() => handleLevelChange(lvl)}
                                    disabled={levelSaving}
                                >
                                    {lvl}
                                    <span className="level-btn-sub">
                                        {LEVEL_LABELS[lvl]}
                                    </span>
                                </button>
                            ))}
                        </div>
                    </div>
                </aside>

                {/* Main content */}
                <div className="profile-main">
                    <div className="profile-tabs">
                        {[
                            { key: "progress", label: "Reading progress" },
                            { key: "achievements", label: `Achievements (${achievements.length})` },
                            { key: "quizzes", label: "Quiz results" },
                        ].map((tab) => (
                            <button
                                key={tab.key}
                                type="button"
                                className={`tab-btn ${activeTab === tab.key ? "active" : ""}`}
                                onClick={() => setActiveTab(tab.key)}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>

                    {activeTab === "progress" && (
                        <section className="profile-section">
                            {progressEntries.length === 0 ? (
                                <p className="empty-state">
                                    You haven't started any novels yet.{" "}
                                    <Link to="/">Browse the library</Link>
                                </p>
                            ) : (
                                <ul className="progress-list">
                                    {progressEntries.map((p) => (
                                        <li key={p.novel_id} className="progress-item">
                                            <div className="progress-item-info">
                                                <Link
                                                    to={`/novel/${p.novel_id}`}
                                                    className="progress-novel-title"
                                                >
                                                    {p.novel_title || `Novel #${p.novel_id}`}
                                                </Link>
                                                <div className="progress-item-meta">
                                                    <span className={`level-badge level-${p.current_level}`}>
                                                        {p.current_level}
                                                    </span>
                                                    {p.is_completed ? (
                                                        <span className="completed-badge">Completed</span>
                                                    ) : null}
                                                </div>
                                            </div>
                                            <div className="progress-bar-wrap">
                                                <div
                                                    className="progress-bar-fill"
                                                    style={{
                                                        width: `${Math.round(p.progress_percent)}%`,
                                                    }}
                                                />
                                                <span className="progress-bar-label">
                                                    {Math.round(p.progress_percent)}%
                                                </span>
                                            </div>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </section>
                    )}

                    {activeTab === "achievements" && (
                        <section className="profile-section">
                            {achievements.length === 0 ? (
                                <p className="empty-state">
                                    No achievements yet. Keep reading to earn them!
                                </p>
                            ) : (
                                <div className="achievements-grid">
                                    {achievements.map((ua) => (
                                        <div
                                            key={ua.id}
                                            className="achievement-card"
                                            title={ua.achievement.description}
                                        >
                                            <div className="achievement-icon">
                                                {ua.achievement.icon || "🏆"}
                                            </div>
                                            <div className="achievement-title">
                                                {ua.achievement.title}
                                            </div>
                                            <div className="achievement-points">
                                                +{ua.achievement.points} pts
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </section>
                    )}

                    {activeTab === "quizzes" && (
                        <section className="profile-section">
                            {quizAttempts.length === 0 ? (
                                <p className="empty-state">
                                    No quiz attempts yet.
                                </p>
                            ) : (
                                <ul className="quiz-results-list">
                                    {quizAttempts.map((attempt) => (
                                        <li key={attempt.id} className="quiz-result-item">
                                            <div className="quiz-result-info">
                                                <span className="quiz-result-title">
                                                    {attempt.quiz_title || `Quiz #${attempt.quiz_id}`}
                                                </span>
                                                <span className="quiz-result-date">
                                                    {new Date(
                                                        attempt.completed_at
                                                    ).toLocaleDateString()}
                                                </span>
                                            </div>
                                            <div className="quiz-result-score">
                                                <span
                                                    className={`quiz-result-badge ${attempt.passed ? "passed" : "failed"}`}
                                                >
                                                    {attempt.passed ? "Passed" : "Failed"}
                                                </span>
                                                <span className="quiz-result-fraction">
                                                    {attempt.score}/{attempt.max_score}
                                                </span>
                                            </div>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </section>
                    )}
                </div>
            </div>
        </main>
    );
}
