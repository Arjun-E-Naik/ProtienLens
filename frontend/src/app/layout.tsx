import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { WorkspaceProvider } from "@/context/WorkspaceContext";
import { AppShell } from "@/components/AppShell";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "ProteinLens-OS | Clinical Variant Intelligence & 3D Pocket DMS",
  description:
    "Open-source, local-first clinical genomics platform uniting ESM2 Masked-Marginal LLR, 3D-Pocket Deep Mutational Scanning, True-Path GO DAG, and Auto-Configuring Gemini/Grok XAI.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${mono.variable}`} suppressHydrationWarning>
      <body className="font-sans">
        <WorkspaceProvider>
          <AppShell>{children}</AppShell>
        </WorkspaceProvider>
      </body>
    </html>
  );
}
