import os
from typing import Any
from urllib import request
from pathlib import Path
from http.client import HTTPConnection
import base64
import json
import time
import secrets
from pprint import pprint

from dotenv import load_dotenv

from keccak import keccak256
from secp import address, sign

ROOT_ENV = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ROOT_ENV)

PRIVATE_KEY_HEX = os.environ.get("AGENT_PRIVATE_KEY", "")
if not PRIVATE_KEY_HEX:
    raise SystemExit("AGENT_PRIVATE_KEY is required (set it in the root .env)")
PRIV = int(PRIVATE_KEY_HEX, 16)
WALLET_ADDRESS = os.environ.get("AGENT_ADDRESS") or address(PRIV)

def print_lines():
    return print("\n" + "=" * 80 + "\n")

def enc_address(addr_hex: str) -> bytes:
    """address -> 32 bytes (left-padded with 12 zero bytes)."""
    h = addr_hex[2:] if addr_hex.startswith("0x") else addr_hex
    return bytes(12) + bytes.fromhex(h)

def enc_uint256(n: int) -> bytes:
    return n.to_bytes(32, "big")

def enc_bytes32(h: str) -> bytes:
    raw = h[2:] if h.startswith("0x") else h
    return bytes.fromhex(raw)


# step 1. GET /api/joke/
print_lines()
print("GET /api/joke/")
print_lines()
conn = HTTPConnection("localhost", 4021)
conn.request("GET", "/api/joke")
resp = conn.getresponse()
print("status", resp.status)
for name, value in resp.getheaders():
    print(f"{name:<30}: {value}")

payment_required = resp.getheader("PAYMENT-REQUIRED")
conn.close()

# step 2. sign the payment request
print_lines()
print("signing payment request")
print_lines()

payment_required_json = json.loads(base64.b64decode(payment_required))
print("payment required:")
pprint(payment_required_json)

## EIP-712 signing
accepted = payment_required_json["accepts"][0]
chain_id = int(accepted["network"].split(":")[1])
now = int(time.time())
valid_after = str(now)
valid_before = str(now + accepted["maxTimeoutSeconds"])
nonce_hex = "0x" + secrets.token_bytes(32).hex()

domain = {
    "name": accepted["extra"]["name"],
    "version": accepted["extra"]["version"],
    "chainId": chain_id,
    "verifyingContract": accepted["asset"],
}

domain_type_hash = keccak256(
    b"EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
)

domain_separator = keccak256(
    domain_type_hash
    + keccak256(domain["name"].encode())
    + keccak256(domain["version"].encode())
    + enc_uint256(domain["chainId"])
    + enc_address(domain["verifyingContract"])
)

authorization = {
    "from": WALLET_ADDRESS,
    "to": accepted["payTo"],
    "value": accepted["amount"],
    "validAfter": valid_after,
    "validBefore": valid_before,
    "nonce": nonce_hex,
}

struct_type_hash = keccak256(
    b"TransferWithAuthorization(address from,address to,uint256 value,"
    b"uint256 validAfter,uint256 validBefore,bytes32 nonce)"
)

struct_hash = keccak256(
    struct_type_hash
    + enc_address(authorization["from"])
    + enc_address(authorization["to"])
    + enc_uint256(int(authorization["value"]))
    + enc_uint256(int(authorization["validAfter"]))
    + enc_uint256(int(authorization["validBefore"]))
    + enc_bytes32(authorization["nonce"])
)

digest = keccak256(b"\x19\x01" + domain_separator + struct_hash)
print("digest", "0x" + digest.hex())

# step 3. sign the digest
print_lines()
print("signing digest")
print_lines()

r, s, v = sign(PRIV, digest)
signature = r.to_bytes(32, "big") + s.to_bytes(32, "big") + bytes([v])
sig_hex = "0x" + signature.hex()

payment_payload = {
    "x402Version": payment_required_json["x402Version"],
    "resource": payment_required_json["resource"],
    "accepted": accepted,
    "payload": {
        "signature": sig_hex,
        "authorization": authorization,
    },
}

ps_b64 = base64.b64encode(json.dumps(payment_payload).encode()).decode()
headers2 = {"Accept": "*/*", "PAYMENT-SIGNATURE": ps_b64}
conn = HTTPConnection("localhost", 4021)
conn.request("GET", "/api/joke", headers=headers2)
resp = conn.getresponse()
print("status", resp.status)
for name, value in resp.getheaders():
    print(f"{name:<30}: {value}")
print("response body:", resp.read().decode())
conn.close()
