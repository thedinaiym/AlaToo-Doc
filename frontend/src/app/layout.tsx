import type { Metadata } from "next";
import type { ReactNode } from "react";

import Header from "../components/Header";

export const metadata: Metadata = {
  title: "Alatoo-Doc",
  description: "University document management portal",
};

type RootLayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50">
        <Header />
        <main>{children}</main>
      </body>
    </html>
  );
}
