import warnings
import math

from svg_to_gcode import formulas
from svg_to_gcode.compiler.interfaces import Interface
from svg_to_gcode.geometry import Vector
from svg_to_gcode import TOLERANCES

verbose = False


class Gcode(Interface):

    def __init__(self):
        self.position = None
        self._next_speed = None
        self._current_speed = None
        self.pen_up_height = 5  # Adjust this value as needed for your machine
        self.pen_down_height = 0  # Adjust this value as needed for your machine

        # Round outputs to the same number of significant figures as the operational tolerance.
        self.precision = abs(round(math.log(TOLERANCES["operation"], 10)))

    def set_movement_speed(self, speed):
        self._next_speed = speed
        return ''

    def linear_move(self, x=None, y=None, z=None):

        if self._next_speed is None:
            raise ValueError("Undefined movement speed. Call set_movement_speed before executing movement commands.")

        # Don't do anything if linear move was called without passing a value.
        if x is None and y is None and z is None:
            warnings.warn("linear_move command invoked without arguments.")
            return ''

        # Todo, investigate G0 command and replace movement speeds with G1 (normal speed) and G0 (fast move)
        command = "G1"

        if self._current_speed != self._next_speed:
            self._current_speed = self._next_speed
            command += f" F{self._current_speed}"

        # Move if not 0 and not None
        command += f" X{x:.{self.precision}f}" if x is not None else ''
        command += f" Y{y:.{self.precision}f}" if y is not None else ''
        command += f" Z{z:.{self.precision}f}" if z is not None else ''

        if self.position is not None or (x is not None and y is not None):
            if x is None:
                x = self.position.x

            if y is None:
                y = self.position.y

            self.position = Vector(x, y)

        if verbose:
            print(f"Move to {x}, {y}, {z}")

        return command + ';'

    def pen_up(self):
        # Adjust the Z coordinate upwards to raise the pen
        return f"G0 Z{self.pen_up_height:.{self.precision}f};"

    def pen_down(self):
        # Adjust the Z coordinate downwards to lower the pen to the paper
        return f"G0 Z{self.pen_down_height:.{self.precision}f};"

    def set_absolute_coordinates(self):
        return "G90;"

    def set_relative_coordinates(self):
        return "G91;"

    def dwell(self, milliseconds):
        return f"G4 P{milliseconds}"

    def set_origin_at_position(self):
        self.position = Vector(0, 0)
        return "G92 X0 Y0 Z0;"

    def set_unit(self, unit):
        if unit == "mm":
            return "G21;"

        if unit == "in":
            return "G20;"

        return ''

    def home_axes(self):
        return "G28;"

    def convert_absolute_to_relative_coordinates(commands):
        relative_commands = []
        last_x, last_y = 0, 0  # Starting point

        for command in commands:
            if command.startswith("G1") or command.startswith("G0"):
                parts = command.split()
                x_part = next((part for part in parts if part.startswith('X')), None)
                y_part = next((part for part in parts if part.startswith('Y')), None)
                x = float(x_part[1:]) if x_part else last_x
                y = float(y_part[1:]) if y_part else last_y

                # Calculate the relative move
                dx = x - last_x if x_part else 0
                dy = y - last_y if y_part else 0
                last_x, last_y = x, y  # Update last positions

                # Construct the new command with relative distances
                new_command = command[0:3]  # Keep G0/G1
                if x_part: new_command += " X{:.3f}".format(dx)
                if y_part: new_command += " Y{:.3f}".format(dy)
                relative_commands.append(new_command)
            else:
                relative_commands.append(command)  # Non-movement commands are unchanged

        return relative_commands