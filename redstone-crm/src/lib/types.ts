export type BotStatus = "active" | "online" | "offline" | "restarting";

export interface Bot {
  id: string;
  name: string;
  campaign: string;
  status: BotStatus;
  callsToday: number;
}

export type CallOutcome = "transferred" | "no-answer" | "hung-up" | "voicemail";

export interface CallLog {
  id: string;
  customerName: string;
  botName: string;
  duration: string; // mm:ss
  outcome: CallOutcome;
  recordingUrl: string | null;
  timestamp: string; // ISO string
}