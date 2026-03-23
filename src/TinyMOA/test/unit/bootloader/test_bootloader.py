"""
Test suite for the boot FSM (boot_fsm)

- reset_holds_boot_done_low
- idle_to_fetch_on_reset_deassert
- flash_addr_starts_at_0x001000
- flash_read_asserted_during_fetch
- write_tcm_sram_wen_one_cycle
- write_tcm_correct_sram_addr
- word_index_increments_after_each_word
- all_512_words_copied_in_order
- boot_done_asserts_after_512_words
- boot_done_stays_high_after_completion
- flash_stall_fsm_waits_for_ready
- flash_ready_deasserted_after_word
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles, Timer


FLASH_BASE = 0x001000
WORD_COUNT = 512


async def setup(dut):
    """Start clock, hold reset, return with nrst=1."""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.rom_ready.value = 0
    dut.rom_rdata.value = 0

    dut.nrst.value = 0
    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1


async def fast_rom(dut, word_count=None):
    """
    Background coroutine: respond to rom_read with ready=1 every cycle.
    Returns {tcm_addr: rom_data} dict of all TCM writes observed.
    """
    writes = {}
    count = 0
    while True:
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        if int(dut.rom_read.value):
            addr = int(dut.rom_addr.value)
            # Respond immediately next posedge
            dut.rom_rdata.value = addr  # use address as data for traceability
            dut.rom_ready.value = 1
        else:
            dut.rom_ready.value = 0
        if int(dut.tcm_wen.value):
            ta = int(dut.tcm_addr.value)
            td = int(dut.tcm_din.value)
            writes[ta] = td
            count += 1
            if word_count is not None and count >= word_count:
                break
    return writes


@cocotb.test()
async def reset_holds_boot_done_low(dut):
    """boot_done must be low while nrst is asserted."""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    dut.rom_ready.value = 0
    dut.rom_rdata.value = 0
    dut.nrst.value = 0
    await ClockCycles(dut.clk, 3)
    assert int(dut.boot_done.value) == 0, "boot_done should be low during reset"


@cocotb.test()
async def flash_addr_starts_at_0x001000(dut):
    """First rom_addr after reset must be FLASH_BASE = 0x001000."""
    await setup(dut)

    # After 2 clock cycles (IDLE->FETCH), rom_addr should be set
    for _ in range(5):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        if int(dut.rom_read.value):
            addr = int(dut.rom_addr.value)
            assert addr == FLASH_BASE, (
                f"First ROM addr: expected 0x{FLASH_BASE:06X}, got 0x{addr:06X}"
            )
            return

    assert False, "rom_read never asserted within 5 cycles"


@cocotb.test()
async def flash_read_asserted_during_fetch(dut):
    """rom_read must stay asserted until rom_ready goes high."""
    await setup(dut)

    # Don't respond with ready - verify rom_read stays asserted
    read_cycles = 0
    for _ in range(8):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        if int(dut.rom_read.value):
            read_cycles += 1

    assert read_cycles >= 3, (
        f"rom_read should stay asserted while stalled, only saw {read_cycles} cycles"
    )


@cocotb.test()
async def write_tcm_sram_wen_one_cycle(dut):
    """tcm_wen must be asserted for exactly one clock cycle per word."""
    await setup(dut)

    wen_pulses = []
    last_wen = 0

    # Respond immediately to ROM reads
    async def rom_model():
        while True:
            await RisingEdge(dut.clk)
            await Timer(1, units="ns")
            if int(dut.rom_read.value):
                dut.rom_rdata.value = 0xDEADC0DE
                dut.rom_ready.value = 1
            else:
                dut.rom_ready.value = 0

    cocotb.start_soon(rom_model())

    # Observe for 20 cycles to catch first few writes
    wen_high_count = 0
    for _ in range(20):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        cur = int(dut.tcm_wen.value)
        if cur and not last_wen:
            wen_pulses.append(1)
            wen_high_count = 1
        elif cur and last_wen:
            wen_high_count += 1
        elif not cur and last_wen:
            wen_pulses.append(wen_high_count)
        last_wen = cur

    # Each wen pulse should be 1 cycle
    # wen_pulses[0] is the first complete pulse (start + end observed)
    if len(wen_pulses) >= 2:
        for p in wen_pulses[:-1]:  # last may be incomplete
            assert p == 1, f"tcm_wen pulse width: expected 1, got {p}"


@cocotb.test()
async def write_tcm_correct_sram_addr(dut):
    """First 4 TCM writes go to addresses 0, 1, 2, 3."""
    await setup(dut)

    tcm_addrs = []

    async def rom_model():
        while True:
            await RisingEdge(dut.clk)
            await Timer(1, units="ns")
            if int(dut.rom_read.value):
                dut.rom_rdata.value = 0x12345678
                dut.rom_ready.value = 1
            else:
                dut.rom_ready.value = 0

    cocotb.start_soon(rom_model())

    for _ in range(40):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        if int(dut.tcm_wen.value):
            tcm_addrs.append(int(dut.tcm_addr.value))
        if len(tcm_addrs) >= 4:
            break

    assert len(tcm_addrs) >= 4, f"Expected at least 4 TCM writes, got {len(tcm_addrs)}"
    assert tcm_addrs[:4] == [0, 1, 2, 3], f"First 4 TCM addresses: {tcm_addrs[:4]}"


@cocotb.test()
async def word_index_increments_after_each_word(dut):
    """ROM addresses increment by 4 with each successive fetch."""
    await setup(dut)

    rom_addrs = []

    for _ in range(100):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        if int(dut.rom_read.value):
            addr = int(dut.rom_addr.value)
            if not rom_addrs or rom_addrs[-1] != addr:
                rom_addrs.append(addr)
            dut.rom_rdata.value = 0
            dut.rom_ready.value = 1
        else:
            dut.rom_ready.value = 0
        if len(rom_addrs) >= 5:
            break

    assert len(rom_addrs) >= 5, (
        f"Expected at least 5 ROM addresses, got {len(rom_addrs)}"
    )
    for i in range(1, len(rom_addrs)):
        diff = rom_addrs[i] - rom_addrs[i - 1]
        assert diff == 4, f"ROM addr[{i}] - addr[{i - 1}] = {diff}, expected 4"


@cocotb.test()
async def all_512_words_copied_in_order(dut):
    """All 512 words are written to TCM in order with correct ROM addresses."""
    await setup(dut)

    tcm_writes = {}  # tcm_addr -> rom_addr (data = rom_addr in our model)

    for _ in range(WORD_COUNT * 4):  # max cycles with stalls
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        if int(dut.rom_read.value):
            addr = int(dut.rom_addr.value)
            dut.rom_rdata.value = addr  # data = rom_addr for easy verification
            dut.rom_ready.value = 1
        else:
            dut.rom_ready.value = 0
        if int(dut.tcm_wen.value):
            ta = int(dut.tcm_addr.value)
            td = int(dut.tcm_din.value)
            tcm_writes[ta] = td
        if int(dut.boot_done.value):
            break

    assert len(tcm_writes) == WORD_COUNT, (
        f"Expected {WORD_COUNT} writes, got {len(tcm_writes)}"
    )
    for i in range(WORD_COUNT):
        assert i in tcm_writes, f"Missing TCM write at address {i}"
        expected_rom_addr = FLASH_BASE + (i * 4)
        assert tcm_writes[i] == expected_rom_addr, (
            f"TCM[{i}] = 0x{tcm_writes[i]:08X}, expected ROM addr 0x{expected_rom_addr:08X}"
        )


@cocotb.test()
async def boot_done_asserts_after_512_words(dut):
    """boot_done goes high after all 512 words are copied."""
    await setup(dut)

    for _ in range(WORD_COUNT * 4):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        if int(dut.rom_read.value):
            dut.rom_rdata.value = 0
            dut.rom_ready.value = 1
        else:
            dut.rom_ready.value = 0
        if int(dut.boot_done.value):
            return

    assert False, "boot_done never asserted after 512*4 cycles"


@cocotb.test()
async def boot_done_stays_high_after_completion(dut):
    """boot_done remains high after asserting."""
    await setup(dut)

    done_cycle = None
    for cycle in range(WORD_COUNT * 4):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        if int(dut.rom_read.value):
            dut.rom_rdata.value = 0
            dut.rom_ready.value = 1
        else:
            dut.rom_ready.value = 0
        if int(dut.boot_done.value) and done_cycle is None:
            done_cycle = cycle

    assert done_cycle is not None, "boot_done never asserted"

    # Run 10 more cycles, verify boot_done stays high
    for _ in range(10):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        assert int(dut.boot_done.value) == 1, "boot_done dropped after asserting"


@cocotb.test()
async def flash_stall_fsm_waits_for_ready(dut):
    """When rom_ready stays low, FSM stalls in FETCH and rom_read stays asserted."""
    await setup(dut)

    # Let FSM advance to FETCH (IDLE->FETCH takes 1 cycle after reset)
    # Then keep rom_ready=0 for 10 cycles
    dut.rom_ready.value = 0

    # Wait until rom_read is asserted
    for _ in range(5):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        if int(dut.rom_read.value):
            break

    assert int(dut.rom_read.value) == 1, "rom_read never asserted"

    # Keep rom_ready=0 for 8 more cycles, verify rom_read stays high
    for _ in range(8):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        assert int(dut.rom_read.value) == 1, "rom_read dropped while stalled"
        assert int(dut.boot_done.value) == 0, "boot_done asserted during stall"


@cocotb.test()
async def flash_ready_deasserted_after_word(dut):
    """rom_read drops to 0 in the cycle after rom_ready is seen."""
    await setup(dut)

    # Let FSM reach FETCH
    dut.rom_ready.value = 0
    for _ in range(5):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        if int(dut.rom_read.value):
            break

    assert int(dut.rom_read.value) == 1, "Never reached FETCH"

    # Assert rom_ready for one cycle
    dut.rom_rdata.value = 0xABCDEF01
    dut.rom_ready.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.rom_ready.value = 0

    # rom_read should now be 0 (FSM moved to WRITE_TCM)
    assert int(dut.rom_read.value) == 0, "rom_read not deasserted after ready"
