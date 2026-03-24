"""
TinyMOA system integration tests.

Pin mapping:
  ui_in[0]    target      0=TCM, 1=DCIM MMIO
  ui_in[1]    rw          0=read, 1=write
  ui_in[2]    addr_load
  ui_in[3]    halt        gates clock for DCIM and ext_io FSM. debug pins remain readable.
  ui_in[4]    strobe
  ui_in[5]    execute
  ui_in[6]    dbg_strobe
  ui_in[7]    spare

  uo_out[0]   spare
  uo_out[1]   ready
  uo_out[2]   word_done
  uo_out[5:3] dbg_state
  uo_out[6]   dcim_busy
  uo_out[7]   dcim_done

  uio[7:0]   bidir data bus
"""

import numpy as np
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


# ui_in bit masks
TARGET = 1 << 0
RW = 1 << 1
ADDR_LOAD = 1 << 2
HALT = 1 << 3
STROBE = 1 << 4
EXECUTE = 1 << 5
DBG_STROBE = 1 << 6


async def setup(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.nrst.value = 0
    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1


# === Low-level IO ===


async def io_write_byte(
    dut, byte_val, target=0, addr_load=0, extra_flags=0, timeout=100
):
    """Write a byte via uio. Sets rw=1 (unless addr_load), strobes, waits for ready."""
    flags = STROBE | extra_flags
    if addr_load:
        flags |= ADDR_LOAD
    else:
        flags |= RW
    if target:
        flags |= TARGET

    dut.uio_in.value = byte_val & 0xFF
    dut.ui_in.value = flags
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = flags & ~STROBE
    for _ in range(timeout):
        await ClockCycles(dut.clk, 1)
        if (int(dut.uo_out.value) >> 1) & 1:
            return
    raise TimeoutError("io_write_byte: ready never went high")


async def io_read_byte(dut, target=0, timeout=100):
    """Read a byte via uio. rw=0, strobes, waits for ready, returns byte."""
    flags = STROBE
    if target:
        flags |= TARGET

    dut.ui_in.value = flags
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = flags & ~STROBE
    for _ in range(timeout):
        await ClockCycles(dut.clk, 1)
        if (int(dut.uo_out.value) >> 1) & 1:
            return int(dut.uio_out.value) & 0xFF
    raise TimeoutError("io_read_byte: ready never went high")


def io_read_debug(dut):
    """Read all uo_out debug pins. Returns dict of current state."""
    uo = int(dut.uo_out.value)
    return {
        "ready": (uo >> 1) & 1,
        "word_done": (uo >> 2) & 1,
        "dbg_state": (uo >> 3) & 7,
        "dcim_busy": (uo >> 6) & 1,
        "dcim_done": (uo >> 7) & 1,
    }


async def io_execute(dut, flags=0, wait_pin="ready", timeout=100):
    """Pulse execute, wait for a uo_out pin to go high."""
    dut.ui_in.value = flags | EXECUTE
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = flags

    pin_bit = {"ready": 1, "word_done": 2, "dcim_done": 7}[wait_pin]
    for _ in range(timeout):
        await ClockCycles(dut.clk, 1)
        if (int(dut.uo_out.value) >> pin_bit) & 1:
            return
    raise TimeoutError(f"io_execute: {wait_pin} never went high after {timeout} cycles")


def verify_io(
    dut,
    *,
    # ui_in
    target=0,
    rw=0,
    addr_load=0,
    halt=0,
    strobe=0,
    execute=0,
    dbg_strobe=0,
    ui_spare7=0,
    # uo_out
    uo_spare0=0,
    ready=0,
    word_done=0,
    dbg_state=0,
    dcim_busy=0,
    dcim_done=0,
    # uio
    uio_out=0x00,
    uio_oe=0x00,
    uio_in=0x00,
):
    """Assert ALL external pins match expected values."""
    ui = int(dut.ui_in.value)
    assert (ui >> 0) & 1 == target, (
        f"ui[0] target: expected {target}, got {(ui >> 0) & 1}"
    )
    assert (ui >> 1) & 1 == rw, f"ui[1] rw: expected {rw}, got {(ui >> 1) & 1}"
    assert (ui >> 2) & 1 == addr_load, (
        f"ui[2] addr_load: expected {addr_load}, got {(ui >> 2) & 1}"
    )
    assert (ui >> 3) & 1 == halt, f"ui[3] halt: expected {halt}, got {(ui >> 3) & 1}"
    assert (ui >> 4) & 1 == strobe, (
        f"ui[4] strobe: expected {strobe}, got {(ui >> 4) & 1}"
    )
    assert (ui >> 5) & 1 == execute, (
        f"ui[5] execute: expected {execute}, got {(ui >> 5) & 1}"
    )
    assert (ui >> 6) & 1 == dbg_strobe, (
        f"ui[6] dbg_strobe: expected {dbg_strobe}, got {(ui >> 6) & 1}"
    )
    assert (ui >> 7) & 1 == ui_spare7, (
        f"ui[7] spare: expected {ui_spare7}, got {(ui >> 7) & 1}"
    )

    uo = int(dut.uo_out.value)
    assert (uo >> 0) & 1 == uo_spare0, (
        f"uo[0] spare: expected {uo_spare0}, got {(uo >> 0) & 1}"
    )
    assert (uo >> 1) & 1 == ready, f"uo[1] ready: expected {ready}, got {(uo >> 1) & 1}"
    assert (uo >> 2) & 1 == word_done, (
        f"uo[2] word_done: expected {word_done}, got {(uo >> 2) & 1}"
    )
    assert (uo >> 3) & 7 == dbg_state, (
        f"uo[5:3] dbg_state: expected {dbg_state}, got {(uo >> 3) & 7}"
    )
    assert (uo >> 6) & 1 == dcim_busy, (
        f"uo[6] dcim_busy: expected {dcim_busy}, got {(uo >> 6) & 1}"
    )
    assert (uo >> 7) & 1 == dcim_done, (
        f"uo[7] dcim_done: expected {dcim_done}, got {(uo >> 7) & 1}"
    )

    assert int(dut.uio_out.value) & 0xFF == uio_out & 0xFF, (
        f"uio_out: expected 0x{uio_out:02X}, got 0x{int(dut.uio_out.value) & 0xFF:02X}"
    )
    assert int(dut.uio_oe.value) & 0xFF == uio_oe & 0xFF, (
        f"uio_oe: expected 0x{uio_oe:02X}, got 0x{int(dut.uio_oe.value) & 0xFF:02X}"
    )
    assert int(dut.uio_in.value) & 0xFF == uio_in & 0xFF, (
        f"uio_in: expected 0x{uio_in:02X}, got 0x{int(dut.uio_in.value) & 0xFF:02X}"
    )


# === Tests ===


@cocotb.test()
async def test_reset_outputs(dut):
    """After reset, all outputs idle."""
    await setup(dut)
    await ClockCycles(dut.clk, 1)
    verify_io(dut)


@cocotb.test()
async def test_tcm_write_read(dut):
    """Write 0xDEADBEEF to TCM[0x010], read it back."""
    await setup(dut)

    # Load address 0x010
    await io_write_byte(dut, 0x10, addr_load=1)
    await io_write_byte(dut, 0x00, addr_load=1)

    # Load data 0xDEADBEEF
    await io_write_byte(dut, 0xEF)
    await io_write_byte(dut, 0xBE)
    await io_write_byte(dut, 0xAD)
    await io_write_byte(dut, 0xDE)

    # Execute TCM write
    await io_execute(dut, RW)

    # Reload address for read
    await io_write_byte(dut, 0x10, addr_load=1)
    await io_write_byte(dut, 0x00, addr_load=1)

    # Execute TCM read
    await io_execute(dut)

    # Read 4 bytes back
    b0 = await io_read_byte(dut)
    b1 = await io_read_byte(dut)
    b2 = await io_read_byte(dut)
    b3 = await io_read_byte(dut)
    result = b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)

    assert result == 0xDEADBEEF, (
        f"TCM read-back: expected 0xDEADBEEF, got 0x{result:08X}"
    )


