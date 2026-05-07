import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { quiz as quizApi } from "@api/client";

export default function QuizPage() {
    const { quizId } = useParams();
    const navigate = useNavigate();

    const [quizData, setQuizData] = useState(null);
    const [answers, setAnswers] = useState({}); // questionId -> Set of choiceIds
    const [result, setResult] = useState(null);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        let cancelled = false;
        quizApi
            .get(quizId)
            .then((data) => {
                if (!cancelled) setQuizData(data);
            })
            .catch(() => {
                if (!cancelled) setError("Failed to load quiz.");
            });
        return () => { cancelled = true; };
    }, [quizId]);

    const toggleChoice = (questionId, choiceId, isSingle) => {
        setAnswers((prev) => {
            const current = new Set(prev[questionId] || []);
            if (isSingle) {
                return { ...prev, [questionId]: new Set([choiceId]) };
            }
            if (current.has(choiceId)) {
                current.delete(choiceId);
            } else {
                current.add(choiceId);
            }
            return { ...prev, [questionId]: current };
        });
    };

    const handleSubmit = async () => {
        if (!quizData) return;
        setSubmitting(true);
        setError(null);
        try {
            const payload = {};
            for (const q of quizData.questions) {
                payload[String(q.id)] = [...(answers[q.id] || new Set())];
            }
            const data = await quizApi.submit(quizId, payload);
            setResult(data);
        } catch (err) {
            setError(err.response?.data?.detail || "Submission failed.");
        } finally {
            setSubmitting(false);
        }
    };

    const allAnswered = quizData?.questions?.every(
        (q) => (answers[q.id]?.size || 0) > 0
    );

    if (error && !quizData) {
        return (
            <main className="quiz-page">
                <p className="page-status">{error}</p>
            </main>
        );
    }

    if (!quizData) return <div className="page-status">Loading…</div>;

    if (result) {
        const { attempt, details } = result;
        const pct = attempt.max_score > 0
            ? Math.round((attempt.score / attempt.max_score) * 100)
            : 0;

        return (
            <main className="quiz-page">
                <div className="quiz-result-screen">
                    <div className={`quiz-result-hero ${attempt.passed ? "passed" : "failed"}`}>
                        <div className="quiz-result-icon">
                            {attempt.passed ? "✓" : "✗"}
                        </div>
                        <h2>{attempt.passed ? "Passed!" : "Not quite"}</h2>
                        <p className="quiz-score-display">
                            {attempt.score}/{attempt.max_score} correct ({pct}%)
                        </p>
                        {attempt.passed ? (
                            <p className="quiz-reward">+{Math.round(attempt.score * 10)} points earned</p>
                        ) : (
                            <p className="muted">
                                Need {Math.round(quizData.pass_threshold * 100)}% to pass.
                                You can retry anytime.
                            </p>
                        )}
                    </div>

                    <div className="quiz-review">
                        <h3>Review</h3>
                        {quizData.questions.map((q) => {
                            const d = details[String(q.id)];
                            if (!d) return null;
                            return (
                                <div
                                    key={q.id}
                                    className={`quiz-review-item ${d.correct ? "correct" : "wrong"}`}
                                >
                                    <p className="quiz-review-question">{q.text}</p>
                                    {q.choices.map((c) => {
                                        const isSelected = d.selected_ids.includes(c.id);
                                        const isCorrect = d.correct_ids.includes(c.id);
                                        return (
                                            <div
                                                key={c.id}
                                                className={`quiz-review-choice ${
                                                    isCorrect
                                                        ? "correct"
                                                        : isSelected
                                                        ? "wrong"
                                                        : ""
                                                }`}
                                            >
                                                {isCorrect ? "✓ " : isSelected ? "✗ " : "  "}
                                                {c.text}
                                                {isSelected && !isCorrect && d.explanations?.[c.id] ? (
                                                    <span className="quiz-explanation">
                                                        {d.explanations[c.id]}
                                                    </span>
                                                ) : null}
                                            </div>
                                        );
                                    })}
                                </div>
                            );
                        })}
                    </div>

                    <div className="quiz-result-actions">
                        <button
                            type="button"
                            className="btn-secondary"
                            onClick={() => {
                                setResult(null);
                                setAnswers({});
                            }}
                        >
                            Retry
                        </button>
                        <button
                            type="button"
                            className="btn-ghost"
                            onClick={() => navigate(-1)}
                        >
                            Go back
                        </button>
                    </div>
                </div>
            </main>
        );
    }

    return (
        <main className="quiz-page">
            <div className="quiz-header">
                <button
                    type="button"
                    className="btn-ghost"
                    onClick={() => navigate(-1)}
                >
                    ← Back
                </button>
                <h1 className="quiz-title">
                    {quizData.title || "Chapter Quiz"}
                </h1>
                <p className="quiz-meta">
                    {quizData.questions.length} questions ·{" "}
                    Pass: {Math.round(quizData.pass_threshold * 100)}%
                </p>
            </div>

            {error ? <p className="auth-error">{error}</p> : null}

            <div className="quiz-questions">
                {quizData.questions.map((q, idx) => {
                    const isSingle = q.question_type !== "multiple";
                    const selected = answers[q.id] || new Set();
                    return (
                        <div key={q.id} className="quiz-question-card">
                            <div className="quiz-question-number">
                                {idx + 1} / {quizData.questions.length}
                            </div>
                            <p className="quiz-question-text">{q.text}</p>
                            {q.hint ? (
                                <details className="quiz-hint">
                                    <summary>Hint</summary>
                                    <p>{q.hint}</p>
                                </details>
                            ) : null}
                            <div className="quiz-choices">
                                {q.choices.map((c) => (
                                    <button
                                        key={c.id}
                                        type="button"
                                        className={`quiz-choice-btn ${
                                            selected.has(c.id) ? "selected" : ""
                                        }`}
                                        onClick={() =>
                                            toggleChoice(q.id, c.id, isSingle)
                                        }
                                    >
                                        <span className="quiz-choice-marker">
                                            {isSingle ? (
                                                selected.has(c.id) ? "●" : "○"
                                            ) : (
                                                selected.has(c.id) ? "☑" : "☐"
                                            )}
                                        </span>
                                        {c.text}
                                    </button>
                                ))}
                            </div>
                        </div>
                    );
                })}
            </div>

            <div className="quiz-submit-row">
                <button
                    type="button"
                    className="btn-primary quiz-submit-btn"
                    onClick={handleSubmit}
                    disabled={submitting || !allAnswered}
                >
                    {submitting ? "Checking…" : "Submit answers"}
                </button>
                {!allAnswered ? (
                    <span className="muted">Answer all questions to submit</span>
                ) : null}
            </div>
        </main>
    );
}
