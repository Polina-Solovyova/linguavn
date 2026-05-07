import React from "react";
import { Link, useNavigate } from "react-router-dom";

import { useUser } from "@providers/UserProvider";

const LEVEL_COLORS = { B1: "#4caf91", B2: "#4c8faf", C1: "#8f4caf" };

export default function Header() {
    const { user, logout } = useUser();
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
        navigate("/login", { replace: true });
    };

    const level = user?.profile?.language_level;

    return (
        <header className="app-header">
            <Link to="/" className="brand">
                VN English
            </Link>
            <nav>
                <Link to="/">Library</Link>
                <Link to="/profile">Profile</Link>
                {level ? (
                    <span
                        className="header-level-badge"
                        style={{ background: LEVEL_COLORS[level] }}
                    >
                        {level}
                    </span>
                ) : null}
                <button type="button" onClick={handleLogout}>
                    Log out{user ? ` (${user.profile.username})` : ""}
                </button>
            </nav>
        </header>
    );
}
