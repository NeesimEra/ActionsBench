import { ApiUnreachable } from "@/components/pill";
import { CaseSearch } from "@/components/case-search";
import { Breadcrumbs } from "@/components/breadcrumbs";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function CasesPage() {
  const payload = await api.cases();
  return (
    <>
      <Breadcrumbs crumbs={[{ label: "Home", href: "/" }, { label: "Cases" }]} />
      <h1>Corpus cases</h1>
      <p>
        Negatives are marked <code>negative</code>; every positive has a clean twin unless
        stated otherwise. <code>ai-reviewed</code> means these labels were reviewed by
        separate AI agent sessions against primary sources, with a dated per-case review
        record.
      </p>

      {payload.kind === "payload" ? <CaseSearch cases={payload.payload.cases} /> : <ApiUnreachable />}
    </>
  );
}
