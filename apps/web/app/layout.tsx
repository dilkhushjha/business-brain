import "./globals.css";
import "./customer-intelligence.css";
import type { ReactNode } from "react";
import DashboardReasoningOverlay from "../components/DashboardReasoningOverlay";

export default function RootLayout({ children }: { children: ReactNode }) {
  return <html lang="en"><body>{children}<DashboardReasoningOverlay /></body></html>;
}
