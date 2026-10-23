"use client";

// Sidebar links with an active state. Client-side only for `usePathname`; every link
// target is a static string, and all data still arrives through server components.

import Link from "next/link";
import { usePathname } from "next/navigation";

const internal: [string, string][] = [
  ["/cases", "Cases"],
  ["/results", "Results"],
];

const external: [string, string][] = [
  ["https://github.com/NeesimEra/ActionsBench/blob/main/docs/PRD.md", "PRD"],
  ["https://github.com/NeesimEra/ActionsBench/blob/main/docs/methodology.md", "Methodology"],
  ["https://github.com/NeesimEra/ActionsBench/blob/main/docs/adr/0007-hosted-platform.md", "ADR 0007"],
];

export function SidebarNav() {
  const pathname = usePathname();
  return (
    <>
      {internal.map(([href, label]) => (
        <Link
          key={href}
          href={href}
          className={`navlink${pathname === href || pathname.startsWith(`${href}/`) ? " active" : ""}`}
        >
          {label}
        </Link>
      ))}
      {external.map(([href, label]) => (
        <a key={href} href={href} className="navlink" target="_blank" rel="noreferrer">
          {label}
          <span className="ext">↗</span>
        </a>
      ))}
    </>
  );
}
