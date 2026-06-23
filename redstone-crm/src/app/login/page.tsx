"use client";

import { useState, FormEvent, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithRedirect,
  getRedirectResult,
} from "firebase/auth";
import { auth, googleProvider } from "@/src/lib/firebase";
import { setToken } from "@/src/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Handle redirect result (Google sign-in)
  useEffect(() => {
    getRedirectResult(auth)
      .then(async (result) => {
        if (!result) return;
        setLoading(true);
        const token = await result.user.getIdToken();
        await exchangeToken(token);
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : "";
        if (!msg.includes("auth/popup-closed-by-user")) {
          setError(msg || "Google sign-in failed");
        }
      })
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function exchangeToken(idToken: string) {
    const res = await fetch("/api/auth/firebase", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id_token: idToken }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Auth failed" }));
      throw new Error(err.detail || "Auth failed");
    }
    const data = await res.json();
    setToken(data.token);
    router.replace("/dashboard");
  }

  async function handleEmailAuth(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      let cred;
      if (isRegister) {
        cred = await createUserWithEmailAndPassword(auth, email, password);
      } else {
        cred = await signInWithEmailAndPassword(auth, email, password);
      }
      const token = await cred.user.getIdToken();
      await exchangeToken(token);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Authentication failed";
      if (msg.includes("auth/email-already-in-use")) setError("Email already registered");
      else if (msg.includes("auth/user-not-found") || msg.includes("auth/invalid-credential"))
        setError("Invalid email or password");
      else if (msg.includes("auth/weak-password")) setError("Password too weak (min 6 chars)");
      else setError(msg);
    } finally {
      setLoading(false);
    }
  }

  function handleGoogleSignIn() {
    signInWithRedirect(auth, googleProvider);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-base px-4">
      <div className="w-full max-w-sm rounded-lg border border-border-soft bg-panel p-8">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-md bg-signal/15 text-lg font-semibold text-signal">
            R
          </div>
          <h1 className="text-lg font-semibold text-text-primary">Redstone CRM</h1>
          <p className="mt-1 text-sm text-text-secondary">
            {isRegister ? "Create your account" : "Sign in to your account"}
          </p>
        </div>

        <button
          type="button"
          onClick={handleGoogleSignIn}
          disabled={loading}
          className="mb-4 flex w-full items-center justify-center gap-3 rounded-md border border-border-soft bg-panel-raised px-4 py-2.5 text-sm font-medium text-text-primary transition-colors hover:bg-panel disabled:opacity-50"
        >
          <svg width="18" height="18" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          {loading ? "Signing in..." : "Continue with Google"}
        </button>

        <div className="relative mb-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-border-soft" />
          </div>
          <div className="relative flex justify-center text-xs">
            <span className="bg-panel px-2 text-text-tertiary">or</span>
          </div>
        </div>

        <form onSubmit={handleEmailAuth} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-text-secondary" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-border-soft bg-panel-raised px-3 py-2 text-sm text-text-primary outline-none transition-colors placeholder:text-text-tertiary focus:border-signal/50 focus:ring-1 focus:ring-signal/20"
              placeholder="Enter email"
              required
              autoFocus
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-medium text-text-secondary" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md border border-border-soft bg-panel-raised px-3 py-2 text-sm text-text-primary outline-none transition-colors placeholder:text-text-tertiary focus:border-signal/50 focus:ring-1 focus:ring-signal/20"
              placeholder={isRegister ? "Min 6 characters" : "Enter password"}
              required
              minLength={6}
            />
          </div>

          {error && (
            <p className="text-sm text-red">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-signal px-4 py-2 text-sm font-medium text-base transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {loading ? "Processing..." : isRegister ? "Create account" : "Sign in"}
          </button>
        </form>

        <p className="mt-4 text-center text-xs text-text-tertiary">
          {isRegister ? "Already have an account? " : "Don't have an account? "}
          <button
            type="button"
            onClick={() => { setIsRegister(!isRegister); setError(""); }}
            className="font-medium text-signal hover:underline"
          >
            {isRegister ? "Sign in" : "Register"}
          </button>
        </p>
      </div>
    </div>
  );
}
