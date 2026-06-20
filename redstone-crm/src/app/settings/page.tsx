"use client";

import { useState } from "react";
import Sidebar from "@/src/components/Sidebar";
import Navbar from "@/src/components/Navbar";

export default function SettingsPage() {
  const [autoRestart, setAutoRestart] = useState(true);
  const [callRecording, setCallRecording] = useState(true);
  const [saved, setSaved] = useState(false);

  function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div className="flex min-h-screen bg-base">
      <Sidebar />
      <div className="flex-1">
        <Navbar title="Settings" />
        <main className="mx-auto max-w-2xl p-5">
          <form onSubmit={handleSave} className="space-y-5">
            <section className="rounded-lg border border-border-soft bg-panel p-5">
              <h2 className="text-sm font-semibold text-text-primary">Account</h2>
              <p className="mt-0.5 text-xs text-text-secondary">
                Your administrator profile details.
              </p>

              <div className="mt-4 space-y-4">
                <div>
                  <label className="block text-xs font-medium text-text-secondary">
                    Name
                  </label>
                  <input
                    type="text"
                    defaultValue="Admin"
                    className="mt-1 w-full rounded-md border border-border-soft bg-panel-raised px-3 py-2 text-sm text-text-primary outline-none focus:border-signal/50"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-text-secondary">
                    Email
                  </label>
                  <input
                    type="email"
                    defaultValue="admin@redstone.ai"
                    className="mt-1 w-full rounded-md border border-border-soft bg-panel-raised px-3 py-2 text-sm text-text-primary outline-none focus:border-signal/50"
                  />
                </div>
              </div>
            </section>

            <section className="rounded-lg border border-border-soft bg-panel p-5">
              <h2 className="text-sm font-semibold text-text-primary">
                System preferences
              </h2>
              <p className="mt-0.5 text-xs text-text-secondary">
                Defaults applied to every bot session.
              </p>

              <div className="mt-4 space-y-4">
                <label className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-text-primary">
                      Auto-restart on failure
                    </p>
                    <p className="text-xs text-text-tertiary">
                      Restart a bot automatically if its VICIdial session drops.
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={autoRestart}
                    onChange={(e) => setAutoRestart(e.target.checked)}
                    className="h-4 w-4 rounded border-border-soft bg-panel-raised accent-signal"
                  />
                </label>

                <label className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-text-primary">
                      Record all calls
                    </p>
                    <p className="text-xs text-text-tertiary">
                      Save audio and transcripts for every bot-handled call.
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={callRecording}
                    onChange={(e) => setCallRecording(e.target.checked)}
                    className="h-4 w-4 rounded border-border-soft bg-panel-raised accent-signal"
                  />
                </label>
              </div>
            </section>

            <div className="flex items-center gap-3">
              <button
                type="submit"
                className="rounded-md bg-signal px-4 py-2 text-xs font-medium text-base transition-opacity hover:opacity-90"
              >
                Save changes
              </button>
              {saved && (
                <span className="text-xs font-medium text-signal">Saved</span>
              )}
            </div>
          </form>
        </main>
      </div>
    </div>
  );
}