@cocotb.test()
async def test_tcm_auto_increment(dut):
    """Write two words at 0x020/0x021, read both back."""
    await setup(dut)

    # Load starting address
    await io_write_byte(dut, 0x20, addr_load=1)
    await io_write_byte(dut, 0x00, addr_load=1)

    # First word: 0x11111111
    for _ in range(4):
        await io_write_byte(dut, 0x11)
    await io_execute(dut, RW)

    # Second word: 0x22222222 (addr should be 0x021)
    for _ in range(4):
        await io_write_byte(dut, 0x22)
    await io_execute(dut, RW)

    # Read back: reload to 0x020
    await io_write_byte(dut, 0x20, addr_load=1)
    await io_write_byte(dut, 0x00, addr_load=1)

    # Read first word
    await io_execute(dut)
    val0 = 0
    for i in range(4):
        val0 |= (await io_read_byte(dut)) << (i * 8)

    # Read second word (addr auto-incremented)
    await io_execute(dut)
    val1 = 0
    for i in range(4):
        val1 |= (await io_read_byte(dut)) << (i * 8)

    assert val0 == 0x11111111, f"TCM[0x020]: expected 0x11111111, got 0x{val0:08X}"
    assert val1 == 0x22222222, f"TCM[0x021]: expected 0x22222222, got 0x{val1:08X}"


