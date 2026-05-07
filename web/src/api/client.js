/**
 * Single source of truth for HTTP calls.
 *
 * Exposes a configured axios instance, helpers for token storage, and a
 * request interceptor that transparently refreshes the JWT access token
 * when it expires.
 */

import axios from "axios";

const ACCESS_KEY = "vn_access_token";
const REFRESH_KEY = "vn_refresh_token";

export const API_BASE_URL =
    process.env.REACT_APP_API_URL || "http://localhost:8000/api";

export const tokens = {
    get access() {
        return localStorage.getItem(ACCESS_KEY);
    },
    get refresh() {
        return localStorage.getItem(REFRESH_KEY);
    },
    set({ access, refresh }) {
        if (access) localStorage.setItem(ACCESS_KEY, access);
        if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
    },
    clear() {
        localStorage.removeItem(ACCESS_KEY);
        localStorage.removeItem(REFRESH_KEY);
    },
};

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 15000,
});

apiClient.interceptors.request.use((config) => {
    const access = tokens.access;
    if (access) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${access}`;
    }
    return config;
});

let refreshInflight = null;

async function refreshAccessToken() {
    if (refreshInflight) return refreshInflight;
    const refresh = tokens.refresh;
    if (!refresh) throw new Error("No refresh token available.");

    refreshInflight = axios
        .post(`${API_BASE_URL}/auth/refresh/`, { refresh })
        .then((response) => {
            tokens.set({ access: response.data.access });
            return response.data.access;
        })
        .finally(() => {
            refreshInflight = null;
        });

    return refreshInflight;
}

apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const original = error.config || {};
        const status = error.response?.status;

        if (status === 401 && !original._retry && tokens.refresh) {
            original._retry = true;
            try {
                const newAccess = await refreshAccessToken();
                original.headers = original.headers || {};
                original.headers.Authorization = `Bearer ${newAccess}`;
                return apiClient(original);
            } catch (refreshError) {
                tokens.clear();
                throw refreshError;
            }
        }
        throw error;
    },
);

export function setSession(payload) {
    if (!payload) return;
    if (payload.access || payload.refresh) tokens.set(payload);
}

export function clearSession() {
    tokens.clear();
}

// Auth
export const auth = {
    register: (data) => apiClient.post("/auth/register/", data).then((r) => r.data),
    login: (data) => apiClient.post("/auth/login/", data).then((r) => r.data),
    logout: () =>
        apiClient
            .post("/auth/logout/", { refresh: tokens.refresh })
            .then((r) => r.data)
            .catch(() => null),
};

// Profile
export const profile = {
    get: () => apiClient.get("/profile/").then((r) => r.data),
    update: (data) => apiClient.patch("/profile/update/", data).then((r) => r.data),
    uploadAvatar: (file) => {
        const data = new FormData();
        data.append("avatar", file);
        return apiClient
            .post("/profile/avatar/", data, {
                headers: { "Content-Type": "multipart/form-data" },
            })
            .then((r) => r.data);
    },
    stats: () => apiClient.get("/profile/stats/").then((r) => r.data),
    achievements: () => apiClient.get("/profile/achievements/").then((r) => r.data),
};

// Novels
export const novels = {
    list: (params = {}) =>
        apiClient.get("/novels/", { params }).then((r) => r.data),
    get: (id) => apiClient.get(`/novels/${id}/`).then((r) => r.data),
    progress: (id) => apiClient.get(`/novels/${id}/progress/`).then((r) => r.data),
    saveProgress: (id, payload) =>
        apiClient.put(`/novels/${id}/progress/update/`, payload).then((r) => r.data),
    resetProgress: (id) =>
        apiClient.post(`/novels/${id}/progress/reset/`).then((r) => r.data),
};

// Vocabulary
export const vocabulary = {
    list: (novelId, params = {}) =>
        apiClient.get(`/novels/${novelId}/vocabulary/`, { params }).then((r) => r.data),
    learn: (wordId) =>
        apiClient.post(`/vocabulary/${wordId}/learn/`).then((r) => r.data),
    forget: (wordId) =>
        apiClient.delete(`/vocabulary/${wordId}/forget/`).then((r) => r.data),
};

// Quiz
export const quiz = {
    listForNovel: (novelId) =>
        apiClient.get(`/novels/${novelId}/quizzes/`).then((r) => r.data),
    get: (quizId) => apiClient.get(`/quizzes/${quizId}/`).then((r) => r.data),
    submit: (quizId, answers) =>
        apiClient.post(`/quizzes/${quizId}/submit/`, { answers }).then((r) => r.data),
    attempts: (quizId) =>
        apiClient.get(`/quizzes/${quizId}/attempts/`).then((r) => r.data),
};

// Achievements
export const achievements = {
    list: () => apiClient.get("/achievements/").then((r) => r.data),
};
