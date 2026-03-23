"""
QSPI controller unit tests (TDD, incremental).

RTL timing reference (src/qspi.v):
  All state transitions happen on posedge clk.
  Outputs (spi_data_out, spi_clk_out, CS, etc.) update on posedge.
  To sample stable outputs, wait 1ns after RisingEdge.

Transaction phases:
  IDLE -> CMD (2 cycles) -> ADDR_TX (6 cycles) -> DATA_RX/TX (2/4/8) -> DONE (1)

  Cycle counts for a word read:  1 (IDLE latch) + 2 (CMD) + 6 (ADDR) + 8 (DATA_RX) + 1 (DONE) = 18
  Cycle counts for a word write: 1 (IDLE latch) + 2 (CMD) + 6 (ADDR) + 8 (DATA_TX) + 1 (DONE) = 18
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, Timer


async def reset(dut):
    """Reset DUT and return with all inputs deasserted."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    dut.read.value = 0
    dut.write.value = 0
    dut.addr.value = 0
    dut.size.value = 0
    dut.wdata.value = 0
    dut.spi_data_in.value = 0
    dut.nrst.value = 0
    await ClockCycles(dut.clk, 2)
    dut.nrst.value = 1
    await ClockCycles(dut.clk, 1)


async def sample(dut):
    """Wait 1ns after posedge for outputs to settle, then return."""
    await Timer(1, units="ns")


async def start_read(dut, addr, size=2):
    """Assert read for one cycle. Returns after the IDLE->CMD posedge."""
    dut.addr.value = addr
    dut.size.value = size
    dut.read.value = 1
    await RisingEdge(dut.clk)  # IDLE posedge: latches addr, asserts CS, state->CMD
    dut.read.value = 0


async def start_write(dut, addr, wdata, size=2):
    """Assert write for one cycle. Returns after the IDLE->CMD posedge."""
    dut.addr.value = addr
    dut.size.value = size
    dut.wdata.value = wdata
    dut.write.value = 1
    await RisingEdge(
        dut.clk
    )  # IDLE posedge: latches addr/wdata, asserts CS, state->CMD
    dut.write.value = 0


async def wait_ready(dut, timeout=50):
    """Wait until ready pulses high. Returns after the posedge where ready=1."""
    for _ in range(timeout):
        await RisingEdge(dut.clk)
        await sample(dut)
        if int(dut.ready.value) == 1:
            return
    raise TimeoutError("ready never asserted")


# === Reset tests ===


@cocotb.test()
async def test_reset_cs_deasserted(dut):
    """After reset, all CS lines are high (deasserted)."""
    await reset(dut)
    await sample(dut)
    assert int(dut.spi_flash_cs_n.value) == 1
    assert int(dut.spi_ram_a_cs_n.value) == 1
    assert int(dut.spi_ram_b_cs_n.value) == 1


@cocotb.test()
async def test_reset_clk_low(dut):
    """After reset, spi_clk_out is low."""
    await reset(dut)
    await sample(dut)
    assert int(dut.spi_clk_out.value) == 0


@cocotb.test()
async def test_reset_ready_low(dut):
    """After reset, ready is low."""
    await reset(dut)
    await sample(dut)
    assert int(dut.ready.value) == 0


@cocotb.test()
async def test_reset_oe_zero(dut):
    """After reset, spi_data_oe is 0."""
    await reset(dut)
    await sample(dut)
    assert int(dut.spi_data_oe.value) == 0


# === CS selection ===


@cocotb.test()
async def test_cs_flash(dut):
    """addr[23:22]=00 asserts flash CS only."""
    await reset(dut)
    await start_read(dut, 0x001234)
    await sample(dut)
    assert int(dut.spi_flash_cs_n.value) == 0, "flash CS should be low"
    assert int(dut.spi_ram_a_cs_n.value) == 1
    assert int(dut.spi_ram_b_cs_n.value) == 1


