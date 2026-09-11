import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "focus-ring inline-flex h-10 items-center justify-center gap-2 rounded-xl px-4 text-sm font-semibold transition duration-200 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary: "bg-[#CC5500] text-white shadow-sm hover:bg-[#CC5500]/80",
        secondary: "bg-[#ADD8E6] text-black hover:bg-[#ADD8E6]/80",
        ghost: "bg-transparent text-white/70 hover:bg-white/10 hover:text-white",
        danger: "bg-red-600 text-white hover:bg-red-700"
      },
      size: {
        sm: "h-9 px-3",
        md: "h-10 px-4",
        icon: "h-10 w-10 px-0"
      }
    },
    defaultVariants: {
      variant: "primary",
      size: "md"
    }
  }
);

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  };

export function Button({ className, variant, size, asChild, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : "button";
  return <Comp className={cn(buttonVariants({ variant, size, className }))} {...props} />;
}
