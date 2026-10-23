"use client";

// The home command bar, Grok-style: type a case id or a weakness class and jump.
// Pure navigation: it only decides between two known URL shapes, it renders no data.

import { useState } from "react";
import { useRouter } from "next/navigation";

const CASE_ID = /^ab-[a-z]{3}-[0-9]{4}$/i;

export function JumpBox({ classValues }: { classValues: string[] }) {
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  function jump(event: React.FormEvent) {
    event.preventDefault();
    const query = value.trim();
    if (CASE_ID.test(query)) {
      router.push(`/cases/${query.toUpperCase()}`);
      setError(null);
      return;
    }
    const slug = query.toLowerCase().replace(/[^a-z0-9-]+/g, "-").replace(/^-|-$/g, "");
    if (slug && classValues.includes(slug)) {
      router.push(`/classes/${slug}`);
      setError(null);
    } else {
      setError("No case or weakness class matches that. Case ids look like AB-INJ-0001.");
    }
  }

  return (
    <>
      <form className="jumpbox" onSubmit={jump} role="search" aria-label="Jump to a case or weakness class">
        <input
          value={value}
          onChange={(event) => {
            setValue(event.target.value);
            setError(null);
          }}
          placeholder="Jump to a case id or weakness class…"
          aria-label="Case id or weakness class"
          autoFocus
        />
        <button type="submit" aria-label="Jump">→</button>
      </form>
      <p className={`jump-hint${error ? " error" : ""}`} aria-live="polite">
        {error ??
          "Try a case id like AB-INJ-0001, or a class name like injection, secrets-exposure, or unpinned-dependency."}
      </p>
    </>
  );
}
