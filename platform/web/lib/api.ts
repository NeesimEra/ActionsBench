// Typed access to the platform API (platform/api). The UI holds no corpus or scoring
// logic of its own: it renders exactly what these endpoints return (ADR 0007).

export const API_BASE = process.env.API_BASE ?? "http://127.0.0.1:8000";

/** A JSON response, or the HTTP status when the API answered with one that is not OK. */
export type JsonRequest<T> =
  | { kind: "payload"; payload: T }
  | { kind: "http"; status: number }
  | { kind: "unreachable" };

async function getJson<T>(path: string): Promise<JsonRequest<T>> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  } catch {
    return { kind: "unreachable" };
  }
  if (response.ok) {
    return { kind: "payload", payload: (await response.json()) as T };
  }
  return { kind: "http", status: response.status };
}

/** A plain text response: status plus body. */
export type TextRequest =
  | { kind: "payload"; text: string }
  | { kind: "http"; status: number }
  | { kind: "unreachable" };

async function getText(path: string): Promise<TextRequest> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  } catch {
    return { kind: "unreachable" };
  }
  if (response.ok) {
    return { kind: "payload", text: await response.text() };
  }
  return { kind: "http", status: response.status };
}

export type ClassRow = { value: string; positives: number; negatives: number };

export type SummaryPayload = {
  case_count: number;
  class_rows: ClassRow[];
  status_totals: Record<string, number>;
  provenance: string;
};

export type CaseListItem = {
  id: string;
  title: string;
  is_negative: boolean;
  classes: string[];
  status: string;
  added_in: string;
};

export type ExpectedFinding = {
  weakness_class: string;
  file: string;
  line: number;
  evidence: string;
};

export type CaseDetailPayload = {
  id: string;
  title: string;
  is_negative: boolean;
  status: string;
  added_in: string;
  provenance: string;
  author: string;
  reviewer: string | null;
  rationale: string;
  notes: string | null;
  references: string[];
  expected: ExpectedFinding[];
  files: string[];
  review_record_link: string | null;
};

export type ClassCases = {
  value: string;
  cases: { id: string; title: string; is_negative: boolean; status: string }[];
};

export type ScoreRow = {
  cls: string;
  in_scope: boolean;
  tp: number;
  fp: number;
  fn: number;
  precision: string;
  recall: string;
  f1: string;
  uncovered: number;
  out_of_scope_findings: number;
};

export type ResultEntry = {
  tool: string;
  version: string;
  path: string;
  scope: string;
  configuration: string;
  matching: string;
  cases_scored: number;
  case_count: number;
  not_run: string[];
  rows: ScoreRow[];
};

export type ResultsPayload = {
  provenance: string;
  harness_version: string;
  corpus_version: string;
  problems: string[];
  entries: ResultEntry[];
};

export const api = {
  summary: () => getJson<SummaryPayload>("/api/summary"),
  cases: () => getJson<{ cases: CaseListItem[] }>("/api/cases"),
  caseDetail: (id: string) => getJson<CaseDetailPayload>(`/api/cases/${id}`),
  classCases: (cls: string) => getJson<ClassCases>(`/api/classes/${cls}`),
  results: () => getJson<ResultsPayload>("/api/results"),
  caseFile: (id: string, relative: string) =>
    getText(`/api/cases/${id}/files/${relative}`),
  record: (relative: string) => getText(`/api/records/${relative}`),
};

export const API_UNREACHABLE =
  "The platform API is unreachable, so this page has nothing to render. Start it with `uv run --project platform/api actionsbench-platform-api` and reload.";
