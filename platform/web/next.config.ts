import type { NextConfig } from "next";

// The API base the app proxies to. Set API_BASE when the API runs elsewhere; the
// default matches `actionsbench-platform-api`'s own default (platform/api).
const API_BASE = process.env.API_BASE ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // Same-origin proxy: the browser only ever talks to this Next.js origin, and
  // server components fetch `${API_BASE}/api/...` directly for the same payload.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_BASE}/api/:path*` }];
  },
};

export default nextConfig;
