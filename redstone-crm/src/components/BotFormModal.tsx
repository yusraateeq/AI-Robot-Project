"use client";

import { useState } from "react";
import { Bot } from "../lib/types";

interface BotFormModalProps {
  bot?: Bot | null;
  onClose: () => void;
  onSave: (data: { name: string; campaign: string }) => void;
}

export default function BotFormModal({ bot, onClose, onSave }: BotFormModalProps) {
  const [name, setName] = useState(bot?.name ?? "");
  const [campaign, setCampaign] = useState(bot?.campaign ?? "");
  const isEditing = Boolean(bot);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    onSave({ name: name.trim(), campaign: campaign.trim() });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="w-full max-w-sm rounded-lg border border-border-soft bg-panel p-5 shadow-2xl">
        <h2 className="text-sm font-semibold text-text-primary">
          {isEditing ? "Edit bot" : "Add bot"}
        </h2>
        <p className="mt-0.5 text-xs text-text-secondary">
          {isEditing
            ? "Update this bot's name and assigned campaign."
            : "Create a new bot and assign it to a campaign."}
        </p>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="block text-xs font-medium text-text-secondary">
              Bot name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Mary-05"
              autoFocus
              className="mt-1 w-full rounded-md border border-border-soft bg-panel-raised px-3 py-2 text-sm text-text-primary outline-none placeholder:text-text-tertiary focus:border-signal/50"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-text-secondary">
              Campaign
            </label>
            <input
              type="text"
              value={campaign}
              onChange={(e) => setCampaign(e.target.value)}
              placeholder="e.g. Medicare 2026"
              className="mt-1 w-full rounded-md border border-border-soft bg-panel-raised px-3 py-2 text-sm text-text-primary outline-none placeholder:text-text-tertiary focus:border-signal/50"
            />
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-border-soft px-3 py-2 text-xs font-medium text-text-secondary transition-colors hover:text-text-primary"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rounded-md bg-signal px-3 py-2 text-xs font-medium text-base transition-opacity hover:opacity-90"
            >
              {isEditing ? "Save changes" : "Add bot"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}