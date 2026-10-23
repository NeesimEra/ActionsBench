import { notFound } from "next/navigation";
import { ApiUnreachable } from "@/components/pill";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function CaseFilePage({
  params,
}: {
  params: Promise<{ id: string; path: string[] }>;
}) {
  const { id, path } = await params;
  // 64,000 bytes maximum is enforced server-side by the API's file endpoint.
  const payload = await api.caseFile(id, path.join("/"));

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

  return (
    <>
      <h1>{path[path.length - 1]}</h1>
      <p className="meta">
        File of <a href={`/cases/${id}`}>{id}</a>, served as text by the platform API — never
        executed.
      </p>
      <pre>{payload.text}</pre>
    </>
  );
}
