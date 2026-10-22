# actionsbench-platform-web

Next.js 16 (App Router, TypeScript) UI for the read-only ActionsBench platform,
ADR 0007, milestone P0. It is presentational only: all data — the corpus, its
labels and per-class results — comes from the JSON API in `../api`, which is the
single source of truth. The app never loads the corpus, validates findings or
scores anything itself.

```sh
npm ci
npm run dev   # http://localhost:3000; proxies /api/* to the API
```

`API_BASE` (default `http://127.0.0.1:8000`) decides where `/api/*` is proxied and
where server components fetch. Run `npm run typecheck` and `npm run build` for the
checks CI runs.
