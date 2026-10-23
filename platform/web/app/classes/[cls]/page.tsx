import Link from "next/link";
import { notFound } from "next/navigation";
import { ApiUnreachable, NegativePill, StatusPill } from "@/components/pill";
import { Breadcrumbs } from "@/components/breadcrumbs";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ClassPage({ params }: { params: Promise<{ cls: string }> }) {
  const { cls } = await params;
  const payload = await api.classCases(cls);

  if (payload.kind === "http" && payload.status === 404) {
    notFound();
  }
  if (payload.kind !== "payload") {
    return (
      <>
        <Breadcrumbs crumbs={[{ label: "Home", href: "/" }, { label: "Classes", href: "/" }, { label: cls }]} />
        <h1>{cls}</h1>
        <ApiUnreachable />
      </>
    );
  }

  return (
    <>
      <Breadcrumbs crumbs={[{ label: "Home", href: "/" }, { label: "Classes", href: "/" }, { label: payload.payload.value }]} />
      <h1>{payload.payload.value}</h1>
      <p>
        All cases labeled (positive or negative) for this class. A negative case is the clean
        twin a scanner must not report.
      </p>
      <div className="tablewrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Title</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {payload.payload.cases.map((entry) => (
              <tr key={entry.id}>
                <td>
                  <Link href={`/cases/${entry.id}`}>{entry.id}</Link>
                  {entry.is_negative ? <NegativePill /> : null}
                </td>
                <td>{entry.title}</td>
                <td>
                  <StatusPill status={entry.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