@cocotb.test()
async def test_dcim_mmio_write_read(dut):
    """Write WEIGHT_BASE via MMIO, read it back."""
    await setup(dut)

    # Load MMIO address 0x08
    await io_write_byte(dut, 0x08, addr_load=1)
    await io_write_byte(dut, 0x00, addr_load=1)

    # Load data 0x1A0
    await io_write_byte(dut, 0xA0, target=1)
    await io_write_byte(dut, 0x01, target=1)
    await io_write_byte(dut, 0x00, target=1)
    await io_write_byte(dut, 0x00, target=1)

    # Execute MMIO write
    await io_execute(dut, TARGET | RW)

    # Reload address
    await io_write_byte(dut, 0x08, addr_load=1)
    await io_write_byte(dut, 0x00, addr_load=1)

    # Execute MMIO read
    await io_execute(dut, TARGET)

    # Read 4 bytes
    result = 0
    for i in range(4):
        result |= (await io_read_byte(dut, target=1)) << (i * 8)

    assert (result & 0x3FF) == 0x1A0, (
        f"WEIGHT_BASE readback: expected 0x1A0, got 0x{result:08X}"
    )


@cocotb.test()
async def test_dcim_status_idle(dut):
    """DCIM idle after reset."""
    await setup(dut)
    await ClockCycles(dut.clk, 1)
    verify_io(dut, dcim_busy=0, dcim_done=0, dbg_state=0)


@cocotb.test()
async def test_halt_pauses_dcim(dut):
    """Start DCIM, assert halt, verify state freezes, release, verify completion.

    Halt gates the clock for both DCIM and the ext_io FSM.
    While halted, no transactions are processed. Debug pins (uo_out)
    are combinational and remain readable -- they reflect the frozen state.
    """
    await setup(dut)

    # Write CTRL = 0x13 to start DCIM
    await io_write_byte(dut, 0x00, addr_load=1)
    await io_write_byte(dut, 0x00, addr_load=1)
    await io_write_byte(dut, 0x13, target=1)
    await io_write_byte(dut, 0x00, target=1)
    await io_write_byte(dut, 0x00, target=1)
    await io_write_byte(dut, 0x00, target=1)
    await io_execute(dut, TARGET | RW)

    # Let DCIM run a few cycles so it leaves IDLE
    await ClockCycles(dut.clk, 3)

    # Assert halt
    dut.ui_in.value = HALT
    await ClockCycles(dut.clk, 1)

    # Read frozen state
    dbg_frozen = io_read_debug(dut)
    assert dbg_frozen["dcim_busy"] == 1, "DCIM should be busy when halted mid-run"

    # Wait -- state must not change
    await ClockCycles(dut.clk, 20)
    dbg_still = io_read_debug(dut)
    assert dbg_frozen["dbg_state"] == dbg_still["dbg_state"], (
        f"state changed while halted: {dbg_frozen['dbg_state']} -> {dbg_still['dbg_state']}"
    )
    assert dbg_still["dcim_done"] == 0, "DCIM should not finish while halted"

    # Release halt -- DCIM should resume and eventually finish
    dut.ui_in.value = 0
    for _ in range(200):
        await ClockCycles(dut.clk, 1)
        dbg = io_read_debug(dut)
        if dbg["dcim_done"]:
            break
    else:
        raise TimeoutError("DCIM never reached DONE after halt released")


