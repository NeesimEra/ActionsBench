"use client";

import { useState } from "react";

export function CopyButton({ text, label = "Copy" }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Fallback silently fails
    }
  }

  return (
    <button
      onClick={copy}
      title={copied ? "Copied!" : `Copy ${label}`}
      style={{
        background: "var(--panel)",
        border: "1px solid var(--border)",
        borderRadius: "8px",
        padding: "0.25rem 0.65rem",
        color: copied ? "var(--good)" : "var(--muted)",
        font: "inherit",
        fontSize: "0.75rem",
        cursor: "pointer",
        transition: "color 120ms ease",
      }}
    >
      {copied ? "Copied" : label}
    </button>
  );
}
