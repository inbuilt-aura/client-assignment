import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = { title: "Service coverage | NOVA", description: "Manage where your business serves customers." };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
