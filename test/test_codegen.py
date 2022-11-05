#!/usr/bin/env python3

import logging
import os
import tempfile
import subprocess
import itertools
import pytest
from src.pycrc.models import CrcModels
from src.pycrc.algorithms import Crc

LOGGER = logging.getLogger(__name__)

use_algo_bit_by_bit = True
use_algo_bit_by_bit_fast = True
use_algo_table_driven = True
use_algo_table_slice = True
use_c89 = True


class TestCodeGen:
    @pytest.mark.skipif(not use_algo_bit_by_bit, reason='bbb tests disabled')
    def test_models_bbb_c99(self):
        compile_and_test_models('bbb', 'c99')

    @pytest.mark.skipif(not use_c89, reason='c89 tests disabled')
    @pytest.mark.skipif(not use_algo_bit_by_bit, reason='bbb tests disabled')
    def test_models_bbb_c89(self):
        compile_and_test_models('bbb', 'c89')

    @pytest.mark.skipif(not use_algo_bit_by_bit_fast, reason='bbf tests disabled')
    def test_models_bbf_c99(self):
        compile_and_test_models('bbf', 'c99')

    @pytest.mark.skipif(not use_c89, reason='c89 tests disabled')
    @pytest.mark.skipif(not use_algo_bit_by_bit_fast, reason='bbf tests disabled')
    def test_models_bbf_c89(self):
        compile_and_test_models('bbf', 'c89')

    @pytest.mark.skipif(not use_algo_table_driven, reason='tbl tests disabled')
    def test_models_tbl_c99(self):
        compile_and_test_models('tbl', 'c99')

    @pytest.mark.skipif(not use_c89, reason='c89 tests disabled')
    @pytest.mark.skipif(not use_algo_table_driven, reason='tbl tests disabled')
    def test_models_tbl_c89(self):
        compile_and_test_models('tbl', 'c89')

    @pytest.mark.skipif(not use_algo_table_driven, reason='tbl tests disabled')
    @pytest.mark.skipif(not use_algo_table_slice, reason='tbl slice tests disabled')
    def test_models_tbl_sb_c99(self):
        compile_and_test_models('tbl', 'c99', ['--slice-by', '4'])
        compile_and_test_models('tbl', 'c99', ['--slice-by', '8'])
        compile_and_test_models('tbl', 'c99', ['--slice-by', '16'])

    # --slice-by not supported with C89

    @pytest.mark.skipif(not use_algo_table_driven, reason="tbl tests disabled")
    def test_incomplete_models_tbl_c99(self):
        params = ['width', 'poly', 'xor_in', 'reflect_in', 'xor_out', 'reflect_out']
        for n in range(len(params)):
            for c in itertools.combinations(params, n):
                compile_and_test_incomplete_models('tbl', 'c99', c)

    def test_special_cases(self):
        compile_and_run_special_cases()

    def test_variable_width(self):
        compile_and_run_variable_width('bbb', 'c99')
        compile_and_run_variable_width('bbf', 'c99')
        compile_and_run_variable_width('tbl', 'c99')


def run_cmd(cmd):
    LOGGER.info(' '.join(cmd))
    ret = subprocess.run(cmd, check=True, capture_output=True)
    return ret


def run_pycrc(args):
    ret = run_cmd(['python3', 'src/pycrc.py'] + args)
    return ret.stdout.decode('utf-8').rstrip()


def gen_src(tmpdir, args, name):
    src_h = os.path.join(tmpdir, f'{name}.h')
    gen = ['--generate', 'h', '-o', src_h]
    run_pycrc(gen + args)

    src_c = os.path.join(tmpdir, f'{name}.c')
    gen = ['--generate', 'c-main', '-o', src_c]
    run_pycrc(gen + args)


def compile_and_run(tmpdir, compile_args, run_args, name, check):
    gen_src(tmpdir, compile_args, name)
    binary = os.path.join(tmpdir, 'a.out')
    compile_src(binary, os.path.join(tmpdir, name + '.c'))
    run_and_check_res([binary] + run_args, check)


