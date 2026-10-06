#!/usr/bin/env python3

"""Tests for the pycrc command line interface."""

import logging
import subprocess
import sys
import tempfile

from pycrc.models import CrcModels

LOGGER = logging.getLogger(__name__)


class TestCli:
    """End-to-end tests that invoke the pycrc CLI."""

    def test_cli(self):
        """All models must yield their check value for every CLI input type."""
        check_bytes = b"123456789"
        with tempfile.NamedTemporaryFile(prefix="pycrc-test.") as f:
            f.write(check_bytes)
            f.seek(0)

            for m in CrcModels().models:
                expected_crc = m["check"]
                args = args_from_model(m)
                check_crc(["--model", m["name"]], expected_crc)
                check_crc(args + ["--check-string", check_bytes.decode("utf-8")], expected_crc)
                check_crc(args + ["--check-hexstring", "".join([f"{i:02x}" for i in check_bytes])], expected_crc)
                check_crc(args + ["--check-file", f.name], expected_crc)

    def test_invalid_hexstring(self):
        """An invalid hex string must fail with a message, not a traceback."""
        ret = subprocess.run(
            [sys.executable, "src/pycrc.py", "--model", "crc-32", "--check-hexstring", "zz"], capture_output=True, text=True
        )
        assert ret.returncode != 0
        assert "invalid hex string" in ret.stderr
        assert "Traceback" not in ret.stderr


def run_cmd(cmd):
    """Run a command, raising on failure, and return the completed process."""
    LOGGER.info(" ".join(cmd))
    ret = subprocess.run(cmd, check=True, capture_output=True)
    return ret


def run_pycrc(args):
    """Run pycrc with the given arguments and return its stripped stdout."""
    ret = run_cmd([sys.executable, "src/pycrc.py"] + args)
    return ret.stdout.decode("utf-8").rstrip()


def check_crc(args, expected_crc):
    """Run pycrc and assert that the printed checksum equals expected_crc."""
    res = run_pycrc(args)
    assert res[:2] == "0x"
    assert int(res, 16) == expected_crc


def args_from_model(m):
    """Return the CLI arguments that describe the given CRC model."""
    args = []
    if "width" in m:
        args += ["--width", f"{m['width']:d}"]
    if "poly" in m:
        args += ["--poly", f"{m['poly']:#x}"]
    if "xor_in" in m:
        args += ["--xor-in", f"{m['xor_in']:#x}"]
    if "reflect_in" in m:
        args += ["--reflect-in", f"{m['reflect_in']}"]
    if "xor_out" in m:
        args += ["--xor-out", f"{m['xor_out']:#x}"]
    if "reflect_out" in m:
        args += ["--reflect-out", f"{m['reflect_out']}"]
    return args
