# x402-demo

[x402](https://x402.org) (HTTP 402 ベースの AI/エージェント向け決済プロトコル) のデモ。
Base Sepolia 上で USDC を使い、以下 2 パターンを試せます。

- `packages/web` — **ユーザーが MetaMask** で署名 → 有料 API を呼ぶ
- `packages/agent` — **AI エージェントが独自ウォレット (秘密鍵)** で自動決済 → 有料 API を呼ぶ
- `packages/server` — 上記から叩かれる有料 API (Express + `@x402/express`)
- `packages/inspector` — `@x402/*` を使わず stdlib + viem だけで書いた TS クライアント。HTTP / 署名を 7 ステージで全部ログ出力
- `python-inspector/` — 同じものを Python で。Keccak-256 + secp256k1 ECDSA も自前実装(`web3.py` 不使用)

検証と決済は Coinbase が公開している testnet facilitator
(`https://x402.org/facilitator`) が肩代わりします。

## 必要なもの

- Node.js 22+ / pnpm 10+ (`mise install` で揃います)
- Base Sepolia の **ETH**(ガス代) と **USDC** を持った EOA × 2 つ
  - 受取り用 (server の `PAY_TO_ADDRESS`)
  - エージェント用 (agent の `AGENT_PRIVATE_KEY`)
- MetaMask デモ用には MetaMask ブラウザ拡張に Base Sepolia を追加し、テスト USDC を入れた口座を使ってください。
- Faucet
  - ETH: <https://portal.cdp.coinbase.com/products/faucet>
  - USDC: <https://faucet.circle.com>

## セットアップ

```bash
pnpm install

# 環境変数はワークスペースルートの .env 1 つで管理する
cp .env.example .env
# → PAY_TO_ADDRESS / AGENT_PRIVATE_KEY を編集
```

server と agent は両方ともこのルート `.env` を読みます (web 側はデフォルト URL で動くので追加の env は不要)。

## 実行

### サーバー起動 (両パターン共通)

```bash
pnpm dev:server
# http://localhost:4021/api/joke が $0.001 USDC で保護される
```

### パターン 1: MetaMask フロー

```bash
pnpm dev:web
# http://localhost:3000 を開き、MetaMask を接続して "Call paid API" を押す
# → MetaMask が EIP-3009 transferWithAuthorization の署名を求めるので承認
```

### パターン 2: AI エージェントフロー

```bash
pnpm agent
# 秘密鍵から作ったローカル EOA が自動で 402 を解釈し、署名し、再リクエストする
```

## 仕組み (ざっくり)

1. クライアントが保護リソースに GET。
2. サーバーが `402 Payment Required` と「受取り先・金額・チェーン・スキーム」を返す。
3. クライアントは USDC の `transferWithAuthorization` を EIP-712 署名 (オフチェーン) する。
4. 署名を `X-PAYMENT` ヘッダに乗せて同じ URL を再 GET。
5. サーバーは facilitator に検証 (`/verify`) と決済 (`/settle`) を依頼。
6. 決済確定後、本来のレスポンスが返る (`PAYMENT-RESPONSE` ヘッダに receipt 付き)。

つまりユーザー側はガスを払わず、USDC のみで都度課金 API に支払えます。
