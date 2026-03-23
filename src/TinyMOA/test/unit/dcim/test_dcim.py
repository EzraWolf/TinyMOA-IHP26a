"""
DCIM unit tests (tinymoa_dcim + tinymoa_compressor, exact compressor by default).

The testbench includes a behavioral 512x32 memory. Tests preload it via
tb_mem_wen/tb_mem_wdata/tb_mem_addr, run inference via MMIO, then read
results back via tb_mem_raddr/tb_mem_rdata.

Tests:
- mmio_write_read_control
- mmio_write_read_addresses
- reset_default_config
- reset_clears_status
- status_busy_after_start
- status_done_after_inference
- weight_loading_count
- skip_reload_finishes_faster
- end_to_end_all_ones_1bit
- end_to_end_all_zeros_1bit
- end_to_end_all_ones_2bit
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles, Timer

# MMIO byte addresses (addr[5:2] selects register)
CTRL_ADDR = 0x00  # {cfg_reload_weights[4], cfg_precision[3:1], cfg_start[0]}
STATUS_ADDR = 0x04  # status: bit0=BUSY, bit1=DONE
WBASE_ADDR = 0x08  # cfg_weight_base [9:0]
ABASE_ADDR = 0x0C  # cfg_act_base    [9:0]
RBASE_ADDR = 0x10  # cfg_result_base [9:0]
SIZE_ADDR = 0x14  # cfg_array_size  [5:0]

DEFAULT_WEIGHT_BASE = 0x1A0  # 416
DEFAULT_ACT_BASE = 0x1C0  # 448
DEFAULT_RESULT_BASE = 0x1E0  # 480
DEFAULT_ARRAY_SIZE = 32
ARRAY_DIM = 32


async def setup(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.mmio_write.value = 0
    dut.mmio_read.value = 0
    dut.mmio_addr.value = 0
    dut.mmio_wdata.value = 0
    dut.tb_mem_wen.value = 0
    dut.tb_mem_wdata.value = 0
    dut.tb_mem_addr.value = 0
    dut.tb_mem_raddr.value = 0

    dut.nrst.value = 0
    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1


async def mmio_write(dut, addr, data):
    """Perform one MMIO write and verify mmio_ready."""
    dut.mmio_write.value = 1
    dut.mmio_addr.value = addr
    dut.mmio_wdata.value = data
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.mmio_ready.value) == 1, (
        f"mmio_ready not asserted for write to 0x{addr:02X}"
    )
    dut.mmio_write.value = 0


async def mmio_read(dut, addr):
    """Perform one MMIO read and return the value."""
    dut.mmio_read.value = 1
    dut.mmio_addr.value = addr
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.mmio_ready.value) == 1, (
        f"mmio_ready not asserted for read from 0x{addr:02X}"
    )
    val = int(dut.mmio_rdata.value)
    dut.mmio_read.value = 0
    return val


async def mem_preload(dut, memory_dict):
    """Write all entries in memory_dict into the testbench memory."""
    for addr, data in memory_dict.items():
        # Set signals AFTER posedge so RTL sees them at the NEXT posedge.
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        dut.tb_mem_wen.value = 1
        dut.tb_mem_addr.value = addr
        dut.tb_mem_wdata.value = data
    # One extra edge to clock in the last write
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.tb_mem_wen.value = 0


async def mem_read_tb(dut, addr):
    """Read one word from testbench memory (combinational read port, needs simulator tick)."""
    dut.tb_mem_raddr.value = addr
    await Timer(1, units="ns")  # allow combinational propagation
    return int(dut.tb_mem_rdata.value)


def make_ctrl(cfg_start=0, cfg_precision=1, cfg_reload_weights=1):
    """Pack control word: {reload[4], precision[3:1], start[0]}."""
    return (
        ((cfg_reload_weights & 1) << 4) | ((cfg_precision & 0x7) << 1) | (cfg_start & 1)
    )


async def start_inference(dut, reload_weights=True, precision=1):
    """Write control register to start inference."""
    ctrl = make_ctrl(
        cfg_start=1, cfg_precision=precision, cfg_reload_weights=int(reload_weights)
    )
    await mmio_write(dut, CTRL_ADDR, ctrl)


async def wait_for_done(dut, max_cycles=400):
    """Wait until status DONE bit (bit 1) is set. Returns cycle count."""
    for i in range(max_cycles):
        await ClockCycles(dut.clk, 1)
        status = await mmio_read(dut, STATUS_ADDR)
        if status & 0x2:
            return i
    assert False, f"DCIM never completed within {max_cycles} cycles"


# ===========================================================
# MMIO Register Tests
# ===========================================================


@cocotb.test()
async def mmio_write_read_control(dut):
    """Write control register and read it back (start=0 to avoid triggering FSM)."""
    await setup(dut)
    ctrl = make_ctrl(cfg_start=0, cfg_precision=2, cfg_reload_weights=0)
    await mmio_write(dut, CTRL_ADDR, ctrl)
    val = await mmio_read(dut, CTRL_ADDR)
    assert (val & 0x1F) == (ctrl & 0x1F), (
        f"Control: expected 0x{ctrl:02X}, got 0x{val:02X}"
    )


@cocotb.test()
async def mmio_write_read_addresses(dut):
    """Write and read back all address config registers and array_size."""
    await setup(dut)
    await mmio_write(dut, WBASE_ADDR, 0x100)
    await mmio_write(dut, ABASE_ADDR, 0x120)
    await mmio_write(dut, RBASE_ADDR, 0x140)
    await mmio_write(dut, SIZE_ADDR, 16)

    assert (await mmio_read(dut, WBASE_ADDR)) == 0x100, "weight_base mismatch"
    assert (await mmio_read(dut, ABASE_ADDR)) == 0x120, "act_base mismatch"
    assert (await mmio_read(dut, RBASE_ADDR)) == 0x140, "result_base mismatch"
    assert (await mmio_read(dut, SIZE_ADDR)) == 16, "array_size mismatch"


@cocotb.test()
async def reset_default_config(dut):
    """Default config values match Architecture spec after reset."""
    await setup(dut)
    assert (await mmio_read(dut, WBASE_ADDR)) == DEFAULT_WEIGHT_BASE
    assert (await mmio_read(dut, ABASE_ADDR)) == DEFAULT_ACT_BASE
    assert (await mmio_read(dut, RBASE_ADDR)) == DEFAULT_RESULT_BASE
    assert (await mmio_read(dut, SIZE_ADDR)) == ARRAY_DIM


@cocotb.test()
async def reset_clears_status(dut):
    """Status register is 0 after reset."""
    await setup(dut)
    status = await mmio_read(dut, STATUS_ADDR)
    assert status == 0, f"Status should be 0 after reset, got {status}"


# ===========================================================
# FSM Status Tests
# ===========================================================


@cocotb.test()
async def status_busy_after_start(dut):
    """BUSY bit is set shortly after cfg_start is written."""
    await setup(dut)
    # Pre-load dummy memory so FSM doesn't stall on uninitialized data
    mem = {DEFAULT_WEIGHT_BASE + i: 0 for i in range(ARRAY_DIM)}
    mem[DEFAULT_ACT_BASE] = 0
    await mem_preload(dut, mem)

    await start_inference(dut, reload_weights=True, precision=1)
    await ClockCycles(dut.clk, 3)  # give FSM time to reach LOAD_WEIGHTS
    status = await mmio_read(dut, STATUS_ADDR)
    assert (status & 0x1) == 1, f"Expected BUSY=1, got status={status}"


@cocotb.test()
async def status_done_after_inference(dut):
    """Status = DONE after full inference run."""
    await setup(dut)
    mem = {DEFAULT_WEIGHT_BASE + i: 0 for i in range(ARRAY_DIM)}
    mem[DEFAULT_ACT_BASE] = 0
    await mem_preload(dut, mem)

    await start_inference(dut, reload_weights=True, precision=1)
    await wait_for_done(dut)

    status = await mmio_read(dut, STATUS_ADDR)
    assert (status & 0x2) == 2, f"Expected DONE bit set, got status={status}"
    assert (status & 0x1) == 0, f"Expected BUSY cleared after DONE, got status={status}"


# ===========================================================
# Weight Loading Tests
# ===========================================================


@cocotb.test()
async def weight_loading_count(dut):
    """Exactly 32 words are written back to result_base after weight-only (all-zero) inference."""
    await setup(dut)
    # Pre-load zeros for weights and activation; pre-init result region to sentinel
    mem = {DEFAULT_WEIGHT_BASE + i: 0 for i in range(ARRAY_DIM)}
    mem[DEFAULT_ACT_BASE] = 0
    mem.update({DEFAULT_RESULT_BASE + i: 0xDEADC0DE for i in range(ARRAY_DIM)})
    await mem_preload(dut, mem)

    await start_inference(dut, reload_weights=True, precision=1)
    await wait_for_done(dut)
    await ClockCycles(dut.clk, 2)  # settle writes

    # All 32 result slots should be overwritten (not 0xDEADC0DE anymore)
    for col in range(ARRAY_DIM):
        addr = DEFAULT_RESULT_BASE + col
        val = await mem_read_tb(dut, addr)
        assert val != 0xDEADC0DE, (
            f"col {col}: result was never written (still sentinel)"
        )


@cocotb.test()
async def skip_reload_finishes_faster(dut):
    """With reload_weights=0, inference completes without weight reads."""
    await setup(dut)
    # Pre-load activation only (no weights needed since weight_reg = 0 from reset)
    mem = {DEFAULT_ACT_BASE: 0}
    await mem_preload(dut, mem)

    # Run once with reload=True to fill weight_reg
    mem_full = {DEFAULT_WEIGHT_BASE + i: 0 for i in range(ARRAY_DIM)}
    mem_full.update(mem)
    await mem_preload(dut, mem_full)
    await start_inference(dut, reload_weights=True, precision=1)
    await wait_for_done(dut)

    # Second inference without reload - should also complete
    await start_inference(dut, reload_weights=False, precision=1)
    await wait_for_done(dut)
    status = await mmio_read(dut, STATUS_ADDR)
    assert (status & 0x2) == 2, (
        "Second inference (skip-reload) should complete with DONE"
    )


# ===========================================================
# End-to-End Compute Tests
# ===========================================================


@cocotb.test()
async def end_to_end_all_ones_1bit(dut):
    """
    All-ones weights, all-ones activation, 1-bit precision, array_size=32.
    popcount = 32 per column. shift_acc = 32.
    bias = 32 * (2^1 - 1) = 32.
    signed = 2*32 - 32 = 32. All 32 results must equal 32.
    """
    await setup(dut)
    mem = {DEFAULT_WEIGHT_BASE + i: 0xFFFFFFFF for i in range(ARRAY_DIM)}
    mem[DEFAULT_ACT_BASE + 0] = 0xFFFFFFFF
    mem.update({DEFAULT_RESULT_BASE + i: 0 for i in range(ARRAY_DIM)})
    await mem_preload(dut, mem)

    await start_inference(dut, reload_weights=True, precision=1)
    await wait_for_done(dut)

    await ClockCycles(dut.clk, 2)  # settle
    for col in range(ARRAY_DIM):
        addr = DEFAULT_RESULT_BASE + col
        got = await mem_read_tb(dut, addr)
        if got >= 0x80000000:
            got -= 0x100000000
        assert got == 32, f"col {col}: expected 32, got {got}"


@cocotb.test()
async def end_to_end_all_zeros_1bit(dut):
    """
    All-zeros weights, all-ones activation, 1-bit precision.
    XNOR(0,1)=0, popcount=0, shift_acc=0.
    bias = 32. signed = 2*0 - 32 = -32. All results must equal -32.
    """
    await setup(dut)
    mem = {DEFAULT_WEIGHT_BASE + i: 0x00000000 for i in range(ARRAY_DIM)}
    mem[DEFAULT_ACT_BASE + 0] = 0xFFFFFFFF
    # Pre-init result region to known non-result value
    mem.update({DEFAULT_RESULT_BASE + i: 0 for i in range(ARRAY_DIM)})
    await mem_preload(dut, mem)

    await start_inference(dut, reload_weights=True, precision=1)
    await wait_for_done(dut)

    await ClockCycles(dut.clk, 2)
    for col in range(ARRAY_DIM):
        addr = DEFAULT_RESULT_BASE + col
        got = await mem_read_tb(dut, addr)
        if got >= 0x80000000:
            got -= 0x100000000
        assert got == -32, f"col {col}: expected -32, got {got}"


@cocotb.test()
async def end_to_end_all_ones_2bit(dut):
    """
    All-ones weights, all-ones activation (both bit-planes), 2-bit precision.
    bit_plane=1: shift_acc = 0*2 + 32 = 32
    bit_plane=0: shift_acc = 32*2 + 32 = 96
    bias = 32 * (2^2 - 1) = 96. signed = 2*96 - 96 = 96.
    """
    await setup(dut)
    mem = {DEFAULT_WEIGHT_BASE + i: 0xFFFFFFFF for i in range(ARRAY_DIM)}
    mem[DEFAULT_ACT_BASE + 0] = 0xFFFFFFFF  # LSB bit-plane
    mem[DEFAULT_ACT_BASE + 1] = 0xFFFFFFFF  # MSB bit-plane
    mem.update({DEFAULT_RESULT_BASE + i: 0 for i in range(ARRAY_DIM)})
    await mem_preload(dut, mem)

    await start_inference(dut, reload_weights=True, precision=2)
    await wait_for_done(dut, max_cycles=500)

    await ClockCycles(dut.clk, 2)
    for col in range(ARRAY_DIM):
        addr = DEFAULT_RESULT_BASE + col
        got = await mem_read_tb(dut, addr)
        if got >= 0x80000000:
            got -= 0x100000000
        assert got == 96, f"col {col}: expected 96, got {got}"
