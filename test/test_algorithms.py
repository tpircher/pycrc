#!/usr/bin/env python3

import logging
from src.pycrc.models import CrcModels
from src.pycrc.algorithms import Crc

LOGGER = logging.getLogger(__name__)


def check_crc(algo, check_str, expected_crc=None):
    res_bbb = algo.bit_by_bit(check_str)
    res_bbf = algo.bit_by_bit_fast(check_str)
    res_tbl = algo.table_driven(check_str)
    LOGGER.info(f"Crc(width={algo.width:#x}, poly={algo.poly:#x}, "
                f"reflect_in={algo.reflect_in:#x}, xor_in={algo.xor_in:#x}, "
                f"reflect_out={algo.reflect_out:#x}, xor_out={algo.xor_out:#x}), "
                f"expected_crc={expected_crc}, "
                f"bbb={res_bbb:#x}, bbf={res_bbf:#x}, tbl={res_tbl:#x}")
    if expected_crc is not None:
        assert res_bbb == res_bbf == res_tbl == expected_crc
    assert res_bbb == res_bbf == res_tbl


def test_all_models_with_check_input():
    """
    Test all models using the basic check sequence.
    """
    check_str = '123456789'
    for m in CrcModels().models:
        algo = Crc(width=m['width'], poly=m['poly'],
                   reflect_in=m['reflect_in'], xor_in=m['xor_in'],
                   reflect_out=m['reflect_out'], xor_out=m['xor_out'])
        check_crc(algo, check_str, m['check'])


def test_all_models_with_cornercase_input():
    """
    Use corner case input strings
    """
    for m in CrcModels().models:
        algo = Crc(width=m['width'], poly=m['poly'],
                   reflect_in=m['reflect_in'], xor_in=m['xor_in'],
                   reflect_out=m['reflect_out'], xor_out=m['xor_out'])
        for check_str in "", b"", b"\0", b"\1", b"\0\0\0\0", b"\xff":
            check_crc(algo, check_str)


def test_other_models():
    """
    Test random parameters.
    """
    check_str = '123456789'
    for width in [5, 8, 16, 32, 65, 513]:
        mask = ((1 << width) - 1)
        for poly in [0x8005, 0x4c11db7, 0xa5a5a5a5]:
            poly &= mask
            for reflect_in in [0, 1]:
                for reflect_out in [0, 1]:
                    for xor_in in [0x0, 0x1, 0x5a5a5a5a]:
                        xor_in &= mask
                        for xor_out in [0x0, 0x1, 0x5a5a5a5a]:
                            xor_out &= mask
                            algo = Crc(width=width, poly=poly,
                                       reflect_in=reflect_in, xor_in=xor_in,
                                       reflect_out=reflect_out, xor_out=xor_out)
                            check_crc(algo, check_str)
