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
