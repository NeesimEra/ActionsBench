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
                  var stored = localStorage.getItem('theme');
                  if (stored === 'light' || stored === 'dark') {
                    document.documentElement.setAttribute('data-theme', stored);
                  } else if (window.matchMedia('(prefers-color-scheme: light)').matches) {
                    document.documentElement.setAttribute('data-theme', 'light');
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
            <div className="sidebar-head">
              <p className="site">
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
