"""
BB84 Quantum Key Distribution Protocol
Simulates full BB84 with optional Eve eavesdropping attack.
"""

import random
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

simulator = AerSimulator()


def encode_bit(bit: int, basis: str) -> QuantumCircuit:
    """Encode a single qubit using the given basis (Z or X)."""
    qc = QuantumCircuit(1, 1)
    if bit == 1:
        qc.x(0)
    if basis == "X":
        qc.h(0)
    return qc


def measure_qubit(qc: QuantumCircuit, basis: str) -> int:
    """Measure the qubit in the given basis."""
    if basis == "X":
        qc.h(0)
    qc.measure(0, 0)
    job = simulator.run(qc, shots=1)
    result = job.result()
    counts = result.get_counts()
    return int(list(counts.keys())[0])


def eve_intercept(qc: QuantumCircuit) -> QuantumCircuit:
    """Eve intercepts and re-sends qubit in a random basis — introduces errors."""
    eve_basis = random.choice(["Z", "X"])
    eve_bit = measure_qubit(qc.copy(), eve_basis)
    # Eve re-encodes what she measured
    new_qc = encode_bit(eve_bit, eve_basis)
    return new_qc


def run_bb84(num_bits: int = 256, eve_present: bool = False, noise_level: float = 0.0):
    """
    Full BB84 simulation.

    Returns:
        dict with raw_key, sifted_key, qber, alice_bits, bob_bits, num_bits
    """
    alice_bits = [random.randint(0, 1) for _ in range(num_bits)]
    alice_bases = [random.choice(["Z", "X"]) for _ in range(num_bits)]
    bob_bases = [random.choice(["Z", "X"]) for _ in range(num_bits)]

    bob_results = []

    for i in range(num_bits):
        qc = encode_bit(alice_bits[i], alice_bases[i])

        # Apply noise (random bit flip channel)
        if noise_level > 0 and random.random() < noise_level:
            qc.x(0)

        # Eve intercepts
        if eve_present and random.random() < 0.5:
            qc = eve_intercept(qc)

        # Bob measures
        measured = measure_qubit(qc.copy(), bob_bases[i])
        bob_results.append(measured)

    # Sifting: keep bits where Alice and Bob used the same basis
    sifted_alice = []
    sifted_bob = []
    for i in range(num_bits):
        if alice_bases[i] == bob_bases[i]:
            sifted_alice.append(alice_bits[i])
            sifted_bob.append(bob_results[i])

    # QBER calculation on a sample (first 50% of sifted key)
    sample_size = max(1, len(sifted_alice) // 2)
    sample_alice = sifted_alice[:sample_size]
    sample_bob = sifted_bob[:sample_size]
    errors = sum(a != b for a, b in zip(sample_alice, sample_bob))
    qber = errors / sample_size if sample_size > 0 else 0.0

    # Final key from the remaining bits
    final_key = sifted_alice[sample_size:]

    return {
        "protocol": "BB84",
        "num_bits": num_bits,
        "sifted_length": len(sifted_alice),
        "key_length": len(final_key),
        "raw_key": final_key,
        "qber": round(qber, 4),
        "eve_present": eve_present,
        "noise_level": noise_level,
        "secure": qber < 0.11,
    }
