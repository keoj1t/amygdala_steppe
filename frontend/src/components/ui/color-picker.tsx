"use client";

import { Input } from "@/components/ui/input";

type ColorPickerProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
};

export function ColorPicker({ label, value, onChange }: ColorPickerProps) {
  return (
    <label className="grid gap-2 text-sm font-medium text-white/75">
      <span>{label}</span>
      <div className="flex items-center gap-2">
        <input
          type="color"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="h-10 w-12 rounded-xl border border-white/15 bg-black p-1"
        />
        <Input value={value} onChange={(event) => onChange(event.target.value)} pattern="^#[0-9A-Fa-f]{6}$" />
      </div>
    </label>
  );
}
