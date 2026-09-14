import type { Metadata } from "next";
import Navbar from "@/components/Navbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "DriveScope | VLA Evaluation & Experiment Infrastructure",
  description: "Reproducible experiment infrastructure for Vision-Language-Action driving agents.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-zinc-950 text-zinc-100 flex flex-col min-h-screen antialiased">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="border-t border-zinc-800/80 py-6 text-center text-xs text-zinc-500">
          DriveScope &bull; VLA Experiment &amp; Evaluation Infrastructure &bull; CPU / Portable Architecture
        </footer>
      </body>
    </html>
  );
}