@cocotb.test()
async def test_cs_ram_a(dut):
    """addr[23:22]=01 asserts ram_a CS only."""
    await reset(dut)
    await start_read(dut, 0x401234)
    await sample(dut)
    assert int(dut.spi_flash_cs_n.value) == 1
    assert int(dut.spi_ram_a_cs_n.value) == 0, "ram_a CS should be low"
    assert int(dut.spi_ram_b_cs_n.value) == 1


@cocotb.test()
async def test_cs_ram_b(dut):
    """addr[23:22]=10 asserts ram_b CS only."""
    await reset(dut)
    await start_read(dut, 0x801234)
    await sample(dut)
    assert int(dut.spi_flash_cs_n.value) == 1
    assert int(dut.spi_ram_a_cs_n.value) == 1
    assert int(dut.spi_ram_b_cs_n.value) == 0, "ram_b CS should be low"


# =========================================================================
# CMD phase
# =========================================================================


@cocotb.test()
async def test_cmd_read_0x03(dut):
    """Read CMD phase outputs nibbles 0x0 then 0x3."""
    await reset(dut)
    await start_read(dut, 0x001000)

    # start_read consumed IDLE posedge. CMD cnt=0 executes on next posedge.
    await RisingEdge(dut.clk)
    await sample(dut)
    n0 = int(dut.spi_data_out.value)

    await RisingEdge(dut.clk)  # CMD cnt=1
    await sample(dut)
    n1 = int(dut.spi_data_out.value)

    assert n0 == 0x0, f"CMD upper nibble: expected 0x0, got {hex(n0)}"
    assert n1 == 0x3, f"CMD lower nibble: expected 0x3, got {hex(n1)}"


@cocotb.test()
async def test_cmd_write_0x02(dut):
    """Write CMD phase outputs nibbles 0x0 then 0x2."""
    await reset(dut)
    await start_write(dut, 0x401000, 0xDEADBEEF)

    await RisingEdge(dut.clk)
    await sample(dut)
    n0 = int(dut.spi_data_out.value)

    await RisingEdge(dut.clk)  # CMD cnt=1
    await sample(dut)
    n1 = int(dut.spi_data_out.value)

    assert n0 == 0x0, f"CMD upper nibble: expected 0x0, got {hex(n0)}"
    assert n1 == 0x2, f"CMD lower nibble: expected 0x2, got {hex(n1)}"


@cocotb.test()
async def test_cmd_oe_high(dut):
    """spi_data_oe = 0xF during CMD phase."""
    await reset(dut)
    await start_read(dut, 0x001000)

    await RisingEdge(dut.clk)  # CMD cnt=0 executes
    await sample(dut)
    assert int(dut.spi_data_oe.value) == 0xF, "OE should be 0xF during CMD"


# =========================================================================
# ADDR_TX phase
# =========================================================================


@cocotb.test()
async def test_addr_phase(dut):
    """ADDR_TX outputs 24-bit address as 6 nibbles, MSN first."""
    await reset(dut)
    test_addr = 0x12AB9C
    await start_read(dut, test_addr)

    # Skip CMD: 2 cycles execute on next 2 posedges. ADDR_TX starts on cycle 3.
    # start_read consumed IDLE posedge. CMD takes 2 posedges. ADDR starts on 3rd.
    await ClockCycles(dut.clk, 2)  # CMD cnt=0 and cnt=1

    # Collect 6 ADDR nibbles (each posedge executes one ADDR_TX cycle)
    expected = [(test_addr >> (20 - i * 4)) & 0xF for i in range(6)]
    got = []
    for i in range(6):
        await RisingEdge(dut.clk)
        await sample(dut)
        got.append(int(dut.spi_data_out.value))

    for i, (g, e) in enumerate(zip(got, expected)):
        assert g == e, f"Addr nibble {i}: expected {hex(e)}, got {hex(g)}"


