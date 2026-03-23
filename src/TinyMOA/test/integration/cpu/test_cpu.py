"""
CPU integration tests (Task 2.5).

Programs are loaded via QSPI simulation (addr >= 256 region, 12-cycle latency).
The bootloader copies them into TCM before releasing the CPU.

Tests here exercise full programs end-to-end: program in QSPI, bootloader loads
into TCM, CPU runs, results written to TCM data region, Python reads them back.

Helpers are identical to test/unit/cpu/test_cpu.py so behaviour is consistent.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
import utility.rv32i_encode as rv32i
import utility.rv32c_encode as rv32c

NOP = rv32i.encode_addi(0, 0, 0)

# QSPI region starts at word 256 (byte addr 0x400).
# Bootloader copies from QSPI_BASE to TCM word 0 before releasing CPU.
QSPI_BASE = 256


async def setup(dut, instrs):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    dut.nrst.value = 0

    for i in range(2048):
        dut.mem[i].value = 0

    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1

    # Load program into QSPI region (bootloader will copy to TCM)
    for i, word in enumerate(instrs):
        dut.mem[QSPI_BASE + i].value = word

    await ClockCycles(dut.clk, 1)


async def run_until_done(dut, instr_ct, timeout=50000, debug=False):
    """Wait for instr_ct WB completions."""
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
        await ClockCycles(dut.clk, 1)
        total += 1


@cocotb.test(skip=True)
async def test_boot_counter(dut):
    """
    Boot a counter program from QSPI flash via bootloader.

    Program counts from 0 to N-1, stores result to TCM data region.
    Exercises: bootloader copy, CPU ALU loop, store to data region.

    Expected: mem[DATA] == N-1 after execution.
    """
    pass


@cocotb.test(skip=True)
async def test_bubble_sort(dut):
    """
    Boot a bubble sort program from QSPI flash via bootloader.

    Program sorts an array of 8 words (pre-loaded into TCM data region),
    writes sorted result back in place.
    Exercises: nested loop, load/store, branch, compare.

    Expected: mem[DATA..DATA+7] is sorted ascending after execution.
    """
    pass


@cocotb.test(skip=True)
async def test_memcpy(dut):
    """
    Boot a memcpy program from QSPI flash via bootloader.

    Program copies N words from src region to dst region in TCM.
    Exercises: pointer arithmetic, load/store loop, QSPI latency during boot.

    Expected: mem[DST..DST+N-1] == mem[SRC..SRC+N-1] after execution.
    """
    pass
