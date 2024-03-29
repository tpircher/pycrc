#  pycrc -- parameterisable CRC calculation utility and C source code generator
#
#  Copyright (c) 2017  Thomas Pircher  <tehpeh-web@tty1.net>
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
use as follows:

    import pycrc.codegen as cg
    import pycrc.opt as opt
    opt = opt.Options()
    print(cg.CodeGen(opt, '', [
        'if (a == b) {',
        cg.CodeGen(opt, 4*' ', ['print("a equals b\\n");']),
        '}',
        ]))
"""

import pycrc.symtable
import pycrc.expr as expr


class CodeGen(object):
    """
    The symbol table class.
    """
    def __init__(self, opt, indent, content=[]):
        """
        The class constructor.
        """
        self.opt = opt
        self.sym = pycrc.symtable.SymbolTable(opt)
        self.indent = indent
        self.content = content

    def gen(self, indent=''):
        """
        Return an array of strings.
        """
        out = []
        if self.indent is None:
            indent = ''
        else:
            indent += self.indent
        for item in self.content:
            if isinstance(item, str):
                out.append(indent + item)
            else:
                out += item.gen(indent)
        return out

    def __str__(self):
        """
        Stringify the object.
        """
        return '\n'.join([i.rstrip() for i in self.gen()])


class Conditional(CodeGen):
    """
    A conditional block of code.
    """
    def __init__(self, opt, indent, condition, content):
        """
        The class constructor.
        """
        super(Conditional, self).__init__(opt, indent)
        if condition:
            self.content = content


class Conditional2(CodeGen):
    """
    A conditional block of code with an else block.
    """
    def __init__(self, opt, indent, condition, content_true, content_false):
        """
        The class constructor.
        """
        super(Conditional2, self).__init__(opt, indent)
        if condition:
            self.content = content_true
        else:
            self.content = content_false


class Comment(CodeGen):
    """
    A comment wrapper.
    """
    def __init__(self, opt, indent, content):
        """
        The class constructor.
        """
        super(Comment, self).__init__(opt, indent)
        self.content = [
                '/**',
                CodeGen(opt, indent + ' * ', content),
                ' */'
                ]


class ParamBlock(CodeGen):
    """
    Print the parameters of the model.
    """
    def __init__(self, opt, indent, algorithm=False):
        """
        The class constructor.
        """
        super(ParamBlock, self).__init__(opt, indent)
        self.content = [
                '- {0:13s} = {1}'.format('Width', self.sym.crc_width),
                '- {0:13s} = {1}'.format('Poly', self.sym.crc_poly),
                '- {0:13s} = {1}'.format('XorIn', self.sym.crc_xor_in),
                '- {0:13s} = {1}'.format('ReflectIn', self.sym.crc_reflect_in),
                '- {0:13s} = {1}'.format('XorOut', self.sym.crc_xor_out),
                '- {0:13s} = {1}'.format('ReflectOut', self.sym.crc_reflect_out),
                Conditional(opt, '', algorithm,
                            ['- {0:13s} = {1}'.format('Algorithm', self.sym.crc_algorithm)]),
                Conditional(opt, '', opt.slice_by > 1,
                            ['- {0:13s} = {1}'.format('SliceBy', opt.slice_by)]),
                ]


class File(CodeGen):
    """
    Generate the file output.
    """
    def __init__(self, opt, indent):
        """
        The class constructor.
        """
        super(File, self).__init__(opt, indent)
        self.content = []

        if opt.action == opt.action_generate_h:
            self.content = self._code_file() + self._header_file()
        if opt.action == opt.action_generate_c:
            self.content = self._code_file() + self._c_file()
        if opt.action == opt.action_generate_c_main:
            self.content = self._code_file() + self._c_file() + self._main_file()
        if opt.action == opt.action_generate_table:
            self.content = [f'{self.sym.crc_table_init}']

    def _code_file(self):
        """
        Add code file
        """
        out = [
                Comment(self.opt, '', [
                    '\\file',
                    'Functions and types for CRC checks.',
                    '',
                    f'Generated on {self.sym.datetime}',
                    f'by {self.sym.program_version}, {self.sym.program_url}',
                    'using the configuration:',
                    ParamBlock(self.opt, ' ', algorithm=True),
                    Conditional(self.opt, '', self.opt.action == self.opt.action_generate_h, [
                        '',
                        f'This file defines the functions {self.sym.crc_init_function}(), {self.sym.crc_update_function}() and {self.sym.crc_finalize_function}().',
                        '',
                        f'The {self.sym.crc_init_function}() function returns the initial \\c crc value and must be called',
                        f'before the first call to {self.sym.crc_update_function}().',
                        f'Similarly, the {self.sym.crc_finalize_function}() function must be called after the last call',
                        f'to {self.sym.crc_update_function}(), before the \\c crc is being used.',
                        'is being used.',
                        '',
                        f'The {self.sym.crc_update_function}() function can be called any number of times (including zero',
                        f'times) in between the {self.sym.crc_init_function}() and {self.sym.crc_finalize_function}() calls.',
                        '',
                        'This pseudo-code shows an example usage of the API:',
                        '\\code{.c}',
                        Conditional(self.opt, '', self.opt.undefined_crc_parameters, [
                            f'{self.sym.cfg_t} cfg = ' + '{',
                            Conditional(self.opt, 4*' ', self.opt.width is None, [
                                '0,      // width',
                                ]),
                            Conditional(self.opt, 4*' ', self.opt.poly is None, [
                                '0,      // poly',
                                ]),
                            Conditional(self.opt, 4*' ', self.opt.reflect_in is None, [
                                '0,      // reflect_in',
                                ]),
                            Conditional(self.opt, 4*' ', self.opt.xor_in is None, [
                                '0,      // xor_in',
                                ]),
                            Conditional(self.opt, 4*' ', self.opt.reflect_out is None, [
                                '0,      // reflect_out',
                                ]),
                            Conditional(self.opt, 4*' ', self.opt.xor_out is None, [
                                '0,      // xor_out',
                                ]),
                            Conditional(self.opt, 4*' ', self.opt.width is None, [
                                '',
                                '0,      // crc_mask',
                                '0,      // msb_mask',
                                '0,      // crc_shift',
                                ]),
                            '};',
                            ]),
                        f'{self.sym.crc_t} crc;',
                        'unsigned char data[MAX_DATA_LEN];',
                        'size_t data_len;',
                        '',
                        Conditional(self.opt, '', _use_crc_table_gen(self.opt), [
                            f'{self.sym.crc_table_gen_function}(&cfg);',
                            ]),
                        'crc = {0}({1});'.format(self.sym.crc_init_function, '' if _use_constant_crc_init(self.sym) else '&cfg'),
                        'while ((data_len = read_data(data, MAX_DATA_LEN)) > 0) {',
                        CodeGen(self.opt, 4*' ', [
                            'crc = {0}({1}crc, data, data_len);'.format(self.sym.crc_update_function, '' if _use_cfg_in_crc_update(self.opt) else '&cfg, '),
                            ]),
                        '}',
                        'crc = {0}({1}crc);'.format(self.sym.crc_finalize_function, '' if _use_cfg_in_finalize(self.opt) else '&cfg, '),
                        '\\endcode',
                        ]),
                    ]),
                ]
        return out

    def _header_file(self):
        """
        Add header content.
        """
        out = [
                f'#ifndef {self.sym.header_protection}',
                f'#define {self.sym.header_protection}',
                '',
                CodeGen(self.opt, '', _includes(self.opt)),
                '#include <stdlib.h>',
                Conditional(self.opt, '', self.opt.c_std != 'C89',
                            ['#include <stdint.h>']),
                Conditional(self.opt, '', _use_cfg(self.opt) and self.opt.c_std != 'C89',
                            ['#include <stdbool.h>']),
                '',
                '#ifdef __cplusplus',
                'extern "C" {',
                '#endif',
                '', '',
                Comment(self.opt, '', [
                    'The definition of the used algorithm.',
                    '',
                    'This is not used anywhere in the generated code, but it may be used by the',
                    'application code to call algorithm-specific code, if desired.',
                    ]),
                '#define {0} 1'.format(_crc_algo_define(self.opt, self.sym)),
                '', '',
                Comment(self.opt, self.indent, [
                    'The type of the CRC values.',
                    '',
                    f'This type must be big enough to contain at least {self.sym.cfg_width} bits.',
                    ]),
                f'typedef {self.sym.underlying_crc_t} {self.sym.crc_t};',
                Conditional(self.opt, '', _use_cfg(self.opt), [
                    '', '',
                    Comment(self.opt, self.indent, ['The configuration type of the CRC algorithm.']),
                    'typedef struct {',
                    Conditional(self.opt, 4*' ', self.opt.width is None,
                                ['{0:24s}    {1}'.format('unsigned int width;',
                                                         '/*!< The width of the polynomial */')]),
                    Conditional(self.opt, 4*' ', self.opt.poly is None,
                                ['{0:24s}    {1}'.format(self.sym.crc_t + ' poly;',
                                                         '/*!< The CRC polynomial */')]),
                    Conditional(self.opt, 4*' ', self.opt.reflect_in is None,
                                ['{0:24s}    {1}'.format(self.sym.c_bool + ' reflect_in;',
                                                         '/*!< Whether the input shall be reflected or not */')]),
                    Conditional(self.opt, 4*' ', self.opt.xor_in is None,
                                ['{0:24s}    {1}'.format(self.sym.crc_t + ' xor_in;',
                                                         '/*!< The initial value of the register */')]),
                    Conditional(self.opt, 4*' ', self.opt.reflect_out is None,
                                ['{0:24s}    {1}'.format(self.sym.c_bool + ' reflect_out;',
                                                         '/*!< Whether the output shall be reflected or not */')]),
                    Conditional(self.opt, 4*' ', self.opt.xor_out is None,
                                ['{0:24s}    {1}'.format(self.sym.crc_t + ' xor_out;',
                                                         '/*!< The value which shall be XOR-ed to the final CRC value */')]),
                    Conditional(self.opt, 4*' ', self.opt.width is None, [
                        '',
                        '/* internal parameters */',
                        '{0:24s}    {1}'.format(self.sym.crc_t + ' msb_mask;',
                                                '/*!< a bitmask with the Most Significant Bit set to 1'),
                        33*' ' + 'initialise as (crc_t)1u << (width - 1) */',
                        '{0:24s}    {1}'.format(self.sym.crc_t + ' crc_mask;',
                                                '/*!< a bitmask with all width bits set to 1'),
                        33*' ' + 'initialise as (cfg->msb_mask - 1) | cfg->msb_mask */',
                        '{0:24s}    {1}'.format('unsigned int crc_shift;',
                                                '/*!< a shift count that is used when width < 8'),
                        33*' ' + 'initialise as cfg->width < 8 ? 8 - cfg->width : 0 */',
                        ]),
                    f'}} {self.sym.cfg_t};',
                    ]),
                Conditional(self.opt, '', _use_reflect_func(self.opt) and not _use_static_reflect_func(self.opt), [
                    '', '',
                    Comment(self.opt, '', [
                        'Reflect all bits of a \\a data word of \\a data_len bytes.',
                        '',
                        '\\param[in] data     The data word to be reflected.',
                        '\\param[in] data_len The width of \\a data expressed in number of bits.',
                        '\\return             The reflected data.'
                        ]),
                    f'{self.sym.crc_t} {self.sym.crc_reflect_function}({self.sym.crc_t} data, size_t data_len);',
                    ]),
                Conditional(self.opt, '', _use_crc_table_gen(self.opt), [
                    '', '',
                    Comment(self.opt, '', [
                        'Populate the private static crc table.',
                        '',
                        f'\\param[in] cfg  A pointer to an initialised {self.sym.cfg_t} structure.',
                        ]),
                    f'void {self.sym.crc_table_gen_function}(const {self.sym.cfg_t} *cfg);',
                    ]),
                '', '',
                Comment(self.opt, '', [
                    'Calculate the initial crc value.',
                    '',
                    Conditional(self.opt, '', _use_cfg(self.opt), [
                        f'\\param[in] cfg  A pointer to an initialised {self.sym.cfg_t} structure.',
                        ]),
                    '\\return     The initial crc value.',
                    ]),
                Conditional2(self.opt, '', _use_constant_crc_init(self.sym), [
                    Conditional2(self.opt, '', self.opt.c_std == 'C89', [
                        f'#define {self.sym.crc_init_function}()      ({self.sym.crc_init_value})',
                        ], [
                        'static inline {0}'.format(_crc_init_function_def(self.opt, self.sym)),
                        '{',
                        f'    return {self.sym.crc_init_value};',
                        '}',
                        ]),
                    ], [
                    '{0};'.format(_crc_init_function_def(self.opt, self.sym)),
                    ]),
                '', '',
                Comment(self.opt, '', [
                    'Update the crc value with new data.',
                    '',
                    '\\param[in] crc      The current crc value.',
                    Conditional(self.opt, '', not _use_cfg_in_crc_update(self.opt), [
                        f'\\param[in] cfg      A pointer to an initialised {self.sym.cfg_t} structure.',
                        ]),
                    '\\param[in] data     Pointer to a buffer of \\a data_len bytes.',
                    '\\param[in] data_len Number of bytes in the \\a data buffer.',
                    '\\return             The updated crc value.',
                    ]),
                '{0};'.format(_crc_update_function_def(self.opt, self.sym)),
                '', '',
                Comment(self.opt, '', [
                    'Calculate the final crc value.',
                    '',
                    Conditional(self.opt, '', not _use_cfg_in_finalize(self.opt), [
                        f'\\param[in] cfg  A pointer to an initialised {self.sym.cfg_t} structure.',
                        ]),
                    '\\param[in] crc  The current crc value.',
                    '\\return     The final crc value.',
                    ]),
                Conditional2(self.opt, '', _use_inline_crc_finalize(self.opt), [
                    Conditional2(self.opt, '', self.opt.c_std == 'C89', [
                        '#define {0}(crc)      ({1})'.format(self.sym.crc_finalize_function, _crc_final_value(self.opt, self.sym)),
                        ], [
                        'static inline {0}'.format(_crc_finalize_function_def(self.opt, self.sym)),
                        '{',
                        '    return {0};'.format(_crc_final_value(self.opt, self.sym)),
                        '}',
                        ]),
                    ], [
                    '{0};'.format(_crc_finalize_function_def(self.opt, self.sym)),
                    ]),
                '', '',
                '#ifdef __cplusplus',
                '}           /* closing brace for extern "C" */',
                '#endif',
                '',
                f'#endif      /* {self.sym.header_protection} */',
                '',
                ]
        return out

    def _c_file(self):
        """
        Add C file content.
        """
        out = [
                CodeGen(self.opt, '', _includes(self.opt)),
                f'#include "{self.sym.header_filename}"     /* include the header file generated with pycrc */',
                '#include <stdlib.h>',
                Conditional(self.opt, '', self.opt.c_std != 'C89', [
                    '#include <stdint.h>',
                    Conditional(self.opt, '', self.opt.undefined_crc_parameters or
                                self.opt.algorithm == self.opt.algo_bit_by_bit or
                                self.opt.algorithm == self.opt.algo_bit_by_bit_fast, [
                                    '#include <stdbool.h>',
                                    ]),
                                ]),
                Conditional(self.opt, '', self.opt.slice_by > 1, [
                    '#include <endian.h>',
                    ]),
                Conditional(self.opt, '', _use_reflect_func(self.opt) and _use_static_reflect_func(self.opt), [
                    '',
                    f'static {self.sym.crc_t} {self.sym.crc_reflect_function}({self.sym.crc_t} data, size_t data_len);',
                    ]),
                '',
                CodeGen(self.opt, '', _crc_table(self.opt, self.sym)),
                CodeGen(self.opt, '', _crc_reflect_function_gen(self.opt, self.sym)),
                CodeGen(self.opt, '', _crc_init_function_gen(self.opt, self.sym)),
                CodeGen(self.opt, '', _crc_table_gen(self.opt, self.sym)),
                CodeGen(self.opt, '', _crc_update_function_gen(self.opt, self.sym)),
                CodeGen(self.opt, '', _crc_finalize_function_gen(self.opt, self.sym)),
                '',
                ]
        return out

    def _main_file(self):
        """
        Add main file content.
        """
        out = [
                '',
                '',
                CodeGen(self.opt, '', _includes(self.opt)),
                '#include <stdio.h>',
                '#include <getopt.h>',
                Conditional(self.opt, '', self.opt.undefined_crc_parameters, [
                    '#include <stdlib.h>',
                    '#include <ctype.h>',
                    ]),
                Conditional(self.opt, '', self.opt.c_std != 'C89', [
                    '#include <stdbool.h>',
                ]),
                '#include <string.h>',
                '',
                'static char str[256] = "123456789";',
                f'static {self.sym.c_bool} verbose = {self.sym.c_false};',
                self._getopt_template(),
                '',
                '',
                Conditional2(self.opt, '', self.opt.undefined_crc_parameters, [
                    f'static void print_params(const {self.sym.cfg_t} *cfg)',
                    ], [
                    'static void print_params(void)',
                    ]),
                '{',
                CodeGen(self.opt, 4*' ', [
                    'char format[32];',
                    '',
                    Conditional2(self.opt, '', self.opt.c_std == 'C89', [
                        f'sprintf(format, "%%-16s = 0x%%0%dlx\\n", (unsigned int)({self.sym.cfg_width} + 3) / 4);',
                        f'printf("%-16s = %d\\n", "width", (unsigned int){self.sym.cfg_width});',
                        f'printf(format, "poly", (unsigned long int){self.sym.cfg_poly});',
                        'printf("%-16s = %s\\n", "reflect_in", {0});'.format(self.sym.cfg_reflect_in + ' ? "true": "false"' if self.opt.reflect_in is None
                                                                             else ('"true"' if self.opt.reflect_in else '"false"')),
                        f'printf(format, "xor_in", (unsigned long int){self.sym.cfg_xor_in});',
                        'printf("%-16s = %s\\n", "reflect_out", {0});'.format(self.sym.cfg_reflect_out + ' ? "true": "false"' if self.opt.reflect_out is None
                                                                              else ('"true"' if self.opt.reflect_out else '"false"')),
                        f'printf(format, "xor_out", (unsigned long int){self.sym.cfg_xor_out});',
                        f'printf(format, "crc_mask", (unsigned long int){self.sym.cfg_mask});',
                        f'printf(format, "msb_mask", (unsigned long int){self.sym.cfg_msb_mask});',
                        ], [
                        f'snprintf(format, sizeof(format), "%%-16s = 0x%%0%dllx\\n", (unsigned int)({self.sym.cfg_width} + 3) / 4);',
                        f'printf("%-16s = %d\\n", "width", (unsigned int){self.sym.cfg_width});',
                        f'printf(format, "poly", (unsigned long long int){self.sym.cfg_poly});',
                        'printf("%-16s = %s\\n", "reflect_in", {0});'.format(self.sym.cfg_reflect_in + ' ? "true": "false"' if self.opt.reflect_in is None
                                                                             else ('"true"' if self.opt.reflect_in else '"false"')),
                        f'printf(format, "xor_in", (unsigned long long int){self.sym.cfg_xor_in});',
                        'printf("%-16s = %s\\n", "reflect_out", {0});'.format(self.sym.cfg_reflect_out + ' ? "true": "false"' if self.opt.reflect_out is None
                                                                              else ('"true"' if self.opt.reflect_out else '"false"')),
                        f'printf(format, "xor_out", (unsigned long long int){self.sym.cfg_xor_out});',
                        f'printf(format, "crc_mask", (unsigned long long int){self.sym.cfg_mask});',
                        f'printf(format, "msb_mask", (unsigned long long int){self.sym.cfg_msb_mask});',
                        ]),
                    ]),
                '}',
                '',
                '',
                Comment(self.opt, '', [
                    'C main function.',
                    '\\param[in] argc the number of arguments in \\a argv.',
                    '\\param[in] argv a NULL-terminated array of pointers to the argument strings.',
                    '\\retval 0 on success.',
                    '\\retval >0 on error.',
                    ]),
                'int main(int argc, char *argv[])',
                '{',
                CodeGen(self.opt, 4*' ', [
                    Conditional(self.opt, '', self.opt.undefined_crc_parameters, [
                        f'{self.sym.cfg_t} cfg = ' + '{',
                        Conditional(self.opt, 4*' ', self.opt.width is None, [
                            '0,      /* width */',
                            ]),
                        Conditional(self.opt, 4*' ', self.opt.poly is None, [
                            '0,      /* poly */',
                            ]),
                        Conditional(self.opt, 4*' ', self.opt.reflect_in is None, [
                            '0,      /* reflect_in */',
                            ]),
                        Conditional(self.opt, 4*' ', self.opt.xor_in is None, [
                            '0,      /* xor_in */',
                            ]),
                        Conditional(self.opt, 4*' ', self.opt.reflect_out is None, [
                            '0,      /* reflect_out */',
                            ]),
                        Conditional(self.opt, 4*' ', self.opt.xor_out is None, [
                            '0,      /* xor_out */',
                            ]),
                        Conditional(self.opt, 4*' ', self.opt.width is None, [
                            '',
                            '0,      /* crc_mask */',
                            '0,      /* msb_mask */',
                            '0,      /* crc_shift */',
                            ]),
                        '};',
                        ]),
                    f'{self.sym.crc_t} crc;',
                    '',
                    Conditional2(self.opt, '', self.opt.undefined_crc_parameters, [
                        'get_config(argc, argv, &cfg);',
                        ], [
                        'get_config(argc, argv);',
                        ]),
                    Conditional(self.opt, '', _use_crc_table_gen(self.opt), [
                        f'{self.sym.crc_table_gen_function}(&cfg);',
                        ]),
                    'crc = {0}({1});'.format(self.sym.crc_init_function, '' if _use_constant_crc_init(self.sym) else '&cfg'),
                    'crc = {0}({1}crc, (void *)str, strlen(str));'.format(self.sym.crc_update_function, '' if _use_cfg_in_crc_update(self.opt) else '&cfg, '),
                    'crc = {0}({1}crc);'.format(self.sym.crc_finalize_function, '' if _use_cfg_in_finalize(self.opt) else '&cfg, '),
                    '',
                    'if (verbose) {',
                    CodeGen(self.opt, 4*' ', [
                        'print_params({0});'.format('&cfg' if self.opt.undefined_crc_parameters else ''),
                        ]),
                    '}',
                    Conditional2(self.opt, '', self.opt.c_std == 'C89', [
                        'printf("0x%lx\\n", (unsigned long int)crc);',
                        ], [
                        'printf("0x%llx\\n", (unsigned long long int)crc);',
                        ]),
                    'return 0;',
                    ]),
                '}',
                ]
        return out

    def _getopt_template(self):
        """
        Add getopt functions.
        """
        out = [
                Conditional(self.opt, '', self.opt.reflect_in is None or self.opt.reflect_out is None, [
                    '',
                    '',
                    f'static {self.sym.c_bool} atob(const char *str)',
                    '{',
                    CodeGen(self.opt, 4*' ', [
                        'if (!str) {',
                        CodeGen(self.opt, 4*' ', [
                            'return 0;',
                            ]),
                        '}',
                        'if (isdigit(str[0])) {',
                        CodeGen(self.opt, 4*' ', [
                            f'return ({self.sym.c_bool})atoi(str);',
                            ]),
                        '}',
                        'if (tolower(str[0]) == \'t\') {',
                        CodeGen(self.opt, 4*' ', [
                            f'return {self.sym.c_true};',
                            ]),
                        '}',
                        f'return {self.sym.c_false};',
                        ]),
                    '}',
                    ]),
                Conditional(self.opt, '', self.opt.poly is None or self.opt.xor_in is None or self.opt.xor_out is None, [
                    '',
                    '',
                    'static crc_t xtoi(const char *str)',
                    '{',
                    CodeGen(self.opt, 4*' ', [
                        'crc_t ret = 0;',
                        '',
                        'if (!str) {',
                        CodeGen(self.opt, 4*' ', [
                            'return 0;',
                            ]),
                        '}',
                        'if (str[0] == \'0\' && tolower(str[1]) == \'x\') {',
                        CodeGen(self.opt, 4*' ', [
                            'str += 2;',
                            'while (*str) {',
                            CodeGen(self.opt, 4*' ', [
                                'if (isdigit(*str))',
                                CodeGen(self.opt, 4*' ', [
                                    'ret = 16 * ret + *str - \'0\';',
                                    ]),
                                'else if (isxdigit(*str))',
                                CodeGen(self.opt, 4*' ', [
                                    'ret = 16 * ret + tolower(*str) - \'a\' + 10;',
                                    ]),
                                'else',
                                CodeGen(self.opt, 4*' ', [
                                    'return ret;',
                                    ]),
                                'str++;',
                                ]),
                            '}',
                            ]),
                        '} else if (isdigit(*str)) {',
                        CodeGen(self.opt, 4*' ', [
                            'while (*str) {',
                            CodeGen(self.opt, 4*' ', [
                                'if (isdigit(*str))',
                                CodeGen(self.opt, 4*' ', [
                                    'ret = 10 * ret + *str - \'0\';',
                                    ]),
                                'else',
                                CodeGen(self.opt, 4*' ', [
                                    'return ret;',
                                    ]),
                                'str++;',
                                ]),
                            '}',
                            ]),
                        '}',
                        'return ret;',
                        ]),
                    '}',
                    ]),
                '',
                '',
                Conditional2(self.opt, '', self.opt.undefined_crc_parameters, [
                    f'static int get_config(int argc, char *argv[], {self.sym.cfg_t} *cfg)',
                    ], [
                    'static int get_config(int argc, char *argv[])',
                    ]),
                '{',
                CodeGen(self.opt, 4*' ', [
                    'int c;',
                    'int option_index;',
                    'static struct option long_options[] = {',
                    CodeGen(self.opt, 4*' ', [
                        Conditional(self.opt, '', self.opt.width is None, [
                            '{"width",           1, 0, \'w\'},',
                            ]),
                        Conditional(self.opt, '', self.opt.poly is None, [
                            '{"poly",            1, 0, \'p\'},',
                            ]),
                        Conditional(self.opt, '', self.opt.reflect_in is None, [
                            '{"reflect-in",      1, 0, \'n\'},',
                            ]),
                        Conditional(self.opt, '', self.opt.xor_in is None, [
                            '{"xor-in",          1, 0, \'i\'},',
                            ]),
                        Conditional(self.opt, '', self.opt.reflect_out is None, [
                            '{"reflect-out",     1, 0, \'u\'},',
                            ]),
                        Conditional(self.opt, '', self.opt.xor_out is None, [
                            '{"xor-out",         1, 0, \'o\'},',
                            ]),
                        '{"verbose",         0, 0, \'v\'},',
                        '{"check-string",    1, 0, \'s\'},',
                        Conditional(self.opt, '', self.opt.width is None, [
                            '{"table-idx-with",  1, 0, \'t\'},',
                            ]),
                        '{0, 0, 0, 0}',
                        ]),
                    '};',
                    '',
                    'while (1) {',
                    CodeGen(self.opt, 4*' ', [
                        'option_index = 0;',
                        '',
                        'c = getopt_long(argc, argv, "w:p:n:i:u:o:s:vt", long_options, &option_index);',
                        'if (c == -1)',
                        CodeGen(self.opt, 4*' ', [
                            'break;',
                            ]),
                        '',
                        'switch (c) {',
                        CodeGen(self.opt, 4*' ', [
                            'case 0:',
                            CodeGen(self.opt, 4*' ', [
                                'printf("option %s", long_options[option_index].name);',
                                'if (optarg)',
                                CodeGen(self.opt, 4*' ', [
                                    'printf(" with arg %s", optarg);',
                                    ]),
                                'printf("\\n");',
                                'break;',
                                ]),
                            Conditional(self.opt, '', self.opt.width is None, [
                                'case \'w\':',
                                CodeGen(self.opt, 4*' ', [
                                    'cfg->width = atoi(optarg);',
                                    'break;',
                                    ]),
                                ]),
                            Conditional(self.opt, '', self.opt.poly is None, [
                                'case \'p\':',
                                CodeGen(self.opt, 4*' ', [
                                    'cfg->poly = xtoi(optarg);',
                                    'break;',
                                    ]),
                                ]),
                            Conditional(self.opt, '', self.opt.reflect_in is None, [
                                'case \'n\':',
                                CodeGen(self.opt, 4*' ', [
                                    'cfg->reflect_in = atob(optarg);',
                                    'break;',
                                    ]),
                                ]),
                            Conditional(self.opt, '', self.opt.xor_in is None, [
                                'case \'i\':',
                                CodeGen(self.opt, 4*' ', [
                                    'cfg->xor_in = xtoi(optarg);',
                                    'break;',
                                    ]),
                                ]),
                            Conditional(self.opt, '', self.opt.reflect_out is None, [
                                'case \'u\':',
                                CodeGen(self.opt, 4*' ', [
                                    'cfg->reflect_out = atob(optarg);',
                                    'break;',
                                    ]),
                                ]),
                            Conditional(self.opt, '', self.opt.xor_out is None, [
                                'case \'o\':',
                                CodeGen(self.opt, 4*' ', [
                                    'cfg->xor_out = xtoi(optarg);',
                                    'break;',
                                    ]),
                                ]),
                            'case \'s\':',
                            CodeGen(self.opt, 4*' ', [
                                'memcpy(str, optarg, strlen(optarg) < sizeof(str) ? strlen(optarg) + 1 : sizeof(str));',
                                'str[sizeof(str) - 1] = \'\\0\';',
                                'break;',
                                ]),
                            'case \'v\':',
                            CodeGen(self.opt, 4*' ', [
                                f'verbose = {self.sym.c_true};',
                                'break;',
                                ]),
                            Conditional(self.opt, '', self.opt.width is None, [
                                'case \'t\':',
                                CodeGen(self.opt, 4*' ', [
                                    '/* ignore --table_idx_width option */',
                                    'break;',
                                    ]),
                                ]),
                            'case \'?\':',
                            CodeGen(self.opt, 4*' ', [
                                'return -1;',
                                ]),
                            'case \':\':',
                            CodeGen(self.opt, 4*' ', [
                                'fprintf(stderr, "missing argument to option %c\\n", c);',
                                'return -1;',
                                ]),
                            'default:',
                            CodeGen(self.opt, 4*' ', [
                                'fprintf(stderr, "unhandled option %c\\n", c);',
                                'return -1;',
                                ]),
                            ]),
                        '}',
                        ]),
                    '}',
                    Conditional(self.opt, '', self.opt.width is None, [
                        'cfg->msb_mask = (crc_t)1u << (cfg->width - 1);',
                        'cfg->crc_mask = (cfg->msb_mask - 1) | cfg->msb_mask;',
                        'cfg->crc_shift = cfg->width < 8 ? 8 - cfg->width : 0;',
                        ]),
                    '',
                    Conditional(self.opt, '', self.opt.poly is None, [
                        f'cfg->poly &= {self.sym.cfg_mask};',
                        ]),
                    Conditional(self.opt, '', self.opt.xor_in is None, [
                        f'cfg->xor_in &= {self.sym.cfg_mask};',
                        ]),
                    Conditional(self.opt, '', self.opt.xor_out is None, [
                        f'cfg->xor_out &= {self.sym.cfg_mask};',
                        ]),
                    'return 0;',
                    ]),
                '}',
                ]
        return CodeGen(self.opt, '', out)


def _includes(opt):
    """
    Return the #include directives for the user-defined list of include files.
    """
    includes = []
    if opt.include_files is not None and len(opt.include_files) > 0:
        for include_file in opt.include_files:
            if include_file[0] == '"' or include_file[0] == '<':
                includes.append('#include {0}'.format(include_file))
            else:
                includes.append('#include "{0}"'.format(include_file))
    return includes


def _crc_algo_define(opt, sym):
    """
    Get the the identifier for header files.
    """
    name = sym.crc_algorithm.upper().replace('-', '_')
    return 'CRC_ALGO_' + name


def _use_cfg(opt):
    """
    Return True if a cfg_t structure is to be used.
    """
    return opt.undefined_crc_parameters


def _use_constant_crc_init(sym):
    """
    Return True if the inintial value is constant.
    """
    return sym.crc_init_value is not None


def _use_reflect_func(opt):
    """
    Return True if the reflect function is to be used.
    """
    if opt.reflect_out is None or opt.reflect_in is None:
        return True
    if opt.algorithm == opt.algo_table_driven:
        if opt.reflect_in and opt.reflect_out:
            return True
        if opt.reflect_in != opt.reflect_out:
            return True
    if opt.algorithm == opt.algo_bit_by_bit:
        if opt.reflect_in:
            return True
        if opt.reflect_out:
            return True
    if opt.algorithm == opt.algo_bit_by_bit_fast:
        if opt.reflect_in:
            return True
        if opt.reflect_out:
            return True
    return False


def _use_static_reflect_func(opt):
    """
    Whether a static reflect function is to be used.
    """
    if opt.algorithm == opt.algo_table_driven:
        return False
    if opt.reflect_out is not None and opt.algorithm == opt.algo_bit_by_bit_fast:
        return False
    return True


def _use_crc_table_gen(opt):
    """
    Return True if the table generator function is to be generated.
    """
    if opt.algorithm == opt.algo_table_driven:
        return opt.width is None or opt.poly is None or opt.reflect_in is None
    else:
        return False


def _crc_init_function_def(opt, sym):
    """
    The definition for the init function.
    """
    if _use_constant_crc_init(sym):
        return f'{sym.crc_t} {sym.crc_init_function}(void)'
    else:
        return f'{sym.crc_t} {sym.crc_init_function}(const {sym.cfg_t} *cfg)'


def _use_cfg_in_crc_update(opt):
    """
    Return True if the update function uses the cfg_t parameter.
    """
    if opt.algorithm in set([opt.algo_bit_by_bit, opt.algo_bit_by_bit_fast]):
        if opt.width is not None and opt.poly is not None and opt.reflect_in is not None:
            return True
    if opt.algorithm == opt.algo_table_driven:
        if opt.width is not None and opt.reflect_in is not None:
            return True
    return False


def _crc_update_function_def(opt, sym):
    """
    The definition of the update function.
    """
    if _use_cfg_in_crc_update(opt):
        return f'{sym.crc_t} {sym.crc_update_function}({sym.crc_t} crc, const void *data, size_t data_len)'
    else:
        return f'{sym.crc_t} {sym.crc_update_function}(const {sym.cfg_t} *cfg, {sym.crc_t} crc, const void *data, size_t data_len)'


def _use_cfg_in_finalize(opt):
    """
    Return True if the cfg_t parameter is used in the finalize function.
    """
    if opt.algorithm == opt.algo_bit_by_bit:
        if opt.width is not None and opt.poly is not None and opt.reflect_out is not None and opt.xor_out is not None:
            return True
    if opt.algorithm == opt.algo_bit_by_bit_fast:
        if opt.width is not None and opt.reflect_out is not None and opt.xor_out is not None:
            return True
    if opt.algorithm == opt.algo_table_driven:
        if opt.width is not None and opt.reflect_in is not None and opt.reflect_out is not None and opt.xor_out is not None:
            return True
    return False


def _use_inline_crc_finalize(opt):
    """
    Return True if the init function can be inlined.
    """
    if opt.algorithm in set([opt.algo_bit_by_bit_fast, opt.algo_table_driven]) and \
            (opt.width is not None and opt.reflect_in is not None and opt.reflect_out is not None and opt.xor_out is not None):
        return True
    else:
        return False


def _use_constant_crc_table(opt):
    """
    Return True is the CRC table is constant.
    """
    if opt.width is not None and opt.poly is not None and opt.reflect_in is not None:
        return True
    else:
        return False


def _crc_finalize_function_def(opt, sym):
    """
    The definition of the finalize function.
    """
    if _use_cfg_in_finalize(opt):
        return f'{sym.crc_t} {sym.crc_finalize_function}({sym.crc_t} crc)'
    else:
        return f'{sym.crc_t} {sym.crc_finalize_function}(const {sym.cfg_t} *cfg, {sym.crc_t} crc)'


def _crc_final_value(opt, sym):
    """
    The return value for the finalize function.
    """
    if opt.algorithm == opt.algo_table_driven:
        if opt.reflect_in == opt.reflect_out:
            return expr.Xor('crc', sym.crc_xor_out).simplify()
        else:
            reflect_fun = expr.FunctionCall(sym.crc_reflect_function, ['crc', sym.crc_width])
            return expr.Xor(reflect_fun, sym.crc_xor_out).simplify()
    if opt.reflect_out:
        reflect_fun = expr.FunctionCall(sym.crc_reflect_function, ['crc', sym.crc_width])
        return expr.Xor(reflect_fun, sym.crc_xor_out).simplify()
    return expr.Xor('crc', sym.crc_xor_out).simplify()


def _crc_table(opt, sym):
    """
    Return the code for the CRC table or the generator function.
    """
    if opt.algorithm != opt.algo_table_driven:
        return []
    return [
            '', '',
            Comment(opt, '', [
                'Static table used for the table_driven implementation.',
                Conditional(opt, '', opt.undefined_crc_parameters, [
                    f'Must be initialised with the {sym.crc_table_gen_function} function.',
                    ]),
                ]),
            Conditional2(opt, '', _use_constant_crc_table(opt), [
                Conditional2(opt, '', opt.slice_by > 1, [
                    f'static const {sym.crc_t} crc_table[{sym.crc_slice_by}][{sym.crc_table_width}] = {sym.crc_table_init};',
                    ], [
                    f'static const {sym.crc_t} crc_table[{sym.crc_table_width}] = {sym.crc_table_init};',
                    ]),
                ], [
                f'static {sym.crc_t} crc_table[{sym.crc_table_width}];',
                ]),
            ]


def _crc_table_gen(opt, sym):
    """
    Return the code for the CRC table or the generator function.
    """
    if opt.algorithm != opt.algo_table_driven or _use_constant_crc_table(opt):
        return []
    return [
            '', '',
            f'void {sym.crc_table_gen_function}(const {sym.cfg_t} *cfg)',
            '{',
            CodeGen(opt, 4*' ', [
                f'{sym.crc_t} crc;',
                'unsigned int i, j;',
                '',
                f'for (i = 0; i < {sym.cfg_table_width}; i++) ' + '{',
                CodeGen(opt, 4*' ', [
                    Conditional2(opt, '', opt.reflect_in is None, [
                        'if (cfg->reflect_in) {',
                        CodeGen(opt, 4*' ', [
                            f'crc = {sym.crc_reflect_function}(i, {sym.cfg_table_idx_width});',
                            ]),
                        '} else {',
                        CodeGen(opt, 4*' ', [
                            'crc = i;',
                            ]),
                        '}',
                        ], [
                            Conditional2(opt, '', opt.reflect_in, [
                                f'crc = {sym.crc_reflect_function}(i, {sym.cfg_table_idx_width});',
                                ], [
                                'crc = i;',
                                ]),
                        ]),
                    'crc <<= {0};'.format(expr.Parenthesis(expr.Add(expr.Sub(sym.cfg_width, sym.cfg_table_idx_width), sym.cfg_shift)).simplify()),
                    f'for (j = 0; j < {sym.cfg_table_idx_width}; j++) ' + '{',
                    CodeGen(opt, 4*' ', [
                        f'if (crc & {sym.cfg_msb_mask_shifted}) ' + '{',
                        CodeGen(opt, 4*' ', [
                            'crc = {0};'.format(expr.Xor(expr.Parenthesis(expr.Shl('crc', 1)), sym.cfg_poly_shifted).simplify()),
                            ]),
                        '} else {',
                        CodeGen(opt, 4*' ', [
                            'crc = crc << 1;',
                            ]),
                        '}',
                        ]),
                    '}',
                    Conditional(opt, '', opt.reflect_in is None, [
                        'if (cfg->reflect_in) {',
                        Conditional2(opt, 4*' ', sym.tbl_shift is None or sym.tbl_shift > 0, [
                            'crc = {0};'.format(expr.Shl(expr.FunctionCall(sym.crc_reflect_function, [expr.Shr('crc', sym.cfg_shift), sym.cfg_width]), sym.cfg_shift).simplify()),
                            ], [
                                f'crc = {sym.crc_reflect_function}(crc, {sym.cfg_width});',
                                ]),
                        '}',
                        ]),
                    Conditional(opt, '', opt.reflect_in, [
                        Conditional2(opt, '', sym.tbl_shift is None or sym.tbl_shift > 0, [
                            'crc = {0};'.format(expr.Shl(expr.FunctionCall(sym.crc_reflect_function, [expr.Shr('crc', sym.cfg_shift), sym.cfg_width]), sym.cfg_shift).simplify()),
                            ], [
                                f'crc = {sym.crc_reflect_function}(crc, {sym.cfg_width});',
                                ]),
                            ]),
                    'crc_table[i] = {0};'.format(expr.Shr(expr.Parenthesis(expr.And('crc', sym.cfg_mask_shifted)), sym.cfg_shift)),
                    ]),
                '}',
                ]),
            '}',
        ]


def _crc_reflect_function_gen(opt, sym):
    """
    Return the code for the reflect functon.
    """
    if not _use_reflect_func(opt):
        return []
    if not (opt.reflect_in is None or opt.reflect_in or opt.reflect_out is None or opt.reflect_out):
        return []
    return [
            '', '',
            f'{sym.crc_t} {sym.crc_reflect_function}({sym.crc_t} data, size_t data_len)',
            '{',
            CodeGen(opt, 4*' ', [
                'unsigned int i;',
                f'{sym.crc_t} ret;',
                '',
                'ret = data & 0x01;',
                'for (i = 1; i < data_len; i++) {',
                CodeGen(opt, 4*' ', [
                    'data >>= 1;',
                    'ret = (ret << 1) | (data & 0x01);',
                    ]),
                '}',
                'return ret;',
                ]),
            '}',
            ]


def _crc_init_function_gen(opt, sym):
    """
    Return the code for the init function.
    """
    if _use_constant_crc_init(sym):
        return []
    out = [
            '', '',
            _crc_init_function_def(opt, sym),
            '{',
            CodeGen(opt, 4*' ', [
                Conditional(opt, '', opt.algorithm == opt.algo_bit_by_bit, [
                    'unsigned int i;',
                    f'{sym.c_bool} bit;'
                    f'{sym.crc_t} crc = {sym.cfg_xor_in};',
                    f'for (i = 0; i < {sym.cfg_width}; i++) ' + '{',
                    CodeGen(opt, 4*' ', [
                        'bit = crc & 0x01;',
                        'if (bit) {',
                        CodeGen(opt, 4*' ', [
                            f'crc = ((crc ^ {sym.cfg_poly}) >> 1) | {sym.cfg_msb_mask};',
                            ]),
                        '} else {',
                        CodeGen(opt, 4*' ', [
                            'crc >>= 1;',
                            ]),
                        '}',
                        ]),
                    '}',
                    f'return crc & {sym.cfg_mask};',
                    ]),
                Conditional(opt, '', opt.algorithm == opt.algo_bit_by_bit_fast, [
                    f'return {sym.cfg_xor_in} & {sym.cfg_mask};',
                    ]),
                Conditional(opt, '', opt.algorithm == opt.algo_table_driven, [
                    Conditional2(opt, '', opt.reflect_in is None, [
                        f'if ({sym.cfg_reflect_in}) ' + '{',
                        CodeGen(opt, 4*' ', [
                            f'return {sym.crc_reflect_function}({sym.cfg_xor_in} & {sym.cfg_mask}, {sym.cfg_width});',
                            ]),
                        '} else {',
                        CodeGen(opt, 4*' ', [
                            f'return {sym.cfg_xor_in} & {sym.cfg_mask};',
                            ]),
                        '}',
                        ], [
                            Conditional2(opt, '', opt.algorithm == opt.reflect_in, [
                                f'return {sym.crc_reflect_function}({sym.cfg_xor_in} & {sym.cfg_mask}, {sym.cfg_width});',
                                ], [
                                    f'return {sym.cfg_xor_in} & {sym.cfg_mask};',
                                    ]),
                                ]),
                        ]),
                ]),
            '}',
            ]
    return out


def _crc_update_function_gen(opt, sym):
    """
    Return the code for the update function.
    """
    out = [
            '', '',
            _crc_update_function_def(opt, sym),
            '{',
            CodeGen(opt, 4*' ', ['const unsigned char *d = (const unsigned char *)data;']),
            ]
    if opt.algorithm == opt.algo_bit_by_bit:
        out += [
                CodeGen(opt, 4*' ', [
                    'unsigned int i;',
                    f'{sym.c_bool} bit;',
                    'unsigned char c;',
                    '',
                    'while (data_len--) {',
                    Conditional2(opt, 4*' ', opt.reflect_in is None, [
                        'if (' + sym.cfg_reflect_in + ') {',
                        CodeGen(opt, 4*' ', [
                            f'c = {sym.crc_reflect_function}(*d++, 8);',
                            ]),
                        '} else {',
                        CodeGen(opt, 4*' ', [
                            'c = *d++;',
                            ]),
                        '}',
                        ], [
                        Conditional2(opt, '', opt.reflect_in, [
                            f'c = {sym.crc_reflect_function}(*d++, 8);',
                            ], [
                            'c = *d++;',
                            ]),
                        ]),

                    CodeGen(opt, 4*' ', [
                        'for (i = 0; i < 8; i++) {',
                        CodeGen(opt, 4*' ', [
                            Conditional2(opt, '', opt.c_std == 'C89', [
                                f'bit = !!(crc & {sym.cfg_msb_mask});',
                                ], [
                                f'bit = crc & {sym.cfg_msb_mask};',
                                ]),
                            'crc = (crc << 1) | ((c >> (7 - i)) & 0x01);',
                            'if (bit) {',
                            CodeGen(opt, 4*' ', [
                                f'crc ^= {sym.cfg_poly};',
                                ]),
                            '}',
                            ]),
                        '}',
                        f'crc &= {sym.cfg_mask};',
                        ]),
                    '}',
                    f'return crc & {sym.cfg_mask};',
                    ]),
                ]

    if opt.algorithm == opt.algo_bit_by_bit_fast:
        out += [
                CodeGen(opt, 4*' ', [
                    'unsigned int i;',
                    f'{sym.crc_t} bit;',
                    'unsigned char c;',
                    '',
                    'while (data_len--) {',
                    CodeGen(opt, 4*' ', [
                        Conditional2(opt, '', opt.reflect_in is None, [
                            'if (' + sym.cfg_reflect_in + ') {',
                            CodeGen(opt, 4*' ', [
                                f'c = {sym.crc_reflect_function}(*d++, 8);',
                                ]),
                            '} else {',
                            CodeGen(opt, 4*' ', [
                                'c = *d++;',
                                ]),
                            '}',
                            ], [
                            'c = *d++;',
                            ]),
                        Conditional2(opt, '', opt.reflect_in, [
                            'for (i = 0x01; i & 0xff; i <<= 1) {',
                            ], [
                            'for (i = 0x80; i > 0; i >>= 1) {',
                            ]),
                        CodeGen(opt, 4*' ', [
                            'bit = ({0}) ^ ({1});'.format(expr.And('crc', sym.cfg_msb_mask).simplify(), '(c & i) ? {0} : 0'.format(sym.cfg_msb_mask)),
                            'crc <<= 1;',
                            'if (bit) {',
                            CodeGen(opt, 4*' ', [
                                f'crc ^= {sym.cfg_poly};',
                                ]),
                            '}',
                            ]),
                        '}',
                        f'crc &= {sym.cfg_mask};'
                        ]),
                    '}',
                    'return {0};'.format(expr.And('crc', sym.cfg_mask).simplify()),
                    ]),
                ]

    if opt.algorithm == opt.algo_table_driven:
        out += [
                CodeGen(opt, 4*' ', [
                    'unsigned int tbl_idx;',
                    '',
                    Conditional2(opt, '', opt.reflect_in is None, [
                        'if (cfg->reflect_in) {',
                        CodeGen(opt, 4*' ', [
                            'while (data_len--) {',
                            CodeGen(opt, 4*' ', [
                                _crc_table_core_algorithm_reflected(opt, sym),
                                'd++;',
                                ]),
                            '}',
                            ]),
                        '} else {',
                        CodeGen(opt, 4*' ', [
                            'while (data_len--) {',
                            CodeGen(opt, 4*' ', [
                                _crc_table_core_algorithm_nonreflected(opt, sym),
                                'd++;',
                                ]),
                            '}',
                            ]),
                        '}',
                        ], [
                            Conditional(opt, '', opt.slice_by > 1, [
                                f'/* Align to a multiple of {sym.crc_slice_by} bytes */',
                                f'while (data_len && (((uintptr_t)(const void *)d) % {sym.crc_slice_by} != 0))' + ' {',
                                CodeGen(opt, 4*' ', [
                                    _crc_table_core_algorithm(opt, sym),
                                    'data_len--;',
                                    ]),
                                '}',
                                '',
                                _crc_table_slice_by_algorithm(opt, sym),
                                '/* Remaining bytes with the standard algorithm */',
                                'd = (const unsigned char *)d32;',
                                ]),
                            'while (data_len--) {',
                            CodeGen(opt, 4*' ', [
                                _crc_table_core_algorithm(opt, sym),
                                ]),
                            '}',
                        ]),
                    'return {0};'.format(expr.And('crc', sym.cfg_mask).simplify()),
                    ]),
            ]
    out += [
            '}',
            ]
    return out


def _crc_finalize_function_gen(opt, sym):
    """
    Return the code for the finalize function.
    """
    if _use_inline_crc_finalize(opt):
        return []
    out = [
            '', '',
            _crc_finalize_function_def(opt, sym),
            '{',
            ]
    if opt.algorithm in set([opt.algo_bit_by_bit, opt.algo_bit_by_bit_fast]):
        out += [
                Conditional(opt, 4*' ', opt.algorithm == opt.algo_bit_by_bit, [
                    'unsigned int i;',
                    f'{sym.c_bool} bit;',
                    '',
                    'for (i = 0; i < ' + sym.cfg_width + '; i++) {',
                    CodeGen(opt, 4*' ', [
                        Conditional2(opt, '', opt.c_std == 'C89', [
                            f'bit = !!(crc & {sym.cfg_msb_mask});'
                            ], [
                            f'bit = crc & {sym.cfg_msb_mask};',
                            ]),
                        'crc <<= 1;',
                        'if (bit) {',
                        CodeGen(opt, 4*' ', [
                            f'crc ^= {sym.cfg_poly};',
                            ]),
                        '}',
                        ]),
                    '}',
                    Conditional(opt, '', opt.reflect_out is None, [
                        'if (' + sym.cfg_reflect_out + ') {',
                        CodeGen(opt, 4*' ', [
                            f'crc = {sym.crc_reflect_function}(crc, {sym.cfg_width});',
                            ]),
                        '}',
                        ]),
                    Conditional(opt, '', opt.reflect_out, [
                        f'crc = {sym.crc_reflect_function}(crc, {sym.cfg_width});',
                        ]),
                    ]),

                Conditional(opt, 4*' ', opt.algorithm == opt.algo_bit_by_bit_fast, [
                    Conditional(opt, '', opt.reflect_out is None, [
                        'if (' + sym.cfg_reflect_out + ') {',
                        CodeGen(opt, 4*' ', [
                            f'crc = {sym.crc_reflect_function}(crc, {sym.cfg_width});',
                            ]),
                        '}',
                    ]),
                    Conditional(opt, '', opt.reflect_out, [
                        f'crc = {sym.crc_reflect_function}(crc, {sym.cfg_width});',
                        ]),
                    ]),
                ]

    if opt.algorithm == opt.algo_table_driven:
        if opt.reflect_in is None or opt.reflect_out is None:
            if opt.reflect_in is None and opt.reflect_out is None:
                cond = 'cfg->reflect_in != cfg->reflect_out'
            elif opt.reflect_out is None:
                cond = ('!' if opt.reflect_in else '') + 'cfg->reflect_out'
            else:
                cond = ('!' if opt.reflect_out else '') + 'cfg->reflect_in'
            out += [
                    CodeGen(opt, 4*' ', [
                        'if (' + cond + ') {',
                        CodeGen(opt, 4*' ', [
                            f'crc = {sym.crc_reflect_function}(crc, {sym.cfg_width});',
                            ]),
                        '}',
                        ]),
                    ]
        elif opt.reflect_in != opt.reflect_out:
            out += [
                    f'crc = {sym.crc_reflect_function}(crc, {sym.cfg_width});',
                    ]
    out += [
            CodeGen(opt, 4*' ', [
                'return {0};'.format(expr.And(expr.Parenthesis(expr.Xor('crc', sym.cfg_xor_out)), sym.cfg_mask).simplify()),
                ]),
            '}',
            ]
    return out


def _crc_table_core_algorithm(opt, sym):
    """
    Return the core of the table-driven algorithm.
    """
    out = []
    out += [
        Conditional2(opt, '', opt.reflect_in, [
            _crc_table_core_algorithm_reflected(opt, sym),
            ], [
            _crc_table_core_algorithm_nonreflected(opt, sym),
            ]),
        'd++;',
    ]
    return CodeGen(opt, '', out)


def _crc_table_core_algorithm_reflected(opt, sym):
    """
    Return the core loop of the table-driven algorithm, reflected variant.
    """
    out = []
    if opt.width is not None and opt.tbl_idx_width is not None and opt.width <= opt.tbl_idx_width:
        crc_xor_expr = '0'
    else:
        crc_xor_expr = f'(crc >> {sym.cfg_table_idx_width})'

    if opt.tbl_idx_width == 8:
        if opt.slice_by > 1:
            crc_lookup = 'crc_table[0][tbl_idx]'
        else:
            crc_lookup = 'crc_table[tbl_idx]'
        crc_exp = expr.And(expr.Parenthesis(expr.Xor(crc_lookup, expr.Parenthesis(expr.Shr('crc', sym.cfg_table_idx_width)))), sym.cfg_mask).simplify()
        out += [
                Conditional2(opt, '', opt.width is None or opt.width > 8, [
                    f'tbl_idx = (crc ^ *d) & {sym.crc_table_mask};',
                    ], [
                    'tbl_idx = crc ^ *d;',
                    ]),
                f'crc = {crc_exp};',
                ]
    else:
        crc_lookup = f'crc_table[tbl_idx & {sym.crc_table_mask}]'
        for i in range(8 // opt.tbl_idx_width):
            idx = expr.Xor('crc', expr.Parenthesis(expr.Shr('*d', expr.Parenthesis(expr.Mul(i, sym.cfg_table_idx_width))))).simplify()
            out += [
                f'tbl_idx = {idx};',
                'crc = {0};'.format(expr.Xor(crc_lookup, crc_xor_expr).simplify())
                ]
    return CodeGen(opt, '', out)


def _crc_table_core_algorithm_nonreflected(opt, sym):
    """
    Return the core loop of the table-driven algorithm, non-reflected variant.
    """
    out = []
    if opt.width is None:
        crc_shifted_right = expr.Parenthesis(expr.Shr('crc', expr.Parenthesis(expr.Sub(sym.cfg_width, sym.cfg_table_idx_width)))).simplify()
    elif opt.width < 8:
        shift_val = opt.width - opt.tbl_idx_width
        if shift_val < 0:
            crc_shifted_right = expr.Parenthesis(expr.Shl('crc', -shift_val)).simplify()
        else:
            crc_shifted_right = expr.Parenthesis(expr.Shr('crc', shift_val)).simplify()
    else:
        shift_val = opt.width - opt.tbl_idx_width
        crc_shifted_right = expr.Parenthesis(expr.Shr('crc', shift_val)).simplify()

    if opt.width is not None and opt.tbl_idx_width is not None and opt.width <= opt.tbl_idx_width:
        crc_xor_expr = '0'
    else:
        crc_xor_expr = f'(crc << {sym.cfg_table_idx_width})'

    if opt.tbl_idx_width == 8:
        if opt.slice_by > 1:
            crc_lookup = 'crc_table[0][tbl_idx]'
        else:
            crc_lookup = 'crc_table[tbl_idx]'
        out += [
                Conditional2(opt, '', opt.width is None or opt.width > 8, [
                    'tbl_idx = {0};'.format(expr.And(expr.Parenthesis(expr.Xor(crc_shifted_right, '*d')),
                                                     sym.crc_table_mask).simplify())
                    ], [
                    'tbl_idx = {0};'.format(expr.Xor(crc_shifted_right, '*d').simplify())
                    ]),
                'crc = {0};'.format(expr.And(expr.Parenthesis(expr.Xor(crc_lookup, crc_xor_expr)), sym.cfg_mask).simplify())
                ]
    else:
        crc_lookup = f'crc_table[tbl_idx & {sym.crc_table_mask}]'
        for i in range(8 // opt.tbl_idx_width):
            str_idx = '{0:d}'.format(8 - (i + 1) * opt.tbl_idx_width)
            out += [
                    'tbl_idx = {0};'.format(expr.Xor(crc_shifted_right, expr.Parenthesis(expr.Shr('*d', str_idx)))),
                    'crc = {0};'.format(expr.Xor(crc_lookup, crc_xor_expr).simplify()),
                    ]
    return CodeGen(opt, '', out)


def _crc_table_slice_by_algorithm(opt, sym):
    update_be = []
    for i in range(opt.slice_by // 4):
        vard = 'd{0}'.format(opt.slice_by // 4 - i)
        for j in range(4):
            idx1 = i * 4 + j
            idx2 = expr.And(expr.Parenthesis(expr.Shr(vard, j*8)), expr.Terminal(255, '0xffu')).simplify()
            update_be.append('crc_table[{0}][{1}]{2}'.format(idx1, idx2, ' ^' if idx1 < opt.slice_by - 1 else ';'))

    update_le = []
    for i in range(opt.slice_by // 4):
        vard = 'd{0}'.format(opt.slice_by // 4 - i)
        for j in range(4):
            idx1 = i * 4 + j
            idx2 = expr.And(expr.Parenthesis(expr.Shr(vard, 24 - j*8)), expr.Terminal(255, '0xffu')).simplify()
            update_le.append('crc_table[{0}][{1}]{2}'.format(idx1, idx2, ' ^' if idx1 < opt.slice_by - 1 else ';'))

    out = [
            'const uint32_t *d32 = (const uint32_t *)d;',
            f'while (data_len >= {sym.crc_slice_by})',
            '{',
            CodeGen(opt, 4*' ', [
                CodeGen(opt, None, [
                    '#if __BYTE_ORDER == __BIG_ENDIAN',
                    ]),
                f'{sym.crc_t} d1 = *d32++ ^ le16toh(crc);',
                Conditional(opt, '', opt.slice_by >= 8, [
                    f'{sym.crc_t} d2 = *d32++;',
                    ]),
                Conditional(opt, '', opt.slice_by >= 16, [
                    f'{sym.crc_t} d3 = *d32++;',
                    f'{sym.crc_t} d4 = *d32++;',
                    ]),
                'crc  =',
                CodeGen(opt, 4*' ', update_be),
                CodeGen(opt, None, [
                    '#else',
                    ]),
                f'{sym.crc_t} d1 = *d32++ ^ crc;',
                Conditional(opt, '', opt.slice_by >= 8, [
                    f'{sym.crc_t} d2 = *d32++;',
                    ]),
                Conditional(opt, '', opt.slice_by >= 16, [
                    f'{sym.crc_t} d3 = *d32++;',
                    f'{sym.crc_t} d4 = *d32++;',
                    ]),
                'crc  =',
                CodeGen(opt, 4*' ', update_le),
                CodeGen(opt, None, [
                    '#endif',
                    ]),
                '',
                f'data_len -= {sym.crc_slice_by};',
                ]),
            '}',
            '',
            ]
    return CodeGen(opt, '', out)
