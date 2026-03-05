"""
One-Time Pad (OTP) Encryption Module
Uses the quantum-generated key for XOR encryption.
"""

import base64


def key_to_bytes(key: list[int]) -> bytes:
    """Convert a list of bits [0,1,1,0,...] to bytes."""
    # Pad to multiple of 8
    padded = key + [0] * ((8 - len(key) % 8) % 8)
    result = bytearray()
    for i in range(0, len(padded), 8):
        byte = 0
        for bit in padded[i:i+8]:
            byte = (byte << 1) | bit
        result.append(byte)
    return bytes(result)


def xor_encrypt(message: str, key: list[int]) -> dict:
    """
    Encrypt a message using OTP XOR with a quantum key.

    Returns ciphertext as base64, along with metadata.
    Raises ValueError if key is too short.
    """
    msg_bytes = message.encode("utf-8")
    key_bytes = key_to_bytes(key)

    if len(key_bytes) < len(msg_bytes):
        raise ValueError(
            f"Key too short: need {len(msg_bytes)} bytes, have {len(key_bytes)}. "
            f"Generate a longer quantum key (increase num_bits)."
        )

    # XOR
    cipher = bytes(m ^ k for m, k in zip(msg_bytes, key_bytes[:len(msg_bytes)]))
    ciphertext_b64 = base64.b64encode(cipher).decode("utf-8")

    return {
        "ciphertext": ciphertext_b64,
        "message_length": len(msg_bytes),
        "key_bits_used": len(msg_bytes) * 8,
        "key_bits_available": len(key) ,
        "encryption": "OTP-XOR",
    }


def xor_decrypt(ciphertext_b64: str, key: list[int]) -> str:
    """
    Decrypt a base64 OTP-XOR ciphertext using the same quantum key.
    """
    cipher = base64.b64decode(ciphertext_b64.encode("utf-8"))
    key_bytes = key_to_bytes(key)

    if len(key_bytes) < len(cipher):
        raise ValueError("Key too short for decryption.")

    plain = bytes(c ^ k for c, k in zip(cipher, key_bytes[:len(cipher)]))
    return plain.decode("utf-8")


def check_key_capacity(key: list[int], message: str) -> dict:
    """Check if a key is long enough to encrypt a given message."""
    key_bytes = len(key) // 8
    msg_bytes = len(message.encode("utf-8"))
    return {
        "key_capacity_bytes": key_bytes,
        "message_bytes": msg_bytes,
        "sufficient": key_bytes >= msg_bytes,
        "surplus_bits": (key_bytes - msg_bytes) * 8,
    }
