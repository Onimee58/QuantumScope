# Circuit verification and truth tables (v0.3.0)

Open **Quantum Circuits → Gate Circuit Simulator** and select an arithmetic circuit from **Examples**. The **Circuit Verification & Truth Table** area runs *every computational-basis input* using the actual statevector gate simulator. Results display observed output, expected output, dominant-state probability and PASS/FAIL.

- **Half adder:** inputs q0=A, q1=B; final sum=q1, carry=q2. Four combinations tested.
- **Half subtractor:** inputs q0=A, q1=B; final difference=q1, borrow=q2. Four combinations tested.
- **2-bit adder:** inputs A=q0q1, B=q2q3 (binary, MSB to LSB), outputs sum bit 0=q1, bit 1=q2, carry=q5. Sixteen combinations tested. Ancillary/control register bits remain part of the reversible full state.

The examples contain leading X gates to set a *demonstration input*. The verifier removes only those known preparatory gates, then initializes each possible binary input and executes the remaining arithmetic network. An example that has been edited is treated as a general circuit so that its former arithmetic assumptions are not silently reused.

For **Bell, GHZ, imported, and hand-drawn circuits**, **Verify circuit / Show truth table** shows the first 16 computational-basis input states and the most likely output for each. A superposition is reported as nondeterministic, not as a failed classical truth table. The simulation remains ideal; these are not hardware measurements.

## Gate operands

The top-row selectors are shown only as needed:
- **Single-qubit gates:** click a wire to choose the target.
- **CX/CZ:** first wire is control; second selector is target.
- **SWAP:** first wire is one swap operand; second selector is its partner.
- **CCX:** wire is control 1; second selector is control 2; third selector is target.
- **CSWAP:** wire is control; second selector is swap 1; third selector is swap 2.

The original ambiguous 'Third 0' control is renamed to its gate-specific role.
