"use client";

import { useEffect, useState } from "react";

export function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark" | "system">("system");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const stored = localStorage.getItem("theme") as "light" | "dark" | null;
    if (stored) {
      setTheme(stored);
      document.documentElement.setAttribute("data-theme", stored);
    } else {
      setTheme("system");
      document.documentElement.removeAttribute("data-theme");
    }
  }, []);

  function toggle() {
    if (theme === "dark") {
      setTheme("light");
      localStorage.setItem("theme", "light");
      document.documentElement.setAttribute("data-theme", "light");
    } else if (theme === "light") {
      setTheme("dark");
      localStorage.setItem("theme", "dark");
      document.documentElement.setAttribute("data-theme", "dark");
    } else {
      // system - switch to dark
      setTheme("dark");
      localStorage.setItem("theme", "dark");
      document.documentElement.setAttribute("data-theme", "dark");
    }
  }

  if (!mounted) {
    return (
      <button
        style={{
          background: "transparent",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          padding: "0.35rem 0.6rem",
          color: "var(--muted)",
          fontSize: "0.75rem",
          cursor: "pointer",
        }}
        aria-label="Toggle theme"
      >
        ◐
      </button>
    );
  }

  const icon = theme === "dark" ? "☾" : theme === "light" ? "☀" : "◐";

  return (
    <button
      onClick={toggle}
      title={`Theme: ${theme}`}
      style={{
        background: "transparent",
        border: "1px solid var(--border)",
        borderRadius: "8px",
        padding: "0.35rem 0.6rem",
        color: "var(--muted)",
        fontSize: "0.9rem",
        cursor: "pointer",
        transition: "background 120ms ease, color 120ms ease",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = "var(--panel-2)";
        e.currentTarget.style.color = "var(--ink)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "transparent";
        e.currentTarget.style.color = "var(--muted)";
      }}
      aria-label="Toggle theme"
    >
      {icon}
    </button>
  );
}
