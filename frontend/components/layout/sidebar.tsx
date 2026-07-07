"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  Upload,
  ShieldCheck,
  User,
  Scale,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { useAuth } from "@/lib/auth/auth-context";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/documents/upload", label: "Upload", icon: Upload },
  { href: "/profile", label: "Profile", icon: User },
];

const ADMIN_ITEM = { href: "/admin", label: "Admin Panel", icon: ShieldCheck };

/** Exact match, or a strict sub-path match (never a bare prefix — "/documents"
 * must not match "/documents/upload", only "/documents/123"). */
function matches(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(`${href}/`);
}

/** Only the most specific (longest) matching href is active, so a page like
 * "/documents/upload" doesn't also light up the "Documents" link. */
function useActiveHref(pathname: string, items: { href: string }[]): string | null {
  const candidates = items.filter((item) => matches(pathname, item.href));
  if (candidates.length === 0) return null;
  return candidates.reduce((longest, item) =>
    item.href.length > longest.href.length ? item : longest
  ).href;
}

export function Sidebar() {
  const pathname = usePathname() ?? "";
  const { user } = useAuth();

  const allItems = user?.role === "admin" ? [...NAV_ITEMS, ADMIN_ITEM] : NAV_ITEMS;
  const activeHref = useActiveHref(pathname, allItems);

  return (
    <aside className="flex h-full w-60 shrink-0 flex-col border-r border-border bg-surface-raised 2xl:w-72">
      <div className="flex items-center gap-2 px-5 py-5">
        <Scale className="h-6 w-6 shrink-0 text-accent" />
        <span className="font-display text-lg font-semibold leading-tight text-ink">
          Contract
          <br />
          Risk Analyzer
        </span>
      </div>

      <nav className="flex-1 space-y-0.5 px-3">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 rounded-md border-l-2 border-transparent px-3 py-2 text-sm font-medium text-ink-muted transition-colors",
              "hover:bg-surface-sunken hover:text-ink",
              activeHref === href && "border-accent bg-accent-tint/40 text-accent"
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </Link>
        ))}

        {user?.role === "admin" && (
          <Link
            href={ADMIN_ITEM.href}
            className={cn(
              "flex items-center gap-3 rounded-md border-l-2 border-transparent px-3 py-2 text-sm font-medium text-ink-muted transition-colors",
              "hover:bg-surface-sunken hover:text-ink",
              activeHref === ADMIN_ITEM.href && "border-accent bg-accent-tint/40 text-accent"
            )}
          >
            <ShieldCheck className="h-4 w-4 shrink-0" />
            {ADMIN_ITEM.label}
          </Link>
        )}
      </nav>

      <div className="border-t border-border px-5 py-4 text-xs text-ink-faint">
        Signed in as
        <div className="mt-0.5 truncate font-medium text-ink-muted">{user?.email}</div>
      </div>
    </aside>
  );
}
