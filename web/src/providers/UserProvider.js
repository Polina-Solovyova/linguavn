import React, {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState,
} from "react";

import {
    auth as authApi,
    clearSession,
    profile as profileApi,
    setSession,
    tokens,
} from "@api/client";

const UserContext = createContext(null);

export function UserProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(Boolean(tokens.access));

    const refresh = useCallback(async () => {
        try {
            const data = await profileApi.get();
            setUser(data);
            return data;
        } catch (error) {
            clearSession();
            setUser(null);
            throw error;
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (tokens.access) {
            refresh().catch(() => {});
        }
    }, [refresh]);

    const login = useCallback(
        async (credentials) => {
            const result = await authApi.login(credentials);
            setSession(result);
            await refresh();
            return result;
        },
        [refresh],
    );

    const register = useCallback(
        async (data) => {
            const result = await authApi.register(data);
            setSession(result);
            await refresh();
            return result;
        },
        [refresh],
    );

    const logout = useCallback(async () => {
        try {
            await authApi.logout();
        } finally {
            clearSession();
            setUser(null);
        }
    }, []);

    const value = useMemo(
        () => ({ user, loading, login, register, logout, refresh, setUser }),
        [user, loading, login, register, logout, refresh],
    );

    return (
        <UserContext.Provider value={value}>{children}</UserContext.Provider>
    );
}

export function useUser() {
    const ctx = useContext(UserContext);
    if (!ctx) throw new Error("useUser must be used inside <UserProvider>");
    return ctx;
}
