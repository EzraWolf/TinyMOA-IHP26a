# TinyMOA

A minimal RISC-V CPU with a Digital Compute-in-Memory (DCIM) accelerator for neural network inference. TinyMOA is built on a 4-bit nibble-serial datapath targeting IHP SG13G2 130nm via [TinyTapeout IHP26a](https://tinytapeout.com/).

The CPU is directly based on [TinyQV](https://github.com/MichaelBell/tinyQV) by [Michael Bell](https://github.com/MichaelBell), and while structurally overhauled to support DCIM and Tighly Coupled Memory (TCM), the serial 4-bit bus architecture, register file design, and pipeline structure are all his work. *TinyMOA would not exist without it.*


## Purpose

Because of the von-Neumann bottleneck, modern GPUs spend up to *80%* of their power budget moving data, not computing. As model sizes grow, the memory bandwidth wall becomes the dominant bottleneck as opposed to computational throughput.

Compute-in-Memory (CIM) eliminates this by processing data where it is stored. TinyMOA implements a *Digital* CIM array: instead of analog crossbars with exotic materials, it uses standard CMOS cells to perform binary XNOR multiply-accumulate operations directly in the memory array. This approach is fully compatible with open-source PDKs and university fabs.

Reference: ISSCC 2022, Wang et al. "DCIM: 2219TOPS/W 2569F2/b Digital In-Memory Computing Macro in 28nm Based on Approximate Arithmetic Hardware"


### Research Question

Using open-source PDKs and standard CMOS logic, can a digital CIM array obtain 30-40x the energy efficiency (TOPS/W) over GPU-class hardware on binary/low-precision neural network inference?

If so, this significantly lowers the barrier for CIM research at institutions without access to specialized fabrication techniques and methodologized.


## Architecture

### CPU Core

RV32EC, nibble-serial, 6-state pipeline:

`FETCH -> DECODE -> EXECUTE -> WRITEBACK -> MEM -> LOAD_WB`

Registers are read and written 4 bits per clock cycle; a full 32-bit operation completes in 8 cycles. Compressed 16-bit instructions complete in 4 cycles (except C.MUL which needs 8).

| Choice | Reason |
|--------|--------|
| RV32 | Smallest ISA with mature C compiler support (GCC, LLVM) |
| E (Embedded) | 16 registers instead of 32 for smaller area |
| C (Compressed) | 16-bit instructions double code density and halve fetch bandwidth |

### ISA

| Extension    | Notes |
|--------------|-------|
| RV32I (base) | Fully implemented |
| E (embedded) | 16 registers instead of 32 (x0–x15) |
| C (compresseD) / Zca | Full Q0, Q1, Q2 |
| Zcb    | Byte ops + C.MUL (16x16 -> 32-bit) |
| Zicond | Full: `czero.eqz`, `czero.nez` |
| Zicsr  | Not implemented |
| M (multiply) | Not implemented - opcodes reserved, C.MUL covers the common case |
| F (float) | Not implemented - opcodes reserved |

### DCIM Accelerator

A 32x32 array of binary XNOR MAC units, controlled entirely via 6 MMIO registers at `0x400000`. The CPU configures and polls the DCIM with ordinary loads and stores so that no custom instructions are necessary.

| Property | Value |
|----------|-------|
| Array | 32x32 XNOR MACs |
| Activation precision | 1, 2, or 4 bits (bit-serial) |
| Compressor | Double-approx (default), single-approx, or exact (set by compile-time flag) |
| Weight storage | 1024 flip-flops (32 cols x 32 bits); loaded from TCM at runtime |
| Signed output | Hardware bias correction: `2 * acc - N*(2^P−1)` |
| Control | MMIO polling; no interrupts |

### Memory

The internal TCM has two ports: Port A for the CPU/Bootloader, Port B DCIM.

| Byte Range            | Target |
|-----------------------|--------|
| `0x000000 - 0x0007FF` | TCM (2 KB, 512x32) |
| `0x000800 - 0x000FFF` | Reserved (future TCM) |
| `0x001000 - 0x3FFFFF` | QSPI Flash |
| `0x400000 - 0x400017` | DCIM MMIO (6 regs) |
| `0x800000 - 0xBFFFFF` | QSPI PSRAM A |
| `0xC00000 - 0xFFFFFF` | QSPI PSRAM B |


## Documentation

All design documents live in [`docs/`](docs/):

| Document | Contents |
|----------|----------|
| [Architecture.md](docs/Architecture.md) | Address map, pipeline, module hierarchy, DCIM MMIO |
| [ISA.md](docs/ISA.md) | Full instruction encoding, opcode map |
| [DCIM.md](docs/DCIM.md) | XNOR array, compressor modes, FSM, signed conversion, cycle counts |
| [Bootloader.md](docs/Bootloader.md) | Boot FSM, flash image layout |
