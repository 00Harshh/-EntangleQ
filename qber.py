"""
QBER Calculation and Attack Detection Module
Computes Quantum Bit Error Rate and classifies channel security.
"""

from dataclasses import dataclass


QBER_THRESHOLDS = {
    "secure":    0.05,   # < 5%  : ideal channel
    "warning":   0.11,   # 5-11% : noise or weak attack
    "attack":    0.20,   # 11-20%: likely eavesdropping (Eve)
    "abort":     1.00,   # > 20% : abort — channel compromised
}


@dataclass
class QBERResult:
    qber: float
    error_bits: int
    total_bits: int
    status: str           # "secure" | "warning" | "attack" | "abort"
    attack_detected: bool
    message: str
    confidence: float     # 0–1 confidence that channel is secure


def compute_qber(alice_bits: list[int], bob_bits: list[int]) -> QBERResult:
    """
    Compute QBER between Alice and Bob's sifted key samples.
    """
    if len(alice_bits) != len(bob_bits):
        raise ValueError("Alice and Bob bit arrays must be equal length.")

    total = len(alice_bits)
    if total == 0:
        raise ValueError("Cannot compute QBER on empty bit array.")

    errors = sum(a != b for a, b in zip(alice_bits, bob_bits))
    qber = errors / total

    # Classify
    if qber < QBER_THRESHOLDS["secure"]:
        status = "secure"
        attack_detected = False
        message = "Channel is clean. Key exchange successful."
        confidence = 1.0 - (qber / QBER_THRESHOLDS["secure"]) * 0.3

    elif qber < QBER_THRESHOLDS["warning"]:
        status = "warning"
        attack_detected = False
        message = "Elevated QBER detected. Possible channel noise or weak interference."
        confidence = 0.6 - (qber - QBER_THRESHOLDS["secure"]) * 5

    elif qber < QBER_THRESHOLDS["attack"]:
        status = "attack"
        attack_detected = True
        message = "⚠️ Eavesdropping likely detected! QBER exceeds 11% threshold."
        confidence = 0.15

    else:
        status = "abort"
        attack_detected = True
        message = "🚨 ABORT: QBER > 20%. Channel severely compromised. Do not use key."
        confidence = 0.0

    return QBERResult(
        qber=round(qber, 4),
        error_bits=errors,
        total_bits=total,
        status=status,
        attack_detected=attack_detected,
        message=message,
        confidence=round(max(0.0, confidence), 4),
    )


def qber_from_protocol_result(result: dict) -> QBERResult:
    """
    Convenience wrapper: compute QBER directly from BB84/E91 protocol result dict.
    """
    raw_key = result.get("raw_key", [])
    qber_value = result.get("qber", 0.0)
    total = len(raw_key)
    errors = round(qber_value * total)

    # Reconstruct simulated alice/bob arrays consistent with the reported QBER
    alice_bits = raw_key.copy()
    bob_bits   = raw_key.copy()
    # Flip 'errors' bits in bob to match computed QBER
    flip_indices = list(range(min(errors, total)))
    for idx in flip_indices:
        bob_bits[idx] = 1 - bob_bits[idx]

    return compute_qber(alice_bits, bob_bits)


def qber_series_analysis(qber_history: list[float]) -> dict:
    """
    Analyze a time-series of QBER values for trend-based attack detection.
    Returns trend and anomaly flags.
    """
    if len(qber_history) < 3:
        return {"trend": "insufficient_data", "anomaly": False, "rising": False}

    import numpy as np
    arr = np.array(qber_history)
    slope = np.polyfit(range(len(arr)), arr, 1)[0]
    mean  = float(np.mean(arr))
    std   = float(np.std(arr))
    latest = qber_history[-1]

    rising  = slope > 0.005
    anomaly = latest > mean + 2 * std

    return {
        "mean_qber": round(mean, 4),
        "std_dev":   round(std, 4),
        "slope":     round(slope, 6),
        "rising":    rising,
        "anomaly":   anomaly,
        "trend":     "rising" if rising else "stable",
        "alert":     rising or anomaly,
    }
