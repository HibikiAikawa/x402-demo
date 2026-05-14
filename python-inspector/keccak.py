"""Keccak-256 (Ethereum variant) implementation in pure Python.

The Keccak algorithm originally submitted to the NIST hash competition
became SHA-3, but with one change: the padding byte was changed from
0x01 to 0x06. Ethereum uses the ORIGINAL Keccak (padding 0x01), which
is why hashlib.sha3_256(b"") differs from keccak256(b"").

Spec: https://keccak.team/keccak_specs_summary.html
"""

# 24 round constants
_RC = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]

# Rotation offsets r[x][y] for the rho step
_R = [
    [ 0, 36,  3, 41, 18],
    [ 1, 44, 10, 45,  2],
    [62,  6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39,  8, 14],
]

_MASK64 = (1 << 64) - 1


def _rotl(x: int, n: int) -> int:
    """64-bit left rotation."""
    n %= 64
    return ((x << n) | (x >> (64 - n))) & _MASK64


def _keccak_f(state: list[list[int]]) -> None:
    """Permutation Keccak-f[1600] (24 rounds), in-place on the 5x5 lane state."""
    for rnd in range(24):
        # θ (theta) — diffusion across columns
        C = [state[x][0] ^ state[x][1] ^ state[x][2] ^ state[x][3] ^ state[x][4] for x in range(5)]
        D = [C[(x - 1) % 5] ^ _rotl(C[(x + 1) % 5], 1) for x in range(5)]
        for x in range(5):
            for y in range(5):
                state[x][y] ^= D[x]

        # ρ (rho) + π (pi) — bit-rotation + lane reshuffling
        B = [[0] * 5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                B[y][(2 * x + 3 * y) % 5] = _rotl(state[x][y], _R[x][y])

        # χ (chi) — non-linear mixing within rows
        for x in range(5):
            for y in range(5):
                state[x][y] = B[x][y] ^ ((~B[(x + 1) % 5][y] & _MASK64) & B[(x + 2) % 5][y])

        # ι (iota) — round constant
        state[0][0] ^= _RC[rnd]


def keccak256(data: bytes) -> bytes:
    """Keccak-256 hash. Returns 32 bytes."""
    rate = 136  # bytes (= 1088 bits) — for output length 256
    # Padding: 0x01 ... 0x80 (Ethereum's Keccak; SHA-3 would use 0x06 here)
    pad_len = rate - (len(data) % rate)
    if pad_len == 1:
        # Special case: 0x01 and 0x80 end up in the same byte
        padded = data + b"\x81"
    else:
        padded = data + b"\x01" + b"\x00" * (pad_len - 2) + b"\x80"

    # 5x5 lanes of 64-bit words, all zero
    state = [[0] * 5 for _ in range(5)]

    # Absorbing phase
    for offset in range(0, len(padded), rate):
        block = padded[offset:offset + rate]
        for i in range(rate // 8):
            lane = int.from_bytes(block[i * 8:(i + 1) * 8], "little")
            # Lanes are stored in column-major order: index i -> (x = i%5, y = i//5)
            state[i % 5][i // 5] ^= lane
        _keccak_f(state)

    # Squeezing phase — first 32 bytes = first 4 lanes
    out = bytearray()
    for i in range(4):
        out += state[i % 5][i // 5].to_bytes(8, "little")
    return bytes(out)


# ---- self-test ------------------------------------------------------
if __name__ == "__main__":
    vectors = {
        b"": "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470",
        b"abc": "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45",
        b"The quick brown fox jumps over the lazy dog":
            "4d741b6f1eb29cb2a9b9911c82f56fa8d73b04959d3d9d222895df6c0b28aa15",
    }
    for inp, expected in vectors.items():
        got = keccak256(inp).hex()
        status = "OK " if got == expected else "FAIL"
        print(f"[{status}] keccak256({inp!r}) = {got}")
        if got != expected:
            print(f"        expected {expected}")
