"use client";
import { useEffect, useState } from "react";
import { Bot } from "./types";

const STORAGE_KEY = "redstone:bots";

export function useLocalBots(seed: Bot[]) {
  const [bots, setBots] = useState<Bot[]>(() => {
    try {
      if (typeof window === "undefined") return seed;
      const stored = window.localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : seed;
    } catch {
      return seed;
    }
  });

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(bots));
    } catch {
      // Storage full or unavailable — changes just won't persist.
    }
  }, [bots]);

  return { bots, setBots, hydrated: true };
}