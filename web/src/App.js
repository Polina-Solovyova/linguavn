import React from "react";
import {
    BrowserRouter,
    Navigate,
    Route,
    Routes,
    useLocation,
} from "react-router-dom";

import Header from "@components/Header";
import { UserProvider, useUser } from "@providers/UserProvider";

import AuthPage from "@pages/AuthPage";
import NovelListPage from "@pages/NovelListPage";
import NovelDetailPage from "@pages/NovelDetailPage";
import NovelReaderPage from "@pages/NovelReaderPage";
import ProfilePage from "@pages/ProfilePage";
import QuizPage from "@pages/QuizPage";
import VocabularyPage from "@pages/VocabularyPage";

function RequireAuth({ children }) {
    const { user, loading } = useUser();
    const location = useLocation();
    if (loading) return <div className="page-status">Loading…</div>;
    if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
    return children;
}

function PublicOnly({ children }) {
    const { user, loading } = useUser();
    if (loading) return <div className="page-status">Loading…</div>;
    if (user) return <Navigate to="/" replace />;
    return children;
}

function Shell() {
    const { user } = useUser();
    const location = useLocation();
    const isReader = location.pathname.endsWith("/play");

    return (
        <>
            {user && !isReader ? <Header /> : null}
            <Routes>
                <Route
                    path="/login"
                    element={
                        <PublicOnly>
                            <AuthPage mode="login" />
                        </PublicOnly>
                    }
                />
                <Route
                    path="/register"
                    element={
                        <PublicOnly>
                            <AuthPage mode="register" />
                        </PublicOnly>
                    }
                />
                <Route
                    path="/"
                    element={
                        <RequireAuth>
                            <NovelListPage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/profile"
                    element={
                        <RequireAuth>
                            <ProfilePage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/novel/:id"
                    element={
                        <RequireAuth>
                            <NovelDetailPage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/novel/:id/play"
                    element={
                        <RequireAuth>
                            <NovelReaderPage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/novel/:id/vocabulary"
                    element={
                        <RequireAuth>
                            <VocabularyPage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/quiz/:quizId"
                    element={
                        <RequireAuth>
                            <QuizPage />
                        </RequireAuth>
                    }
                />
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </>
    );
}

export default function App() {
    return (
        <UserProvider>
            <BrowserRouter>
                <Shell />
            </BrowserRouter>
        </UserProvider>
    );
}
