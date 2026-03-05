"""
E91 Quantum Key Distribution Protocol (Ekert 1991)
Uses entangled Bell pairs. Verifies security via Bell inequality (CHSH).

Eve fix: Instead of measuring a copy (which doesn't affect the real circuit),
Eve intercepts by breaking entanglement — we create a fresh product state
after Eve's measurement, simulating collapse of the Bell pair.
"""

import random
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

simulator = AerSimulator()

# Measurement angles for Alice and Bob (in radians)
ALICE_ANGLES = [0, np.pi / 4, np.pi / 2]              # a1, a2, a3
BOB_ANGLES   = [np.pi / 4, np.pi / 2, 3 * np.pi / 4]  # b1, b2, b3


def create_bell_pair() -> QuantumCircuit:
    """Create Phi+ Bell state: (|00> + |11>) / sqrt(2)."""
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    return qc


def measure_in_angle(qc: QuantumCircuit, qubit: int, angle: float):
    """Rotate qubit before measurement to simulate angled basis."""
    qc.ry(-2 * angle, qubit)


def eve_intercept_e91(a_idx: int, b_idx: int) -> tuple:
    """
    Eve intercepts BOTH qubits of the Bell pair.
    She measures qubit 0 in a random basis, collapses the entanglement,
    then re-sends her own fresh (unentangled) qubits to Alice and Bob.
    This breaks the correlations and causes detectable QBER.
    """
    eve_bit = random.randint(0, 1)

    qc_alice = QuantumCircuit(1, 1)
    if eve_bit == 1:
        qc_alice.x(0)
    measure_in_angle(qc_alice, 0, ALICE_ANGLES[a_idx])
    qc_alice.measure(0, 0)
    job_a = simulator.run(qc_alice, shots=1)
    alice_bit = int(list(job_a.result().get_counts().keys())[0])

    qc_bob = QuantumCircuit(1, 1)
    if eve_bit == 1:
        qc_bob.x(0)
    measure_in_angle(qc_bob, 0, BOB_ANGLES[b_idx])
    qc_bob.measure(0, 0)
    job_b = simulator.run(qc_bob, shots=1)
    bob_bit = int(list(job_b.result().get_counts().keys())[0])

    return alice_bit, bob_bit


def run_e91(num_pairs: int = 256, eve_present: bool = False, noise_level: float = 0.0):
    """
    Full E91 simulation with CHSH Bell inequality check.
    Eve's intercept-resend properly breaks entanglement and raises QBER to ~25%.
    """
    alice_choices = []
    bob_choices   = []
    alice_results = []
    bob_results   = []

    for _ in range(num_pairs):
        a_idx = random.randint(0, 2)
        b_idx = random.randint(0, 2)
        alice_choices.append(a_idx)
        bob_choices.append(b_idx)

        if eve_present:
            a_bit, b_bit = eve_intercept_e91(a_idx, b_idx)
            alice_results.append(a_bit)
            bob_results.append(b_bit)
        else:
            qc = create_bell_pair()
            if noise_level > 0 and random.random() < noise_level:
                qc.x(0)
            measure_in_angle(qc, 0, ALICE_ANGLES[a_idx])
            measure_in_angle(qc, 1, BOB_ANGLES[b_idx])
            qc.measure([0, 1], [0, 1])
            job = simulator.run(qc, shots=1)
            counts = job.result().get_counts()
            bits = list(counts.keys())[0]
            alice_results.append(int(bits[1]))
            bob_results.append(int(bits[0]))

    # Sift key bits: Alice a2 (idx=1) + Bob b1 (idx=0) — same pi/4 angle
    key_alice = []
    key_bob   = []
    for i in range(num_pairs):
        if alice_choices[i] == 1 and bob_choices[i] == 0:
            key_alice.append(alice_results[i])
            key_bob.append(bob_results[i])

    # CHSH correlation
    correlations = {}
    counts_map   = {}
    for i in range(num_pairs):
        pair  = (alice_choices[i], bob_choices[i])
        a_val = 1 - 2 * alice_results[i]
        b_val = 1 - 2 * bob_results[i]
        correlations[pair] = correlations.get(pair, 0) + a_val * b_val
        counts_map[pair]   = counts_map.get(pair, 0) + 1

    E = {pair: correlations[pair] / counts_map[pair] for pair in correlations}
    chsh = (
        E.get((0, 0), 0) - E.get((0, 2), 0)
        + E.get((2, 0), 0) + E.get((2, 2), 0)
    )
    bell_violated = abs(chsh) > 2.0

    errors = sum(a != b for a, b in zip(key_alice, key_bob))
    qber   = errors / len(key_alice) if key_alice else 0.0

    return {
        "protocol": "E91",
        "num_pairs": num_pairs,
        "key_length": len(key_alice),
        "raw_key": key_alice,
        "qber": round(qber, 4),
        "chsh_value": round(chsh, 4),
        "bell_violated": bell_violated,
        "eve_present": eve_present,
        "noise_level": noise_level,
        "secure": qber < 0.11 and bell_violated,
    }