"""
Test runner using cocotb_test - no Makefiles needed per unit.
Run with: `pytest test.py` or `uv run pytest test.py`
"""

import pytest
from pathlib import Path
from cocotb_test import simulator


def run_test(
    src_module,
    test_module,
    test_type="unit",
    dir=None,
    extra_sources=None,
    defines=None,
):
    """
    Run a standard cocotb unit test using pytest and cocotb-test.
    """
    PROJECT_DIR = Path(__file__).parent.resolve()
    SRC_DIR = PROJECT_DIR.parent / "src"
    SIM_BUILD = PROJECT_DIR / "sim_build"

    test_dir = dir or src_module

    src_path = SRC_DIR / (dir or "") / f"{src_module}.v"
    tb_path = PROJECT_DIR / test_type / test_dir / f"tb_{src_module}.v"
    module = f"{test_type}.{test_dir}.test_{test_module}"
    toplevel = f"tb_{src_module}"

    sources = (
        [str(src_path)]
        + [str(SRC_DIR / s) for s in (extra_sources or [])]
        + [str(tb_path)]
    )

    simulator.run(
        verilog_sources=sources,
        toplevel=toplevel,
        module=module,
        simulator="icarus",
        defines=defines or [],
        sim_build=str(SIM_BUILD / src_module),
        python_search=[str(PROJECT_DIR)],
    )


# === Integration tests ===


def test_cpu_integration():
    run_test(
        "cpu",
        "cpu",
        test_type="integration",
        extra_sources=[
            "counter.v",
            "decoder.v",
            "registers.v",
            "alu.v",
        ],
    )


def test_dcim_integration():
    run_test(
        "dcim",
        "dcim",
        dir="dcim",
        test_type="integration",
        extra_sources=["dcim/compressor.v"],
    )


def test_tinymoa_integration():
    run_test(
        "tinymoa",
        "tinymoa",
        test_type="integration",
        extra_sources=[
            "cpu.v",
            "counter.v",
            "decoder.v",
            "registers.v",
            "alu.v",
            "tcm.v",
            "qspi.v",
            "dcim/dcim.v",
            "dcim/compressor.v",
            "bootloader.v",
        ],
        defines=["BEHAVIORAL"],
    )


# === Unit tests ===


def test_alu_unit():
    run_test("alu", "alu")


def test_bootloader_unit():
    run_test("bootloader", "bootloader")


def test_counter_unit():
    run_test("counter", "counter")


def test_cpu_unit():
    run_test(
        "cpu",
        "cpu",
        extra_sources=[
            "counter.v",
            "decoder.v",
            "registers.v",
            "alu.v",
        ],
    )


def test_dcim_unit():
    run_test("dcim", "dcim", dir="dcim", extra_sources=["dcim/compressor.v"])


def test_decoder_rv32c_unit():
    run_test("decoder", "decoder_rv32c")


def test_decoder_rv32i_unit():
    run_test("decoder", "decoder_rv32i")


def test_qspi_unit():
    run_test("qspi", "qspi")


def test_registers_unit():
    run_test("registers", "registers")


def test_tcm_unit():
    run_test("tcm", "tcm", defines=["BEHAVIORAL"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
