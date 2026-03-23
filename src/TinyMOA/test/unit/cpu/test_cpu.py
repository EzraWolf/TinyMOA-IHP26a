"""
CPU unit tests with behavioral TCM memory.

Programs load into dut.mem[] (word-addressed) before reset.
tb_cpu.v behavioral memory:
  addr < 256:  same-cycle ready (TCM, blocking assign)
  addr >= 256: 12-cycle latency (QSPI sim)

Cycle budget per instruction (non-pipelined FSM, same-cycle TCM):
  ALU/LUI/AUIPC:  FETCH(1) + DECODE(1) + EXEC(1) + WB(1) = 4
  Load/Store:      FETCH(1) + DECODE(1) + EXEC(1) + MEM(1) + WB(1) = 5
  Branch/Jump:     FETCH(1) + DECODE(1) + EXEC(1) + WB(1) = 4

  Planned tests:
  test_addi
  test_add
  test_sub
  test_and
  test_or
  test_xor
  test_fibonacci_rv32i
  test_fibonacci_rv32c
  test_is_prime_rv32i
  test_is_prime_rv32c
  test_linked_list_rv32i
  test_linked_list_rv32c
  test_single_neuron_rv32i
  test_single_neuron_rv32c
  test_simple_hash_rv32i
  test_simple_hash_rv32c"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge
import utility.rv32i_encode as rv32i
import utility.rv32c_encode as rv32c

NOP = rv32i.encode_addi(0, 0, 0)

CYCLES_ALU = 4
CYCLES_MEM = 5
CYCLES_BRANCH = 4


async def setup(dut, instrs):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    dut.nrst.value = 0

    for i in range(2048):
        dut.mem[i].value = 0

    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1

    for i, word in enumerate(instrs):
        dut.mem[i].value = word

    await ClockCycles(dut.clk, 1)


async def setup_compressed(dut, c_instrs):
    """Pack 16-bit compressed instructions (two per word) and load into mem."""
    words = []
    for i in range(0, len(c_instrs), 2):
        lo = c_instrs[i]
        hi = (
            c_instrs[i + 1]
            if i + 1 < len(c_instrs)
            else rv32i.encode_addi(0, 0, 0) & 0xFFFF
        )
        words.append((hi << 16) | lo)
    await setup(dut, words)


async def run_until_done(dut, instr_ct, timeout=10000, debug=False):
    """Wait for instr_ct instructions to complete their WB stage."""
    names = ["FETCH", "DECODE", "EXEC", "MEM", "WB"]
    total = 0
    for i in range(instr_ct):
        count = 0
        while int(dut.dbg_done.value) == 0:
            if debug:
                state = int(dut.dbg_state.value)
                pc = int(dut.dbg_pc.value)
                instr = int(dut.dbg_instr.value)
                alu = int(dut.dbg_alu_result.value)
                name = names[state] if state < len(names) else f"?{state}"
                dut._log.info(
                    f"cy {total:4d}  {name:<6s}  pc={pc}  instr={instr:08x}  alu={alu}"
                )
            await ClockCycles(dut.clk, 1)
            count += 1
            total += 1
            if count > timeout:
                raise TimeoutError(f"timed out waiting for instruction {i}")

        if debug:
            pc = int(dut.dbg_pc.value)
            instr = int(dut.dbg_instr.value)
            alu = int(dut.dbg_alu_result.value)
            dut._log.info(
                f"cy {total:4d}  WB      pc={pc}  instr={instr:08x}  alu={alu}  [instr {i} done]"
            )
        # advance one clock past this WB so next iteration does not re-count it
        await ClockCycles(dut.clk, 1)
        total += 1


@cocotb.test()
async def test_addi(dut):
    """
    addi x1, x0, 42   -> x1 = 42
    Check: dbg_alu_result == 42 after first instruction completes.
    """
    await setup(
        dut,
        [
            rv32i.encode_addi(1, 0, 42),
        ],
    )

    # Run until first WB, then check ALU result
    await run_until_done(dut, 1, debug=False)

    result = int(dut.dbg_alu_result.value)
    assert result == 42, f"expected 42, got {result}"


@cocotb.test()
async def test_alu_store_load(dut):
    """
    addi x1, x0, 10      x1 = 10
    addi x2, x0, 7       x2 = 7
    add  x3, x1, x2      x3 = 17
    sw   x3, 128(x0)     mem[128] = 17
    lw   x4, 128(x0)     x4 = 17
    sub  x5, x4, x1      x5 = 17 - 10 = 7
    sw   x5, 129(x0)     mem[129] = 7
    """
    DATA = 128  # word address for data region (away from code)

    await setup(
        dut,
        [
            rv32i.encode_addi(1, 0, 10),  # 0: x1 = 10
            rv32i.encode_addi(2, 0, 7),  # 1: x2 = 7
            rv32i.encode_add(5, 1, 2),  # 2: x5 = 17
            rv32i.encode_sw(0, 5, DATA),  # 3: mem[128] = x5
            rv32i.encode_lw(6, 0, DATA),  # 4: x6 = mem[128]
            rv32i.encode_sub(7, 6, 1),  # 5: x7 = x6 - x1
            rv32i.encode_sw(0, 7, DATA + 1),  # 6: mem[129] = x7
        ],
    )

    await run_until_done(dut, 7, debug=False)

    val_128 = int(dut.mem[DATA].value)
    val_129 = int(dut.mem[DATA + 1].value)
    assert val_128 == 17, f"mem[128] expected 17, got {val_128}"
    assert val_129 == 7, f"mem[129] expected 7, got {val_129}"


@cocotb.test()
async def test_fibonacci_rv32i(dut):
    """
    Compute fib(12) = 144 using a branch loop.

    x5 = a (fib n-2), x6 = b (fib n-1), x7 = tmp
    x8 = loop counter, x9 = limit (12)

    After the loop, store x6 (fib(12)) and x5 (fib(11)) to memory.

    Assembly:
    (0x00)  ADDI x5, x0, 0
    (0x04)  ADDI x6, x0, 1
    (0x08)  ADDI x8, x0, 1
    (0x0C)  ADDI x9, x0, 12
    loop:
    (0x10)  ADD  x7, x5, x6
    (0x14)  ADDI x5, x6, 0
    (0x18)  ADDI x6, x7, 0
    (0x1C)  ADDI x8, x8, 1
    (0x20)  BNE  x8, x9, -16
    (0x24)  SW   x6, 200(x0)    fib(12) -> mem[200]
    (0x28)  SW   x5, 201(x0)    fib(11) -> mem[201]
    """
    RES_A = 200
    RES_B = 201

    await setup(
        dut,
        [
            rv32i.encode_addi(5, 0, 0),
            rv32i.encode_addi(6, 0, 1),
            rv32i.encode_addi(8, 0, 1),
            rv32i.encode_addi(9, 0, 12),
            rv32i.encode_add(7, 5, 6),
            rv32i.encode_addi(5, 6, 0),
            rv32i.encode_addi(6, 7, 0),
            rv32i.encode_addi(8, 8, 1),
            rv32i.encode_bne(8, 9, -16),
            rv32i.encode_sw(0, 6, RES_A),
            rv32i.encode_sw(0, 5, RES_B),
        ],
    )

    await run_until_done(dut, 61, debug=False)

    fib12 = int(dut.mem[RES_A].value)
    fib11 = int(dut.mem[RES_B].value)
    dut._log.info(f"fib(12)={fib12}, fib(11)={fib11}")
    assert fib12 == 144, f"fib(12): got {fib12}, expected 144"
    assert fib11 == 89, f"fib(11): got {fib11}, expected 89"


@cocotb.test()
async def test_fibonacci_rv32c(dut):
    """
    Compute fib(12) = 144 using RV32C compressed instructions.

    Each C instruction is stored one-per-word (16-bit value in lower bits).
    C.BNEZ and C.ADD require x8-x15 (prime registers), so:
      x8  = a (fib n-2), starts 0
      x9  = b (fib n-1), starts 1
      x10 = tmp
      x11 = counter, counts down from 11 to 0

    After 11 iterations: x9 = fib(12) = 144, x8 = fib(11) = 89.

    Assembly (one C instr per word, byte offset = word offset * 4):
    word 0 (0x00)  C.LI   x8,  0      a = 0
    word 1 (0x04)  C.LI   x9,  1      b = 1
    word 2 (0x08)  C.LI   x11, 11     counter = 11
    loop:
    word 3 (0x0C)  C.MV   x10, x9    tmp = b
    word 4 (0x10)  C.ADD  x9,  x8    b += a
    word 5 (0x14)  C.MV   x8,  x10   a = tmp
    word 6 (0x18)  C.ADDI x11, -1    counter--
    word 7 (0x1C)  C.BNEZ x11, -16   if counter != 0, goto word 3
    word 8 (0x20)  SW     x9,  200(x0)   fib(12) -> mem[200]
    word 9 (0x24)  SW     x8,  201(x0)   fib(11) -> mem[201]

    C.BNEZ offset -16 bytes: CPU divides by 4 -> -4 words; 7 + (-4) = 3 (loop start).
    """
    RES_A = 200
    RES_B = 201

    await setup(
        dut,
        [
            rv32c.encode_c_li(8, 0),  # word 0
            rv32c.encode_c_li(9, 1),  # word 1
            rv32c.encode_c_li(11, 11),  # word 2
            rv32c.encode_c_mv(10, 9),  # word 3  loop start
            rv32c.encode_c_add(9, 8),  # word 4
            rv32c.encode_c_mv(8, 10),  # word 5
            rv32c.encode_c_addi(11, -1),  # word 6
            rv32c.encode_c_bnez(11, -16),  # word 7  branch back to word 3
            rv32i.encode_sw(0, 9, RES_A),  # word 8
            rv32i.encode_sw(0, 8, RES_B),  # word 9
        ],
    )

    # 3 setup + 11 iters * 5 instrs + 2 stores = 60 instructions
    await run_until_done(dut, 100, debug=False)

    fib12 = int(dut.mem[RES_A].value)
    fib11 = int(dut.mem[RES_B].value)
    dut._log.info(f"fib(12)={fib12}, fib(11)={fib11}")
    assert fib12 == 144, f"fib(12): got {fib12}, expected 144"
    assert fib11 == 89, f"fib(11): got {fib11}, expected 89"


@cocotb.test()
async def test_is_prime_rv32i(dut):
    """
    Test if N=7 is prime via trial division. x6=1 if prime, 0 if not.

    x5=N, x6=result, x7=divisor, x9=remainder

    word  0: ADDI x5, x0, 7       N = 7
    word  1: ADDI x6, x0, 1       result = 1 (assume prime)
    word  2: ADDI x7, x0, 2       divisor = 2
    word  3: BEQ  x7, x5, 36      if divisor==N, goto 12 (store)
    word  4: ADDI x9, x5, 0       remainder = N
    word  5: BLT  x9, x7, 12      if rem < div, goto 8
    word  6: SUB  x9, x9, x7      rem -= div
    word  7: BEQ  x0, x0, -8      goto 5
    word  8: BNE  x9, x0, 8       if rem != 0, skip
    word  9: ADDI x6, x0, 0       result = 0
    word 10: ADDI x7, x7, 1       divisor++
    word 11: BEQ  x0, x0, -32     goto 3
    word 12: SW   x6, 200(x0)     store result
    """
    RES = 200
    await setup(
        dut,
        [
            rv32i.encode_addi(5, 0, 7),
            rv32i.encode_addi(6, 0, 1),
            rv32i.encode_addi(7, 0, 2),
            rv32i.encode_beq(7, 5, 36),
            rv32i.encode_addi(9, 5, 0),
            rv32i.encode_blt(9, 7, 12),
            rv32i.encode_sub(9, 9, 7),
            rv32i.encode_beq(0, 0, -8),
            rv32i.encode_bne(9, 0, 8),
            rv32i.encode_addi(6, 0, 0),
            rv32i.encode_addi(7, 7, 1),
            rv32i.encode_beq(0, 0, -32),
            rv32i.encode_sw(0, 6, RES),
        ],
    )
    await run_until_done(dut, 200, debug=False)
    val = int(dut.mem[RES].value)
    dut._log.info(f"is_prime(7) = {val}")
    assert val == 1, f"is_prime(7): got {val}, expected 1"


@cocotb.test()
async def test_is_not_prime_rv32i(dut):
    """Same as test_is_prime_rv32i but N=12 (not prime, divisible by 2)."""
    RES = 200
    await setup(
        dut,
        [
            rv32i.encode_addi(5, 0, 12),
            rv32i.encode_addi(6, 0, 1),
            rv32i.encode_addi(7, 0, 2),
            rv32i.encode_beq(7, 5, 36),
            rv32i.encode_addi(9, 5, 0),
            rv32i.encode_blt(9, 7, 12),
            rv32i.encode_sub(9, 9, 7),
            rv32i.encode_beq(0, 0, -8),
            rv32i.encode_bne(9, 0, 8),
            rv32i.encode_addi(6, 0, 0),
            rv32i.encode_addi(7, 7, 1),
            rv32i.encode_beq(0, 0, -32),
            rv32i.encode_sw(0, 6, RES),
        ],
    )
    await run_until_done(dut, 500, debug=False)
    val = int(dut.mem[RES].value)
    dut._log.info(f"is_prime(12) = {val}")
    assert val == 0, f"is_prime(12): got {val}, expected 0"


@cocotb.test()
async def test_is_prime_rv32c(dut):
    """
    Test if N=7 is prime using RV32C where possible.

    x8=N, x9=result, x10=divisor, x11=remainder

    word  0: C.LI   x9,  1
    word  1: C.LI   x10, 2
    word  2: C.LI   x8,  7
    word  3: BEQ    x10, x8, 36    if div==N, goto 12
    word  4: C.MV   x11, x8        rem = N
    word  5: BLT    x11, x10, 12   if rem < div, goto 8
    word  6: C.SUB  x11, x10       rem -= div
    word  7: BEQ    x0,  x0, -8    goto 5
    word  8: BNE    x11, x0, 8     if rem != 0, skip (C.BNEZ broken for +imm)
    word  9: C.LI   x9,  0         result = 0
    word 10: C.ADDI x10, 1         div++
    word 11: BEQ    x0,  x0, -32   goto 3
    word 12: SW     x9, 200(x0)
    """
    RES = 200
    await setup(
        dut,
        [
            rv32c.encode_c_li(9, 1),
            rv32c.encode_c_li(10, 2),
            rv32c.encode_c_li(8, 7),
            rv32i.encode_beq(10, 8, 36),
            rv32c.encode_c_mv(11, 8),
            rv32i.encode_blt(11, 10, 12),
            rv32c.encode_c_sub(11, 10),
            rv32i.encode_beq(0, 0, -8),
            rv32i.encode_bne(11, 0, 8),
            rv32c.encode_c_li(9, 0),
            rv32c.encode_c_addi(10, 1),
            rv32i.encode_beq(0, 0, -32),
            rv32i.encode_sw(0, 9, RES),
        ],
    )
    await run_until_done(dut, 200, debug=False)
    val = int(dut.mem[RES].value)
    dut._log.info(f"is_prime_rv32c(7) = {val}")
    assert val == 1, f"is_prime_rv32c(7): got {val}, expected 1"
