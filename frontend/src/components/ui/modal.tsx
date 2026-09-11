"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";

type ModalProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  children: React.ReactNode;
};

export function Modal({ open, onOpenChange, title, children }: ModalProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[min(92vw,420px)] -translate-x-1/2 -translate-y-1/2 rounded-xl border border-white/15 bg-black p-5 text-white shadow-2xl">
          <div className="mb-4 flex items-center justify-between gap-3">
            <Dialog.Title className="text-lg font-semibold text-white">{title}</Dialog.Title>
            <Dialog.Close asChild>
              <Button type="button" variant="ghost" size="icon" aria-label="Close">
                <X className="h-4 w-4" />
              </Button>
            </Dialog.Close>
          </div>
          {children}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
