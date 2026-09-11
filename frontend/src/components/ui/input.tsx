import type { InputHTMLAttributes, TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "focus-ring h-10 w-full rounded-xl border border-white/15 bg-black px-3 text-sm text-white shadow-sm transition placeholder:text-white/30",
        className
      )}
      {...props}
    />
  );
}

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "focus-ring min-h-28 w-full resize-none rounded-xl border border-white/15 bg-black px-3 py-2 text-sm text-white shadow-sm transition placeholder:text-white/30",
        className
      )}
      {...props}
    />
  );
}
