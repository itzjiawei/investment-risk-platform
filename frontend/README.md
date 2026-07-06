# Frontend

React + TypeScript + Vite frontend for the Investment Risk Analytics Platform.

## Scripts

```bash
npm install
npm run dev
npm run build
```

`npm run dev` starts the local Vite development server. `npm run build` type-checks the frontend and creates the production bundle in `dist/`.

## Configuration

The frontend reads the backend API base URL from:

```text
VITE_API_BASE_URL
```

Local default:

```text
http://127.0.0.1:8000
```

For Vercel, set `VITE_API_BASE_URL` to the deployed Render backend URL and redeploy the frontend.
