"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { signOut } from "firebase/auth";
import { auth } from "@/src/lib/firebase";
import { fetchProfile, updateProfile, removeToken, type Profile } from "@/src/lib/api";
import Sidebar from "@/src/components/Sidebar";
import Navbar from "@/src/components/Navbar";

const AVATARS = [
  { emoji: "🦊", bg: "#ff6b6b20" },
  { emoji: "🐼", bg: "#4ecdc420" },
  { emoji: "🦁", bg: "#f7d79420" },
  { emoji: "🐰", bg: "#ff9ff320" },
  { emoji: "🐸", bg: "#55efc420" },
  { emoji: "🦉", bg: "#74b9ff20" },
  { emoji: "🐧", bg: "#fd79a820" },
  { emoji: "🦄", bg: "#a29bfe20" },
];

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [displayName, setDisplayName] = useState("");
  const [username, setUsername] = useState("");
  const [phone, setPhone] = useState("");
  const [selectedAvatar, setSelectedAvatar] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetchProfile().then((p) => {
      setProfile(p);
      setDisplayName(p.display_name || "");
      setUsername(p.username || "");
      setPhone(p.phone || "");
      setSelectedAvatar(p.avatar_url || "");
      setLoading(false);
    }).catch(() => {
      router.replace("/login");
    });
  }, [router]);

  async function handleSave() {
    setSaving(true);
    setMessage("");
    try {
      const updated = await updateProfile({
        display_name: displayName,
        username,
        phone,
        avatar_url: selectedAvatar,
      });
      setProfile(updated);
      setMessage("Profile updated successfully!");
    } catch {
      setMessage("Failed to update profile");
    } finally {
      setSaving(false);
    }
  }

  async function handleLogout() {
    removeToken();
    await signOut(auth);
    router.replace("/login");
  }

  if (loading) {
    return (
      <div className="flex min-h-screen bg-base">
        <Sidebar />
        <div className="flex-1">
          <Navbar title="Profile" />
          <main className="p-5">
            <p className="text-sm text-text-tertiary">Loading...</p>
          </main>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-base">
      <Sidebar />
      <div className="flex-1">
        <Navbar title="Profile" />
        <main className="mx-auto max-w-2xl space-y-6 p-5">
          <div className="rounded-lg border border-border-soft bg-panel p-6">
            <h2 className="mb-4 text-sm font-semibold text-text-primary">Account Info</h2>
            <div className="mb-6 flex items-center gap-4">
              <div
                className="flex h-16 w-16 items-center justify-center rounded-full text-2xl"
                style={{ backgroundColor: selectedAvatar ? "#3DDC8420" : "#3DDC8420" }}
              >
                {selectedAvatar ? (
                  <span className="text-2xl">{selectedAvatar}</span>
                ) : (
                  <span className="text-lg font-semibold text-signal">
                    {(profile?.email?.[0] || "?").toUpperCase()}
                  </span>
                )}
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary">
                  {profile?.email || "No email"}
                </p>
                <p className="text-xs text-text-tertiary">ID: {profile?.firebase_uid?.slice(0, 12)}...</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="mb-1.5 block text-xs font-medium text-text-secondary">Display Name</label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="w-full rounded-md border border-border-soft bg-panel-raised px-3 py-2 text-sm text-text-primary outline-none focus:border-signal/50 focus:ring-1 focus:ring-signal/20"
                  placeholder="Enter your name"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-text-secondary">Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full rounded-md border border-border-soft bg-panel-raised px-3 py-2 text-sm text-text-primary outline-none focus:border-signal/50 focus:ring-1 focus:ring-signal/20"
                  placeholder="Choose a username"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-text-secondary">Phone</label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full rounded-md border border-border-soft bg-panel-raised px-3 py-2 text-sm text-text-primary outline-none focus:border-signal/50 focus:ring-1 focus:ring-signal/20"
                  placeholder="+1 (555) 123-4567"
                />
              </div>

              <div>
                <label className="mb-2 block text-xs font-medium text-text-secondary">Avatar</label>
                <div className="flex flex-wrap gap-2">
                  {AVATARS.map((a) => (
                    <button
                      key={a.emoji}
                      type="button"
                      onClick={() => setSelectedAvatar(a.emoji)}
                      className={`flex h-10 w-10 items-center justify-center rounded-full text-lg transition-all ${
                        selectedAvatar === a.emoji
                          ? "ring-2 ring-signal ring-offset-2 ring-offset-panel"
                          : "opacity-60 hover:opacity-100"
                      }`}
                      style={{ backgroundColor: a.bg }}
                    >
                      {a.emoji}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {message && (
              <p className={`mt-4 text-sm ${message.includes("success") ? "text-signal" : "text-red"}`}>
                {message}
              </p>
            )}

            <button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="mt-4 w-full rounded-md bg-signal px-4 py-2 text-sm font-medium text-base transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save changes"}
            </button>
          </div>

          <div className="rounded-lg border border-border-soft bg-panel p-6">
            <h2 className="mb-4 text-sm font-semibold text-text-primary">Session</h2>
            <button
              type="button"
              onClick={handleLogout}
              className="w-full rounded-md border border-red/30 bg-red-dim/10 px-4 py-2 text-sm font-medium text-red transition-opacity hover:opacity-90"
            >
              Sign out
            </button>
          </div>
        </main>
      </div>
    </div>
  );
}
