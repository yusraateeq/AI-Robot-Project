# Redstone CRM — AI Voice Bot Agent System

AI-powered voice bot system integrated with VICIdial, using OpenAI and ElevenLabs for natural conversations.

## Architecture

```
redstone-crm/       Next.js frontend (React, Firebase Auth, Tailwind)
AI Agents/          Python backend (FastAPI, SQLite, OpenAI, ElevenLabs)
```

- **Frontend**: Next.js 16 + Firebase Auth (Google & Email/Password) + Chart.js dashboard + sidebar layout
- **Backend**: FastAPI + aiosqlite + VICIdial automation + Playwright browser agent
- **Auth**: Firebase Authentication + JWT session tokens

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Firebase project (see [SETUP.md](./SETUP.md))

### Backend

```powershell
cd "AI Agents"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env        # edit with your keys
python run.py
```

### Frontend

```powershell
cd redstone-crm
cp .env.local.example .env.local   # edit with Firebase config
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Environment Variables

| File | Purpose |
|------|---------|
| `AI Agents/.env` | Backend: OpenAI, ElevenLabs, VICIdial, Firebase Admin |
| `redstone-crm/.env.local` | Frontend: Firebase Web SDK config |

See `AI Agents/.env.example` and `SETUP.md` for all required keys.

## License

Private — internal use only.
