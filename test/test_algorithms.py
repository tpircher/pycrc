#!/usr/bin/env python3

"""Regression tests for the pure Python CRC algorithms."""

import logging

import pytest

from pycrc.algorithms import Crc
from pycrc.models import CrcModels

LOGGER = logging.getLogger(__name__)


def check_crc(algo, check_str, expected_crc=None):
    """Check that all three algorithms agree and optionally match expected_crc."""
    res_bbb = algo.bit_by_bit(check_str)
    res_bbf = algo.bit_by_bit_fast(check_str)
    res_tbl = algo.table_driven(check_str)
    LOGGER.info(
        f"Crc(width={algo.width:#x}, poly={algo.poly:#x}, "
        f"reflect_in={algo.reflect_in:#x}, xor_in={algo.xor_in:#x}, "
        f"reflect_out={algo.reflect_out:#x}, xor_out={algo.xor_out:#x}), "
        f"expected_crc={expected_crc}, "
        f"bbb={res_bbb:#x}, bbf={res_bbf:#x}, tbl={res_tbl:#x}"
    )
    if expected_crc is not None:
        assert res_bbb == res_bbf == res_tbl == expected_crc
    assert res_bbb == res_bbf == res_tbl


def test_all_models_with_check_input():
    """
    Test all models using the basic check sequence.
    """
    check_str = "123456789"
    for m in CrcModels().models:
        algo = Crc(
            width=m["width"],
            poly=m["poly"],
            reflect_in=m["reflect_in"],
            xor_in=m["xor_in"],
            reflect_out=m["reflect_out"],
            xor_out=m["xor_out"],
        )
        check_crc(algo, check_str, m["check"])


def test_all_models_with_cornercase_input():
    """
    Use corner case input strings
    """
    for m in CrcModels().models:
        algo = Crc(
            width=m["width"],
            poly=m["poly"],
            reflect_in=m["reflect_in"],
            xor_in=m["xor_in"],
            reflect_out=m["reflect_out"],
            xor_out=m["xor_out"],
        )
        for check_str in "", b"", b"\0", b"\1", b"\0\0\0\0", b"\xff":
            check_crc(algo, check_str)


def test_other_models():
    """
    Test random parameters.
    """
    check_str = "123456789"
    for width in [5, 8, 16, 32, 65, 513]:
        mask = (1 << width) - 1
        for poly in [0x8005, 0x4C11DB7, 0xA5A5A5A5]:
            poly &= mask
            for reflect_in in [0, 1]:
                for reflect_out in [0, 1]:
                    for xor_in in [0x0, 0x1, 0x5A5A5A5A]:
                        xor_in &= mask
                        for xor_out in [0x0, 0x1, 0x5A5A5A5A]:
                            xor_out &= mask
                            algo = Crc(
                                width=width,
                                poly=poly,
                                reflect_in=reflect_in,
                                xor_in=xor_in,
                                reflect_out=reflect_out,
                                xor_out=xor_out,
                            )
                            check_crc(algo, check_str)


def test_all_algorithms_mask_xor_out():
    """
    All algorithms must return a value within the configured width, even if
    xor_out has bits set above the width.
    """
    xor_out = 0x1FF
    for reflect in (False, True):
        algo = Crc(width=8, poly=0x07, reflect_in=reflect, xor_in=0, reflect_out=reflect, xor_out=xor_out)
        for res in (algo.bit_by_bit("123456789"), algo.bit_by_bit_fast("123456789"), algo.table_driven("123456789")):
            assert res == res & algo.mask


def test_table_driven_rejects_other_index_widths():
    """
    The Python table_driven() implementation only supports an index width of
    8 bits and must fail cleanly for other widths.
    """
    for tbl_idx_width in (1, 2, 4):
        algo = Crc(width=8, poly=0x07, reflect_in=False, xor_in=0, reflect_out=False, xor_out=0, table_idx_width=tbl_idx_width)
        with pytest.raises(ValueError):
            algo.table_driven("123456789")


def test_incremental_bit_by_bit_fast():
    """
    Feeding the data in chunks through bit_by_bit_fast_update() must give the
    same result as passing it all at once.
    """
    check_str = "123456789"
    for m in CrcModels().models:
        algo = Crc(
            width=m["width"],
            poly=m["poly"],
            reflect_in=m["reflect_in"],
            xor_in=m["xor_in"],
            reflect_out=m["reflect_out"],
            xor_out=m["xor_out"],
        )
        reg = algo.direct_init
        for octet in check_str.encode("ascii"):
            reg = algo.bit_by_bit_fast_update(reg, bytes([octet]))
        if algo.reflect_out:
            reg = algo.reflect(reg, algo.width)
        assert (reg ^ algo.xor_out) & algo.mask == algo.bit_by_bit_fast(check_str)
