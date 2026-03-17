# Makefile
# See https://docs.cocotb.org/en/stable/quickstart.html for more info

# defaults
SIM ?= icarus
FST ?= -fst # Use more efficient FST format
TOPLEVEL_LANG ?= verilog
SRC_DIR = $(PWD)/../src
PROJECT_SOURCES = project.v




ifneq ($(GATES),yes)

# RTL simulation:
SIM_BUILD       = sim_build/rtl
COMPILE_ARGS   += -DFUNCTIONAL
VERILOG_SOURCES += $(addprefix $(SRC_DIR)/,$(PROJECT_SOURCES))

# Add the SRAM models to RTL sim too
VERILOG_SOURCES += $(SRC_DIR)/TinyMOA/macro/SRAM_512x32/RM_IHPSG13_1P_core_behavioral_bm_bist.v
VERILOG_SOURCES += $(SRC_DIR)/TinyMOA/macro/SRAM_512x32/RM_IHPSG13_1P_512x32_c2_bm_bist.v

else

# Gate level simulation:
SIM_BUILD       = sim_build/gl
COMPILE_ARGS   += -DGL_TEST
COMPILE_ARGS   += -DFUNCTIONAL
COMPILE_ARGS   += -DSIM
VERILOG_SOURCES += $(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_io/verilog/sg13g2_io.v
VERILOG_SOURCES += $(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog/sg13g2_stdcell.v

# IHP SP SRAM 512x32 models
# VERILOG_SOURCES += $(SRC_DIR)/TinyMOA/macro/SRAM_SP_512x32/RM_IHPSG13_1P_512x32_c2_bm_bist.v
# VERILOG_SOURCES += $(SRC_DIR)/TinyMOA/macro/SRAM_SP_512x32/RM_IHPSG13_1P_core_behavioral_bm_bist.v

# IHP DP SRAM 512x32 models
VERILOG_SOURCES += $(SRC_DIR)/TinyMOA/macro/SRAM_DP_512x32/RM_IHPSG13_2P_512x32_c2_bm_bist.v
VERILOG_SOURCES += $(SRC_DIR)/TinyMOA/macro/SRAM_DP_512x32/RM_IHPSG13_2P_core_behavioral_bm_bist.v

# this gets copied in by the GDS action workflow
VERILOG_SOURCES += $(PWD)/gate_level_netlist.v

endif




# Allow sharing configuration between design and testbench via `include`:
COMPILE_ARGS 		+= -I$(SRC_DIR)

# Include the testbench sources:
VERILOG_SOURCES += $(PWD)/tb.v
TOPLEVEL = tb

# List test modules to run, separated by commas and without the .py suffix:
COCOTB_TEST_MODULES = test

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim
