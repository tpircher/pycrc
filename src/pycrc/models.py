#  pycrc -- parameterisable CRC calculation utility and C source code generator
#
#  Copyright (c) 2006-2026  Thomas Pircher  <thp.oss@p5r.uk>
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
Collection of CRC models. This module contains the CRC models known to pycrc.

To print the parameters of a particular model:

    import pycrc.models as cm

    models = cm.CrcModels()
    print(", ".join(models.names()))
    m = models.get_params("crc-32")
    if m is not None:
        print("Width:        {width:d}".format(**m))
        print("Poly:         {poly:#x}".format(**m))
        print("ReflectIn:    {reflect_in}".format(**m))
        print("XorIn:        {xor_in:#x}".format(**m))
        print("ReflectOut:   {reflect_out}".format(**m))
        print("XorOut:       {xor_out:#x}".format(**m))
        print("Check:        {check:#x}".format(**m))
    else:
        print("model not found.")
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True)
class CrcParams:
    """
    The parameters of a CRC model (the Rocksoft model).

    Instances are immutable and may be used wherever a model's parameters are
    needed. For convenience they also support dictionary-style access, e.g.
    ``params["width"]`` and ``dict(params)``.
    """

    name: str
    width: int
    poly: int
    reflect_in: bool
    xor_in: int
    reflect_out: bool
    xor_out: int
    check: int

    def keys(self) -> tuple[str, ...]:
        """Return the names of the model parameters."""
        return tuple(field.name for field in fields(self))

    def __contains__(self, key: object) -> bool:
        """Return True if the named model parameter exists."""
        return isinstance(key, str) and key in self.keys()

    def __getitem__(self, key: str) -> Any:
        """Return the named model parameter, or raise KeyError."""
        if key not in self.keys():
            raise KeyError(key)
        return getattr(self, key)