def compile_and_test_models(algo, cstd, opt_args=[]):
    with tempfile.TemporaryDirectory(prefix='pycrc-test.') as tmpdir:
        for m in CrcModels().models:
            # Don't test width > 32 for C89, as I don't know how to ask for an data type > 32 bits.
            if cstd == 'c89' and m['width'] > 32:
                continue
            args = args_from_model(m)
            args += ['--algorithm', algo, '--std', cstd]
            args += opt_args
            compile_and_run(tmpdir, args, [], m['name'], m['check'])


def compile_and_test_incomplete_models(algo, cstd, erase_params=[]):
    if cstd == 'c89':
        pytest.skip('C89 not supported')
    model = CrcModels().get_params('crc-32')
    with tempfile.TemporaryDirectory(prefix='pycrc-test.') as tmpdir:
        for algo in ['bbb', 'bbf', 'tbl']:
            m = dict(model)
            for param in erase_params:
                del m[param]
            args = args_from_model(m)
            args += ['--algorithm', algo, '--std', cstd]
            run_args = args_from_model({param: model[param] for param in erase_params})
            compile_and_run(tmpdir, args, run_args, f'{m["name"]}_incomplete', m['check'])


def compile_and_run_special_cases():
    with tempfile.TemporaryDirectory(prefix='pycrc-test.') as tmpdir:
        crc_5_args = ['--model=crc-5', '--reflect-in=0', '--algorithm', 'table-driven']
        compile_and_run(tmpdir, crc_5_args + ['--table-idx-width=8'], [], 'special', 0x01)
        compile_and_run(tmpdir, crc_5_args + ['--table-idx-width=4'], [], 'special', 0x01)
        compile_and_run(tmpdir, crc_5_args + ['--table-idx-width=2'], [], 'special', 0x01)


def compile_and_run_variable_width(algo, cstd):
    check_str = "123456789"
    models = CrcModels()
    m = models.get_params('crc-64-jones')
    with tempfile.TemporaryDirectory(prefix='pycrc-test.') as tmpdir:
        for width in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 23, 24, 25, 31, 32, 33, 63, 64]:
            mask = (1 << width) - 1
            mw = {
                    'width':            width,
                    'poly':             m['poly'] & mask,
                    'reflect_in':       m['reflect_in'],
                    'xor_in':           m['xor_in'] & mask,
                    'reflect_out':      m['reflect_out'],
                    'xor_out':          m['xor_out'] & mask,
            }
            args = [
                    '--width',          '{:d}'.format(mw['width']),
                    '--poly',           '{:#x}'.format(mw['poly']),
                    '--xor-in',         '{:#x}'.format(mw['xor_in']),
                    '--reflect-in',     '{:d}'.format(mw['reflect_in']),
                    '--xor-out',        '{:#x}'.format(mw['xor_out']),
                    '--reflect-out',    '{:d}'.format(mw['reflect_out']),
                    ]
            reference = Crc(width=mw['width'], poly=mw['poly'],
                            reflect_in=mw['reflect_in'], xor_in=mw['xor_in'],
                            reflect_out=mw['reflect_out'], xor_out=mw['xor_out'])
            check = reference.bit_by_bit_fast(check_str)
            compile_and_run(tmpdir, ['--algorithm', algo, '--std', cstd] + args, [], 'var_width', check)


def run_and_check_res(cmd, expected_crc):
    res = run_cmd(cmd).stdout.decode('utf-8').rstrip()
    assert res[:2] == '0x'
    assert int(res, 16) == expected_crc


def compile_src(out_file, src_file, cstd='c99'):
    run_cmd(['cc', '-W', '-Wall', '-pedantic', '-Werror', f'-std={cstd}', '-o', out_file, src_file])


def args_from_model(m):
    args = []
    if 'width' in m:
        args += ['--width', f'{m["width"]:d}']
    if 'poly' in m:
        args += ['--poly', f'{m["poly"]:#x}']
    if 'xor_in' in m:
        args += ['--xor-in', f'{m["xor_in"]:#x}']
    if 'reflect_in' in m:
        args += ['--reflect-in', f'{m["reflect_in"]}']
    if 'xor_out' in m:
        args += ['--xor-out', f'{m["xor_out"]:#x}']
    if 'reflect_out' in m:
        args += ['--reflect-out', f'{m["reflect_out"]}']
    return args
