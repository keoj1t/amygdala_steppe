"use client";

import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useToastStore } from "@/store/toast-store";

export function Toaster() {
  const { toasts, dismiss } = useToastStore();
  return (
    <div className="fixed right-4 top-4 z-[60] grid w-[min(92vw,360px)] gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={cn(
            "flex items-center justify-between gap-3 rounded-xl border px-4 py-3 text-sm shadow-lg",
            toast.tone === "success" && "border-[#ADD8E6]/50 bg-[#ADD8E6]/15 text-white",
            toast.tone === "error" && "border-[#CC5500]/60 bg-[#CC5500]/15 text-white",
            toast.tone === "info" && "border-white/20 bg-white/10 text-white"
          )}
        >
          <span>{toast.title}</span>
          <Button type="button" variant="ghost" size="icon" onClick={() => dismiss(toast.id)} aria-label="Dismiss">
            <X className="h-4 w-4" />
          </Button>
        </div>
      ))}
    </div>
  );
}
