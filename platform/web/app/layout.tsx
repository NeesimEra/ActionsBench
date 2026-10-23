import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { api } from "@/lib/api";
import { SidebarNav } from "@/components/sidebar-nav";
import { ThemeToggle } from "@/components/theme-toggle";

export const metadata: Metadata = {
  title: "ActionsBench — a labeled benchmark for GitHub Actions security scanners",
  description:
    "A labeled corpus and per-class results for GitHub Actions workflow security scanners. Read-only evidence, no ranking.",
};

export default async function Layout({ children }: { children: React.ReactNode }) {
  // One fetch, no caching: the sidebar always reflects what the API answered.
  const summary = await api.summary();
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  const theme = localStorage.getItem('theme');
                  if (theme === 'light') {
                    document.documentElement.setAttribute('data-theme', 'light');
                  } else if (theme === 'dark') {
                    document.documentElement.setAttribute('data-theme', 'dark');
                  }
                } catch (e) {}
              })();
            `,
          }}
        />
      </head>
      <body>
        <div className="shell">
          <aside className="sidebar">
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%", marginBottom: "0.75rem" }}>
              <p className="site" style={{ margin: 0 }}>
                <Link href="/">ActionsBench</Link>
              </p>
              <ThemeToggle />
            </div>
            <nav aria-label="Platform navigation">
              <SidebarNav />
            </nav>
          </aside>
          <main>
            {children}
            <footer className="guardrail">
              {summary.kind === "payload" ? <p>{summary.payload.provenance}</p> : null}
              <p>
                Read-only corpus and per-class results. No overall score is shown anywhere on
                this site, and the review status of the labels behind every score is stated
                with it.
              </p>
            </footer>
          </main>
        </div>
      </body>
    </html>
  );
}
