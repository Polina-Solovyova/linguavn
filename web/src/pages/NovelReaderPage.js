import React, { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from "axios";

import { novels as novelsApi, vocabulary as vocabApi } from "@api/client";
import { useUser } from "@providers/UserProvider";
import { VisualNovelRuntime } from "@vn/runtime";

export default function NovelReaderPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const { user } = useUser();
    const userLevelRef = useRef(user?.profile?.language_level || "B2");

    const runtimeRef = useRef(null);
    const [frame, setFrame] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);
    const [vocabPopup, setVocabPopup] = useState(null); // { word, translation, transcription, definition }
    const [novelVocab, setNovelVocab] = useState({}); // word.toLowerCase() -> VocabularyWord
    const audioRef = useRef(null);
    const currentTrackRef = useRef(null);
    const saveTimer = useRef(null);

    const syncFrame = useCallback(() => {
        const rt = runtimeRef.current;
        if (rt) setFrame(rt.currentFrame);
    }, []);

    // Load metadata, scenario JSON, saved progress, and vocabulary in parallel
    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const novel = await novelsApi.get(id);
                if (!novel.scenario_url) throw new Error("Novel has no scenario file.");

                const [scenarioResp, progress, vocabList] = await Promise.all([
                    axios.get(novel.scenario_url),
                    novelsApi.progress(id),
                    vocabApi.list(id).catch(() => []),
                ]);
                if (cancelled) return;

                const rt = new VisualNovelRuntime(scenarioResp.data);
                if (progress?.current_node_id) {
                    rt.loadState(progress);
                } else {
                    const userLevel = userLevelRef.current;
                    rt.loadState({ state_snapshot: { vars: { _level: userLevel } } });
                }
                runtimeRef.current = rt;

                const vocabMap = {};
                for (const w of vocabList) {
                    vocabMap[w.word.toLowerCase()] = w;
                }
                setNovelVocab(vocabMap);
                setFrame(rt.currentFrame);
            } catch (err) {
                if (!cancelled) setError(err.message || "Failed to load scenario.");
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => {
            cancelled = true;
            if (saveTimer.current) clearTimeout(saveTimer.current);
        };
    }, [id]);

    // Persist progress with debounce
    const scheduleSave = useCallback(() => {
        const rt = runtimeRef.current;
        if (!rt) return;
        if (saveTimer.current) clearTimeout(saveTimer.current);
        saveTimer.current = setTimeout(() => {
            novelsApi.saveProgress(id, rt.getState()).catch(() => {});
        }, 400);
    }, [id]);

    // Save on unmount
    useEffect(() => {
        return () => {
            if (saveTimer.current) clearTimeout(saveTimer.current);
            const rt = runtimeRef.current;
            if (rt) novelsApi.saveProgress(id, rt.getState()).catch(() => {});
        };
    }, [id]);

    // Background music management
    useEffect(() => {
        if (!frame) return;
        const trackId = frame.music?.id || null;
        if (trackId === currentTrackRef.current) return;
        currentTrackRef.current = trackId;

        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current = null;
        }
        if (frame.music?.file) {
            const audio = new Audio(frame.music.file);
            audio.loop = true;
            audio.volume = 0.4;
            audio.play().catch(() => {});
            audioRef.current = audio;
        }
        return () => {
            if (audioRef.current) {
                audioRef.current.pause();
                audioRef.current = null;
            }
        };
    }, [frame]);

    // Keyboard navigation: Space/Enter = advance, number keys = pick choice
    useEffect(() => {
        const handler = (e) => {
            if (vocabPopup) {
                if (e.key === "Escape") setVocabPopup(null);
                return;
            }
            if (!frame || frame.isFinished) return;
            if (frame.type === "choice") {
                const idx = parseInt(e.key, 10) - 1;
                if (!isNaN(idx) && idx >= 0 && idx < frame.choices.length) {
                    doPickChoice(idx);
                }
            } else if (e.key === " " || e.key === "Enter") {
                e.preventDefault();
                doAdvance();
            }
        };
        window.addEventListener("keydown", handler);
        return () => window.removeEventListener("keydown", handler);
    }, [frame, vocabPopup]); // eslint-disable-line react-hooks/exhaustive-deps

    const doAdvance = useCallback(() => {
        const rt = runtimeRef.current;
        if (!rt) return;
        try {
            rt.advance();
            syncFrame();
            scheduleSave();
        } catch (err) {
            setError(err.message);
        }
    }, [syncFrame, scheduleSave]);

    const doPickChoice = useCallback((idx) => {
        const rt = runtimeRef.current;
        if (!rt) return;
        try {
            rt.pickChoice(idx);
            syncFrame();
            scheduleSave();
        } catch (err) {
            setError(err.message);
        }
    }, [syncFrame, scheduleSave]);

    const handleClickArea = useCallback(() => {
        if (!frame) return;
        if (frame.isFinished) {
            navigate(`/novel/${id}`);
            return;
        }
        if (frame.type !== "choice") doAdvance();
    }, [frame, id, navigate, doAdvance]);

    const handleWordClick = useCallback((e) => {
        e.stopPropagation();
        const word = e.target.dataset.word;
        if (word && novelVocab[word]) {
            setVocabPopup(novelVocab[word]);
        }
    }, [novelVocab]);

    const handleLearnWord = useCallback(async (wordId) => {
        try {
            await vocabApi.learn(wordId);
            setVocabPopup(prev => prev ? { ...prev, is_learned: true } : prev);
        } catch (_) {}
    }, []);

    if (error) {
        return (
            <main className="reader reader-error">
                <p className="reader-error-msg">{error}</p>
                <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => navigate(`/novel/${id}`)}
                >
                    Back
                </button>
            </main>
        );
    }

    if (loading || !frame) {
        return <div className="page-status">Loading…</div>;
    }

    const isChoice = frame.type === "choice";
    const rt = runtimeRef.current;

    return (
        <main
            className="reader"
            style={{
                backgroundImage: frame.background
                    ? `url(${frame.background.image})`
                    : "none",
            }}
            onClick={handleClickArea}
        >
            <header className="reader-toolbar" onClick={(e) => e.stopPropagation()}>
                <button
                    type="button"
                    className="reader-exit-btn"
                    onClick={() => navigate(`/novel/${id}`)}
                >
                    ← Exit
                </button>
                <div className="reader-toolbar-center">
                    {frame.music && (
                        <span className="reader-music-indicator" title={frame.music.id}>
                            ♪
                        </span>
                    )}
                </div>
                <div className="reader-progress">
                    {rt ? Math.round(rt.progressPercent) : 0}%
                </div>
            </header>

            {frame.character ? (
                <img
                    className={`reader-character pos-${frame.position}`}
                    src={frame.character.image}
                    alt={frame.character.name}
                />
            ) : null}

            {frame.isFinished ? (
                <div className="reader-end" onClick={(e) => e.stopPropagation()}>
                    <div className="reader-end-content">
                        <h2>The End</h2>
                        <p className="muted">You've finished this chapter.</p>
                        <button
                            type="button"
                            className="btn-primary"
                            onClick={() => navigate(`/novel/${id}`)}
                        >
                            Back to novel
                        </button>
                    </div>
                </div>
            ) : isChoice ? (
                <div
                    className="reader-choices"
                    onClick={(e) => e.stopPropagation()}
                >
                    {frame.prompt ? (
                        <div className="reader-choice-prompt">{frame.prompt}</div>
                    ) : null}
                    <div className="reader-choice-list">
                        {frame.choices.map((c) => (
                            <button
                                key={c.index}
                                type="button"
                                className="choice-button"
                                onClick={() => doPickChoice(c.index)}
                            >
                                <span className="choice-number">{c.index + 1}</span>
                                {c.text}
                            </button>
                        ))}
                    </div>
                </div>
            ) : (
                <div className="reader-dialogue" onClick={(e) => e.stopPropagation()}>
                    {frame.character ? (
                        <div className="reader-speaker">{frame.character.name}</div>
                    ) : null}
                    <p
                        className="reader-text"
                        onClick={handleWordClick}
                        dangerouslySetInnerHTML={{
                            __html: annotateWords(frame.text || "", novelVocab),
                        }}
                    />
                    <div className="reader-hint">
                        Click to continue&nbsp;&nbsp;·&nbsp;&nbsp;
                        <kbd>Space</kbd> or <kbd>Enter</kbd>
                    </div>
                </div>
            )}

            {vocabPopup ? (
                <div
                    className="vocab-popup-overlay"
                    onClick={() => setVocabPopup(null)}
                >
                    <div
                        className="vocab-popup"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <button
                            className="vocab-popup-close"
                            type="button"
                            onClick={() => setVocabPopup(null)}
                        >
                            ✕
                        </button>
                        <div className="vocab-popup-word">{vocabPopup.word}</div>
                        {vocabPopup.transcription ? (
                            <div className="vocab-popup-transcription">
                                [{vocabPopup.transcription}]
                            </div>
                        ) : null}
                        {vocabPopup.translation ? (
                            <div className="vocab-popup-translation">
                                {vocabPopup.translation}
                            </div>
                        ) : null}
                        {vocabPopup.definition ? (
                            <div className="vocab-popup-definition">
                                {vocabPopup.definition}
                            </div>
                        ) : null}
                        {vocabPopup.example ? (
                            <div className="vocab-popup-example">
                                <em>{vocabPopup.example}</em>
                            </div>
                        ) : null}
                        {!vocabPopup.is_learned ? (
                            <button
                                type="button"
                                className="btn-primary vocab-learn-btn"
                                onClick={() => handleLearnWord(vocabPopup.id)}
                            >
                                + Add to my words
                            </button>
                        ) : (
                            <div className="vocab-learned-badge">Learned ✓</div>
                        )}
                    </div>
                </div>
            ) : null}
        </main>
    );
}

function annotateWords(text, vocabMap) {
    if (!text || !Object.keys(vocabMap).length) {
        return escapeHtml(text || "");
    }
    const tokens = text.split(/(\s+|[.,!?;:'"()—–-])/);
    return tokens
        .map((token) => {
            const key = token.toLowerCase().replace(/[^a-z']/g, "");
            if (key && vocabMap[key]) {
                return `<span class="vocab-word" data-word="${key}">${escapeHtml(token)}</span>`;
            }
            return escapeHtml(token);
        })
        .join("");
}

function escapeHtml(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}
