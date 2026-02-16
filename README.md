![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg) ![](../../workflows/fpga/badge.svg) ![](../../workflows/gds/badge.svg)


# TinyMOA Overview

A modified [TinyQV](https://github.com/MichaelBell/tinyQV) RISC-V CPU with an SRAM-based analog compute-in-memory (CIM) accelerator demonstrating CMOS-compatible matrix-vector multiplication (MVM).

Fabricated on an IHP 130nm process with the [IHP SG13G2 OpenPDK](https://www.ihp-microelectronics.com/services/research-and-prototyping-service/fast-design-enablement/open-source-pdk) toolkit, submited through [TinyTapeout](https://www.tinytapeout.com) (TT) on shuttle [IHP26a](https://app.tinytapeout.com/shuttles/ttihp26a).

> **NOTE**: [The TinyMOA CPU and CIM cores are developed here](https://github.com/EzraWolf/TinyMOA) - this repo is only the *implementation* of TinyMOA for TT. 
> 
> **Status**: Under active development.
> 
> *Licensed under Apache 2.0*. If interested in using this work commercially or for research, don't hesistate to reach out for partnership or help.


## What is this?

A neural network accelerator that performs matrix multiplication directly inside SRAM arrays, eliminating data movement between the CPU and memory. Your brain operates similarly by processing your thoughts in the same place it stores your memories.

A RISC-V CPU based on [TinyQV](https://github.com/MichaelBell/tinyQV) acts as an embedded interface and controller for the CIM core so that it can run programs without external peripherals. Exact CPU and CIM architectural diagrams will be added shortly.

CIM achieves significant performance, power, and efficiency improvements over the traditional von-Neumann architecture which must load data from memory, process it, and store it - repeated billions of times.


## Key specs

- Process: IHP SG13G2 130nm BiCMOS
- Size: 8x2 tiles (~1280x200um)
- CPU: Miniature RISC-V (RV32EC) CPU based on [TinyQV](https://tinytapeout.com/chips/ttihp25a/tt_um_MichaelBell_tinyQV) with 8b bus
- CIM: 2x2 corelet array each an 8x8 cell array with 4b weights (~16x16x4b)
- Target benchmarks: TBD


## How TinyMOA's CIM Works

Traditional 6T SRAM cells only store binary 0 and 1 values. By adding 2 specially designed transistors to each cell, we can perform analog computation directly in memory.

**4b weights:** Four 8T SRAM cells form one 4b weight. Each cell is designed with what is called "binary-weighted conductance" meaning that `bit 3` conducts `2^2 = 8` times more current than `bit 0`. Thus, `bit 2` conducts 4x, `bit 1` conducts 2x, and `bit 0` is the baseline. This gives 16 possible conductance levels (0-15) per weight. Below is the proposed 4b weight layout by Jaiswal et al (2019).

![CIM Bitcell Layout](/assets/cim_bitcell_layout.png)
*Figure adapted from Jaiswal et al. (2019), Figure 7: Proposed 4b cell group layout using 8T SRAM cells.*

**Analog multiplication:** Apply input voltages to source lines (SLs) and by using Ohm's law (`current = voltage * conductance`), each weight outputs a current proportional to the input voltage times the stored weight value. An op-amp reads the summed current. That's compute in memory!

**Matrix operation:** Organize these 4b weight groups into an 8x8 array such that each row computes one dot product in parallel, completing an 8x8 matrix-vector multiplication in a single clock cycle all without moving data to a CPU.

![CIM Bitcell Organization](/assets/cim_bitcell_organization.png)
*Figure adapted from Jaiswal et al. (2019), Figure 9: 8T SRAM bitcell organization for analog compute-in-memory operations.*

## Resources

Contact wolfez@mail.uc.edu for technical collaboration, research, or commercial partnerships.


## Acknowledgements

- Jaiswal, A., Chakraborty, I., Agrawal, A., & Roy, K. (2019). "8T SRAM Cell as a Multibit Dot-Product Engine for Beyond Von Neumann Computing." *IEEE Transactions on Very Large Scale Integration (VLSI) Systems*, 27(11), 2556-2567.
- [TinyQV](https://tinytapeout.com/chips/ttihp25a/tt_um_MichaelBell_tinyQV) by Michael Bell
