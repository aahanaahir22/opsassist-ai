import type { Metadata } from "next";
import "./globals.css";
import { OpsAssistAuthProvider } from "./auth-provider";

export const metadata: Metadata = {
  title: "OpsAssist AI — Evidence-Backed Incident Intelligence",
  description: "Investigate synthetic incidents, inspect cited evidence, simulate remediations, approve safe actions and verify recovery.",
  icons: { icon: "/favicon.svg", shortcut: "/favicon.svg" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><OpsAssistAuthProvider>{children}</OpsAssistAuthProvider></body></html>;
}
