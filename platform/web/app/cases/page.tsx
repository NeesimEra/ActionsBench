import Link from "next/link";
import { ApiUnreachable, NegativePill, StatusPill } from "@/components/pill";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function CasesPage() {
  const payload = await api.cases();
  return (
    <>
      <h1>Corpus cases</h1>
      <p>
        Negatives are marked <code>negative</code>; every positive has a clean twin unless
        stated otherwise. <code>ai-reviewed</code> means these labels were reviewed by
        separate AI agent sessions against primary sources, with a dated per-case review
        record.
      </p>

      {payload.kind === "payload" ? (
        <div className="tablewrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Classes</th>
                <th>Status</th>
                <th>Added in</th>
              </tr>
            </thead>
            <tbody>
              {payload.payload.cases.map((entry) => (
                <tr key={entry.id}>
                  <td>
                    <Link href={`/cases/${entry.id}`}>{entry.id}</Link>
                  </td>
                  <td>
                    {entry.title}
                    {entry.is_negative ? <NegativePill /> : null}
                  </td>
                  <td>{entry.classes.join(", ")}</td>
                  <td>
                    <StatusPill status={entry.status} />
                  </td>
                  <td>{entry.added_in}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <ApiUnreachable />
      )}
    </>
  );
}
