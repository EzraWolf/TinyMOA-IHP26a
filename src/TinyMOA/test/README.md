# TinyMOA Test Suite

cocotb + pytest tests. Each 32-bit operation requires 8 clock cycles on the 4-bit datapath; test helpers drive signals using `nibble_ct` accordingly.

Credit: adapted from [TinyQV](https://github.com/MichaelBell/tinyQV/tree/858986b72975157ebf27042779b6caaed164c57b/test).

## Tests

| Test | Description |
|------|-------------|
| `integration/cpu` | Full RV32EC program core execution |
| `integration/dcim` | DCIM weight load, inference, signed output |
| `integration/tinymoa` | Top-level system program smoke tests |
| `unit/alu` | ALU ops: add, sub, shifts, logic, compare |
| `unit/bootloader` | Boot FSM flash-to-TCM load sequence |
| `unit/counter` | PC increment and reset |
| `unit/cpu` | CPU unit execution/edge case tests |
| `unit/dcim` | DCIM unit execution/edge case tests |
| `unit/decoder` | RV32I and RV32C instruction decoding |
| `unit/qspi` | QSPI controller command, read/write, etc. |
| `unit/registers` | Register file write and dual-port read |
| `unit/tcm` | Dual-port Tightly-Coupled Memory (TCM) read/write serial/parallel |

## Running

```bash
# All tests
uv run pytest test/test.py

# Single module
uv run pytest test/test.py::test_alu
```

Waveforms are written as `.fst` files to `test/sim_build/`. View with `gtkwave` or `surfer`.

## Docs

| Document | Contents |
|----------|----------|
| [Architecture.md](../docs/Architecture.md) | Address map, pipeline, module hierarchy, DCIM MMIO |
| [ISA.md](../docs/ISA.md) | Full instruction encoding, opcode map |
| [DCIM.md](../docs/DCIM.md) | XNOR array, compressor modes, FSM, signed conversion, cycle counts |
| [Bootloader.md](../docs/Bootloader.md) | Boot FSM, flash image layout |
