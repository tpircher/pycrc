#!/usr/bin/env python3

"""Unit tests for the code generation symbol table helpers."""

from pycrc.opt import Options
from pycrc import symtable


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
