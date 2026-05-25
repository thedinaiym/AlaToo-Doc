import axios from "axios";

const TOKEN_KEY = "access_token";

function getCookie(name: string): string | null {
  if (typeof document === "undefined") {
    return null;
  }

  const cookie = document.cookie
    .split("; ")
    .find((item) => item.startsWith(`${name}=`));

  return cookie ? decodeURIComponent(cookie.split("=")[1]) : null;
}

function getJwtToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return getCookie(TOKEN_KEY) ?? window.localStorage.getItem(TOKEN_KEY);
}

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = getJwtToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export default api;
