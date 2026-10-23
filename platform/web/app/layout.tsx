import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { api } from "@/lib/api";
import { SidebarNav } from "@/components/sidebar-nav";

export const metadata: Metadata = {
  title: "ActionsBench — a labeled benchmark for GitHub Actions security scanners",
  description:
    "A labeled corpus and per-class results for GitHub Actions workflow security scanners. Read-only evidence, no ranking.",
};

export default async function Layout({ children }: { children: React.ReactNode }) {
  // One fetch, no caching: the sidebar always reflects what the API answered.
  const summary = await api.summary();
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <aside className="sidebar">
            <p className="site">
              <Link href="/">ActionsBench</Link>
            </p>
            <nav aria-label="Platform navigation">
              <SidebarNav />
            </nav>
            <div className="sidebottom">
              {summary.kind === "payload" ? <p>{summary.payload.provenance}</p> : null}
              <p>
                Read-only corpus and per-class results. No overall score is shown anywhere
                on this site, and the review status of the labels behind every score is
                stated with it.
              </p>
            </div>
          </aside>
          <main>{children}</main>
        </div>
      </body>
    </html>
  );
}
