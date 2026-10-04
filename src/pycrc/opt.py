#  pycrc -- parameterisable CRC calculation utility and C source code generator
#
#  Copyright (c) 2006-2017  Thomas Pircher  <tehpeh-web@tty1.net>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
#  IN THE SOFTWARE.


"""
Option parsing library for pycrc.
use as follows:

   from pycrc.opt import Options

   opt = Options()
   opt.parse(sys.argv[1:])
"""

import argparse
import sys
from pycrc.models import CrcModels


class Options(object):
    """
    The options parsing and validating class.
    """
    # pylint: disable=too-many-instance-attributes, too-few-public-methods

    # Bitmap of the algorithms
    algo_none = 0x00
    algo_bit_by_bit = 0x01
    algo_bit_by_bit_fast = 0x02
    algo_table_driven = 0x08

    action_check_str = 0x01
    action_check_hex_str = 0x02
    action_check_file = 0x03
    action_generate_h = 0x04
    action_generate_c = 0x05
    action_generate_c_main = 0x06
    action_generate_table = 0x07

    def __init__(self, progname='pycrc', version='unknown', url='unknown'):
        self.program_name = progname
        self.version = version
        self.version_str = f"{progname} v{version}"
        self.web_address = url

        self.width = None
        self.poly = None
        self.reflect_in = None
        self.xor_in = None
        self.reflect_out = None
        self.xor_out = None
        self.tbl_idx_width = 8
        self.tbl_width = 1 << self.tbl_idx_width
        self.slice_by = 1
        self.verbose = False
        self.check_string = "123456789"
        self.msb_mask = None
        self.mask = None

        self.algorithm = self.algo_none
        self.symbol_prefix = "crc_"
        self.crc_type = None
        self.include_files = []
        self.output_file = None
        self.action = self.action_check_str
        self.check_file = None
        self.c_std = None
        self.undefined_crc_parameters = False

    def parse(self, argv=None):
        """
        Parses and validates the options given as arguments
        """

        usage = """python %(prog)s [OPTIONS]

To calculate the checksum of a string or hexadecimal data:
    python %(prog)s [model] --check-string "123456789"
    python %(prog)s [model] --check-hexstring "313233343536373839"

To calculate the checksum of a file:
    python %(prog)s [model] --check-file filename

To generate the C source code and write it to filename:
    python %(prog)s [model] --generate c -o filename

The model can be defined either with the --model switch or by specifying each
of the following parameters:
    --width --poly --reflect-in --xor-in --reflect-out --xor-out"""

        models = CrcModels()
        model_list = ", ".join(models.names())
        parser = argparse.ArgumentParser(prog=self.program_name, usage=usage)
        parser.add_argument(
                "-v", "--verbose",
                action="store_true", default=False,
                help="be more verbose; print the value of the parameters "
                "and the chosen model to stdout")
        parser.add_argument(
                "--check-string",
                dest="check_string",
                help="calculate the checksum of a string (default: '123456789')",
                metavar="STRING")
        parser.add_argument(
                "--check-hexstring",
                dest="check_hexstring",
                help="calculate the checksum of a hexadecimal number string",
                metavar="STRING")
        parser.add_argument(
                "--check-file",
                dest="check_file",
                help="calculate the checksum of a file",
                metavar="FILE")
        parser.add_argument(
                "--generate",
                dest="generate", default=None,
                help="generate C source code; choose the type from {h, c, c-main, table}",
                metavar="CODE")
        parser.add_argument(
                "--std",
                dest="c_std", default="C99",
                help="choose the C dialect of the generated code from {C89, ANSI, C99}",
                metavar="STD")
        parser.add_argument(
                "--algorithm",
                dest="algorithm", default="all",
                help="choose an algorithm from "
                "{bit-by-bit, bbb, bit-by-bit-fast, bbf, table-driven, tbl, all}",
                metavar="ALGO")
        parser.add_argument(
                "--model",
                action=_ModelAction, dest="model", default=None,
                help=f"choose a parameter set from {{{model_list}}}",
                metavar="MODEL")
        parser.add_argument(
                "--width",
                type=_hex_type, dest="width",
                help="use NUM bits in the polynomial",
                metavar="NUM")
        parser.add_argument(
                "--poly",
                type=_hex_type, dest="poly",
                help="use HEX as polynomial",
                metavar="HEX")
        parser.add_argument(
                "--reflect-in",
                type=_bool_type, dest="reflect_in",
                help="reflect the octets in the input message",
                metavar="BOOL")
        parser.add_argument(
                "--xor-in",
                type=_hex_type, dest="xor_in",
                help="use HEX as initial value",
                metavar="HEX")
        parser.add_argument(
                "--reflect-out",
                type=_bool_type, dest="reflect_out",
                help="reflect the resulting checksum before applying the --xor-out value",
                metavar="BOOL")
        parser.add_argument(
                "--xor-out",
                type=_hex_type, dest="xor_out",
                help="xor the final CRC value with HEX",
                metavar="HEX")
        parser.add_argument(
                "--slice-by",
                type=int, dest="slice_by",
                help="read NUM bytes at a time from the input. NUM must be one of the values {4, 8, 16}",
                metavar="NUM")
        parser.add_argument(
                "--table-idx-width",
                type=int, dest="table_idx_width",
                help="use NUM bits to index the CRC table; NUM must be one of the values {1, 2, 4, 8}",
                metavar="NUM")
        parser.add_argument(
                "--force-poly",
                action="store_true", default=False,
                help="override any errors about possibly unsuitable polynoms")
        parser.add_argument(
                "--symbol-prefix",
                dest="symbol_prefix",
                help="when generating source code, use STRING as prefix to the exported C symbols",
                metavar="STRING")
        parser.add_argument(
                "--crc-type",
                dest="crc_type",
                help="when generating source code, use STRING as crc_t type",
                metavar="STRING")
        parser.add_argument(
                "--include-file",
                action="append", dest="include_files",
                help="when generating source code, include also FILE as header file; "
                "can be specified multiple times",
                metavar="FILE")
        parser.add_argument(
                "-o", "--output",
                dest="output_file",
                help="write the generated code to file instead to stdout",
                metavar="FILE")
        parser.add_argument(
                "--version",
                action="version", version=self.version_str)

        options, args = parser.parse_known_args(argv)

        self._parse_c_std(options)
        undefined_params = self._parse_model_params(options)
        self._parse_table_idx_width(options)
        self._validate_bits(options)

        self._parse_slice_by(options)
        self._parse_algorithm(options)
        self._parse_output_options(options)
        self._resolve_action(options)
        self._validate_action(options, args, undefined_params)

    def _parse_c_std(self, options):
        """
        Validate and store the requested C standard.
        """
        if options.c_std is not None:
            std = options.c_std.upper()
            if std == "ANSI" or std == "C89":
                self.c_std = "C89"
            elif std == "C99":
                self.c_std = std
            else:
                self.__error(f"unknown C standard {options.c_std}")

    def _parse_model_params(self, options):
        """
        Store the individual CRC model parameters and return the list of the
        parameters that were not supplied.
        """
        undefined_params = []
        if options.width is not None:
            self.width = options.width
        else:
            undefined_params.append("--width")
        if options.poly is not None:
            self.poly = options.poly
        else:
            undefined_params.append("--poly")
        if options.reflect_in is not None:
            self.reflect_in = options.reflect_in
        else:
            undefined_params.append("--reflect-in")
        if options.xor_in is not None:
            self.xor_in = options.xor_in
        else:
            undefined_params.append("--xor-in")
        if options.reflect_out is not None:
            self.reflect_out = options.reflect_out
        else:
            undefined_params.append("--reflect-out")
        if options.xor_out is not None:
            self.xor_out = options.xor_out
        else:
            undefined_params.append("--xor-out")
        return undefined_params

    def _parse_table_idx_width(self, options):
        """
        Validate and store the table index width.
        """
        if options.table_idx_width is not None:
            if options.table_idx_width in set((1, 2, 4, 8)):
                self.tbl_idx_width = options.table_idx_width
                self.tbl_width = 1 << options.table_idx_width
            else:
                self.__error(f"unsupported table-idx-width {options.table_idx_width}")

    def _validate_bits(self, options):
        """
        Validate the width and polynomial and derive the bit masks.
        """
        if self.poly is not None and self.poly % 2 == 0 and not options.force_poly:
            self.__error("even polinomials are not allowed by default. Use --force-poly to override this.")

        if self.width is not None:
            if self.width <= 0:
                self.__error("Width must be strictly positive")
            self.msb_mask = 0x1 << (self.width - 1)
            self.mask = ((self.msb_mask - 1) << 1) | 1
            if self.poly is not None and self.poly >> (self.width + 1) != 0 and not options.force_poly:
                self.__error("the polynomial is wider than the supplied Width. Use --force-poly to override this.")
            if self.poly is not None:
                self.poly = self.poly & self.mask
            if self.xor_in is not None:
                self.xor_in = self.xor_in & self.mask
            if self.xor_out is not None:
                self.xor_out = self.xor_out & self.mask
        else:
            self.msb_mask = None
            self.mask = None

        self.undefined_crc_parameters = not (
            self.width is not None and self.poly is not None and
            self.reflect_in is not None and self.xor_in is not None and
            self.reflect_out is not None and self.xor_out is not None)

    def _parse_slice_by(self, options):
        """
        Validate and store the --slice-by value.
        """
        if options.slice_by is not None:
            if options.slice_by in set((4, 8, 16)):
                self.slice_by = options.slice_by
            else:
                self.__error(f"unsupported slice-by {options.slice_by}")
            if self.undefined_crc_parameters:
                self.__error("slice-by is only implemented for fully defined models")
            if self.tbl_idx_width != 8:
                self.__error("slice-by is only implemented for table-idx-width=8")
            # FIXME tp: Fix corner cases and disable the following tests
            if self.width < 16 or self.width > 32:
                self.__warning(f"disabling slice-by for width {self.width}")
                self.slice_by = 1
            if not self.reflect_in:
                self.__warning("disabling slice-by for non-reflected algorithm")
                self.slice_by = 1