@cocotb.test()
async def test_dcim_inference(dut):
    """Single 16x16 binary dot product via DCIM.

    Program:
      1. write TCM[0x180..0x18F] = 16 weight rows (all 0xFFFF)
      2. write TCM[0x1A0]        = activation     (0xFFFF)
      3. write MMIO WEIGHT_BASE  = 0x180
      4. write MMIO ACT_BASE     = 0x1A0
      5. write MMIO RESULT_BASE  = 0x1B0
      6. write MMIO ARRAY_SIZE   = 16
      7. write MMIO CTRL         = 0x13 (reload=1, prec=1, start=1)
      8. poll  MMIO STATUS       until DONE
      9. read  TCM[0x1B0..0x1BF] = 16 signed results

    Math: XNOR(1,1)=1 for all 16 bits, popcount=16 per column.
    Signed = 2*16 - 16*(2^1 - 1) = 32 - 16 = 16.
    """
    await setup(dut)

    # 1. Load 16 weight words at 0x180
    await io_write_byte(dut, 0x80, addr_load=1)
    await io_write_byte(dut, 0x01, addr_load=1)
    for _ in range(16):
        await io_write_byte(dut, 0xFF)
        await io_write_byte(dut, 0xFF)
        await io_write_byte(dut, 0x00)
        await io_write_byte(dut, 0x00)
        await io_execute(dut, RW)

    # 2. Load 1 activation word at 0x1A0
    await io_write_byte(dut, 0xA0, addr_load=1)
    await io_write_byte(dut, 0x01, addr_load=1)
    await io_write_byte(dut, 0xFF)
    await io_write_byte(dut, 0xFF)
    await io_write_byte(dut, 0x00)
    await io_write_byte(dut, 0x00)
    await io_execute(dut, RW)

    # 3. Configure DCIM
    # WEIGHT_BASE = 0x180
    await io_write_byte(dut, 0x08, addr_load=1)
    await io_write_byte(dut, 0x00, addr_load=1)
    await io_write_byte(dut, 0x80, target=1)
    await io_write_byte(dut, 0x01, target=1)
    await io_write_byte(dut, 0x00, target=1)
    await io_write_byte(dut, 0x00, target=1)
    await io_execute(dut, TARGET | RW)

    # ACT_BASE = 0x1A0
    await io_write_byte(dut, 0x0C, addr_load=1)
    await io_write_byte(dut, 0x00, addr_load=1)
    await io_write_byte(dut, 0xA0, target=1)
    await io_write_byte(dut, 0x01, target=1)
    await io_write_byte(dut, 0x00, target=1)
    await io_write_byte(dut, 0x00, target=1)
    await io_execute(dut, TARGET | RW)

    # RESULT_BASE = 0x1B0
    await io_write_byte(dut, 0x10, addr_load=1)
    await io_write_byte(dut, 0x00, addr_load=1)
    await io_write_byte(dut, 0xB0, target=1)
    await io_write_byte(dut, 0x01, target=1)
    await io_write_byte(dut, 0x00, target=1)
    await io_write_byte(dut, 0x00, target=1)
    await io_execute(dut, TARGET | RW)

    # ARRAY_SIZE = 16
    await io_write_byte(dut, 0x14, addr_load=1)
    await io_write_byte(dut, 0x00, addr_load=1)
    await io_write_byte(dut, 0x10, target=1)
    await io_write_byte(dut, 0x00, target=1)
    await io_write_byte(dut, 0x00, target=1)
    await io_write_byte(dut, 0x00, target=1)
    await io_execute(dut, TARGET | RW)

    # 4. CTRL = 0x13 (reload=1, prec=1, start=1)
    await io_write_byte(dut, 0x00, addr_load=1)
    await io_write_byte(dut, 0x00, addr_load=1)
    await io_write_byte(dut, 0x13, target=1)
    await io_write_byte(dut, 0x00, target=1)
    await io_write_byte(dut, 0x00, target=1)
    await io_write_byte(dut, 0x00, target=1)
    await io_execute(dut, TARGET | RW)

    # 5. Poll STATUS until DONE
    for _ in range(5000):
        await io_write_byte(dut, 0x04, addr_load=1)
        await io_write_byte(dut, 0x00, addr_load=1)
        await io_execute(dut, TARGET)
        b0 = await io_read_byte(dut, target=1)
        if b0 & 0x2:
            break
        await ClockCycles(dut.clk, 1)
    else:
        raise TimeoutError("DCIM never reached DONE")

    # === Compute expected result with numpy ===
    # Weight matrix: 16x16 all ones (binary +1)
    # Activation vector: 16 all ones (binary +1)
    # XNOR dot product: popcount(XNOR(w_col, act)) per column
    # Signed conversion: 2*popcount - N*(2^P - 1)
    N = 16
    P = 1
    W = np.ones((N, N), dtype=np.int8)   # binary weights, all 1
    a = np.ones(N, dtype=np.int8)         # binary activation, all 1
    # XNOR: 1 when bits match
    xnor = np.where(W == a, 1, 0)        # all 1 since both are 1
    popcount = xnor.sum(axis=0)           # 16 per column
    bias = N * ((1 << P) - 1)             # 16 * 1 = 16
    expected = 2 * popcount - bias        # 2*16 - 16 = 16 per column
    dut._log.info(f"numpy expected results: {expected.tolist()}")

    # === Probe RTL internals to trace where data dies ===
    # Check TCM memory directly: did DCIM write to result region?
    tcm_mem = dut.dut.tcm.mem
    for i in range(4):
        raw = tcm_mem[0x1B0 + i].value
        dut._log.info(f"TCM mem[0x{0x1B0+i:03X}] = {raw}")

    # Check DCIM internals
    dcim = dut.dut.dcim
    dut._log.info(f"DCIM state={dcim.state.value} status={dcim.status_reg.value}")
    dut._log.info(f"DCIM cfg: wb={dcim.cfg_weight_base.value} ab={dcim.cfg_act_base.value} rb={dcim.cfg_result_base.value} sz={dcim.cfg_array_size.value}")
    dut._log.info(f"DCIM bias_reg={dcim.bias_reg.value}")
    for i in range(4):
        dut._log.info(f"DCIM shift_acc[{i}]={dcim.shift_acc[i].value} weight_reg[{i}]={dcim.weight_reg[i].value}")

    # Check Port B signals
    dut._log.info(f"Port B: b_en={dut.dut.tcm.b_en.value} b_wen={dut.dut.tcm.b_wen.value} b_addr={dut.dut.tcm.b_addr.value}")

    # Check ext_io read path
    dut._log.info(f"ext_io: read_reg={dut.dut.read_reg.value} uio_out_reg={dut.dut.uio_out_reg.value} uio_driving={dut.dut.uio_driving.value}")

    # 6. Read 16 results from 0x1B0
    results = []
    for i in range(16):
        await io_write_byte(dut, (0x1B0 + i) & 0xFF, addr_load=1)
        await io_write_byte(dut, ((0x1B0 + i) >> 8) & 0xFF, addr_load=1)
        await io_execute(dut)
        val = 0
        for j in range(4):
            try:
                val |= (await io_read_byte(dut)) << (j * 8)
            except ValueError as e:
                dut._log.error(f"result[{i}] byte {j}: {e}")
                val = 0xDEAD
                break
        if val != 0xDEAD and val >= 0x80000000:
            val -= 0x100000000
        results.append(val)

    dut._log.info(f"results: {results}")
    for i, val in enumerate(results):
        assert val == expected[i], f"result[{i}] = {val}, expected {expected[i]}"
