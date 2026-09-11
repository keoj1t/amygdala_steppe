import { Toaster } from "@/components/ui/toaster";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="grid min-h-screen place-items-center bg-black p-4">
      {children}
      <Toaster />
    </main>
  );
}
