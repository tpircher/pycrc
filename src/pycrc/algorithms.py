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
CRC algorithms implemented in Python.
If you want to study the Python implementation of the CRC routines, then this
is a good place to start from.

The algorithms Bit by Bit, Bit by Bit Fast and Table-Driven are implemented.

This module can also be used as a library from within Python.

Examples
========

This is an example use of the different algorithms:

    from pycrc.algorithms import Crc

    crc = Crc(width = 16, poly = 0x8005,
            reflect_in = True, xor_in = 0x0000,
            reflect_out = True, xor_out = 0x0000)
    print("{0:#x}".format(crc.bit_by_bit("123456789")))
    print("{0:#x}".format(crc.bit_by_bit_fast("123456789")))
    print("{0:#x}".format(crc.table_driven("123456789")))

A model can also be selected by name:

    from pycrc.algorithms import Crc

    crc = Crc.from_model("crc-32")
    print("{0:#x}".format(crc.bit_by_bit_fast("123456789")))
"""

from __future__ import annotations

from typing import TypeAlias

from pycrc.models import CrcModels, CrcParams

#: The input accepted by the CRC routines. Plain strings are encoded with the
#: encoding passed to the respective routine (UTF-8 by default).
BytesLike: TypeAlias = str | bytes | bytearray


class Crc:
    """
    A base class for CRC routines.

    The configuration attributes (width, poly, reflect_in, ...) are set once by
    the constructor and must not be modified afterwards; changing them would
    leave the cached lookup table and the derived masks inconsistent.
    """

    def __init__(
        self,
        width: int,
        poly: int,
        reflect_in: bool,
        xor_in: int,
        reflect_out: bool,
        xor_out: int,
        table_idx_width: int | None = None,
        slice_by: int = 1,
    ) -> None:
        """
        Create a CRC object, using the Rocksoft model.

        The parameters are as follows:
            width
            poly
            reflect_in
            xor_in
            reflect_out
            xor_out

        Raises ValueError if a parameter has an unsuitable type or value.

        The table_idx_width parameter selects the size of the lookup table; any
        value that divides 8 (i.e. 1, 2, 4 or 8) is supported by the Python
        table_driven() implementation. The slice_by parameter is only used by
        the generated C code; it does not affect the result of the Python
        algorithms.
        """

        self.width: int = width
        self.poly: int = poly
        self.reflect_in: bool = reflect_in
        self.xor_in: int = xor_in
        self.reflect_out: bool = reflect_out
        self.xor_out: int = xor_out
        self.slice_by: int = slice_by
        if table_idx_width is None:
            table_idx_width = 8
        self.table_idx_width: int = table_idx_width
        if 8 % self.table_idx_width != 0:
            raise ValueError(f"table_idx_width must divide 8, got {self.table_idx_width}")

        self.msb_mask: int = 0x1 << (self.width - 1)
        self.mask: int = ((self.msb_mask - 1) << 1) | 1
        self.tbl_width: int = 1 << self.table_idx_width

        self.direct_init: int = self.xor_in
        self.nondirect_init: int = self.__get_nondirect_init(self.xor_in)
        if self.width < 8:
            self.crc_shift: int = 8 - self.width
        else:
            self.crc_shift = 0

        self.tbl: list[list[int]] = self._gen_table()
        # State used by the incremental update()/digest() API. None means that
        # no computation is in progress.
        self._register: int | None = None

    def __repr__(self) -> str:
        return (
            f"Crc(width={self.width}, poly={self.poly:#x}, reflect_in={self.reflect_in}, "
            f"xor_in={self.xor_in:#x}, reflect_out={self.reflect_out}, xor_out={self.xor_out:#x})"
        )

    @property
    def tbl_idx_width(self) -> int:
        """Deprecated alias for :attr:`table_idx_width`."""
        return self.table_idx_width

    @tbl_idx_width.setter
    def tbl_idx_width(self, value: int) -> None:
        """Deprecated alias for :attr:`table_idx_width`."""
        self.table_idx_width = value
        self.tbl_width = 1 << value
        self.tbl = self._gen_table()

    @property
    def table(self) -> list[list[int]]:
        """The cached lookup table used by the table-driven algorithm."""
        return self.tbl

    @classmethod
    def from_params(cls, params: CrcParams) -> Crc:
        """
        Create a Crc object from a :class:`~pycrc.models.CrcParams` model.
        """
        return cls(
            width=params.width,
            poly=params.poly,
            reflect_in=params.reflect_in,
            xor_in=params.xor_in,
            reflect_out=params.reflect_out,
            xor_out=params.xor_out,
        )

    @classmethod
    def from_model(cls, model: str) -> Crc:
        """
        Create a Crc object for a named model (e.g. "crc-32").

        Raises ValueError if the model is unknown.
        """
        params = CrcModels().get(model)
        if params is None:
            raise ValueError(f"unknown CRC model {model!r}")
        return cls.from_params(params)

    def __get_nondirect_init(self, init: int) -> int:
        """
        return the non-direct init if the direct algorithm has been selected.
        """
        crc = init
        for _ in range(self.width):
            bit = crc & 0x01
            if bit:
                crc ^= self.poly
            crc >>= 1
            if bit:
                crc |= self.msb_mask
        return crc & self.mask

    @staticmethod
    def _as_bytes(data: BytesLike, encoding: str = "utf-8") -> bytes | bytearray:
        """
        Return *data* as a bytes-like object.

        Strings are encoded using *encoding*; bytes and bytearrays are
        returned unchanged.
        """
        if isinstance(data, str):
            return bytearray(data, encoding)
        return data

    @staticmethod
    def reflect(data: int, width: int) -> int:
        """
        reflect a data word, i.e. reverts the bit order.
        """

        res = data & 0x01
        for _ in range(width - 1):
            data >>= 1
            res = (res << 1) | (data & 0x01)
        return res

    def bit_by_bit(self, in_data: BytesLike, encoding: str = "utf-8") -> int:
        """
        Classic simple and slow CRC implementation.  This function iterates bit
        by bit over the augmented input message and returns the calculated CRC
        value at the end.

        Strings are encoded using *encoding* (UTF-8 by default).
        """
        data = self._as_bytes(in_data, encoding)

        reg = self.nondirect_init
        for octet in data:
            if self.reflect_in:
                octet = self.reflect(octet, 8)
            for i in range(8):
                topbit = reg & self.msb_mask
                reg = ((reg << 1) & self.mask) | ((octet >> (7 - i)) & 0x01)
                if topbit:
                    reg ^= self.poly

        for _ in range(self.width):
            topbit = reg & self.msb_mask
            reg = (reg << 1) & self.mask
            if topbit:
                reg ^= self.poly

        if self.reflect_out:
            reg = self.reflect(reg, self.width)
        return (reg ^ self.xor_out) & self.mask

    def bit_by_bit_fast_update(self, reg: int, in_data: BytesLike, encoding: str = "utf-8") -> int:
        """
        Update a CRC register with the bit-by-bit-fast algorithm and return
        the new register value.

        This is the incremental core of bit_by_bit_fast(): it does not apply
        the initial value, the output reflection or the final xor-out value, so
        it can be used to process data in chunks.

        Strings are encoded using *encoding* (UTF-8 by default).
        """
        data = self._as_bytes(in_data, encoding)

        for octet in data:
            if self.reflect_in:
                octet = self.reflect(octet, 8)
            for i in range(8):
                topbit = reg & self.msb_mask
                if octet & (0x80 >> i):
                    topbit ^= self.msb_mask
                reg <<= 1
                if topbit:
                    reg ^= self.poly
            reg &= self.mask
        return reg

    def bit_by_bit_fast(self, in_data: BytesLike, encoding: str = "utf-8") -> int:
        """
        This is a slightly modified version of the bit-by-bit algorithm: it
        does not need to loop over the augmented bits, i.e. the Width 0-bits
        which are appended to the input message in the bit-by-bit algorithm.

        Strings are encoded using *encoding* (UTF-8 by default).
        """
        reg = self.bit_by_bit_fast_update(self.direct_init, in_data, encoding)
        if self.reflect_out:
            reg = self.reflect(reg, self.width)
        return (reg ^ self.xor_out) & self.mask

    def reset(self) -> None:
        """
        Discard the state of any in-progress incremental computation.
        """
        self._register = None

    def update(self, data: BytesLike, encoding: str = "utf-8") -> None:
        """
        Feed more data into an incremental bit-by-bit-fast computation.

        The result is obtained with :meth:`digest`. The computation is
        initialised implicitly on the first call. Strings are encoded using
        *encoding* (UTF-8 by default).
        """
        if self._register is None:
            self._register = self.direct_init
        self._register = self.bit_by_bit_fast_update(self._register, data, encoding)

    def digest(self) -> int:
        """
        Return the CRC of all data fed to :meth:`update` so far.

        The value is identical to calling :meth:`bit_by_bit_fast` on the
        concatenation of all the chunks. If no data has been fed, the CRC of
        the empty message is returned.
        """
        reg = self.direct_init if self._register is None else self._register
        if self.reflect_out:
            reg = self.reflect(reg, self.width)
        return (reg ^ self.xor_out) & self.mask

    def _gen_table(self) -> list[list[int]]:
        """
        Generate the CRC table used for the table_driven CRC algorithm.

        This is an internal helper; use the read-only :attr:`table` property
        instead. The table is generated for the requested index width.
        """
        table_length = 1 << self.table_idx_width
        tbl = [[0 for i in range(table_length)] for j in range(self.slice_by)]
        for i in range(table_length):
            reg = i
            if self.reflect_in:
                reg = self.reflect(reg, self.table_idx_width)
            reg = reg << (self.width - self.table_idx_width + self.crc_shift)
            for _ in range(self.table_idx_width):
                reg = (
                    (reg << 1) ^ (self.poly << self.crc_shift) if reg & (self.msb_mask << self.crc_shift) != 0 else (reg << 1)
                )
            if self.reflect_in:
                reg = self.reflect(reg >> self.crc_shift, self.width) << self.crc_shift
            tbl[0][i] = (reg >> self.crc_shift) & self.mask

        for j in range(1, self.slice_by):
            for i in range(table_length):
                tbl[j][i] = (tbl[j - 1][i] >> 8) ^ tbl[0][tbl[j - 1][i] & 0xFF]
        return tbl

    def gen_table(self) -> list[list[int]]:
        """Deprecated alias for :meth:`_gen_table`; use :attr:`table`."""
        return self._gen_table()

    def table_driven(self, in_data: BytesLike, encoding: str = "utf-8") -> int:
        """
        The standard table-driven CRC algorithm.

        Any table index width that divides 8 (i.e. 1, 2, 4 or 8) is supported.
        Strings are encoded using *encoding* (UTF-8 by default).
        """

        data = self._as_bytes(in_data, encoding)

        idx_width = self.table_idx_width
        table_mask = (1 << idx_width) - 1
        table = self.tbl[0]

        if self.reflect_in:
            reg = self.reflect(self.direct_init, self.width)
            for octet in data:
                for i in range(8 // idx_width):
                    tblidx = (reg ^ (octet >> (i * idx_width))) & table_mask
                    reg = (table[tblidx] ^ (reg >> idx_width)) & self.mask
            reg = self.reflect(reg, self.width) & self.mask
        else:
            shift = self.width - idx_width
            reg = self.direct_init & self.mask
            for octet in data:
                for i in range(8 // idx_width):
                    part = (octet >> (8 - (i + 1) * idx_width)) & table_mask
                    crc_high = reg >> shift if shift >= 0 else reg << (-shift)
                    tblidx = (crc_high ^ part) & table_mask
                    reg = (table[tblidx] ^ (reg << idx_width)) & self.mask

        if self.reflect_out:
            reg = self.reflect(reg, self.width)
        return (reg ^ self.xor_out) & self.mask