@cocotb.test()
async def test_addr_oe_high(dut):
    """spi_data_oe = 0xF during ADDR_TX phase."""
    await reset(dut)
    await start_read(dut, 0x001000)

    # Skip CMD (2 posedges), sample first ADDR_TX posedge
    await ClockCycles(dut.clk, 2)
    await RisingEdge(dut.clk)
    await sample(dut)
    assert int(dut.spi_data_oe.value) == 0xF, "OE should be 0xF during ADDR_TX"


# =========================================================================
# DATA_TX phase (write)
# =========================================================================


@cocotb.test()
async def test_data_tx_word(dut):
    """DATA_TX drives wdata nibbles MSN first for a word write."""
    await reset(dut)
    test_word = 0xDEADBEEF
    await start_write(dut, 0x401000, test_word)

    # Skip CMD(2) + ADDR(6) posedges
    await ClockCycles(dut.clk, 2 + 6)

    expected = [(test_word >> (28 - i * 4)) & 0xF for i in range(8)]
    got = []
    for i in range(8):
        await RisingEdge(dut.clk)
        await sample(dut)
        got.append(int(dut.spi_data_out.value))

    for i, (g, e) in enumerate(zip(got, expected)):
        assert g == e, f"TX nibble {i}: expected {hex(e)}, got {hex(g)}"


@cocotb.test()
async def test_data_tx_byte(dut):
    """DATA_TX drives 2 nibbles for a byte write."""
    await reset(dut)
    await start_write(dut, 0x401000, 0xAB, size=0)

    # Skip CMD(2) + ADDR(6) posedges
    await ClockCycles(dut.clk, 2 + 6)

    # Byte: wdata_reg = {0xAB, 24'b0}, so MSN = 0xA, then 0xB
    await RisingEdge(dut.clk)
    await sample(dut)
    n0 = int(dut.spi_data_out.value)
    await RisingEdge(dut.clk)
    await sample(dut)
    n1 = int(dut.spi_data_out.value)

    assert n0 == 0xA, f"TX byte nibble 0: expected 0xA, got {hex(n0)}"
    assert n1 == 0xB, f"TX byte nibble 1: expected 0xB, got {hex(n1)}"


@cocotb.test()
async def test_data_tx_oe_high(dut):
    """spi_data_oe = 0xF during DATA_TX phase."""
    await reset(dut)
    await start_write(dut, 0x401000, 0x12345678)

    # Skip CMD(2) + ADDR(6) posedges, sample first DATA_TX
    await ClockCycles(dut.clk, 2 + 6)
    await RisingEdge(dut.clk)
    await sample(dut)
    assert int(dut.spi_data_oe.value) == 0xF, "OE should be 0xF during DATA_TX"


# =========================================================================
# DATA_RX phase (read)
# =========================================================================


@cocotb.test()
async def test_data_rx_word(dut):
    """DATA_RX assembles 8 nibbles into rdata for a word read."""
    await reset(dut)
    await start_read(dut, 0x001000, size=2)

    # Skip CMD(2) + ADDR(6) = 8 cycles to reach DATA_RX
    await ClockCycles(dut.clk, 2 + 6)

    # Feed 8 nibbles: 0xDEADBEEF
    rx = [0xD, 0xE, 0xA, 0xD, 0xB, 0xE, 0xE, 0xF]
    for i in range(8):
        dut.spi_data_in.value = rx[i]
        await RisingEdge(dut.clk)

    # Now in DONE state. Wait for ready.
    await wait_ready(dut, timeout=5)
    result = int(dut.rdata.value)
    assert result == 0xDEADBEEF, f"rdata: expected 0xDEADBEEF, got {hex(result)}"


