"""
IBM Quantum - Bell State, BB84, and E91 in one file
- Bell State + BB84 run on REAL IBM Quantum hardware
- E91 runs on AerSimulator (300 rounds) for accurate CHSH value
Requires: pip install qiskit qiskit-ibm-runtime qiskit-aer
"""

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator
import random
import math

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
IBM_API_KEY = "API_KEY"
SHOTS = 1024

# E91 angle sets
# Alice: a0=0°, a1=45°, a2=90°
# Bob:   b0=45°, b1=90°, b2=135°
# Key sifting: Alice a1 (45°) + Bob b0 (45°) — same physical angle
# CHSH uses: (a0,b0), (a0,b2), (a2,b0), (a2,b2) — all non-matching
ALICE_ANGLES = [0, math.pi/4, math.pi/2]
BOB_ANGLES   = [math.pi/4, math.pi/2, 3*math.pi/4]


# ─────────────────────────────────────────────
# INIT IBM RUNTIME SERVICE
# ─────────────────────────────────────────────
def get_backend():
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=IBM_API_KEY)
    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=2)
    print(f"✅ Using backend: {backend.name}")
    return service, backend


def run_circuit_real(backend, circuit, shots=SHOTS):
    """Run a circuit on real IBM hardware using SamplerV2."""
    pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
    isa_circuit = pm.run(circuit)
    sampler = Sampler(backend)
    job = sampler.run([isa_circuit], shots=shots)
    print(f"   Job ID: {job.job_id()} — waiting for result...")
    result = job.result()
    counts = result[0].data.c.get_counts()
    return counts


def run_circuit_sim(circuit, shots=1):
    """Run a circuit on local AerSimulator (no quota used)."""
    sim = AerSimulator()
    job = sim.run(circuit, shots=shots)
    counts = job.result().get_counts()
    return counts


# ═══════════════════════════════════════════════════════════════
# 1. BELL STATE — runs on REAL hardware
# ═══════════════════════════════════════════════════════════════
def bell_state_circuit():
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    return qc


def run_bell_state(backend):
    print("\n" + "═"*50)
    print("  BELL STATE  |Φ+⟩ = (|00⟩ + |11⟩) / √2")
    print("  Running on: REAL IBM HARDWARE")
    print("═"*50)
    qc = bell_state_circuit()
    print(qc.draw("text"))
    counts = run_circuit_real(backend, qc)
    print(f"Results ({SHOTS} shots): {counts}")
    total = sum(counts.values())
    for state, count in sorted(counts.items()):
        print(f"  |{state}⟩ : {count} ({100*count/total:.1f}%)")
    print("Expected: ~50% |00⟩, ~50% |11⟩")
    print("Note: small deviations are due to real hardware noise")


# ═══════════════════════════════════════════════════════════════
# 2. BB84 QKD — runs on REAL hardware
# ═══════════════════════════════════════════════════════════════
def bb84_circuit(alice_bits, alice_bases, bob_bases):
    n = len(alice_bits)
    qr = QuantumRegister(n, 'q')
    cr = ClassicalRegister(n, 'c')
    qc = QuantumCircuit(qr, cr)

    for i in range(n):
        if alice_bits[i] == 1:
            qc.x(i)
        if alice_bases[i] == 1:
            qc.h(i)

    qc.barrier()

    for i in range(n):
        if bob_bases[i] == 1:
            qc.h(i)
        qc.measure(qr[i], cr[i])

    return qc


def run_bb84(backend, n_bits=8):
    print("\n" + "═"*50)
    print("  BB84 QUANTUM KEY DISTRIBUTION")
    print("  Running on: REAL IBM HARDWARE")
    print("═"*50)

    alice_bits  = [random.randint(0, 1) for _ in range(n_bits)]
    alice_bases = [random.randint(0, 1) for _ in range(n_bits)]
    bob_bases   = [random.randint(0, 1) for _ in range(n_bits)]

    print(f"Alice bits : {alice_bits}")
    print(f"Alice bases: {alice_bases}  (0=Z, 1=X)")
    print(f"Bob bases  : {bob_bases}   (0=Z, 1=X)")

    qc = bb84_circuit(alice_bits, alice_bases, bob_bases)
    counts = run_circuit_real(backend, qc, shots=1)

    bob_measurement = max(counts, key=counts.get)
    bob_bits = [int(b) for b in reversed(bob_measurement)]

    sifted_key = []
    matching_positions = []
    for i in range(n_bits):
        if alice_bases[i] == bob_bases[i]:
            sifted_key.append(alice_bits[i])
            matching_positions.append(i)

    print(f"\nBob measured: {bob_bits}")
    print(f"Matching bases at positions: {matching_positions}")
    print(f"Sifted secret key: {sifted_key}")
    print(f"Key length: {len(sifted_key)} bits (from {n_bits} qubits)")


