import Link from "next/link";

type Crumb = {
  label: string;
  href?: string;
};

export function Breadcrumbs({ crumbs }: { crumbs: Crumb[] }) {
  return (
    <nav aria-label="Breadcrumb" style={{ marginBottom: "1rem" }}>
      <ol
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          gap: "0.5rem",
          listStyle: "none",
          padding: 0,
          margin: 0,
          fontSize: "0.82rem",
        }}
      >
        {crumbs.map((crumb, i) => (
          <li key={i} style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            {crumb.href ? (
              <Link href={crumb.href} style={{ color: "var(--muted)" }}>
                {crumb.label}
              </Link>
            ) : (
              <span style={{ color: "var(--ink)" }}>{crumb.label}</span>
            )}
            {i < crumbs.length - 1 && <span style={{ color: "var(--faint)" }}>/</span>}
          </li>
        ))}
      </ol>
    </nav>
  );
}
