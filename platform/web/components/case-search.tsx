"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { NegativePill, StatusPill } from "@/components/pill";
import type { CaseListItem } from "@/lib/api";

export function CaseSearch({ cases }: { cases: CaseListItem[] }) {
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [classFilter, setClassFilter] = useState("all");

  const classes = useMemo(() => {
    const all = new Set<string>();
    cases.forEach((c) => c.classes.forEach((cls) => all.add(cls)));
    return Array.from(all).sort();
  }, [cases]);

  const statuses = useMemo(() => {
    const all = new Set<string>();
    cases.forEach((c) => all.add(c.status));
    return Array.from(all).sort();
  }, [cases]);

  const filtered = useMemo(() => {
    const q = query.toLowerCase().trim();
    return cases.filter((c) => {
      const matchesQuery =
        q === "" ||
        c.id.toLowerCase().includes(q) ||
        c.title.toLowerCase().includes(q) ||
        c.classes.some((cls) => cls.toLowerCase().includes(q));
      const matchesStatus = statusFilter === "all" || c.status === statusFilter;
      const matchesClass = classFilter === "all" || c.classes.includes(classFilter);
      return matchesQuery && matchesStatus && matchesClass;
    });
  }, [cases, query, statusFilter, classFilter]);

  return (
    <>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", margin: "1.5rem 0", alignItems: "center" }}>
        <input
          type="search"
          placeholder="Search by ID, title, or class..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{
            flex: "1 1 20rem",
            background: "var(--panel)",
            border: "1px solid var(--border)",
            borderRadius: "10px",
            padding: "0.5rem 0.9rem",
            color: "var(--ink)",
            font: "inherit",
            fontSize: "0.9rem",
          }}
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border)",
            borderRadius: "10px",
            padding: "0.5rem 0.9rem",
            color: "var(--ink)",
            font: "inherit",
            fontSize: "0.85rem",
          }}
        >
          <option value="all">All statuses</option>
          {statuses.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={classFilter}
          onChange={(e) => setClassFilter(e.target.value)}
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border)",
            borderRadius: "10px",
            padding: "0.5rem 0.9rem",
            color: "var(--ink)",
            font: "inherit",
            fontSize: "0.85rem",
          }}
        >
          <option value="all">All classes</option>
          {classes.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        {(query || statusFilter !== "all" || classFilter !== "all") && (
          <button
            onClick={() => {
              setQuery("");
              setStatusFilter("all");
              setClassFilter("all");
            }}
            style={{
              background: "transparent",
              border: "1px solid var(--border)",
              borderRadius: "10px",
              padding: "0.5rem 0.9rem",
              color: "var(--muted)",
              font: "inherit",
              fontSize: "0.85rem",
              cursor: "pointer",
            }}
          >
            Clear filters
          </button>
        )}
      </div>
      <p className="meta" style={{ margin: "-0.75rem 0 1rem" }}>
        Showing {filtered.length} of {cases.length} cases
      </p>
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
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: "center", color: "var(--muted)", padding: "2rem" }}>
                  No cases match your filters
                </td>
              </tr>
            ) : (
              filtered.map((entry) => (
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
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