# ═══════════════════════════════════════════════════════════════
# 3. E91 QKD — runs on AerSimulator
#
# ANGLE ASSIGNMENT:
#   Alice indices: 0 → 0°,  1 → 45°, 2 → 90°
#   Bob   indices: 0 → 45°, 1 → 90°, 2 → 135°
#
# KEY SIFTING:
#   Alice a1 (45°) + Bob b0 (45°) → same physical angle → key bits
#   For |Φ+⟩ Bell state, results are anti-correlated:
#   Alice=0 → Bob=1, Alice=1 → Bob=0
#   We flip Bob's bit to get a matching key.
#
# CHSH TEST:
#   Uses all non-matching angle pairs.
#   S = E(a0,b0) - E(a0,b2) + E(a2,b0) + E(a2,b2)
#   Classical limit:     |S| ≤ 2
#   Quantum (Bell pair): |S| → 2√2 ≈ 2.828
#   |S| > 2 confirms Bell inequality violated → channel secure
#
# WHY SIMULATOR:
#   300 rounds = 300 IBM jobs on real hardware → burns free quota
#   Simulator gives identical quantum circuit results at zero cost
# ═══════════════════════════════════════════════════════════════
def e91_circuit(alice_angle_idx, bob_angle_idx):
    qc = QuantumCircuit(2, 2)
    # Create Bell pair |Φ+⟩
    qc.h(0)
    qc.cx(0, 1)
    qc.barrier()
    # Rotate before measurement to simulate angled basis
    qc.ry(-ALICE_ANGLES[alice_angle_idx], 0)
    qc.ry(-BOB_ANGLES[bob_angle_idx], 1)
    qc.measure([0, 1], [0, 1])
    return qc


def run_e91(n_rounds=300):
    print("\n" + "═"*50)
    print("  E91 (EKERT 91) QKD")
    print(f"  Running on: AerSimulator ({n_rounds} rounds)")
    print("  (Simulator used to preserve IBM quota)")
    print("═"*50)

    key_bits_alice = []
    key_bits_bob   = []
    correlations   = {}
    counts_map     = {}

    for i in range(n_rounds):
        a_idx = random.randint(0, 2)
        b_idx = random.randint(0, 2)

        qc = e91_circuit(a_idx, b_idx)
        counts = run_circuit_sim(qc, shots=1)
        result = max(counts, key=counts.get)

        # Qiskit bit order: result[0]=qubit1(Bob), result[1]=qubit0(Alice)
        bob_bit   = int(result[0])
        alice_bit = int(result[1])

        # Map bits to +1/-1 for correlation
        a_val = 1 - 2 * alice_bit
        b_val = 1 - 2 * bob_bit

        # ── KEY SIFTING ──────────────────────────────────────────────
        # Alice a1 (45°) + Bob b0 (45°) = same physical angle
        # |Φ+⟩ anti-correlates results, so flip Bob's bit for key match
        if a_idx == 1 and b_idx == 0:
           
           key_bits_alice.append(alice_bit)
           key_bits_bob.append(bob_bit)
        else:
            # ── CHSH TEST ────────────────────────────────────────────
            pair = (a_idx, b_idx)
            correlations[pair] = correlations.get(pair, 0) + a_val * b_val
            counts_map[pair]   = counts_map.get(pair, 0) + 1

    # E(a,b) — average correlation for angle pair
    def E(a, b):
        pair = (a, b)
        if counts_map.get(pair, 0) == 0:
            return 0.0
        return correlations[pair] / counts_map[pair]

    # CHSH value: S = E(a0,b0) - E(a0,b2) + E(a2,b0) + E(a2,b2)
    S = E(0, 0) - E(0, 2) + E(2, 0) + E(2, 2)

    # QBER on key bits
    if key_bits_alice:
        errors = sum(a != b for a, b in zip(key_bits_alice, key_bits_bob))
        qber   = errors / len(key_bits_alice) * 100
    else:
        qber = 0.0

    print(f"\nTotal rounds         : {n_rounds}")
    print(f"Key bits sifted      : {len(key_bits_alice)}")
    print(f"Alice sifted key     : {key_bits_alice[:20]}{'...' if len(key_bits_alice) > 20 else ''}")
    print(f"Bob sifted key       : {key_bits_bob[:20]}{'...' if len(key_bits_bob) > 20 else ''}")
    print(f"QBER                 : {qber:.2f}%")
    print(f"\nCHSH value S         : {S:.4f}")
    print(f"Classical limit      : |S| ≤ 2.000")
    print(f"Ideal quantum value  : |S| = 2√2 ≈ 2.828")
    print(f"Bell inequality      : {'✅ VIOLATED — channel is quantum & secure' if abs(S) > 2 else '❌ NOT VIOLATED — possible eavesdropping'}")
    print(f"Channel status       : {'✅ SECURE' if abs(S) > 2 and qber < 11 else '⚠️  CHECK CHANNEL'}")

    print(f"\nCorrelation breakdown:")
    for pair in [(0,0), (0,2), (2,0), (2,2)]:
        a, b = pair
        n = counts_map.get(pair, 0)
        print(f"  E(a{a},b{b}) = {E(a,b):+.4f}  (from {n} pairs)")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    service, backend = get_backend()

    # Bell State + BB84 on real IBM hardware
    run_bell_state(backend)
    run_bb84(backend, n_bits=8)

    # E91 on AerSimulator — 300 rounds for statistically valid CHSH
    run_e91(n_rounds=300)

    print("\n✅ All done!")