# TinyMOA Source

Verilog sources for TinyMOA. The CPU uses a 4-bit serial datapath and each 32-bit operation takes 8 clock cycles (4 bits/cycle). A `nibble_ct` counter sequences nibbles through the pipeline. Compressed 16-bit instructions complete in 4 cycles.

## Structure

```
src/
├── tinymoa.v        # Top-level wrapper (CPU, TCM, QSPI, DCIM)
├── cpu.v            # RV32EC pure execution core (no memory)
├── decoder.v        # RV32I, RV32C decoder
├── alu.v            # Nibble-serial ALU
├── registers.v      # RV32E register file
├── counter.v        # Configurable program/nibble counter
├── tcm.v            # Tightly Coupled Memory (dual port 512x32 SRAM macro)
├── qspi.v           # QSPI controller for external flash and PSRAM
├── bootloader.v     # Bootloader FSM to load program from QSPI flash into TCM
└── dcim/
    ├── compressor.v # Approximate Popcount compressor
    └── dcim.v       # DCIM core
```

## Key Modules

| File | Module | Purpose |
|------|--------|---------|
| `tinymoa.v` | `tinymoa` | TinyTapeout wrapper; integrates all subsystems |
| `cpu.v` | `tinymoa_cpu` | 6-stage nibble-serial RISC-V pipeline |
| `decoder.v` | `tinymoa_decoder` | Decodes RV32I/C instructions to control signals |
| `alu.v` | `tinymoa_alu` | 4-bit slice ALU; result assembled over 8 cycles |
| `registers.v` | `tinymoa_registers` | 16x32 register file; gp/tp pseudo-hardwired |
| `counter.v` | `tinymoa_counter` | PC with nibble-serial increment |
| `tcm.v` | `tinymoa_tcm` | Wraps IHP `SRAM_DP_512x32` macro; Port A = CPU, Port B = DCIM |
| `qspi.v` | `tinymoa_qspi` | 4-wire SPI; supports flash XIP and PSRAM read/write |
| `bootloader.v` | `tinymoa_bootloader` | Copies flash image to TCM on reset |
| `dcim/dcim.v` | `tinymoa_dcim` | 32x32 XNOR MAC array with FSM control |
| `dcim/compressor.v` | `tinymoa_compressor` | Per-column popcount; compile-time mode selection |

## See Also

- [docs/ISA.md](../docs/ISA.md) — Instruction encoding and opcode map
- [docs/CIM.md](../docs/CIM.md) — DCIM architecture, FSM, signed conversion
- [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) — Module hierarchy and memory map
- [test/README.md](../test/README.md) — Running tests and waveform viewing
