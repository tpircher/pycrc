#!/usr/bin/env python3

"""Tests for the new pure Python CRC API.

The tests for the legacy API live in ``test_algorithms_legacy.py``.
"""

import binascii
import zlib

import pytest

from pycrc.algorithms import Crc
from pycrc.models import CrcModels


def test_table_driven_index_widths() -> None:
    """table_driven() supports every index width that divides 8."""
    for reflect in (False, True):
        for tbl_idx_width in (1, 2, 4, 8):
            algo = Crc(
                width=8,
                poly=0x07,
                reflect_in=reflect,
                xor_in=0,
                reflect_out=reflect,
                xor_out=0,
                table_idx_width=tbl_idx_width,
            )
            assert algo.table_driven("123456789") == algo.bit_by_bit("123456789")


def test_all_models_all_index_widths() -> None:
    """table_driven() must agree with bit_by_bit() for every index width."""
    for m in CrcModels().models:
        for tbl_idx_width in (1, 2, 4, 8):
            algo = Crc(
                width=m.width,
                poly=m.poly,
                reflect_in=m.reflect_in,
                xor_in=m.xor_in,
                reflect_out=m.reflect_out,
                xor_out=m.xor_out,
                table_idx_width=tbl_idx_width,
            )
            assert algo.table_driven("123456789") == algo.bit_by_bit("123456789")


def test_table_driven_rejects_non_divisor_index_width() -> None:
    """An index width that does not divide 8 must be rejected."""
    for tbl_idx_width in (3, 5, 6, 7, 16):
        with pytest.raises(ValueError):
            Crc(
                width=8,
                poly=0x07,
                reflect_in=False,
                xor_in=0,
                reflect_out=False,
                xor_out=0,
                table_idx_width=tbl_idx_width,
            )


def test_from_model() -> None:
    """Crc.from_model/from_params must build the named model correctly."""
    params = CrcModels().get("crc-32")
    assert params is not None
    from_model = Crc.from_model("crc-32")
    from_params = Crc.from_params(params)
    for crc in (from_model, from_params):
        assert crc.bit_by_bit_fast("123456789") == params.check
        assert crc.bit_by_bit("123456789") == params.check


def test_from_model_unknown() -> None:
    """An unknown model name must raise a clear error."""
    with pytest.raises(ValueError):
        Crc.from_model("no-such-model")


def test_model_mapping() -> None:
    """CrcModels behaves like a read-only mapping of name to CrcParams."""
    models = CrcModels()
    assert "crc-32" in models
    assert "CRC-32" in models
    assert models["crc-32"] is models.get("crc-32")
    assert len(models) == len(models.names())
    assert models.get("no-such-model") is None
    assert models.get_params("no-such-model") is None
    with pytest.raises(KeyError):
        models["no-such-model"]


def test_legacy_get_params_returns_a_copy() -> None:
    """The legacy get_params() returns a mutable dict that does not modify the model."""
    models = CrcModels()
    legacy = models.get_params("crc-32")
    assert legacy is not None
    legacy["xor_in"] = 0x12345678
    assert models["crc-32"].xor_in != 0x12345678


def test_streaming_update_digest() -> None:
    """Streaming update()/digest() must match the one-shot bit_by_bit_fast()."""
    check_str = "123456789"
    for m in CrcModels().models:
        algo = Crc.from_params(m)
        for size in (1, 3, 7, len(check_str)):
            algo.reset()
            for i in range(0, len(check_str), size):
                algo.update(check_str[i : i + size])
            assert algo.digest() == algo.bit_by_bit_fast(check_str)


def test_digest_empty() -> None:
    """digest() without update() equals the CRC of the empty message."""
    for m in CrcModels().models:
        algo = Crc.from_params(m)
        assert algo.digest() == algo.bit_by_bit_fast(b"")
        algo.update(b"")
        assert algo.digest() == algo.bit_by_bit_fast(b"")


def test_explicit_encoding() -> None:
    """Strings are encoded with the requested encoding."""
    algo = Crc.from_model("crc-32")
    text = "Grüße"
    assert algo.bit_by_bit_fast(text) == algo.bit_by_bit_fast(text.encode("utf-8"))
    assert algo.bit_by_bit_fast(text, encoding="latin-1") == algo.bit_by_bit_fast(text.encode("latin-1"))
    assert algo.table_driven(text, encoding="latin-1") == algo.bit_by_bit_fast(text.encode("latin-1"))


def test_repr() -> None:
    """repr() must show the model parameters."""
    text = repr(Crc.from_model("crc-32"))
    assert "width=32" in text
    assert "poly=0x4c11db7" in text
    assert "reflect_out=True" in text


def test_table_property_and_alias() -> None:
    """The table is exposed read-only and tbl_idx_width remains an alias."""
    algo = Crc.from_model("crc-32")
    assert algo.table is algo.tbl
    assert algo.gen_table() == algo.table
    assert algo.tbl_idx_width == algo.table_idx_width == 8


def test_reflect_is_static() -> None:
    """reflect() can be called without an instance."""
    assert Crc.reflect(0x80, 8) == 0x01
    assert Crc.from_model("crc-32").reflect(0x01, 8) == 0x80


def test_matches_zlib_crc32() -> None:
    """The crc-32 model must match zlib.crc32."""
    algo = Crc.from_model("crc-32")
    for data in (b"", b"123456789", b"The quick brown fox jumps over the lazy dog"):
        assert algo.bit_by_bit_fast(data) == zlib.crc32(data)
        assert algo.table_driven(data) == zlib.crc32(data)


def test_matches_binascii_crc_hqx() -> None:
    """The xmodem model must match binascii.crc_hqx."""
    algo = Crc.from_model("xmodem")
    for data in (b"", b"123456789", b"The quick brown fox jumps over the lazy dog"):
        assert algo.bit_by_bit_fast(data) == binascii.crc_hqx(data, 0)
        assert algo.table_driven(data) == binascii.crc_hqx(data, 0)
