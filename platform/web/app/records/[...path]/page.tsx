import { notFound } from "next/navigation";
import { ApiUnreachable } from "@/components/pill";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function RecordPage({
  params,
}: {
  params: Promise<{ path: string[] }>;
}) {
  const { path } = await params;
  // The API serves only `.md`/`.txt` files under the repository's docs directory.
  const payload = await api.record(path.join("/"));

  if (payload.kind === "http" && payload.status === 404) {
    notFound();
  }
  if (payload.kind !== "payload") {
    return (
      <>
        <h1>Record</h1>
        <ApiUnreachable />
      </>
    );
  }

  return (
    <>
      <h1>{path[path.length - 1]}</h1>
      <p className="meta">Dated review record, served as text by the platform API.</p>
      <pre>{payload.text}</pre>
    </>
  );
}
