# Resume Intelligence Frontend (React + Vite)

A modern React frontend for the Resume Intelligence & Candidate Matching System.

## Quick Start

Prereqs:
- Node.js 18+ recommended
- Backend gateway running on `http://localhost:8000`

```bash
cd frontend
npm install
npm run dev
```

Vite default dev URL: `http://localhost:5173`

## Configuration

The API base URL is configured in `frontend/src/utils/api.js`:

```js
const API_BASE_URL = "http://localhost:8000";
```

## Pages

- `frontend/src/pages/Match.jsx`
  - Submit a job description to `POST /api/v1/match` (via the gateway)
  - Shows validation errors and loading state

- `frontend/src/pages/Results.jsx`
  - Renders ranked candidates
  - Displays recruiter-style explanations and Strengths/Gaps bullets (from `candidate.explanation`)

- `frontend/src/pages/Analytics.jsx`
  - Uses `GET /api/v1/stats` and `GET /health` (via the gateway)
  - Refresh is manual (no auto-refresh interval)

## Project Structure

```text
frontend/
|-- public/
|   `-- index.html
|-- src/
|   |-- components/
|   |-- context/
|   |-- pages/
|   |-- utils/
|   |-- App.jsx
|   |-- index.jsx
|   `-- index.css
|-- package.json
|-- tailwind.config.js
|-- postcss.config.js
|-- vite.config.js
`-- .gitignore
```

## Troubleshooting

- If the UI cannot reach the backend:
  - Confirm gateway is running: `http://localhost:8000/health`
  - Confirm `API_BASE_URL` points to the gateway (port 8000)

