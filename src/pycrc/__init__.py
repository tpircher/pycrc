"""pycrc -- parameterisable CRC calculation utility and C source code generator."""

from pycrc.algorithms import Crc
from pycrc.models import CrcModels, CrcParams

__version__ = "0.11.0"
__author__ = "Thomas Pircher"

__all__ = ["Crc", "CrcModels", "CrcParams", "__author__", "__version__", "crc"]


def crc(model: str, data: str | bytes | bytearray, algorithm: str = "bit-by-bit-fast") -> int:
    """
    Return the CRC of *data* for the named CRC *model*.

    This is a small convenience wrapper around :class:`pycrc.algorithms.Crc`
    for one-shot calculations:

        import pycrc

        pycrc.crc("crc-32", b"123456789")   # -> 0xCBF43926

    The *algorithm* may be one of "bit-by-bit", "bit-by-bit-fast" (the
    default) or "table-driven".
    """
    crc_obj = Crc.from_model(model)
    if algorithm in {"bit-by-bit", "bbb"}:
        return crc_obj.bit_by_bit(data)
    if algorithm in {"bit-by-bit-fast", "bbf"}:
        return crc_obj.bit_by_bit_fast(data)
    if algorithm in {"table-driven", "tbl"}:
        return crc_obj.table_driven(data)
    raise ValueError(f"unknown algorithm {algorithm!r}")
