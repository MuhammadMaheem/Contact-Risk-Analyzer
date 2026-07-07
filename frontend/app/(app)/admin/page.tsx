"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { adminApi } from "@/lib/api/admin";
import { useAuth } from "@/lib/auth/auth-context";
import type { AdminUserOut, AuditLogOut, DocumentListItem, SystemStatsOut } from "@/lib/types";
import { PageHeader } from "@/components/layout/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { UserTable } from "@/components/admin/user-table";
import { AuditLogTable } from "@/components/admin/audit-log-table";
import { SystemStatsCards } from "@/components/admin/system-stats-cards";
import { DocumentsTable } from "@/components/documents/documents-table";
import { Skeleton } from "@/components/ui/skeleton";

export default function AdminPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [users, setUsers] = useState<AdminUserOut[] | null>(null);
  const [logs, setLogs] = useState<AuditLogOut[] | null>(null);
  const [stats, setStats] = useState<SystemStatsOut | null>(null);
  const [documents, setDocuments] = useState<DocumentListItem[] | null>(null);

  useEffect(() => {
    if (!authLoading && user && user.role !== "admin") {
      router.replace("/dashboard");
    }
  }, [authLoading, user, router]);

  function reloadAll() {
    adminApi.users().then(setUsers);
    adminApi.logs().then(setLogs);
    adminApi.stats().then(setStats);
    adminApi.documents().then(setDocuments);
  }

  useEffect(() => {
    if (user?.role === "admin") reloadAll();
  }, [user]);

  if (!user || user.role !== "admin") return null;

  return (
    <div>
      <PageHeader
        title="Admin Panel"
        description="Manage users, monitor AI usage, and review system activity."
      />

      <Tabs defaultValue="users">
        <TabsList>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="stats">System Stats</TabsTrigger>
          <TabsTrigger value="logs">Audit Log</TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
        </TabsList>

        <TabsContent value="users">
          <Card>
            <CardHeader>
              <CardTitle>Manage Users</CardTitle>
            </CardHeader>
            <CardContent>
              {users === null ? (
                <Skeleton className="h-40" />
              ) : (
                <UserTable
                  users={users}
                  onToggleActive={async (userId, isActive) => {
                    await adminApi.updateUser(userId, { is_active: isActive });
                    reloadAll();
                  }}
                  onToggleRole={async (userId, role) => {
                    await adminApi.updateUser(userId, { role });
                    reloadAll();
                  }}
                />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="stats">
          {stats === null ? <Skeleton className="h-24" /> : <SystemStatsCards stats={stats} />}
        </TabsContent>

        <TabsContent value="logs">
          <Card>
            <CardHeader>
              <CardTitle>System Logs</CardTitle>
            </CardHeader>
            <CardContent>
              {logs === null ? <Skeleton className="h-40" /> : <AuditLogTable logs={logs} />}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="documents">
          <Card>
            <CardHeader>
              <CardTitle>All Uploaded Documents</CardTitle>
            </CardHeader>
            <CardContent>
              {documents === null ? <Skeleton className="h-40" /> : <DocumentsTable documents={documents} />}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
