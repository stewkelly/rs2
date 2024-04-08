import typing
import warnings

from svg_to_gcode.compiler.interfaces import Interface
from svg_to_gcode.geometry import Curve, Line
from svg_to_gcode.geometry import LineSegmentChain
from svg_to_gcode import UNITS, TOLERANCES

class Compiler:
    """
    The Compiler class handles the process of drawing geometric objects using interface commands and assembling
    the resulting numerical control code for a drawing machine. Designed for operations where the pen is lifted for
    movement and lowered for drawing.
    """

    def __init__(self, interface_class: typing.Type[Interface], movement_speed, drawing_speed, dwell_time=0, unit=None, custom_header=None, custom_footer=None):
        """
        Initialize the Compiler with the necessary settings for a drawing machine.
        
        :param interface_class: Specify which interface to use. Commonly a gcode interface for drawing machines.
        :param movement_speed: Speed to move the pen when not drawing. Units are determined by the machine.
        :param drawing_speed: Speed to move the pen when drawing.
        :param dwell_time: Time in ms for the pen to wait before starting to draw. Useful for precise positioning.
        :param unit: Measurement unit for the machine.
        :param custom_header: Commands executed before all generated commands. Defaults to lifting the pen.
        :param custom_footer: Commands executed after all generated commands. Defaults to lifting the pen.
        """
        self.interface = interface_class()
        self.movement_speed = movement_speed
        self.drawing_speed = drawing_speed
        self.dwell_time = dwell_time

        if (unit is not None) and (unit not in UNITS):
            raise ValueError(f"Unknown unit {unit}. Please specify one of the following: {UNITS}")
        
        self.unit = unit

        if custom_header is None:
            custom_header = [self.interface.pen_up()]

        if custom_footer is None:
            custom_footer = [self.interface.pen_up()]

        self.header = [self.interface.set_relative_coordinates(),
                       self.interface.set_movement_speed(self.movement_speed)] + custom_header
        self.footer = custom_footer
        self.body = []

    def compile(self):
        """
        Assembles the code in the header, body, and footer, returning the assembled code.
        """

        if len(self.body) == 0:
            warnings.warn("Compile with an empty body (no lines or curves). Is this intentional?")

        gcode = []

        gcode.extend(self.header)
        gcode.append(self.interface.set_unit(self.unit))
        gcode.extend(self.body)
        gcode.extend(self.footer)

        gcode = filter(lambda command: len(command) > 0, gcode)

        return '\n'.join(gcode)

    def compile_to_file(self, file_name: str):
        """
        Assembles the code and saves it to a file.
        :param file_name: Path to save the file.
        """
        with open(file_name, 'w') as file:
            file.write(self.compile())

    def append_line_chain(self, line_chain: LineSegmentChain):
        """
        Draws a LineSegmentChain by moving the pen. The resulting code is appended to self.body.
        """
        if line_chain.chain_size() == 0:
            warnings.warn("Attempted to parse empty LineChain")
            return

        # Lift pen before moving to the start of the line chain
        code = [self.interface.pen_up(), 
                self.interface.set_movement_speed(self.movement_speed)]

        start = line_chain.get(0).start
        code.append(self.interface.linear_move(start.x, start.y))  # Move to start position

        # Lower pen for drawing
        code += [self.interface.pen_down(),
                 self.interface.set_movement_speed(self.drawing_speed)]

        for line in line_chain:
            code.append(self.interface.linear_move(line.end.x, line.end.y))  # Draw the line

        self.body.extend(code)

    def append_curves(self, curves: [typing.Type[Curve]]):
        """
        Draws curves by approximating them as line segments and then drawing those lines.
        """
        for curve in curves:
            line_chain = LineSegmentChain()
            approximation = LineSegmentChain.line_segment_approximation(curve)
            line_chain.extend(approximation)
            self.append_line_chain(line_chain)
            