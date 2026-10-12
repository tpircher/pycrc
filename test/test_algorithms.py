#!/usr/bin/env python3

"""Tests for the new pure Python CRC API.

The tests for the legacy API live in ``test_algorithms_legacy.py``.
"""

import pytest

from pycrc.algorithms import Crc
from pycrc.models import CrcModels


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


def test_constructor_validation() -> None:
    """Unsuitable constructor arguments must raise ValueError."""
    with pytest.raises(ValueError):
        Crc(width=0, poly=0x07, reflect_in=False, xor_in=0, reflect_out=False, xor_out=0)
    with pytest.raises(ValueError):
        Crc(width=8, poly=0x07, reflect_in=False, xor_in=0, reflect_out=False, xor_out=0, slice_by=0)
    with pytest.raises(ValueError):
        Crc(width=8, poly=0x07, reflect_in=False, xor_in=0, reflect_out=False, xor_out=0, table_idx_width=0)
    with pytest.raises(ValueError):
        Crc(width=8, poly=0x07, reflect_in="no", xor_in=0, reflect_out=False, xor_out=0)  # type: ignore[arg-type]


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
