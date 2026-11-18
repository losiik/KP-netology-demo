// Обёртка над fetch: добавляет токен и приводит ошибки сервера к одному виду.

const TOKEN_KEY = "kp_token";

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    // localStorage недоступен — вход просто не переживёт перезагрузку
  }
}

export class ApiError extends Error {
  constructor(status, message, errors = {}, retry = false) {
    super(message);
    this.status = status;
    this.errors = errors;
    this.retry = retry;
  }
}

let onUnauthorized = () => {};
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

export async function api(path, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(path, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "Сервер недоступен. Проверьте, что бэкенд запущен.");
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message =
      data.message || (typeof data.detail === "string" ? data.detail : "Ошибка сервера");
    if (response.status === 401 && path !== "/api/auth/login") onUnauthorized();
    throw new ApiError(response.status, message, data.errors || {}, Boolean(data.retry));
  }
  return data;
}
