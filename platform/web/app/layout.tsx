import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { api } from "@/lib/api";

export const metadata: Metadata = {
  title: "ActionsBench — a labeled benchmark for GitHub Actions security scanners",
  description:
    "A labeled corpus and per-class results for GitHub Actions workflow security scanners. Read-only evidence, no ranking.",
};

const guardrailSentence = (
  <p>
    Read-only corpus and per-class results. No overall score is shown anywhere on this site,
    and the review status of the labels behind every score is stated with it. See{" "}
    <a href="https://github.com/NeesimEra/ActionsBench/blob/main/docs/adr/0007-hosted-platform.md">ADR 0007</a>.
  </p>
);

const navLinks: [string, string][] = [
  ["/cases", "Cases"],
  ["/results", "Results"],
  ["https://github.com/NeesimEra/ActionsBench/blob/main/docs/PRD.md", "PRD"],
  [
    "https://github.com/NeesimEra/ActionsBench/blob/main/docs/methodology.md",
    "Methodology",
  ],
];

export default async function Layout({ children }: { children: React.ReactNode }) {
  // One fetch, no caching: the footer always reflects what the API answered.
  const summary = await api.summary();
  return (
    <html lang="en">
      <body>
        <header>
          <p className="site">
            <Link href="/">ActionsBench</Link>
          </p>
          <nav>
            {navLinks.map(([href, label]) =>
              href.startsWith("/") ? (
                <Link key={href} href={href}>
                  {label}
                </Link>
              ) : (
                <a key={href} href={href}>
                  {label}
                </a>
              ),
            )}
          </nav>
        </header>
        <main>{children}</main>
        <footer>
          {summary.kind === "payload" ? <p>{summary.payload.provenance}</p> : null}
          {guardrailSentence}
        </footer>
      </body>
    </html>
  );
}
