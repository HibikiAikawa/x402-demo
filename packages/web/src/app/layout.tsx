import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "x402 MetaMask Demo",
  description: "Pay-per-request with x402 / USDC on Base Sepolia using MetaMask",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ja">
      <body style={{ fontFamily: "system-ui, sans-serif", margin: 0, padding: 24 }}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
