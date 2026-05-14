"use client";

import { useEffect, useState } from "react";
import {
  useAccount,
  useConnect,
  useDisconnect,
  usePublicClient,
  useSwitchChain,
  useWalletClient,
} from "wagmi";
import { baseSepolia } from "wagmi/chains";
import { x402Client, wrapFetchWithPayment } from "@x402/fetch";
import { ExactEvmScheme } from "@x402/evm/exact/client";
import { walletClientToX402Signer } from "@/lib/x402Signer";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:4021/api/joke";

export default function Home() {
  const { address, isConnected, chainId } = useAccount();
  const { connectors, connect, status: connectStatus, error: connectError } = useConnect();
  const { disconnect } = useDisconnect();
  const { switchChainAsync } = useSwitchChain();
  const { data: walletClient } = useWalletClient();
  const publicClient = usePublicClient();

  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string>("");
  const [error, setError] = useState<string>("");

  useEffect(() => {
    if (isConnected && chainId !== baseSepolia.id) {
      switchChainAsync({ chainId: baseSepolia.id }).catch(console.error);
    }
  }, [isConnected, chainId, switchChainAsync]);

  const callPaidApi = async () => {
    if (!walletClient || !publicClient) return;
    setBusy(true);
    setError("");
    setResult("");
    try {
      const signer = walletClientToX402Signer(walletClient, publicClient);
      const client = new x402Client().register("eip155:84532", new ExactEvmScheme(signer));
      const fetchWithPayment = wrapFetchWithPayment(fetch, client);
      const response = await fetchWithPayment(API_URL);
      const data = await response.json();
      setResult(JSON.stringify(data, null, 2));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main style={{ maxWidth: 640, margin: "0 auto" }}>
      <h1>x402 + MetaMask demo</h1>
      <p>
        Base Sepolia の USDC で <code>{API_URL}</code> を呼び出します。 MetaMask で
        EIP-3009 (transferWithAuthorization) の署名を求められるので承認してください。
      </p>

      <section style={{ marginTop: 24 }}>
        {isConnected ? (
          <>
            <p>
              Connected: <code>{address}</code> (chainId {chainId})
            </p>
            <button type="button" onClick={() => disconnect()}>
              Disconnect
            </button>
          </>
        ) : (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {connectors.map((c) => (
              <button
                key={c.uid}
                type="button"
                onClick={() => connect({ connector: c })}
                disabled={connectStatus === "pending"}
              >
                Connect: {c.name}
              </button>
            ))}
            {connectError ? <p style={{ color: "crimson" }}>{connectError.message}</p> : null}
          </div>
        )}
      </section>

      <section style={{ marginTop: 24 }}>
        <button
          type="button"
          onClick={callPaidApi}
          disabled={!isConnected || busy || chainId !== baseSepolia.id}
        >
          {busy ? "Paying..." : "Call paid API ($0.001 USDC)"}
        </button>
      </section>

      {result ? (
        <pre style={{ marginTop: 16, background: "#f5f5f5", padding: 12 }}>{result}</pre>
      ) : null}
      {error ? <p style={{ color: "crimson", marginTop: 16 }}>{error}</p> : null}
    </main>
  );
}
