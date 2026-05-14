import { config as dotenvConfig } from "dotenv";
dotenvConfig({ path: "../../.env" });

import { privateKeyToAccount } from "viem/accounts";
import { x402Client, wrapFetchWithPayment, decodePaymentResponseHeader } from "@x402/fetch";
import { ExactEvmScheme } from "@x402/evm/exact/client";

const PRIVATE_KEY = process.env.AGENT_PRIVATE_KEY as `0x${string}` | undefined;
const API_URL = process.env.API_URL ?? "http://localhost:4021/api/joke";

if (!PRIVATE_KEY) {
  throw new Error("AGENT_PRIVATE_KEY is required");
}

const account = privateKeyToAccount(PRIVATE_KEY);
console.log(`Agent wallet: ${account.address}`);

const client = new x402Client().register("eip155:84532", new ExactEvmScheme(account));
const fetchWithPayment = wrapFetchWithPayment(fetch, client);

console.log(`Calling ${API_URL}...`);
const response = await fetchWithPayment(API_URL);
const data = await response.json();
console.log("Response:", data);

const paymentHeader = response.headers.get("payment-response");
if (paymentHeader) {
  console.log("Payment receipt:", decodePaymentResponseHeader(paymentHeader));
}
