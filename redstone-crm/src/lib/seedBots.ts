import { Bot } from "./types";

// Used only the first time, before anything is saved to
// localStorage. Once a real backend exists, delete this file
// and have useLocalBots fetch from the API instead.
export const SEED_BOTS: Bot[] = [
  { id: "mary-01", name: "Mary-01", campaign: "Medicare 2026", status: "offline", callsToday: 0 },
  { id: "mary-02", name: "Mary-02", campaign: "Callback 55+", status: "offline", callsToday: 0 },
  { id: "mary-03", name: "Mary-03", campaign: "Outreach Q3", status: "offline", callsToday: 0 },
  { id: "mary-04", name: "Mary-04", campaign: "—", status: "offline", callsToday: 0 },
];