@cocotb.test()
async def test_data_rx_byte(dut):
    """DATA_RX assembles 2 nibbles for a byte read."""
    await reset(dut)
    await start_read(dut, 0x001000, size=0)

    # Skip CMD(2) + ADDR(6)
    await ClockCycles(dut.clk, 2 + 6)

    rx = [0xA, 0xB]
    for n in rx:
        dut.spi_data_in.value = n
        await RisingEdge(dut.clk)

    await wait_ready(dut, timeout=5)
    result = int(dut.rdata.value) & 0xFF
    assert result == 0xAB, f"rdata byte: expected 0xAB, got {hex(result)}"


@cocotb.test()
async def test_data_rx_halfword(dut):
    """DATA_RX assembles 4 nibbles for a halfword read."""
    await reset(dut)
    await start_read(dut, 0x001000, size=1)

    # Skip CMD(2) + ADDR(6)
    await ClockCycles(dut.clk, 2 + 6)

    rx = [0xC, 0xA, 0xF, 0xE]
    for n in rx:
        dut.spi_data_in.value = n
        await RisingEdge(dut.clk)

    await wait_ready(dut, timeout=5)
    result = int(dut.rdata.value) & 0xFFFF
    assert result == 0xCAFE, f"rdata half: expected 0xCAFE, got {hex(result)}"


@cocotb.test()
async def test_data_rx_oe_zero(dut):
    """spi_data_oe = 0 during DATA_RX phase."""
    await reset(dut)
    await start_read(dut, 0x001000, size=2)

    # Skip CMD(2) + ADDR(6), sample first DATA_RX
    await ClockCycles(dut.clk, 2 + 6)
    await RisingEdge(dut.clk)
    await sample(dut)
    assert int(dut.spi_data_oe.value) == 0, "OE should be 0 during DATA_RX"


# =========================================================================
# DONE / ready / CS deassert
# =========================================================================


@cocotb.test()
async def test_ready_pulses_one_cycle(dut):
    """ready=1 for exactly one cycle after DONE."""
    await reset(dut)
    await start_read(dut, 0x001000, size=2)

    # Run through full transaction
    # CMD(2) + ADDR(6) + DATA_RX(8) = 16 cycles, then DONE
    for i in range(8):
        await RisingEdge(dut.clk)  # CMD + ADDR
    for i in range(8):
        dut.spi_data_in.value = 0
        await RisingEdge(dut.clk)  # DATA_RX

    # DONE cycle
    await RisingEdge(dut.clk)
    await sample(dut)
    assert int(dut.ready.value) == 1, "ready should be 1 in DONE"

    # Next cycle: ready should be 0
    await RisingEdge(dut.clk)
    await sample(dut)
    assert int(dut.ready.value) == 0, "ready should deassert after 1 cycle"


@cocotb.test()
async def test_cs_deasserted_after_done(dut):
    """All CS lines return high after transaction completes."""
    await reset(dut)
    await start_read(dut, 0x001000, size=2)

    await wait_ready(dut, timeout=30)
    assert int(dut.spi_flash_cs_n.value) == 1, "flash CS should be high after done"
    assert int(dut.spi_ram_a_cs_n.value) == 1
    assert int(dut.spi_ram_b_cs_n.value) == 1


@cocotb.test()
async def test_clk_low_after_done(dut):
    """spi_clk_out returns to 0 after transaction."""
    await reset(dut)
    await start_read(dut, 0x001000, size=2)

    await wait_ready(dut, timeout=30)
    assert int(dut.spi_clk_out.value) == 0, "spi_clk_out should be 0 after done"


@cocotb.test()
async def test_clk_toggles_during_cmd(dut):
    """spi_clk_out toggles each cycle during CMD phase."""
    await reset(dut)
    await start_read(dut, 0x001000)

    await sample(dut)
    clk0 = int(dut.spi_clk_out.value)

    await RisingEdge(dut.clk)
    await sample(dut)
    clk1 = int(dut.spi_clk_out.value)

    assert clk0 != clk1, f"spi_clk_out should toggle: got {clk0} then {clk1}"
