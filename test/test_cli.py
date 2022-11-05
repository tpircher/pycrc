#!/usr/bin/env python3

import logging
import tempfile
import subprocess
from src.pycrc.models import CrcModels

LOGGER = logging.getLogger(__name__)


class TestCli:
    def test_cli(self):
        check_bytes = b"123456789"
        with tempfile.NamedTemporaryFile(prefix="pycrc-test.") as f:
            f.write(check_bytes)
            f.seek(0)

            for m in CrcModels().models:
                expected_crc = m["check"]
                args = args_from_model(m)
                check_crc(["--model", m["name"]], expected_crc)
                check_crc(args + ["--check-string", check_bytes.decode("utf-8")], expected_crc)
                check_crc(args + ["--check-hexstring", ''.join([f"{i:02x}" for i in check_bytes])], expected_crc)
                check_crc(args + ["--check-file", f.name], expected_crc)


def run_cmd(cmd):
    LOGGER.info(' '.join(cmd))
    ret = subprocess.run(cmd, check=True, capture_output=True)
    return ret


def run_pycrc(args):
    ret = run_cmd(['python3', 'src/pycrc.py'] + args)
    return ret.stdout.decode('utf-8').rstrip()


def check_crc(args, expected_crc):
    res = run_pycrc(args)
    assert res[:2] == "0x"
    assert int(res, 16) == expected_crc


def args_from_model(m):
    args = []
    if 'width' in m:
        args += ["--width", f"{m['width']:d}"]
    if 'poly' in m:
        args += ["--poly", f"{m['poly']:#x}"]
    if 'xor_in' in m:
        args += ["--xor-in", f"{m['xor_in']:#x}"]
    if 'reflect_in' in m:
        args += ["--reflect-in", f"{m['reflect_in']}"]
    if 'xor_out' in m:
        args += ["--xor-out", f"{m['xor_out']:#x}"]
    if 'reflect_out' in m:
        args += ["--reflect-out", f"{m['reflect_out']}"]
    return args
