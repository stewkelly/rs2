import os
from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces
from path_optimisation.path_optimisation import solve_tsp, reorder_curves_greedy

def convert_svg_to_gcode(svg_file_name, gcode_file_name):
    # Get the full path of the current script directory
    script_directory = os.path.dirname(os.path.abspath(__file__))

    # Construct the full paths for the SVG and G-code files
    svg_file_path = os.path.join(script_directory, svg_file_name)
    gcode_file_path = os.path.join(script_directory, gcode_file_name)

    # Instantiate a compiler, specifying the interface type, movement speed and drawing speed at which the tool moves while 
    gcode_compiler = Compiler(interfaces.Gcode)

    # Parse an svg file into geometric curves, and compile to gcode
    curves = parse_file(svg_file_path)
    reordered_curves = reorder_curves_greedy(curves)
    # reordered_curves = solve_tsp(curves)
    gcode_compiler.append_curves(reordered_curves)

    # Compile the G-code and save it directly to a file
    gcode_compiler.compile_to_file(gcode_file_path)

if __name__ == "__main__":
    convert_svg_to_gcode("drawing.svg", "drawing.gcode")