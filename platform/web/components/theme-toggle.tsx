"use client";

// Light/dark switch. The initial value comes from localStorage; if nothing is
// stored the OS preference decides (the inline script in layout.tsx applies it
// before paint, so there is no flash). Only the theme attribute changes — no
// data, scoring or corpus behaviour is involved.

import { useEffect, useState } from "react";

type Theme = "light" | "dark";

function resolvedTheme(): Theme {
  const stored = localStorage.getItem("theme");
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("dark");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setTheme(resolvedTheme());
    setMounted(true);
  }, []);

  function toggle() {
    const next: Theme = theme === "dark" ? "light" : "dark";
    setTheme(next);
    localStorage.setItem("theme", next);
    document.documentElement.setAttribute("data-theme", next);
  }

  const icon = mounted && theme === "light" ? "☀" : "☾";
  const label = mounted
    ? `Switch to ${theme === "dark" ? "light" : "dark"} theme`
    : "Toggle theme";

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={toggle}
      aria-label={label}
      title={label}
      suppressHydrationWarning
    >
      <span suppressHydrationWarning aria-hidden="true">
        {icon}
      </span>
    </button>
  );
}
