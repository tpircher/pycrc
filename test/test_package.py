#!/usr/bin/env python3

"""Tests for the top-level pycrc package API."""

import pytest

import pycrc
from pycrc.models import CrcModels


def test_public_api_exports() -> None:
    """The public names are re-exported at package level."""
    assert pycrc.Crc is not None
    assert pycrc.CrcModels is not None
    assert pycrc.CrcParams is not None
    assert set(pycrc.__all__) >= {"Crc", "CrcModels", "CrcParams", "crc"}


def test_crc_convenience() -> None:
    """pycrc.crc() must match the model's check value for every algorithm."""
    for m in CrcModels().models:
        assert pycrc.crc(m.name, "123456789") == m.check
        assert pycrc.crc(m.name, b"123456789", algorithm="bit-by-bit") == m.check
        assert pycrc.crc(m.name, b"123456789", algorithm="table-driven") == m.check


def test_crc_unknown_algorithm() -> None:
    """An unknown algorithm must raise a clear error."""
    with pytest.raises(ValueError):
        pycrc.crc("crc-32", b"123456789", algorithm="nope")
