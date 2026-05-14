# python-inspector

x402 v2 のクライアント側を Python で**ゼロから手書き**したもの。

依存は Python stdlib + `python-dotenv` のみ。`web3.py` / `eth-account` 等は一切使っていません。
ハッシュ(Keccak-256)も楕円曲線署名(secp256k1 ECDSA)も自前実装です。

## ファイル

| ファイル | 役割 |
|---|---|
| `keccak.py` | Keccak-256 (Ethereum 派生。NIST の SHA3-256 と padding が違う) |
| `secp.py` | secp256k1 の点演算 + ECDSA 署名 (EIP-2 の low-s 正規化 + Ethereum 形式の v=27/28) |
| `inspector.py` | メイン。1〜7 ステージで HTTP + 中間データを整形出力 |
| `pyproject.toml` | uv プロジェクト定義 (依存は python-dotenv のみ) |

## 動かす

1 つ上の階層の `packages/server` を起動してから:

```bash
cd python-inspector
uv sync                       # venv 作成 + python-dotenv インストール
uv run python inspector.py
```

ルートの `.env` の `AGENT_PRIVATE_KEY` と `API_URL` を読みます。

## セルフテスト

Keccak と secp256k1 はそれぞれ単独で実行するとベクタテストが走ります:

```bash
uv run python keccak.py
# [OK ] keccak256(b'') = c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470
# [OK ] keccak256(b'abc') = 4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45
# [OK ] keccak256(b'The quick brown fox jumps over the lazy dog') = 4d741b6f1eb29cb2a9b9911c82f56fa8d73b04959d3d9d222895df6c0b28aa15

uv run python secp.py
# ルートの .env の AGENT_PRIVATE_KEY と AGENT_ADDRESS を読み、
# 秘密鍵から導出したアドレスが AGENT_ADDRESS と一致するかを確認します。
# [OK ] address(0x........…) -> 0x...
```