# FIXME tp: reintroduce this?
#            if self.width % 8 != 0:
#                self.__error("slice-by is only implemented for width multiples of 8")
#            if options.slice_by < self.width / 8:
#                self.__error("slice-by must be greater or equal width / 8")
            if self.c_std == "C89":
                self.__error("--slice-by not supported for C89")

    def _parse_algorithm(self, options):
        """
        Validate and store the selected algorithm(s).
        """
        if options.algorithm is not None:
            alg = options.algorithm.lower()
            if alg in set(["bit-by-bit", "bbb", "all"]):
                self.algorithm |= self.algo_bit_by_bit
            if alg in set(["bit-by-bit-fast", "bbf", "all"]):
                self.algorithm |= self.algo_bit_by_bit_fast
            if alg in set(["table-driven", "tbl", "all"]):
                self.algorithm |= self.algo_table_driven
            if self.algorithm == 0:
                self.__error(f"unknown algorithm {options.algorithm}")

    def _parse_output_options(self, options):
        """
        Store the options that affect the generated source code.
        """
        if options.symbol_prefix is not None:
            self.symbol_prefix = options.symbol_prefix
        if options.include_files is not None:
            self.include_files = options.include_files
        if options.crc_type is not None:
            self.crc_type = options.crc_type
        if options.output_file is not None:
            self.output_file = options.output_file

    def _resolve_action(self, options):
        """
        Determine which action was requested and make sure exactly one was
        given. Return the number of actions.
        """
        op_count = 0
        if options.check_string is not None:
            self.action = self.action_check_str
            self.check_string = options.check_string
            op_count += 1
        if options.check_hexstring is not None:
            self.action = self.action_check_hex_str
            self.check_string = options.check_hexstring
            op_count += 1
        if options.check_file is not None:
            self.action = self.action_check_file
            self.check_file = options.check_file
            op_count += 1
        if options.generate is not None:
            arg = options.generate.lower()
            if arg == 'h':
                self.action = self.action_generate_h
            elif arg == 'c':
                self.action = self.action_generate_c
            elif arg == 'c-main':
                self.action = self.action_generate_c_main
            elif arg == 'table':
                self.action = self.action_generate_table
            else:
                self.__error(f"don't know how to generate {options.generate}")
            op_count += 1

            if self.action == self.action_generate_table:
                if self.algorithm & self.algo_table_driven == 0:
                    self.__error("the --generate table option is incompatible "
                                 "with the --algorithm option")
                self.algorithm = self.algo_table_driven
            elif self.algorithm not in set(
                    [self.algo_bit_by_bit, self.algo_bit_by_bit_fast, self.algo_table_driven]):
                self.__error("select an algorithm to be used in the generated file. "
                             "(Hint: use the --algorithm option.)")
        else:
            if self.tbl_idx_width != 8:
                self.__warning("reverting to Table Index Width = 8 "
                               "for internal CRC calculation")
                self.tbl_idx_width = 8
                self.tbl_width = 1 << self.tbl_idx_width
        if op_count == 0:
            self.action = self.action_check_str
        if op_count > 1:
            self.__error("too many actions specified")
        return op_count

    def _validate_action(self, options, args, undefined_params):
        """
        Perform the checks that depend on the resolved action.
        """
        c_generation_actions = set([
            self.action_generate_h, self.action_generate_c,
            self.action_generate_c_main, self.action_generate_table])
        if self.width is not None and self.width > 64 and self.crc_type is None and \
                self.action in c_generation_actions:
            self.__error("width values greater than 64 bits cannot be represented "
                         "by the type of the generated C code; use --crc-type to "
                         "supply a wider integer type")

        if len(args) != 0:
            self.__error("unrecognized argument(s): {0:s}".format(" ".join(args)))

        def_params_acts = (self.action_check_str, self.action_check_hex_str,
                           self.action_check_file, self.action_generate_table)
        if self.undefined_crc_parameters and self.action in set(def_params_acts):
            undefined_params_str = ", ".join(undefined_params)
            self.__error(f"undefined parameters: Add {undefined_params_str} or use --model")
        self.verbose = options.verbose

    def __warning(self, message):
        """
        Print a warning message to stderr.
        """
        sys.stderr.write(f"{self.program_name}: warning: {message}\n")

    def __error(self, message):
        """
        Print a error message to stderr and terminate the program.
        """
        self.__warning(message)
        sys.exit(1)


class _ModelAction(argparse.Action):
    """
    Set the individual model parameters when the --model option is given.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        models = CrcModels()
        model = models.get_params(values.lower())
        if model is None:
            model_list = ", ".join(models.names())
            raise argparse.ArgumentError(
                self, f"unsupported model {values}. Supported models are: {model_list}.")
        for key in ("width", "poly", "reflect_in", "xor_in", "reflect_out", "xor_out"):
            setattr(namespace, key, model[key])
        setattr(namespace, self.dest, values)


def _hex_type(value):
    """
    Convert a decimal or hexadecimal integer string to an integer.
    """
    try:
        if value.lower().startswith("0x"):
            return int(value, 16)
        return int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid integer or hexadecimal value: {value}.")


def _bool_type(value):
    """
    Convert 0/1, "true" or "false" to a boolean value.
    """
    if value.isdigit():
        return int(value, 10) != 0
    if value.lower() == "false":
        return False
    if value.lower() == "true":
        return True
    raise argparse.ArgumentTypeError(f"invalid boolean value: {value}.")
