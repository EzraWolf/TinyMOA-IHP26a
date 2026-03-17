# Credit goes to Urish:
# https://github.com/urish/ttihp-sram-test/blob/main/src/pdn_cfg.tcl
# 
# This file SHOULD work with all IHP SRAM macros, but was only tested with RM_IHPSG13_1P_1024x8_c2_bm_bist (*) as of March 2026.
# https://www.tinytapeout.com/chips/ttihp0p2/tt_um_urish_sram_test
# 
# (*) UPDATE: RM_IHPSG13_1P_512x32_c2_bm_bist requires a hacky fix to move layer 235/4 to 189/4. *DO NOT* delete it.
#     - https://github.com/IHP-GmbH/IHP-Open-PDK/issues/615
#
# Custom PDN configuration for SRAM macro integration
#
# The SRAM macro (RM_IHPSG13_1P_1024x8_c2_bm_bist) has power pins
# (VDD!, VDDARRAY!, VSS!) on Metal4. The default macro PDN grid tries
# to connect TopMetal1<->TopMetal2, which fails when FP_PDN_MULTILAYER=0
# (no TopMetal2 stripes). This custom config connects Metal4<->TopMetal1
# for the macro grid instead.
#
# Modifications based on LibreLane's default `pdn_cfg.tcl`:
# 1. Removed TopMetal2 (PDN_HORIZONTAL_LAYER) to fix TinyTapeout forbidden layer Precheck.
# 2. Replaced horizontal routing with Metal5.
# 3. Adjusted macro connections for "N" (North) orientation instead of R90.

source $::env(SCRIPTS_DIR)/openroad/common/set_global_connections.tcl
set_global_connections

set secondary []
foreach vdd $::env(VDD_NETS) gnd $::env(GND_NETS) {
    if { $vdd != $::env(VDD_NET)} {
        lappend secondary $vdd
        set db_net [[ord::get_db_block] findNet $vdd]
        if {$db_net == "NULL"} {
            set net [odb::dbNet_create [ord::get_db_block] $vdd]
            $net setSpecial
            $net setSigType "POWER"
        }
    }
    if { $gnd != $::env(GND_NET)} {
        lappend secondary $gnd
        set db_net [[ord::get_db_block] findNet $gnd]
        if {$db_net == "NULL"} {
            set net [odb::dbNet_create [ord::get_db_block] $gnd]
            $net setSpecial
            $net setSigType "GROUND"
        }
    }
}

set_voltage_domain -name CORE -power $::env(VDD_NET) -ground $::env(GND_NET) \
    -secondary_power $secondary

# STDCELL grid
# Define pins: ONLY export TopMetal1 (Vertical) to prevent TT pre-check failures
define_pdn_grid \
    -name stdcell_grid \
    -starts_with POWER \
    -voltage_domain CORE \
    -pins "$::env(PDN_VERTICAL_LAYER)"

# Vertical stripes (TopMetal1)
add_pdn_stripe \
    -grid stdcell_grid \
    -layer $::env(PDN_VERTICAL_LAYER) \
    -width $::env(PDN_VWIDTH) \
    -pitch $::env(PDN_VPITCH) \
    -offset $::env(PDN_VOFFSET) \
    -spacing $::env(PDN_VSPACING) \
    -starts_with POWER -extend_to_core_ring

# Standard cell rails on Metal1
if { $::env(PDN_ENABLE_RAILS) == 1 } {
    add_pdn_stripe \
        -grid stdcell_grid \
        -layer $::env(PDN_RAIL_LAYER) \
        -width $::env(PDN_RAIL_WIDTH) \
        -followpins

    add_pdn_connect \
        -grid stdcell_grid \
        -layers "$::env(PDN_RAIL_LAYER) $::env(PDN_VERTICAL_LAYER)"
}

# SRAM macro grid & connections
define_pdn_grid \
    -macro \
    -default \
    -name macro \
    -starts_with POWER \
    -halo "$::env(PDN_HORIZONTAL_HALO) $::env(PDN_VERTICAL_HALO)"

# Horizontal stripes (Changed to Metal5 to avoid TopMetal2 forbidden layer)
# FIX: localized to the macro grid to avoid blocking standard cell power (PDN-0179).
add_pdn_stripe \
    -grid macro \
    -layer Metal5 \
    -width $::env(PDN_HWIDTH) \
    -pitch $::env(PDN_HPITCH) \
    -offset $::env(PDN_HOFFSET) \
    -spacing $::env(PDN_HSPACING) \
    -starts_with POWER

# Connect global TopMetal1 (Vertical) down to local Metal5 (Horizontal) over macro
# Layers must be listed Bottom-to-Top: Metal5 is below TopMetal1.
add_pdn_connect \
    -grid macro \
    -layers "Metal5 $::env(PDN_VERTICAL_LAYER)"

# N (North) Orientation
# Connect SRAM's Vertical Metal4 pins to Horizontal Metal5 stripes
add_pdn_connect \
    -grid macro \
    -layers "Metal4 Metal5"

# R90 Orientation (Reference Only)
# add_pdn_connect \
#     -grid macro \
#     -layers "Metal4 $::env(PDN_VERTICAL_LAYER)"
