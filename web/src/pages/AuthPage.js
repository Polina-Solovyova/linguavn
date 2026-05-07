import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useUser } from "@providers/UserProvider";

export default function AuthPage({ mode }) {
    const isRegister = mode === "register";
    const { login, register } = useUser();
    const navigate = useNavigate();

    const [form, setForm] = useState({ username: "", email: "", password: "" });
    const [error, setError] = useState(null);
    const [submitting, setSubmitting] = useState(false);

    const handleChange = (e) =>
        setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setSubmitting(true);
        try {
            if (isRegister) {
                await register(form);
            } else {
                await login({ username: form.username, password: form.password });
            }
            navigate("/", { replace: true });
        } catch (err) {
            const data = err.response?.data;
            const msg =
                data?.detail ||
                (data && Object.values(data).flat().join(" ")) ||
                "Authentication failed.";
            setError(msg);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <main className="auth-page">
            <form className="auth-card" onSubmit={handleSubmit}>
                <h1>{isRegister ? "Create account" : "Welcome back"}</h1>
                {error ? <p className="auth-error">{error}</p> : null}

                <label>
                    <span>Username</span>
                    <input
                        name="username"
                        value={form.username}
                        onChange={handleChange}
                        required
                        autoComplete="username"
                    />
                </label>

                {isRegister ? (
                    <label>
                        <span>Email</span>
                        <input
                            type="email"
                            name="email"
                            value={form.email}
                            onChange={handleChange}
                            required
                            autoComplete="email"
                        />
                    </label>
                ) : null}

                <label>
                    <span>Password</span>
                    <input
                        type="password"
                        name="password"
                        value={form.password}
                        onChange={handleChange}
                        required
                        autoComplete={isRegister ? "new-password" : "current-password"}
                        minLength={8}
                    />
                </label>

                <button type="submit" disabled={submitting}>
                    {submitting ? "Please wait…" : isRegister ? "Sign up" : "Log in"}
                </button>

                <p className="auth-switch">
                    {isRegister ? (
                        <>Already have an account? <Link to="/login">Log in</Link></>
                    ) : (
                        <>New here? <Link to="/register">Create an account</Link></>
                    )}
                </p>
            </form>
        </main>
    );
}
