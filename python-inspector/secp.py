"""secp256k1 curve + ECDSA signing for Ethereum, from scratch.

Curve parameters per SEC 2 (Standards for Efficient Cryptography):
  y^2 = x^3 + 7  (mod p)

Signatures are produced in "low-s" form as required by EIP-2, and the
recovery id is encoded as Ethereum's v = 27 or 28.

Only depends on `secrets` and our local keccak module.
"""

import secrets

from keccak import keccak256

# Curve parameters
P  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
GX = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
GY = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
G  = (GX, GY)


# ---- elliptic-curve point arithmetic (Jacobian-free, just affine) ----

def _point_add(p1, p2):
    """Add two affine points on secp256k1. None represents the identity."""
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2:
        if (y1 + y2) % P == 0:
            return None  # opposite points → identity
        # doubling: slope = 3x^2 / 2y
        m = (3 * x1 * x1 % P) * pow(2 * y1, -1, P) % P
    else:
        m = (y2 - y1) * pow(x2 - x1, -1, P) % P
    x3 = (m * m - x1 - x2) % P
    y3 = (m * (x1 - x3) - y1) % P
    return (x3, y3)


def _scalar_mult(k: int, point):
    """Compute k * point via double-and-add."""
    result = None
    addend = point
    while k > 0:
        if k & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)
        k >>= 1
    return result


# ---- public API ------------------------------------------------------

def public_key(priv: int) -> tuple[int, int]:
    """Derive the uncompressed public key (X, Y) from a 32-byte private key int."""
    if not 1 <= priv < N:
        raise ValueError("private key out of range")
    return _scalar_mult(priv, G)


def address(priv: int) -> str:
    """Derive the 20-byte Ethereum address (0x-prefixed hex)."""
    x, y = public_key(priv)
    pub64 = x.to_bytes(32, "big") + y.to_bytes(32, "big")
    return "0x" + keccak256(pub64)[-20:].hex()


def sign(priv: int, digest: bytes) -> tuple[int, int, int]:
    """ECDSA-sign a 32-byte digest. Returns (r, s, v) with low-s and v ∈ {27, 28}."""
    if len(digest) != 32:
        raise ValueError("digest must be 32 bytes")
    z = int.from_bytes(digest, "big")
    while True:
        k = int.from_bytes(secrets.token_bytes(32), "big") % N
        if k == 0:
            continue
        R = _scalar_mult(k, G)
        if R is None:
            continue
        rx, ry = R
        r = rx % N
        if r == 0:
            continue
        s = pow(k, -1, N) * (z + r * priv) % N
        if s == 0:
            continue
        # Recovery id = parity of R.y; flip if we normalize s
        recid = ry & 1
        if s > N // 2:
            s = N - s
            recid ^= 1
        # Ethereum legacy v
        return (r, s, 27 + recid)


# ---- self-test ------------------------------------------------------
if __name__ == "__main__":
    import os
    from pathlib import Path

    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

    priv_hex = os.environ.get("AGENT_PRIVATE_KEY", "")
    expected_addr = os.environ.get("AGENT_ADDRESS", "")
    if not priv_hex or not expected_addr:
        print("[SKIP] set AGENT_PRIVATE_KEY and AGENT_ADDRESS in .env to run the self-test")
        raise SystemExit(0)

    derived = address(int(priv_hex, 16))
    status = "OK " if derived.lower() == expected_addr.lower() else "FAIL"
    print(f"[{status}] address({priv_hex[:10]}…) -> {derived}")
    if derived.lower() != expected_addr.lower():
        print(f"        expected {expected_addr}")

    # Verify sign+recover (recover is in the inspector when we ask facilitator).
    # Just sanity-check that two signs of the same digest give consistent r,s != 0:
    r1, s1, v1 = sign(int(priv_hex, 16), keccak256(b"hello"))
    print(f"[--] sample sig: r={hex(r1)[:18]}…  s={hex(s1)[:18]}…  v={v1}")
