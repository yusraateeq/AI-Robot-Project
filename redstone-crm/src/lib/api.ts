const BASE = "/api";
const BASE_URL = "http://localhost:3002";

export interface LoginResponse {
  token: string;
  user: { id: number; username: string };
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(err.detail || "Login failed");
  }
  return res.json();
}

export async function register(username: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Registration failed" }));
    throw new Error(err.detail || "Registration failed");
  }
  return res.json();
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export function setToken(token: string): void {
  localStorage.setItem("token", token);
}

export function removeToken(): void {
  localStorage.removeItem("token");
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export function logout(): void {
  removeToken();
  import("firebase/auth").then(({ signOut }) => {
    import("@/src/lib/firebase").then(({ auth }) => signOut(auth));
  });
  window.location.href = "/login";
}

export interface Profile {
  firebase_uid: string;
  email: string;
  username: string;
  display_name: string | null;
  avatar_url: string | null;
  phone: string | null;
  role?: string;
  company?: string;
  timezone?: string;
  registration_complete?: boolean;
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function fetchProfile(): Promise<Profile> {
  const res = await fetch(`${BASE}/profile`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch profile");
  return res.json();
}

export async function updateProfile(data: Partial<Profile>): Promise<Profile> {
  const res = await fetch(`${BASE}/profile`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update profile");
  return res.json();
}

export interface Bot {
  id: string;
  name: string;
  campaign: string;
  status: string;
  callsToday: number;
  active: boolean;
}

export async function fetchBots(): Promise<Bot[]> {
  const res = await fetch(`${BASE_URL}/api/bots`);
  if (!res.ok) throw new Error("Failed to fetch bots");
  const data = await res.json();
  return data.bots ?? data;
}

// ─── Bot actions ──────────────────────────────────────────────

export interface BotActionResult {
  status: string;
  bot_id: string;
}

async function botFetch(url: string, method: string = "POST"): Promise<BotActionResult> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(url, { method, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export async function loginBot(botId: string): Promise<void> {
  const url = `${BASE}/bots/${botId}/login`;
  console.log(`[API] loginBot — fetching ${url}`);
  const res = await fetch(url, { method: "POST" });
  console.log(`[API] loginBot — response status=${res.status}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || "Request failed");
  }
}

export async function loginBotPoll(botId: string, interval = 2000, timeoutMs = 300000): Promise<void> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const res = await fetch(`${BASE}/bots/${botId}/login-status`);
    if (!res.ok) {
      await new Promise((r) => setTimeout(r, interval));
      continue;
    }
    const data = await res.json();
    if (data.status === "completed") return;
    if (data.status === "failed") throw new Error(data.error || "Login failed");
    if (data.status === "idle") throw new Error("No login process found");
    await new Promise((r) => setTimeout(r, interval));
  }
  throw new Error("Login timed out");
}

// ─── Dashboard stats ──────────────────────────────────────────

export interface DashboardStats {
  total_calls: number;
  transfers: number;
  success_rate: number;
  active_bots: number;
  call_volume: { labels: string[]; data: number[] };
}

export interface BotStatusInfo {
  id: string;
  name: string;
  campaign: string;
  status: string;
  callsToday: number;
  vicidial_status: string | null;
  active: boolean;
}

export async function fetchStats(): Promise<DashboardStats> {
  const res = await fetch(`${BASE}/stats`);
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

export async function fetchBotStatuses(): Promise<BotStatusInfo[]> {
  const res = await fetch(`${BASE}/bots`);
  if (!res.ok) throw new Error("Failed to fetch bot statuses");
  const data = await res.json();
  return data.bots;
}

export async function logoutBot(botId: string): Promise<BotActionResult> {
  return botFetch(`${BASE}/bots/${botId}/logout`);
}

export async function restartBot(botId: string): Promise<BotActionResult> {
  return botFetch(`${BASE}/bots/${botId}/restart`);
}

export async function addBot(name: string, campaign: string = "") {
  const token = getToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${BASE}/bots/add`, {
    method: "POST",
    headers,
    body: JSON.stringify({ name, campaign }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to add bot" }));
    throw new Error(err.detail || "Failed to add bot");
  }
  return res.json();
}

export async function deleteBot(botId: string): Promise<BotActionResult> {
  return botFetch(`${BASE}/bots/${botId}`, "DELETE");
}
