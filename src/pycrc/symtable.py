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
Symbol table for the macro processor used by pycrc.
use as follows:

    import pycrc.opt as opt
    import pycrc.symtable as sym

    opt = opt.Options()
    sym = sym.SymbolTable(opt)

    print(sym.crc_width)
    print(f'width: {sym.crc_width}, poly: {sym.crc_poly}')
"""

from pycrc.algorithms import Crc
import time
import os


class SymbolTable:
    """
    A class with the symbols as public members.
    """

    def __init__(self, opt):
        self._opt = opt
        self.tbl_shift = _tbl_shift(opt)

        self.datetime = time.asctime()
        self.program_version = self._opt.version_str
        self.program_url = self._opt.web_address
        self.filename = 'pycrc_stdout' if self._opt.output_file is None else os.path.basename(self._opt.output_file)
        self.header_filename = _pretty_header_filename(self._opt.output_file)
        self.header_protection = _pretty_hdrprotection(self._opt)

        self.crc_algorithm = _pretty_algorithm(self._opt)
        self.crc_width = _pretty_str(self._opt.width)
        self.crc_poly = _pretty_hex(self._opt.poly, self._opt.width)
        self.crc_reflect_in = _pretty_bool(self._opt.reflect_in)
        self.crc_xor_in = _pretty_hex(self._opt.xor_in, self._opt.width)
        self.crc_reflect_out = _pretty_bool(self._opt.reflect_out)
        self.crc_xor_out = _pretty_hex(self._opt.xor_out, self._opt.width)
        self.crc_slice_by = _pretty_str(self._opt.slice_by)
        self.crc_table_idx_width = str(self._opt.tbl_idx_width)
        self.crc_table_width = _pretty_str(1 << self._opt.tbl_idx_width)
        self.crc_table_mask = _pretty_hex(self._opt.tbl_width - 1, 8)
        self.crc_mask = _pretty_hex(self._opt.mask, self._opt.width)
        self.crc_msb_mask = _pretty_hex(self._opt.msb_mask, self._opt.width)
        self.crc_shift = _pretty_str(self.tbl_shift)

        self.cfg_width = self.crc_width if self._opt.width is not None else 'cfg->width'
        self.cfg_poly = self.crc_poly if self._opt.poly is not None else 'cfg->poly'
        self.cfg_reflect_in = self.crc_reflect_in if self._opt.reflect_in is not None else 'cfg->reflect_in'
        self.cfg_xor_in = self.crc_xor_in if self._opt.xor_in is not None else 'cfg->xor_in'
        self.cfg_reflect_out = self.crc_reflect_out if self._opt.reflect_out is not None else 'cfg->reflect_out'
        self.cfg_xor_out = self.crc_xor_out if self._opt.xor_out is not None else 'cfg->xor_out'
        self.cfg_table_idx_width = self.crc_table_idx_width if self._opt.tbl_idx_width is not None else 'cfg->table_idx_width'
        self.cfg_table_width = self.crc_table_width if self._opt.tbl_width is not None else 'cfg->table_width'
        self.cfg_mask = self.crc_mask if self._opt.mask is not None else 'cfg->crc_mask'
        self.cfg_msb_mask = self.crc_msb_mask if self._opt.msb_mask is not None else 'cfg->msb_mask'
        self.cfg_shift = self.crc_shift if self.tbl_shift is not None else 'cfg->crc_shift'
        self.cfg_poly_shifted = f'({self.cfg_poly} << {self.cfg_shift})' if self.tbl_shift is None or self.tbl_shift > 0 else self.cfg_poly
        self.cfg_mask_shifted = f'({self.cfg_mask} << {self.cfg_shift})' if self.tbl_shift is None or self.tbl_shift > 0 else self.cfg_mask
        self.cfg_msb_mask_shifted = f'({self.cfg_msb_mask} << {self.cfg_shift})' if self.tbl_shift is None or self.tbl_shift > 0 else self.cfg_msb_mask

        self.c_bool = 'int' if self._opt.c_std == 'C89' else 'bool'
        self.c_true = '1' if self._opt.c_std == 'C89' else 'true'
        self.c_false = '0' if self._opt.c_std == 'C89' else 'false'

        self.underlying_crc_t = _get_underlying_crc_t(self._opt)
        self.crc_t = self._opt.symbol_prefix + 't'
        self.cfg_t = self._opt.symbol_prefix + 'cfg_t'
        self.crc_reflect_function = self._opt.symbol_prefix + 'reflect'
        self.crc_table_gen_function = self._opt.symbol_prefix + 'table_gen'
        self.crc_init_function = self._opt.symbol_prefix + 'init'
        self.crc_update_function = self._opt.symbol_prefix + 'update'
        self.crc_finalize_function = self._opt.symbol_prefix + 'finalize'

        self.crc_init_value = _get_init_value(self._opt)
        self._crc_table_init = None

    @property
    def crc_table_init(self):
        if self._crc_table_init is None:
            self._crc_table_init = _get_table_init(self._opt)
        return self._crc_table_init


def _pretty_str(value):
    """
    Return a value of width bits as a pretty string.
    """
    if value is None:
        return 'Undefined'
    return str(value)


def _pretty_hex(value, width=None):
    """
    Return a value of width bits as a pretty hexadecimal formatted string.
    """
    if value is None:
        return 'Undefined'
    if width is None:
        return '{0:#x}'.format(value)
    width = (width + 3) // 4
    hex_str = "{{0:#0{0:d}x}}".format(width + 2)
    return hex_str.format(value)


def _pretty_bool(value):
    """
    Return a boolen value of width bits as a pretty formatted string.
    """
    if value is None:
        return 'Undefined'
    return 'True' if value else 'False'


def _pretty_algorithm(opt):
    """
    Return the algorithm name.
    """
    if opt.algorithm == opt.algo_bit_by_bit:
        return 'bit-by-bit'
    elif opt.algorithm == opt.algo_bit_by_bit_fast:
        return 'bit-by-bit-fast'
    elif opt.algorithm == opt.algo_table_driven:
        return 'table-driven'
    else:
        return 'UNDEFINED'


def _pretty_header_filename(filename):
    """
    Return the sanitized filename of a header file.
    """
    if filename is None:
        return 'pycrc_stdout.h'
    filename = os.path.basename(filename)
    if filename[-2:] == '.c':
        return filename[0:-1] + 'h'
    else:
        return filename + '.h'


def _pretty_hdrprotection(opt):
    """
    Return the name of a C header protection (e.g. CRC_IMPLEMENTATION_H).
    """
    if opt.output_file is None:
        filename = 'pycrc_stdout'
    else:
        filename = os.path.basename(opt.output_file)
    out_str = ''.join([s.upper() if s.isalnum() else '_' for s in filename])
    return out_str


def _get_underlying_crc_t(opt):     # noqa: C901
    # pylint: disable=too-many-return-statements, too-many-branches
    """
    Return the C type of the crc_t typedef.
    """

    if opt.crc_type is not None:
        return opt.crc_type
    if opt.c_std == 'C89':
        if opt.width is None:
            return 'unsigned long int'
        if opt.width <= 8:
            return 'unsigned char'
        if opt.width <= 16:
            return 'unsigned int'
        return 'unsigned long int'
    else:   # C99
        if opt.width is None:
            return 'unsigned long long int'
        if opt.width <= 8:
            return 'uint_fast8_t'
        if opt.width <= 16:
            return 'uint_fast16_t'
        if opt.width <= 32:
            return 'uint_fast32_t'
        if opt.width <= 64:
            return 'uint_fast64_t'
        if opt.width <= 128:
            return 'uint_fast128_t'
        return 'uintmax_t'


def _get_init_value(opt):
    """
    Return the init value of a C implementation, according to the selected
    algorithm and to the given options.
    If no default option is given for a given parameter, value in the cfg_t
    structure must be used.
    """
    if opt.algorithm == opt.algo_bit_by_bit:
        if opt.xor_in is None or opt.width is None or opt.poly is None:
            return None
        crc = Crc(
            width=opt.width, poly=opt.poly,
            reflect_in=opt.reflect_in, xor_in=opt.xor_in,
            reflect_out=opt.reflect_out, xor_out=opt.xor_out,
            table_idx_width=opt.tbl_idx_width)
        init = crc.nondirect_init
    elif opt.algorithm == opt.algo_bit_by_bit_fast:
        if opt.xor_in is None:
            return None
        init = opt.xor_in
    elif opt.algorithm == opt.algo_table_driven:
        if opt.reflect_in is None or opt.xor_in is None or opt.width is None:
            return None
        if opt.poly is None:
            poly = 0
        else:
            poly = opt.poly
        crc = Crc(
            width=opt.width, poly=poly,
            reflect_in=opt.reflect_in, xor_in=opt.xor_in,
            reflect_out=opt.reflect_out, xor_out=opt.xor_out,
            table_idx_width=opt.tbl_idx_width)
        if opt.reflect_in:
            init = crc.reflect(crc.direct_init, opt.width)
        else:
            init = crc.direct_init
    else:
        init = 0
    return _pretty_hex(init, opt.width)


def _get_simple_table(opt, crc_tbl, values_per_line, format_width, indent):
    """
    Get one CRC table, formatted as string with appropriate indenting and
    line breaks.
    """
    out = ""
    for i in range(opt.tbl_width):
        if i % values_per_line == 0:
            out += " " * indent
        tbl_val = _pretty_hex(crc_tbl[i], format_width)
        if i == (opt.tbl_width - 1):
            out += "{0:s}".format(tbl_val)
        elif i % values_per_line == (values_per_line - 1):
            out += "{0:s},\n".format(tbl_val)
        else:
            out += "{0:s}, ".format(tbl_val)
    return out


def _get_table_init(opt):       # TODO: change to return a list
    """
    Return the precalculated CRC table for the table_driven implementation.
    """
    if opt.algorithm != opt.algo_table_driven:
        return "0"
    if opt.width is None or opt.poly is None or opt.reflect_in is None:
        return "0"
    crc = Crc(
        width=opt.width, poly=opt.poly,
        reflect_in=opt.reflect_in,
        xor_in=0, reflect_out=False, xor_out=0,     # set unimportant variables to known values
        table_idx_width=opt.tbl_idx_width,
        slice_by=opt.slice_by)
    crc_tbl = crc.gen_table()
    if opt.width > 32:
        values_per_line = 4
    elif opt.width >= 16:
        values_per_line = 8
    else:
        values_per_line = 16
    format_width = max(opt.width, 8)
    if opt.slice_by == 1:
        indent = 4
    else:
        indent = 8

    out = [''] * opt.slice_by
    for i in range(opt.slice_by):
        out[i] = _get_simple_table(opt, crc_tbl[i], values_per_line, format_width, indent)
    fixed_indent = ' ' * (indent - 4)
    out = '{0:s}{{\n'.format(fixed_indent) + \
        '\n{0:s}}},\n{0:s}{{\n'.format(fixed_indent).join(out) + \
        '\n{0:s}}}'.format(fixed_indent)
    if opt.slice_by == 1:
        return out
    return '{\n' + out + '\n}'


def _tbl_shift(opt):
    """
    Return the table shift value
    """
    if opt.algorithm == opt.algo_table_driven and (opt.width is None or opt.width < 8):
        if opt.width is None:
            return None
        else:
            return 8 - opt.width
    else:
        return 0
