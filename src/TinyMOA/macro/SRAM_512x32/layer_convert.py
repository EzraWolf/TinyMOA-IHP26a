# Some IHP pre-generated SRAM macros use Sky130A 235/4 layers instead of 189/4
# This causes GDS to fatally crash after properly generating the blackbox, so we fix it here.
#
# Source and credit:
# https://github.com/FPGA-Research/heichips25-tapeout/blob/main/scripts/convert_layers.py
#
# Tracked PDK issue:
# https://github.com/IHP-GmbH/IHP-Open-PDK/issues/615

import os
import pya


def main():
    TARGET_GDS: str = "RM_IHPSG13_1P_512x32_c2_bm_bist.gds"
    TARGET_DIR: str = os.path.dirname(os.path.abspath(__file__))
    TARGET_PATH: str = os.path.join(TARGET_DIR, TARGET_GDS)

    layout = pya.Layout()
    layout.read(TARGET_PATH)
    top = layout.top_cell()

    # Find source and target layers
    source_layer = layout.layer(235, 4)
    target_layer = layout.layer(189, 4)

    change_layer(top, source_layer, target_layer)
    layout.write(TARGET_PATH)


def change_layer(cell, source, target):
    print(cell.name)

    # Get the Shapes object that holds the shapes of a cell/layer
    source_shapes = cell.shapes(source)
    target_shapes = cell.shapes(target)

    # Moves shapes
    target_shapes.insert(source_shapes)
    source_shapes.clear()
    for c in cell.each_child_cell():
        change_layer(cell.layout().cell(c), source, target)


if __name__ == "__main__":
    main()
