import type { Metadata } from "next";
import "./globals.css";
import AuthProvider from "@/src/components/AuthProvider";

export const metadata: Metadata = {
  title: "Redstone AI Voice Bot CRM",
  description: "AI voice bot CRM with VICIdial integration",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body><AuthProvider>{children}</AuthProvider></body>
    </html>
  );
}  