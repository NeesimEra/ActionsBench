import Link from "next/link";
import { notFound } from "next/navigation";
import { ApiUnreachable, NegativePill, StatusPill } from "@/components/pill";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function CaseDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const payload = await api.caseDetail(id);

  if (payload.kind === "http" && payload.status === 404) {
    notFound();
  }
  if (payload.kind !== "payload") {
    return (
      <>
        <h1>{id}</h1>
        <ApiUnreachable />
      </>
    );
  }
  const d = payload.payload;

  return (
    <>
      <h1>
        {d.id} <StatusPill status={d.status} />
        {d.is_negative ? <NegativePill /> : null}
      </h1>
      <p className="lede">{d.title}</p>

      <section>
        <h2>Source</h2>
        <ul className="meta">
          <li>
            Author: <code>{d.author}</code>
            {d.reviewer ? (
              <>
                , reviewed by <code>{d.reviewer}</code>
              </>
            ) : null}
          </li>
          <li>
            Added in corpus {d.added_in}, provenance <code>{d.provenance}</code>
          </li>
          {d.review_record_link ? (
            <li>
              Review record: <a href={`/${d.review_record_link}`}>read it</a>{" "}
              <code>({d.review_record_link})</code>
            </li>
          ) : null}
        </ul>
      </section>

      <section>
        <h2>Expected findings{d.is_negative ? " (clean twin claims)" : ""}</h2>
        <div className="tablewrap">
          <table>
            <thead>
              <tr>
                <th>Class</th>
                <th>File</th>
                <th>Line</th>
                <th>Evidence substring</th>
              </tr>
            </thead>
            <tbody>
              {d.expected.map((expected) => (
                <tr key={`${expected.file}:${expected.line}`}>
                  <td>
                    <Link href={`/classes/${expected.weakness_class}`}>
                      {expected.weakness_class}
                    </Link>
                  </td>
                  <td>
                    <Link href={`/cases/${d.id}/files/${expected.file}`}>{expected.file}</Link>
                  </td>
                  <td>{expected.line}</td>
                  <td>
                    <code>{expected.evidence}</code>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2>Rationale</h2>
        <p>{d.rationale}</p>
        {d.notes ? <p className="meta">Notes: {d.notes}</p> : null}
        {d.references.length > 0 ? (
          <>
            <h2>References</h2>
            <ul>
              {d.references.map((ref) => (
                <li key={ref}>
                  {ref.startsWith("http") ? <a href={ref}>{ref}</a> : ref}
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </section>

      <section>
        <h2>Files</h2>
        <ul>
          {d.files.map((relative) => (
            <li key={relative}>
              <a href={`/cases/${d.id}/files/${relative}`}>{relative}</a>
            </li>
          ))}
        </ul>
        <p className="meta">Shown as text, never executed.</p>
      </section>
    </>
  );
}
