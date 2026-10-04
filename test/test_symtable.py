#!/usr/bin/env python3

"""Unit tests for the code generation symbol table helpers."""

from pycrc.opt import Options
from pycrc import symtable


def _opt(**kwargs):
    """Return an Options object with the given attributes set."""
    opt = Options()
    for key, value in kwargs.items():
        setattr(opt, key, value)
    return opt


def test_pretty_str():
    assert symtable._pretty_str(None) == "Undefined"
    assert symtable._pretty_str(8) == "8"


def test_pretty_hex():
    assert symtable._pretty_hex(None, 16) == "Undefined"
    assert symtable._pretty_hex(0x0f, 8) == "0x0f"
    assert symtable._pretty_hex(0x01, 32) == "0x00000001"
    assert symtable._pretty_hex(0x2a) == "0x2a"


def test_pretty_bool():
    assert symtable._pretty_bool(None) == "Undefined"
    assert symtable._pretty_bool(True) == "True"
    assert symtable._pretty_bool(0) == "False"


def test_pretty_algorithm():
    opt = Options()
    opt.algorithm = opt.algo_bit_by_bit
    assert symtable._pretty_algorithm(opt) == "bit-by-bit"
    opt.algorithm = opt.algo_bit_by_bit_fast
    assert symtable._pretty_algorithm(opt) == "bit-by-bit-fast"
    opt.algorithm = opt.algo_table_driven
    assert symtable._pretty_algorithm(opt) == "table-driven"
    opt.algorithm = opt.algo_none
    assert symtable._pretty_algorithm(opt) == "UNDEFINED"


def test_pretty_header_filename():
    assert symtable._pretty_header_filename(None) == "pycrc_stdout.h"
    assert symtable._pretty_header_filename("foo.c") == "foo.h"
    assert symtable._pretty_header_filename("foo") == "foo.h"


def test_header_protection_from_filename():
    opt = Options()
    opt.output_file = "my-crc.c"
    assert symtable._pretty_hdrprotection(opt) == "MY_CRC_C"


def test_header_protection_leading_digit():
    # A header guard must be a valid C identifier, so a file name starting
    # with a digit must not produce one that starts with a digit.
    opt = Options()
    opt.output_file = "1weird-name.c"
    assert symtable._pretty_hdrprotection(opt) == "_1WEIRD_NAME_C"


def test_underlying_crc_t_c99():
    assert symtable._get_underlying_crc_t(_opt(c_std="C99", width=None)) == "unsigned long long int"
    assert symtable._get_underlying_crc_t(_opt(c_std="C99", width=8)) == "uint_fast8_t"
    assert symtable._get_underlying_crc_t(_opt(c_std="C99", width=16)) == "uint_fast16_t"
    assert symtable._get_underlying_crc_t(_opt(c_std="C99", width=32)) == "uint_fast32_t"
    assert symtable._get_underlying_crc_t(_opt(c_std="C99", width=64)) == "uint_fast64_t"
    assert symtable._get_underlying_crc_t(_opt(c_std="C99", width=100)) == "uint_fast128_t"


def test_underlying_crc_t_c89():
    assert symtable._get_underlying_crc_t(_opt(c_std="C89", width=None)) == "unsigned long int"
    assert symtable._get_underlying_crc_t(_opt(c_std="C89", width=8)) == "unsigned char"
    assert symtable._get_underlying_crc_t(_opt(c_std="C89", width=16)) == "unsigned int"
    assert symtable._get_underlying_crc_t(_opt(c_std="C89", width=32)) == "unsigned long int"
