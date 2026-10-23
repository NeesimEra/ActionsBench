// Small presentational helpers shared by the data pages.

export function Pill({ value, negative }: { value: string; negative?: boolean }) {
  return negative ? <span className="pill neg">{value}</span> : <span className={`pill ${value}`}>{value}</span>;
}

export function NegativePill() {
  return <Pill value="negative" negative />;
}

export function StatusPill({ status }: { status: string }) {
  return <Pill value={status} />;
}

export function ProblemNote({ children }: { children: React.ReactNode }) {
  return <div className="problem">{children}</div>;
}

export function ApiUnreachable() {
  return (
    <div className="problem">
      The platform API is unreachable, so this page has nothing to render. Start it with{" "}
      <code>uv run --project platform/api actionsbench-platform-api</code> and reload.
    </div>
  );
}
