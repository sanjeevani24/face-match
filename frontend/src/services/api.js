import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL;
const API_TIMEOUT = Number(import.meta.env.VITE_API_TIMEOUT) || 15000;

if (!API_URL && import.meta.env.DEV) {
  // eslint-disable-next-line no-console
  console.warn(
    "[api] VITE_API_URL is not set. Copy .env.example to .env and point it at your FastAPI backend."
  );
}

const api = axios.create({
  baseURL: API_URL,
  timeout: API_TIMEOUT,
});

// Central place to attach auth headers once JWT auth lands (Future Features).
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("skf_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Normalize errors so components/hooks don't need to know about axios internals.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const normalized = {
      status: error.response?.status ?? null,
      message:
        error.response?.data?.detail ||
        error.response?.data?.message ||
        error.message ||
        "Something went wrong. Please try again.",
      original: error,
    };
    return Promise.reject(normalized);
  }
);

export default api;
