# Homework 4: Campus Customs Shop + Chatbot

## AI provider note

Every AI call uses the model **`gpt-6-luna`** through the **Portkey** gateway.

- Model: `gpt-6-luna`, read from `PORTKEY_MODEL`
- API key: read from `PORTKEY_API_KEY` in a local `.env` file; the Portkey base URL
  is `PORTKEY_BASE_URL` (defaults to `https://api.portkey.ai/v1`)
- The key is sent to Portkey as a header, and the key's own default config routes
  the call to OpenAI's `gpt-6-luna`.
- The real `.env` is never committed; `.env.example` lists the variable names only.

## Setup

1. Place the data pack one level above this folder so you have `../data/campus_customs.db`
   and `../data/products/`. (Or set `DATA_DIR` in `.env` to wherever you unzipped it.)
2. Copy `.env.example` to `.env` and fill in your values.

## Run the back end (FastAPI, port 8000)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

## Run the front end (React + Vite, port 5173)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite forwards `/api` and `/images` requests to the back end.
