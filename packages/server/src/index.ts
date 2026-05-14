import { config as dotenvConfig } from "dotenv";
dotenvConfig({ path: "../../.env" });

import cors from "cors";
import express from "express";
import { HTTPFacilitatorClient } from "@x402/core/server";
import { ExactEvmScheme } from "@x402/evm/exact/server";
import { paymentMiddleware, x402ResourceServer } from "@x402/express";

const PAY_TO = process.env.PAY_TO_ADDRESS as `0x${string}` | undefined;
const FACILITATOR_URL = process.env.FACILITATOR_URL ?? "https://x402.org/facilitator";
const PORT = Number(process.env.PORT ?? 4021);

if (!PAY_TO) {
  throw new Error("PAY_TO_ADDRESS is required");
}

const facilitatorClient = new HTTPFacilitatorClient({ url: FACILITATOR_URL });
const resourceServer = new x402ResourceServer(facilitatorClient).register(
  "eip155:84532",
  new ExactEvmScheme(),
);

const app = express();
app.use(
  cors({
    exposedHeaders: ["PAYMENT-REQUIRED", "PAYMENT-RESPONSE"],
  }),
);

app.use(
  paymentMiddleware(
    {
      "GET /api/joke": {
        accepts: [
          {
            scheme: "exact",
            price: "$0.01",
            network: "eip155:84532",
            payTo: PAY_TO,
          },
        ],
        description: "Premium joke endpoint",
        mimeType: "application/json",
      },
    },
    resourceServer,
  ),
);

const JOKES = [
  "Why do programmers prefer dark mode? Because light attracts bugs.",
  "I told my computer I needed a break, and it said 'no problem, I'll go to sleep.'",
  "There are 10 types of people in this world: those who understand binary and those who don't.",
];

app.get("/", (_req, res) => {
  res.json({ ok: true, paid_endpoint: "/api/joke" });
});

app.get("/api/joke", (_req, res) => {
  res.json({ joke: JOKES[Math.floor(Math.random() * JOKES.length)] });
});

app.listen(PORT, () => {
  console.log(`x402 server listening on http://localhost:${PORT}`);
  console.log(`  Paid endpoint: GET /api/joke ($0.001 USDC on Base Sepolia)`);
  console.log(`  Receiving address: ${PAY_TO}`);
});
