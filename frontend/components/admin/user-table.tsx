"use client";

import type { AdminUserOut } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils/format";

export function UserTable({
  users,
  onToggleActive,
  onToggleRole,
}: {
  users: AdminUserOut[];
  onToggleActive: (userId: number, isActive: boolean) => void;
  onToggleRole: (userId: number, role: "admin" | "user") => void;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-ink-faint">
            <th className="py-2 pr-4 font-medium">User</th>
            <th className="py-2 pr-4 font-medium">Role</th>
            <th className="py-2 pr-4 font-medium">Documents</th>
            <th className="py-2 pr-4 font-medium">Status</th>
            <th className="py-2 pr-4 font-medium">Joined</th>
            <th className="py-2 pr-0 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id} className="border-b border-border/60 last:border-0">
              <td className="py-3 pr-4">
                <div className="font-medium text-ink">{u.full_name}</div>
                <div className="text-xs text-ink-faint">{u.email}</div>
              </td>
              <td className="py-3 pr-4">
                <Badge className="capitalize">{u.role}</Badge>
              </td>
              <td className="py-3 pr-4 tabular-nums text-ink-muted">{u.document_count}</td>
              <td className="py-3 pr-4">
                {u.is_active ? (
                  <span className="text-success">Active</span>
                ) : (
                  <span className="text-danger">Disabled</span>
                )}
              </td>
              <td className="py-3 pr-4 text-ink-faint">{formatDate(u.created_at)}</td>
              <td className="py-3 pr-0 text-right">
                <div className="flex justify-end gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onToggleRole(u.id, u.role === "admin" ? "user" : "admin")}
                  >
                    Make {u.role === "admin" ? "User" : "Admin"}
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => onToggleActive(u.id, !u.is_active)}>
                    {u.is_active ? "Disable" : "Enable"}
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
