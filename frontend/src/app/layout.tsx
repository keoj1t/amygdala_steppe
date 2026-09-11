import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "amygdala content factory",
  description: "AI-ready content operations workspace"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