class CrcModels(Mapping[str, CrcParams]):
    """
    CRC Models.

    All models are defined as constant class variables. The class behaves like
    a read-only mapping from model name to :class:`CrcParams`, so models can be
    looked up by name in constant time:

        models = CrcModels()
        params = models["crc-32"]
        if "crc-32" in models:
            ...
    """

    _models: list[dict[str, Any]] = []

    _models.append(
        {
            "name": "crc-5",
            "width": 5,
            "poly": 0x05,
            "reflect_in": True,
            "xor_in": 0x1F,
            "reflect_out": True,
            "xor_out": 0x1F,
            "check": 0x19,
        }
    )
    _models.append(
        {
            "name": "crc-8",
            "width": 8,
            "poly": 0x07,
            "reflect_in": False,
            "xor_in": 0x0,
            "reflect_out": False,
            "xor_out": 0x0,
            "check": 0xF4,
        }
    )
    _models.append(
        {
            "name": "dallas-1-wire",
            "width": 8,
            "poly": 0x31,
            "reflect_in": True,
            "xor_in": 0x0,
            "reflect_out": True,
            "xor_out": 0x0,
            "check": 0xA1,
        }
    )
    _models.append(
        {
            "name": "crc-12-3gpp",
            "width": 12,
            "poly": 0x80F,
            "reflect_in": False,
            "xor_in": 0x0,
            "reflect_out": True,
            "xor_out": 0x0,
            "check": 0xDAF,
        }
    )
    _models.append(
        {
            "name": "crc-15",
            "width": 15,
            "poly": 0x4599,
            "reflect_in": False,
            "xor_in": 0x0,
            "reflect_out": False,
            "xor_out": 0x0,
            "check": 0x59E,
        }
    )
    _models.append(
        {
            "name": "crc-16",
            "width": 16,
            "poly": 0x8005,
            "reflect_in": True,
            "xor_in": 0x0,
            "reflect_out": True,
            "xor_out": 0x0,
            "check": 0xBB3D,
        }
    )
    _models.append(
        {
            "name": "crc-16-usb",
            "width": 16,
            "poly": 0x8005,
            "reflect_in": True,
            "xor_in": 0xFFFF,
            "reflect_out": True,
            "xor_out": 0xFFFF,
            "check": 0xB4C8,
        }
    )
    _models.append(
        {
            "name": "crc-16-modbus",
            "width": 16,
            "poly": 0x8005,
            "reflect_in": True,
            "xor_in": 0xFFFF,
            "reflect_out": True,
            "xor_out": 0x0,
            "check": 0x4B37,
        }
    )
    _models.append(
        {
            "name": "crc-16-genibus",
            "width": 16,
            "poly": 0x1021,
            "reflect_in": False,
            "xor_in": 0xFFFF,
            "reflect_out": False,
            "xor_out": 0xFFFF,
            "check": 0xD64E,
        }
    )
    _models.append(
        {
            "name": "crc-16-ccitt",
            "width": 16,
            "poly": 0x1021,
            "reflect_in": False,
            "xor_in": 0x1D0F,
            "reflect_out": False,
            "xor_out": 0x0,
            "check": 0xE5CC,
        }
    )
    _models.append(
        {
            "name": "r-crc-16",
            "width": 16,
            "poly": 0x0589,
            "reflect_in": False,
            "xor_in": 0x0,
            "reflect_out": False,
            "xor_out": 0x0001,
            "check": 0x007E,
        }
    )
    _models.append(
        {
            "name": "kermit",
            "width": 16,
            "poly": 0x1021,
            "reflect_in": True,
            "xor_in": 0x0,
            "reflect_out": True,
            "xor_out": 0x0,
            "check": 0x2189,
        }
    )
    _models.append(
        {
            "name": "x-25",
            "width": 16,
            "poly": 0x1021,
            "reflect_in": True,
            "xor_in": 0xFFFF,
            "reflect_out": True,
            "xor_out": 0xFFFF,
            "check": 0x906E,
        }
    )
    _models.append(
        {
            "name": "xmodem",
            "width": 16,
            "poly": 0x1021,
            "reflect_in": False,
            "xor_in": 0x0,
            "reflect_out": False,
            "xor_out": 0x0,
            "check": 0x31C3,
        }
    )
    _models.append(
        {
            "name": "zmodem",
            "width": 16,
            "poly": 0x1021,
            "reflect_in": False,
            "xor_in": 0x0,
            "reflect_out": False,
            "xor_out": 0x0,
            "check": 0x31C3,
        }
    )
    _models.append(
        {
            "name": "crc-24",
            "width": 24,
            "poly": 0x864CFB,
            "reflect_in": False,
            "xor_in": 0xB704CE,
            "reflect_out": False,
            "xor_out": 0x0,
            "check": 0x21CF02,
        }
    )
    _models.append(
        {
            "name": "crc-32",
            "width": 32,
            "poly": 0x4C11DB7,
            "reflect_in": True,
            "xor_in": 0xFFFFFFFF,
            "reflect_out": True,
            "xor_out": 0xFFFFFFFF,
            "check": 0xCBF43926,
        }
    )
    _models.append(
        {
            "name": "crc-32c",
            "width": 32,
            "poly": 0x1EDC6F41,
            "reflect_in": True,
            "xor_in": 0xFFFFFFFF,
            "reflect_out": True,
            "xor_out": 0xFFFFFFFF,
            "check": 0xE3069283,
        }
    )
    _models.append(
        {
            "name": "crc-32-mpeg",
            "width": 32,
            "poly": 0x4C11DB7,
            "reflect_in": False,
            "xor_in": 0xFFFFFFFF,
            "reflect_out": False,
            "xor_out": 0x0,
            "check": 0x0376E6E7,
        }
    )
    _models.append(
        {
            "name": "crc-32-bzip2",
            "width": 32,
            "poly": 0x04C11DB7,
            "reflect_in": False,
            "xor_in": 0xFFFFFFFF,
            "reflect_out": False,
            "xor_out": 0xFFFFFFFF,
            "check": 0xFC891918,
        }
    )
    _models.append(
        {
            "name": "posix",
            "width": 32,
            "poly": 0x4C11DB7,
            "reflect_in": False,
            "xor_in": 0x0,
            "reflect_out": False,
            "xor_out": 0xFFFFFFFF,
            "check": 0x765E7680,
        }
    )
    _models.append(
        {
            "name": "jam",
            "width": 32,
            "poly": 0x4C11DB7,
            "reflect_in": True,
            "xor_in": 0xFFFFFFFF,
            "reflect_out": True,
            "xor_out": 0x0,
            "check": 0x340BC6D9,
        }
    )
    _models.append(
        {
            "name": "xfer",
            "width": 32,
            "poly": 0x000000AF,
            "reflect_in": False,
            "xor_in": 0x0,
            "reflect_out": False,
            "xor_out": 0x0,
            "check": 0xBD0BE338,
        }
    )
    _models.append(
        {
            "name": "crc-64",
            "width": 64,
            "poly": 0x000000000000001B,
            "reflect_in": True,
            "xor_in": 0x0,
            "reflect_out": True,
            "xor_out": 0x0,
            "check": 0x46A5A9388A5BEFFE,
        }
    )
    _models.append(
        {
            "name": "crc-64-jones",
            "width": 64,
            "poly": 0xAD93D23594C935A9,
            "reflect_in": True,
            "xor_in": 0xFFFFFFFFFFFFFFFF,
            "reflect_out": True,
            "xor_out": 0x0,
            "check": 0xCAA717168609F281,
        }
    )
    _models.append(
        {
            "name": "crc-64-xz",
            "width": 64,
            "poly": 0x42F0E1EBA9EA3693,
            "reflect_in": True,
            "xor_in": 0xFFFFFFFFFFFFFFFF,
            "reflect_out": True,
            "xor_out": 0xFFFFFFFFFFFFFFFF,
            "check": 0x995DC9BBDF1939FA,
        }
    )

    # Make the collection immutable so that callers cannot accidentally add
    # or remove model definitions. The lookup table is built once, so name
    # lookups are O(1).
    models: tuple[CrcParams, ...] = tuple(CrcParams(**definition) for definition in _models)
    _by_name: Mapping[str, CrcParams] = MappingProxyType({model.name: model for model in models})

    def __getitem__(self, name: str) -> CrcParams:
        """Return the model with the given (case-insensitive) name."""
        return self._by_name[name.lower()]

    def __iter__(self) -> Iterator[str]:
        """Iterate over the names of the supported models."""
        return iter(self._by_name)

    def __len__(self) -> int:
        """Return the number of supported models."""
        return len(self._by_name)

    def names(self) -> list[str]:
        """Return the list of supported CRC models."""
        return list(self._by_name)

    def get_params(self, model: str) -> dict[str, Any] | None:
        """
        Return a copy of the parameters of a given model, or None if it is
        unknown.

        This is the legacy interface: it returns a plain, mutable ``dict`` so
        that existing callers can keep modifying the result without affecting
        the (immutable) model definitions. New code should prefer the
        read-only mapping interface, i.e. ``models[model]`` or
        ``models.get(model)``, which return an immutable :class:`CrcParams`.

        The model name is matched case-insensitively.
        """
        params = self._by_name.get(model.lower())
        if params is None:
            return None
        return {field.name: getattr(params, field.name) for field in fields(params)}
