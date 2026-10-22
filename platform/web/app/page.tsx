import Link from "next/link";
import { ApiUnreachable } from "@/components/pill";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const summary = await api.summary();
  return (
    <>
      <h1>A labeled benchmark for GitHub&nbsp;Actions workflow security scanners</h1>
      <p className="lede">
        A small hand-built corpus of minimized workflows — each labeled with the weakness it
        demonstrates, or its negative — and harnesses that score scanners against it, one
        weakness class at a time. Everything here is evidence, not a ranking.
      </p>

      {summary.kind === "unreachable" ? <ApiUnreachable /> : null}
      {summary.kind === "http" ? <ApiUnreachable /> : null}

      {summary.kind === "payload" ? (
        <>
          <section>
            <h2>The corpus</h2>
            <table>
              <thead>
                <tr>
                  <th>Weakness class</th>
                  <th>Positive</th>
                  <th>Negative</th>
                </tr>
              </thead>
              <tbody>
                {summary.payload.class_rows.map((row) => (
                  <tr key={row.value}>
                    <td>
                      <Link href={`/classes/${row.value}`}>{row.value}</Link>
                    </td>
                    <td>{row.positives}</td>
                    <td>{row.negatives}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section>
            <h2>At a glance</h2>
            <ul>
              <li>
                <strong>{summary.payload.case_count}</strong> cases. Statuses:{" "}
                {Object.entries(summary.payload.status_totals).map(([status, count], index, all) => (
                  <span key={status}>
                    <strong>{status}</strong> {count}
                    {index < all.length - 1 ? ", " : ""}
                  </span>
                ))}
                .
              </li>
              <li>
                Every case carries a rationale a reviewer can check, a dated review record and
                references; browse under <Link href="/cases">cases</Link>.
              </li>
            </ul>
          </section>
        </>
      ) : null}
    </>
  );
}
