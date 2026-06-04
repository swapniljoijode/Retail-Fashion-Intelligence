import type { Metadata } from "next";
import "./globals.css";
import SideNav from "@/components/SideNav";

export const metadata: Metadata = {
  title: "Fashion Retail Intelligence",
  description:
    "End-to-end medallion data platform — executive dashboards across Sales, Marketing, Category, Planning, and Placement domains.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="flex h-screen overflow-hidden" style={{ background: "var(--bg)" }}>
        <SideNav />
        <main className="flex-1 overflow-y-auto p-6 lg:p-8">{children}</main>
      </body>
    </html>
  );
}
