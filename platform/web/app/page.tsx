import Link from "next/link";
import { ApiUnreachable } from "@/components/pill";
import { JumpBox } from "@/components/jump-box";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const summary = await api.summary();
  return (
    <>
      <div className="hero">
        <h1>What would you like to inspect?</h1>
        <p className="lede">
          A labeled corpus of minimized GitHub&nbsp;Actions workflows — each labeled with the
          weakness it demonstrates, or its clean twin — and per-class scores for reviewers.
          Everything here is evidence, not a ranking.
        </p>

        {summary.kind === "payload" ? (
          <JumpBox classValues={summary.payload.class_rows.map((row) => row.value)} />
        ) : null}
        {summary.kind !== "payload" ? <ApiUnreachable /> : null}

        <div className="chips">
          {summary.kind === "payload" ? (
            <Link className="chip" href="/cases">
              {summary.payload.case_count} cases
            </Link>
          ) : null}
          <Link className="chip" href="/results">
            Scored results
          </Link>
          <a
            className="chip"
            href="https://github.com/NeesimEra/ActionsBench/blob/main/docs/methodology.md"
            target="_blank"
            rel="noreferrer"
          >
            Methodology ↗
          </a>
          <a
            className="chip"
            href="https://github.com/NeesimEra/ActionsBench/blob/main/docs/adr/0007-hosted-platform.md"
            target="_blank"
            rel="noreferrer"
          >
            ADR 0007 ↗
          </a>
        </div>
      </div>

      {summary.kind === "payload" ? (
        <>
          <div className="statrow">
            <span className="stat">
              <b>{summary.payload.case_count}</b>
              <span>cases</span>
            </span>
            {Object.entries(summary.payload.status_totals).map(([status, count]) => (
              <span className="stat" key={status}>
                <b>{count}</b>
                <span>{status}</span>
              </span>
            ))}
          </div>

          <section>
            <h2>Weakness classes</h2>
            <div className="cardgrid">
              {summary.payload.class_rows.map((row) => (
                <Link key={row.value} className="card" href={`/classes/${row.value}`}>
                  <h3>{row.value}</h3>
                  <span className="count">
                    {row.positives} positive · {row.negatives} negative
                  </span>
                </Link>
              ))}
            </div>
          </section>

          <p className="meta">
            Every case carries a rationale a reviewer can check, a dated review record and
            references. <Link href="/cases">Browse all cases →</Link>
          </p>
        </>
      ) : null}
    </>
  );
}
