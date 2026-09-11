import { ProtectedShell } from "@/components/app/protected-shell";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <ProtectedShell>{children}</ProtectedShell>;
}
