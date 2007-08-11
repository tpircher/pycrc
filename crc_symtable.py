#  pycrc -- flexible CRC calculation utility and C source file generator
# -*- coding: Latin-1 -*-

#  Copyright (c) 2006-2007  Thomas Pircher  <tehpeh@gmx.net>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.


"""
Symbol table for pycrc
use as follows:

   #from crc_opt import Options
   #opt = Options("0.6")
   #opt.parse(sys.argv)

This file is part of pycrc.
"""

from crc_algorithms import Crc
import time
import os


# Class SymbolTable
###############################################################################
class SymbolTable:
    """
    The symbol table class
    """
    opt = None

    # __init__
    ###############################################################################
    def __init__(self, opt):
        """
        The class constructor
        """
        self.opt = opt

        self.table = {}
        self.table["crc_width"] = self.__pretty_str(self.opt.Width)
        self.table["crc_poly"] = self.__pretty_hex(self.opt.Poly, self.opt.Width)
        self.table["crc_reflect_in"] = self.__pretty_bool(self.opt.ReflectIn)
        self.table["crc_xor_in"] = self.__pretty_hex(self.opt.XorIn, self.opt.Width)
        self.table["crc_reflect_out"] = self.__pretty_bool(self.opt.ReflectOut)
        self.table["crc_xor_out"] = self.__pretty_hex(self.opt.XorOut, self.opt.Width)
        self.table["crc_table_idx_width"] = str(self.opt.TableIdxWidth)
        self.table["crc_table_width"] = str(1 << self.opt.TableIdxWidth)
        self.table["crc_table_mask"] = self.__pretty_hex(self.opt.TableWidth - 1, 8)
        self.table["crc_mask"] = self.__pretty_hex(self.opt.Mask, self.opt.Width)
        self.table["crc_msb_mask"] = self.__pretty_hex(self.opt.MSB_Mask, self.opt.Width)

        self.table["cfg_width"] = "{%if $crc_width != Undefined%}{%crc_width%}{%else%}cfg->width{%endif%}"
        self.table["cfg_poly"] = "{%if $crc_poly != Undefined%}{%crc_poly%}{%else%}cfg->poly{%endif%}"
        self.table["cfg_reflect_in"] = "{%if $crc_reflect_in != Undefined%}{%crc_reflect_in%}{%else%}cfg->reflect_in{%endif%}"
        self.table["cfg_xor_in"] = "{%if $crc_xor_in != Undefined%}{%crc_xor_in%}{%else%}cfg->xor_in{%endif%}"
        self.table["cfg_reflect_out"] = "{%if $crc_reflect_out != Undefined%}{%crc_reflect_out%}{%else%}cfg->reflect_out{%endif%}"
        self.table["cfg_xor_out"] = "{%if $crc_xor_out != Undefined%}{%crc_xor_out%}{%else%}cfg->xor_out{%endif%}"
        self.table["cfg_table_idx_width"] = "{%if $crc_table_idx_width != Undefined%}{%crc_table_idx_width%}{%else%}cfg->table_idx_width{%endif%}"
        self.table["cfg_table_width"] = "{%if $crc_table_width != Undefined%}{%crc_table_width%}{%else%}cfg->table_width{%endif%}"
        self.table["cfg_mask"] = "{%if $crc_mask != Undefined%}{%crc_mask%}{%else%}cfg->crc_mask{%endif%}"
        self.table["cfg_msb_mask"] = "{%if $crc_msb_mask != Undefined%}{%crc_msb_mask%}{%else%}cfg->msb_mask{%endif%}"

        self.table["undefined_parameters"] = self.__pretty_bool(self.opt.UndefinedCrcParameters)
        self.table["use_cfg_t"] = self.__pretty_bool(self.opt.UndefinedCrcParameters)
        self.table["c_std"] = self.opt.CStd
        self.table["c_bool"] = "{%if $c_std == C89%}int{%else%}bool{%endif%}"
        self.table["c_true"] = "{%if $c_std == C89%}1{%else%}true{%endif%}"
        self.table["c_false"] = "{%if $c_std == C89%}0{%else%}false{%endif%}"

        if self.__get_init_value() == None:
            self.table["constant_crc_init"] = self.__pretty_bool(False)
        else:
            self.table["constant_crc_init"] =  self.__pretty_bool(True)

        if (self.opt.Algorithm == self.opt.Algo_Bit_by_Bit_Fast or self.opt.Algorithm == self.opt.Algo_Table_Driven) and \
                (self.opt.Width != None and self.opt.ReflectOut != None and self.opt.XorOut != None):
            self.table["inline_crc_finalize"] = self.__pretty_bool(True)
        else:
            self.table["inline_crc_finalize"] = self.__pretty_bool(False)

        if self.opt.Algorithm != self.opt.Algo_Bit_by_Bit and (self.opt.Width != None and self.opt.ReflectOut != None and self.opt.XorOut != None) \
                or self.opt.Algorithm == self.opt.Algo_Bit_by_Bit and \
                (self.opt.Width != None and self.opt.ReflectOut != None and self.opt.XorOut != None and self.opt.Poly != None):
            self.table["simple_crc_finalize_def"] = self.__pretty_bool(True)
        else:
            self.table["simple_crc_finalize_def"] = self.__pretty_bool(False)

        if self.opt.ReflectOut == False and self.opt.ReflectIn == False:
            self.table["use_reflect_func"] = self.__pretty_bool(False)
        else:
            self.table["use_reflect_func"] = self.__pretty_bool(True)

        if self.opt.Algorithm == self.opt.Algo_Table_Driven:
            self.table["static_reflect_func"] = self.__pretty_bool(False)
        elif self.opt.ReflectOut != None and self.opt.Algorithm == self.opt.Algo_Bit_by_Bit_Fast:
            self.table["static_reflect_func"] = self.__pretty_bool(False)
        else:
            self.table["static_reflect_func"] = self.__pretty_bool(True)

        if self.opt.Algorithm == self.opt.Algo_Bit_by_Bit:
            self.table["crc_algorithm"] = "bit-by-bit"
        elif self.opt.Algorithm == self.opt.Algo_Bit_by_Bit_Fast:
            self.table["crc_algorithm"] = "bit-by-bit-fast"
        elif self.opt.Algorithm == self.opt.Algo_Table_Driven:
            self.table["crc_algorithm"] = "table-driven"
        else:
            self.table["crc_algorithm"] = "UNKNOWN"

        self.table["datetime"] = time.asctime()
        self.table["program_version"] = self.opt.VersionStr
        self.table["program_url"] = self.opt.WebAddress

        if self.opt.OutputFile == None:
            self.table["filename"] = "stdout"
        else:
            self.table["filename"] = self.opt.OutputFile

        if self.opt.OutputFile == None:
            self.table["header_filename"] = "stdout.h"
        elif self.opt.OutputFile[-2:] == ".c":
            self.table["header_filename"] = self.opt.OutputFile[0:-1] + "h"
        else:
            self.table["header_filename"] = self.opt.OutputFile + ".h"

        self.table["header_protection"] = self.__pretty_hdrprotection()

        if self.opt.Width == None:
            self.table["underlying_crc_t"] = "unsigned long"
        elif self.opt.Width <= 8:
            self.table["underlying_crc_t"] = "uint8_t"
        elif self.opt.Width <= 16:
            self.table["underlying_crc_t"] = "uint16_t"
        elif self.opt.Width <= 32:
            self.table["underlying_crc_t"] = "uint32_t"
        else:
            self.table["underlying_crc_t"] = "unsigned long"

        self.table["crc_t"] = self.opt.SymbolPrefix + "t"
        self.table["cfg_t"] = self.opt.SymbolPrefix + "cfg_t"
        self.table["crc_reflect_function"] = self.opt.SymbolPrefix + "reflect"
        self.table["crc_table_gen_function"] = self.opt.SymbolPrefix + "table_gen"
        self.table["crc_init_function"] = self.opt.SymbolPrefix + "init"
        self.table["crc_update_function"] = self.opt.SymbolPrefix + "update"
        self.table["crc_finalize_function"] = self.opt.SymbolPrefix + "finalize"

        ret = self.__get_init_value()
        if ret == None:
            self.table["crc_init_value"] = ""
        else:
            self.table["crc_init_value"] = ret

        self.table["crc_final_value"] = """\
{%if $crc_reflect_out == True%}
{%crc_reflect_function%}(crc, {%crc_width%}) ^ {%crc_xor_out%}\
{%else%}
crc ^ {%crc_xor_out%}\
{%endif%}\
"""

        self.table["crc_table_init"] = self.__get_table_init()

        self.table["h_template"] = """\
{%source_header%}
#ifndef {%header_protection%}
#define {%header_protection%}

#include <stdint.h>
#include <unistd.h>
{%if $undefined_parameters == True and $c_std != C89%}
#include <stdbool.h>
{%endif%}

/**
 * \\brief   The definition of the used algorithm.
 *****************************************************************************/
{%if $crc_algorithm == "bit-by-bit"%}
#define CRC_ALGO_BIT_BY_BIT 1
{%elif $crc_algorithm == "bit-by-bit-fast"%}
#define CRC_ALGO_BIT_BY_BIT_FAST 1
{%elif $crc_algorithm == "table-driven"%}
#define CRC_ALGO_TABLE_DRIVEN 1
{%endif%}

/**
 * \\brief   The type of the CRC values.
 *
 * This type must be big enough to contain at least {%cfg_width%} bits.
 *****************************************************************************/
typedef {%underlying_crc_t%} {%crc_t%};

{%if $undefined_parameters == True%}
/**
 * \\brief   The configuration type of the CRC algorithm.
 *****************************************************************************/
typedef struct {
{%if $crc_width == Undefined%}
    unsigned int width;     /*!< The width of the polynom */
{%endif%}
{%if $crc_poly == Undefined%}
    {%crc_t%} poly;             /*!< The CRC polynom */
{%endif%}
{%if $crc_reflect_in == Undefined%}
    {%c_bool%} reflect_in;        /*!< Whether the input shall be reflected or not */
{%endif%}
{%if $crc_xor_in == Undefined%}
    {%crc_t%} xor_in;           /*!< The initial value of the algorithm */
{%endif%}
{%if $crc_reflect_out == Undefined%}
    {%c_bool%} reflect_out;       /*!< Wether the output shall be reflected or not */
{%endif%}
{%if $crc_xor_out == Undefined%}
    {%crc_t%} xor_out;          /*!< The value which shall be XOR-ed to the final CRC value */
{%endif%}
{%if $crc_width == Undefined%}

    /* internal parameters */
    {%crc_t%} msb_mask;         /*!< a bitmask with the Most Significant Bit set to 1
                                 initialise as 0x01 << (width - 1) */
    {%crc_t%} crc_mask;         /*!< a bitmask with all width bits set to 1
                                 initialise as (cfg->msb_mask - 1) | cfg->msb_mask */
{%endif%}
} {%cfg_t%};

{%endif%}
{%if $use_reflect_func == True and $static_reflect_func != True%}
{%crc_reflect_doc%}
{%crc_reflect_function_def%};

{%endif%}
{%if $crc_algorithm == "table-driven" and $undefined_parameters == True%}
{%crc_table_gen_doc%}
void {%crc_table_gen_function%}(const {%cfg_t%} *cfg);

{%endif%}
{%crc_init_doc%}
{%if $constant_crc_init == False%}
{%crc_init_function_def%};
{%elif $c_std == C89%}
#define {%crc_init_function%}()      ({%crc_init_value%})
{%else%}
static inline {%crc_init_function_def%}{%%}
{
    return {%crc_init_value%};
}
{%endif%}

{%crc_update_doc%}
{%crc_update_function_def%};

{%crc_finalize_doc%}
{%if $inline_crc_finalize == True%}
{%if $c_std == C89%}
#define {%crc_finalize_function%}(crc)      ({%crc_final_value%})
{%else%}
static inline {%crc_finalize_function_def%}{%%}
{
    return {%crc_final_value%};
}
{%endif%}
{%else%}
{%crc_finalize_function_def%};
{%endif%}

#endif      /* {%header_protection%} */
"""

        self.table["source_header"] = """\
/**
 * \\file {%filename%}
 * Functions and types for CRC checks.
 *
 * Generated on {%datetime%},
 * by {%program_version%}, {%program_url%}
 * using the configuration:
 *    Width        = {%crc_width%}
 *    Poly         = {%crc_poly%}
 *    XorIn        = {%crc_xor_in%}
 *    ReflectIn    = {%crc_reflect_in%}
 *    XorOut       = {%crc_xor_out%}
 *    ReflectOut   = {%crc_reflect_out%}
 *    Algorithm    = {%crc_algorithm%}
 *****************************************************************************/\
"""

        self.table["crc_reflect_doc"] = """\
/**
 * \\brief      Reflect all bits of a \\a data word of \\a data_len bytes.
 * \\param data         The data word to be reflected.
 * \\param data_len     The width of \\a data expressed in number of bits.
 * \\return     The reflected data.
 *****************************************************************************/\
"""

        self.table["crc_reflect_function_def"] = """\
long {%crc_reflect_function%}(long data, size_t data_len)\
"""

        self.table["crc_reflect_function_body"] = """\
{%if $crc_reflect_in == Undefined or $crc_reflect_in == True or $crc_reflect_out == Undefined or $crc_reflect_out == True%}
{%crc_reflect_doc%}
{%crc_reflect_function_def%}{%%}
{
    unsigned int i;
    long ret;

    ret = 0;
    for (i = 0; i < data_len; i++)
    {
        if (data & 0x01) {
            ret = (ret << 1) | 1;
        } else {
            ret = ret << 1;
        }
        data >>= 1;
    }
    return ret;
}
{%endif%}\
"""

        self.table["crc_table_gen_doc"] = """\
/**
 * \\brief      Populate the private static crc table.
 * \\param cfg  A pointer to a initialised {%cfg_t%} structure.
 * \\return     void
 *****************************************************************************/\
"""

        self.table["crc_init_doc"] = """\
/**
 * \\brief      Calculate the initial crc value.
{%if $use_cfg_t == True%}
 * \\param cfg  A pointer to a initialised {%cfg_t%} structure.
{%endif%}
 * \\return     The initial crc value.
 *****************************************************************************/\
"""
    
        self.table["crc_init_function_def"] = """\
{%if $constant_crc_init == False%}
{%crc_t%} {%crc_init_function%}(const {%cfg_t%} *cfg)\
{%else%}
{%crc_t%} {%crc_init_function%}(void)\
{%endif%}\
"""

        self.table["crc_update_doc"] = """\
/**
 * \\brief          Update the crc value with new data.
 * \\param crc      The current crc value.
{%if $use_cfg_t == True%}
 * \\param cfg      A pointer to a initialised {%cfg_t%} structure.
{%endif%}
 * \\param data     Pointer to a buffer of \\a data_len bytes.
 * \\param data_len Number of bytes in the \\a data buffer.
 * \\return         The updated crc value.
 *****************************************************************************/\
"""

        self.table["crc_update_function_def"] = """\
{%if $undefined_parameters == True%}
{%crc_t%} {%crc_update_function%}(const {%cfg_t%} *cfg, {%crc_t%} crc, const unsigned char *data, size_t data_len)\
{%else%}
{%crc_t%} {%crc_update_function%}({%crc_t%} crc, const unsigned char *data, size_t data_len)\
{%endif%}\
"""

        self.table["crc_finalize_doc"] = """\
/**
 * \\brief      Calculate the final crc value.
{%if $use_cfg_t == True%}
 * \\param cfg  A pointer to a initialised {%cfg_t%} structure.
{%endif%}
 * \\param crc  The current crc value.
 * \\return     The final crc value.
 *****************************************************************************/\
"""

        self.table["crc_finalize_function_def"] = """\
{%if $simple_crc_finalize_def != True%}
{%crc_t%} {%crc_finalize_function%}(const {%cfg_t%} *cfg, {%crc_t%} crc)\
{%else%}
{%crc_t%} {%crc_finalize_function%}({%crc_t%} crc)\
{%endif%}\
"""

        self.table["c_template"] = """\
{%source_header%}
#include "{%header_filename%}"
#include <stdint.h>
#include <unistd.h>
{%if $undefined_parameters == True or $crc_algorithm == "bit-by-bit" or $crc_algorithm == "bit-by-bit-fast"%}
{%if $c_std != C89%}
#include <stdbool.h>
{%endif%}
{%endif%}

{%if $use_reflect_func == True and $static_reflect_func == True%}
static {%crc_reflect_function_def%};

{%endif%}
{%if $crc_algorithm == "bit-by-bit"%}
{%c_bit_by_bit%}
{%elif $crc_algorithm == "bit-by-bit-fast"%}
{%c_bit_by_bit_fast%}
{%elif $crc_algorithm == "table-driven"%}
{%c_table_driven%}
{%endif%}
{%endif%}
"""

        self.table["c_table"] = """\
/**
 * Static table used for the table_driven implementation.
{%if $undefined_parameters == True%}
 * Must be initialised with the {%crc_init_function%} function.
{%endif%}
 *****************************************************************************/
{%if $undefined_parameters == True%}
static {%crc_t%} crc_table[{%crc_table_width%}];
{%else%}
static const {%crc_t%} crc_table[{%crc_table_width%}] = {
{%crc_table_init%}
};
{%endif%}
"""

        self.table["c_bit_by_bit"] = """\
{%if $use_reflect_func == True%}
{%crc_reflect_function_body%}

{%endif%}
{%if $constant_crc_init == False%}
{%crc_init_doc%}
{%crc_init_function_def%}{%%}
{
    unsigned int i;
    {%c_bool%} bit;
    {%crc_t%} crc = {%cfg_xor_in%};
    for (i = 0; i < {%cfg_width%}; i++) {
        bit = crc & 0x01;
        if (bit) {
            crc = ((crc ^ {%cfg_poly%}) >> 1) | {%cfg_msb_mask%};
        } else {
            crc >>= 1;
        }
    }
    return crc & {%cfg_mask%};
}
{%endif%}

{%crc_update_doc%}
{%crc_update_function_def%}{%%}
{
    unsigned int i;
    {%c_bool%} bit;
    unsigned char c;

    while (data_len--) {
{%if $crc_reflect_in == Undefined%}
        if ({%cfg_reflect_in%}) {
            c = {%crc_reflect_function%}(*data++, 8);
        } else {
            c = *data++;
        }
{%elif $crc_reflect_in == True%}
        c = {%crc_reflect_function%}(*data++, 8);
{%else%}
        c = *data++;
{%endif%}
        for (i = 0; i < 8; i++) {
            bit = crc & {%cfg_msb_mask%};
            crc = (crc << 1) | ((c >> (7 - i)) & 0x01);
            if (bit) {
                crc ^= {%cfg_poly%};
            }
        }
        crc &= {%cfg_mask%};
    }
    return crc & {%cfg_mask%};
}


{%crc_finalize_doc%}
{%crc_finalize_function_def%}{%%}
{
    unsigned int i;
    {%c_bool%} bit;

    for (i = 0; i < {%cfg_width%}; i++) {
        bit = crc & {%cfg_msb_mask%};
        crc = (crc << 1) | 0x00;
        if (bit) {
            crc ^= {%cfg_poly%};
        }
    }
{%if $crc_reflect_out == Undefined%}
    if ({%cfg_reflect_out%}) {
        crc = {%crc_reflect_function%}(crc, {%cfg_width%});
    }
{%elif $crc_reflect_out == True%}
    crc = {%crc_reflect_function%}(crc, {%cfg_width%});
{%endif%}
    return (crc ^ {%cfg_xor_out%}) & {%cfg_mask%};
}
"""

        self.table["c_bit_by_bit_fast"] = """\
{%if $use_reflect_func == True%}
{%crc_reflect_function_body%}

{%endif%}
{%if $constant_crc_init == False%}
{%crc_init_doc%}
{%crc_init_function_def%}{%%}
{
    return {%cfg_xor_in%} & {%cfg_mask%};
}
{%endif%}

{%crc_update_doc%}
{%crc_update_function_def%}{%%}
{
    unsigned int i;
    {%c_bool%} bit;
    unsigned char c;

    while (data_len--) {
{%if $crc_reflect_in == Undefined%}
        if ({%cfg_reflect_in%}) {
            c = {%crc_reflect_function%}(*data++, 8);
        } else {
            c = *data++;
        }
{%else%}
        c = *data++;
{%endif%}
{%if $crc_reflect_in == True%}
        for (i = 0x01; i <= 0x80; i <<= 1) {
{%else%}
        for (i = 0x80; i > 0; i >>= 1) {
{%endif%}
            bit = crc & {%cfg_msb_mask%};
            if (c & i) {
                bit = !bit;
            }
            crc <<= 1;
            if (bit) {
                crc ^= {%cfg_poly%};
            }
        }
        crc &= {%cfg_mask%};
    }
    return crc & {%cfg_mask%};
}

{%if $inline_crc_finalize != True%}
{%crc_finalize_doc%}
{%crc_finalize_function_def%}{%%}
{
{%if $crc_reflect_out == Undefined%}
    if (cfg->reflect_out) {
        crc = {%crc_reflect_function%}(crc, {%cfg_width%});
    }
{%elif $crc_reflect_out == True%}
    crc = {%crc_reflect_function%}(crc, {%cfg_width%});
{%endif%}
    return (crc ^ {%cfg_xor_out%}) & {%cfg_mask%};
}

{%endif%}
"""

        self.table["c_table_driven"] = """\
{%c_table%}
{%if $use_reflect_func == True%}
{%crc_reflect_function_body%}
{%endif%}

{%if $constant_crc_init == False%}
{%crc_init_doc%}
{%crc_init_function_def%}{%%}
{
{%if $crc_reflect_in == Undefined%}
    if ({%cfg_reflect_in%}) {
        return {%crc_reflect_function%}({%cfg_xor_in%} & {%cfg_mask%}, {%cfg_width%});
    } else {
        return {%cfg_xor_in%} & {%cfg_mask%};
    }
{%elif $crc_reflect_in == True%}
    return {%crc_reflect_function%}({%cfg_xor_in%} & {%cfg_mask%}, {%cfg_width%});
{%else%}
    return {%cfg_xor_in%} & {%cfg_mask%};
{%endif%}
}
{%endif%}

{%if $undefined_parameters == True%}
{%crc_table_gen_doc%}
void {%crc_table_gen_function%}(const {%cfg_t%} *cfg)
{
    {%crc_t%} crc;
    unsigned int i, j;

    for (i = 0; i < {%cfg_table_width%}; i++) {
{%if $crc_reflect_in == Undefined%}
        if (cfg->reflect_in) {
            crc = {%crc_reflect_function%}(i, {%cfg_table_idx_width%});
        } else {
            crc = i;
        }
{%elif $crc_reflect_in == True%}
        crc = {%crc_reflect_function%}(i, {%cfg_table_idx_width%});
{%else%}
        crc = i;
{%endif%}
        crc <<= ({%cfg_width%} - {%cfg_table_idx_width%});
        for (j = 0; j < {%cfg_table_idx_width%}; j++) {
            if (crc & {%cfg_msb_mask%}) {
                crc = (crc << 1) ^ {%cfg_poly%};
            } else {
                crc = crc << 1;
            }
        }
{%if $crc_reflect_in == Undefined%}
        if (cfg->reflect_in) {
            crc = {%crc_reflect_function%}(crc, {%cfg_width%});
        }
{%elif $crc_reflect_in == True%}
        crc = {%crc_reflect_function%}(crc, {%cfg_width%});
{%endif%}
        crc_table[i] = crc & {%cfg_mask%};
    }
}

{%endif%}
{%crc_update_doc%}
{%crc_update_function_def%}{%%}
{
    unsigned int tbl_idx;

{%if $crc_reflect_in == Undefined%}
    if (cfg->reflect_in) {
        while (data_len--) {
{%if $crc_table_idx_width == 8%}
            tbl_idx = (crc ^ *data) & {%crc_table_mask%};
            crc = (crc_table[tbl_idx] ^ (crc >> 8)) & {%cfg_mask%};
{%else%}
            tbl_idx = crc ^ (*data >> (0 * {%cfg_table_idx_width%}));
            crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc >> {%cfg_table_idx_width%});
{%if $crc_table_idx_width <= 4%}
            tbl_idx = crc ^ (*data >> (1 * {%cfg_table_idx_width%}));
            crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc >> {%cfg_table_idx_width%});
{%endif%}
{%if $crc_table_idx_width <= 2%}
            tbl_idx = crc ^ (*data >> (2 * {%cfg_table_idx_width%}));
            crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc >> {%cfg_table_idx_width%});
            tbl_idx = crc ^ (*data >> (3 * {%cfg_table_idx_width%}));
            crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc >> {%cfg_table_idx_width%});
{%endif%}
{%if $crc_table_idx_width <= 1%}
            tbl_idx = crc ^ (*data >> (4 * {%cfg_table_idx_width%}));
            crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc >> {%cfg_table_idx_width%});
            tbl_idx = crc ^ (*data >> (5 * {%cfg_table_idx_width%}));
            crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc >> {%cfg_table_idx_width%});
            tbl_idx = crc ^ (*data >> (6 * {%cfg_table_idx_width%}));
            crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc >> {%cfg_table_idx_width%});
            tbl_idx = crc ^ (*data >> (7 * {%cfg_table_idx_width%}));
            crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc >> {%cfg_table_idx_width%});
{%endif%}
{%endif%}
            data++;
        }
        crc = {%crc_reflect_function%}(crc, {%cfg_width%});
    } else {
        while (data_len--) {
{%if $crc_table_idx_width == 8%}
            tbl_idx = ((crc >> ({%cfg_width%} - 8)) ^ *data) & {%crc_table_mask%};
            crc = (crc_table[tbl_idx] ^ (crc << 8)) & {%cfg_mask%};
{%else%}
            tbl_idx = (crc >> ({%cfg_width%} - {%cfg_table_idx_width%})) ^ (*data >> (8 - (0 + 1) * {%cfg_table_idx_width%}));
            crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc << {%cfg_table_idx_width%});
{%if $crc_table_idx_width <= 4%}
            tbl_idx = (crc >> ({%cfg_width%} - {%cfg_table_idx_width%})) ^ (*data >> (8 - (1 + 1) * {%cfg_table_idx_width%}));
            crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc << {%cfg_table_idx_width%});
{%endif%}
{%if $crc_table_idx_width <= 2%}
            tbl_idx = (crc >> ({%cfg_width%} - {%cfg_table_idx_width%})) ^ (*data >> (8 - (2 + 1) * {%cfg_table_idx_width%}));
            crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc << {%cfg_table_idx_width%});
            tbl_idx = (crc >> ({%cfg_width%} - {%cfg_table_idx_width%})) ^ (*data >> (8 - (3 + 1) * {%cfg_table_idx_width%}));
            crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc << {%cfg_table_idx_width%});
{%endif%}
{%if $crc_table_idx_width <= 1%}
            tbl_idx = (crc >> ({%cfg_width%} - {%cfg_table_idx_width%})) ^ (*data >> (8 - (4 + 1) * {%cfg_table_idx_width%}));
            crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc << {%cfg_table_idx_width%});
            tbl_idx = (crc >> ({%cfg_width%} - {%cfg_table_idx_width%})) ^ (*data >> (8 - (5 + 1) * {%cfg_table_idx_width%}));
            crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc << {%cfg_table_idx_width%});
            tbl_idx = (crc >> ({%cfg_width%} - {%cfg_table_idx_width%})) ^ (*data >> (8 - (6 + 1) * {%cfg_table_idx_width%}));
            crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc << {%cfg_table_idx_width%});
            tbl_idx = (crc >> ({%cfg_width%} - {%cfg_table_idx_width%})) ^ (*data >> (8 - (7 + 1) * {%cfg_table_idx_width%}));
            crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc << {%cfg_table_idx_width%});
{%endif%}
{%endif%}
            data++;
        }
    }
{%elif $crc_reflect_in == True%}
    while (data_len--) {
{%if $crc_table_idx_width == 8%}
        tbl_idx = (crc ^ *data) & {%crc_table_mask%};
        crc = crc_table[tbl_idx] ^ (crc >> 8);
{%else%}
        tbl_idx = crc ^ (*data >> (0 * {%cfg_table_idx_width%}));
        crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc >> {%cfg_table_idx_width%});
{%if $crc_table_idx_width <= 4%}
        tbl_idx = crc ^ (*data >> (1 * {%cfg_table_idx_width%}));
        crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc >> {%cfg_table_idx_width%});
{%endif%}
{%if $crc_table_idx_width <= 2%}
        tbl_idx = crc ^ (*data >> (2 * {%cfg_table_idx_width%}));
        crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc >> {%cfg_table_idx_width%});
        tbl_idx = crc ^ (*data >> (3 * {%cfg_table_idx_width%}));
        crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc >> {%cfg_table_idx_width%});
{%endif%}
{%if $crc_table_idx_width <= 1%}
        tbl_idx = crc ^ (*data >> (4 * {%cfg_table_idx_width%}));
        crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc >> {%cfg_table_idx_width%});
        tbl_idx = crc ^ (*data >> (5 * {%cfg_table_idx_width%}));
        crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc >> {%cfg_table_idx_width%});
        tbl_idx = crc ^ (*data >> (6 * {%cfg_table_idx_width%}));
        crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc >> {%cfg_table_idx_width%});
        tbl_idx = crc ^ (*data >> (7 * {%cfg_table_idx_width%}));
        crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc >> {%cfg_table_idx_width%});
{%endif%}
{%endif%}
        data++;
    }
    crc = {%crc_reflect_function%}(crc, {%cfg_width%});
{%elif $crc_reflect_in == False%}
    while (data_len--) {
{%if $crc_table_idx_width == 8%}
        tbl_idx = (crc >> ({%cfg_width%} - 8)) ^ *data;
        crc = (crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc << 8));
{%else%}
        tbl_idx = (crc >> ({%cfg_width%} - {%cfg_table_idx_width%})) ^ (*data >> (8 - (0 + 1) * {%cfg_table_idx_width%}));
        crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc << {%cfg_table_idx_width%});
{%if $crc_table_idx_width <= 4%}
        tbl_idx = (crc >> ({%cfg_width%} - {%cfg_table_idx_width%})) ^ (*data >> (8 - (1 + 1) * {%cfg_table_idx_width%}));
        crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc << {%cfg_table_idx_width%});
{%endif%}
{%if $crc_table_idx_width <= 2%}
        tbl_idx = (crc >> ({%cfg_width%} - {%cfg_table_idx_width%})) ^ (*data >> (8 - (2 + 1) * {%cfg_table_idx_width%}));
        crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc << {%cfg_table_idx_width%});
        tbl_idx = (crc >> ({%cfg_width%} - {%cfg_table_idx_width%})) ^ (*data >> (8 - (3 + 1) * {%cfg_table_idx_width%}));
        crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc << {%cfg_table_idx_width%});
{%endif%}
{%if $crc_table_idx_width <= 1%}
        tbl_idx = (crc >> ({%cfg_width%} - {%cfg_table_idx_width%})) ^ (*data >> (8 - (4 + 1) * {%cfg_table_idx_width%}));
        crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc << {%cfg_table_idx_width%});
        tbl_idx = (crc >> ({%cfg_width%} - {%cfg_table_idx_width%})) ^ (*data >> (8 - (5 + 1) * {%cfg_table_idx_width%}));
        crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc << {%cfg_table_idx_width%});
        tbl_idx = (crc >> ({%cfg_width%} - {%cfg_table_idx_width%})) ^ (*data >> (8 - (6 + 1) * {%cfg_table_idx_width%}));
        crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc << {%cfg_table_idx_width%});
        tbl_idx = (crc >> ({%cfg_width%} - {%cfg_table_idx_width%})) ^ (*data >> (8 - (7 + 1) * {%cfg_table_idx_width%}));
        crc = crc_table[tbl_idx & {%crc_table_mask%}] ^ (crc << {%cfg_table_idx_width%});
{%endif%}
{%endif%}
        data++;
    }

{%endif%}
    return crc & {%cfg_mask%};
}

{%if $inline_crc_finalize == False%}
{%crc_finalize_doc%}
{%crc_finalize_function_def%}{%%}
{
{%if $crc_reflect_out == Undefined%}
    if (cfg->reflect_out) {
        crc = {%crc_reflect_function%}(crc, {%cfg_width%});
    }
{%elif $crc_reflect_out == True%}
    crc = {%crc_reflect_function%}(crc, {%cfg_width%});
{%endif%}
    return (crc ^ {%cfg_xor_out%}) & {%cfg_mask%};
}
"""

        self.table["main_template"] = """\
#include <stdio.h>
{%if $undefined_parameters == True%}
#include <unistd.h>
#include <getopt.h>
#include <stdlib.h>
#include <stdio.h>
#include <ctype.h>
{%endif%}
{%if $c_std != C89%}
#include <stdbool.h>
{%endif%}
#include <string.h>

static char str[256] = "123456789";
static {%c_bool%} verbose = {%c_false%};

void print_params({%if $undefined_parameters == True%}const {%cfg_t%} *cfg{%else%}{%endif%});
{%if $undefined_parameters == True%}
{%getopt_template%}
{%endif%}

void print_params({%if $undefined_parameters == True%}const {%cfg_t%} *cfg{%else%}{%endif%})
{
    char format[20];

    snprintf(format, sizeof(format), "%%-16s = 0x%%0%dx\\n", (unsigned int)({%cfg_width%} + 3) / 4);
    printf("%-16s = %d\\n", "width", (unsigned int){%cfg_width%});
    printf(format, "poly", (unsigned int){%cfg_poly%});
    printf("%-16s = %s\\n", "reflect_in", {%if crc_reflect_in == Undefined%}{%cfg_reflect_in%} ? "true": "false"{%else%}{%if crc_reflect_in == True%}"true"{%else%}"false"{%endif%}{%endif%});
    printf(format, "xor_in", {%cfg_xor_in%});
    printf("%-16s = %s\\n", "reflect_out", {%if crc_reflect_out == Undefined%}{%cfg_reflect_out%} ? "true": "false"{%else%}{%if crc_reflect_out == True%}"true"{%else%}"false"{%endif%}{%endif%});
    printf(format, "xor_out", (unsigned int){%cfg_xor_out%});
    printf(format, "crc_mask", (unsigned int){%cfg_mask%});
    printf(format, "msb_mask", (unsigned int){%cfg_msb_mask%});
}

/**
 * \\brief      C main function.
 * \\return     0 on success, != 0 on error.
 *****************************************************************************/
int main({%if $undefined_parameters == True%}int argc, char *argv[]{%else%}void{%endif%})
{
{%if $undefined_parameters == True%}
    {%cfg_t%} cfg = {
{%if $crc_width == Undefined%}
            0,      /* width */
{%endif%}
{%if $crc_poly == Undefined%}
            0,      /* poly */
{%endif%}
{%if $crc_xor_in == Undefined%}
            0,      /* xor_in */
{%endif%}
{%if $crc_reflect_in == Undefined%}
            0,      /* reflect_in */
{%endif%}
{%if $crc_xor_out == Undefined%}
            0,      /* xor_out */
{%endif%}
{%if $crc_reflect_out == Undefined%}
            0,      /* reflect_out */
{%endif%}
{%if $crc_width == Undefined%}

            0,      /* crc_mask */
            0,      /* msb_mask */
{%endif%}
    };
{%endif%}
    {%crc_t%} crc;

{%if $undefined_parameters == True%}
    get_config(argc, argv, &cfg);
{%if $crc_algorithm == "table-driven"%}
    {%crc_table_gen_function%}(&cfg);
{%endif%}
{%endif%}
{%if $undefined_parameters == True%}
    crc = {%crc_init_function%}({%if $constant_crc_init == False%}&cfg{%endif%});
    crc = {%crc_update_function%}(&cfg, crc, (unsigned char *)str, strlen(str));
{%else%}
    crc = {%crc_init_function%}();
    crc = {%crc_update_function%}(crc, (unsigned char *)str, strlen(str));
{%endif%}
{%if $simple_crc_finalize_def != True%}
    crc = {%crc_finalize_function%}(&cfg, crc);
{%else%}
    crc = {%crc_finalize_function%}(crc);
{%endif%}

    if (verbose) {
        print_params({%if $undefined_parameters == True%}&cfg{%endif%});
    }
    printf("0x%lx\\n", (long)crc);
    return 0;
}
"""

        self.table["getopt_template"] = """\
{%if $crc_reflect_in == Undefined or $crc_reflect_out == Undefined%}
static {%c_bool%} atob(const char *str);
{%endif%}
{%if $crc_poly == Undefined or $crc_xor_in == Undefined or $crc_xor_out == Undefined%}
static int xtoi(const char *str);
{%endif%}
static int get_config(int argc, char *argv[], {%cfg_t%} *cfg);


{%if $crc_reflect_in == Undefined or $crc_reflect_out == Undefined%}
{%c_bool%} atob(const char *str)
{
    if (!str) {
        return 0;
    }
    if (isdigit(str[0])) {
        return ({%c_bool%})atoi(str);
    }
    if (tolower(str[0]) == 't') {
        return {%c_true%};
    }
    return {%c_false%};
}
{%endif%}

{%if $crc_poly == Undefined or $crc_xor_in == Undefined or $crc_xor_out == Undefined%}
int xtoi(const char *str)
{
    int ret = 0;

    if (!str) {
        return 0;
    }
    if (str[0] == '0' && tolower(str[1]) == 'x') {
        str += 2;
        while (*str) {
            if (isdigit(*str))
                ret = 16 * ret + *str - '0';
            else if (isxdigit(*str))
                ret = 16 * ret + tolower(*str) - 'a' + 10;
            else
                return ret;
            str++;
        }
    } else if (isdigit(*str)) {
        while (*str) {
            if (isdigit(*str))
                ret = 10 * ret + *str - '0';
            else
                return ret;
            str++;
        }
    }
    return ret;
}
{%endif%}


int get_config(int argc, char *argv[], {%cfg_t%} *cfg)
{
    int c;
    int this_option_optind;
    int option_index;
    static struct option long_options[] = {
        {"width",           1, 0, 'w'},
        {"poly",            1, 0, 'p'},
        {"reflect-in",      1, 0, 'n'},
        {"xor-in",          1, 0, 'i'},
        {"reflect-out",     1, 0, 'u'},
        {"xor-out",         1, 0, 'o'},
        {"verbose",         0, 0, 'v'},
        {"check-string",    1, 0, 's'},
        {"table-idx-with",  1, 0, 't'},
        {0, 0, 0, 0}
    };

    while (1) {
        this_option_optind = optind ? optind : 1;
        option_index = 0;

        c = getopt_long (argc, argv, "w:p:ni:uo:s:v", long_options, &option_index);
        if (c == -1)
            break;

        switch (c) {
            case 0:
                printf ("option %s", long_options[option_index].name);
                if (optarg)
                    printf (" with arg %s", optarg);
                printf ("\\n");
{%if $crc_width == Undefined%}
            case 'w':
                cfg->width = atoi(optarg);
                break;
{%endif%}
{%if $crc_poly == Undefined%}
            case 'p':
                cfg->poly = xtoi(optarg);
                break;
{%endif%}
{%if $crc_reflect_in == Undefined%}
            case 'n':
                cfg->reflect_in = atob(optarg);
                break;
{%endif%}
{%if $crc_xor_in == Undefined%}
            case 'i':
                cfg->xor_in = xtoi(optarg);
                break;
{%endif%}
{%if $crc_reflect_out == Undefined%}
            case 'u':
                cfg->reflect_out = atob(optarg);
                break;
{%endif%}
{%if $crc_xor_out == Undefined%}
            case 'o':
                cfg->xor_out = xtoi(optarg);
                break;
{%endif%}
            case 's':
                memcpy(str, optarg, strlen(optarg) < sizeof(str) ? strlen(optarg) + 1 : sizeof(str));
                str[sizeof(str) - 1] = '\\0';
                break;
            case 'v':
                verbose = {%c_true%};
                break;
            case 't':
                /* ignore --table_idx_with option */
                break;
            case '?':
                return -1;
            case ':':
                fprintf(stderr, "missing argument to option %c\\n", c);
                return -1;
            default:
                fprintf(stderr, "unhandled option %c\\n", c);
                return -1;
        }
    }
{%if $crc_width == Undefined%}
    cfg->msb_mask = 1 << (cfg->width - 1);
    cfg->crc_mask = (cfg->msb_mask - 1) | cfg->msb_mask;
{%endif%}

{%if $crc_poly == Undefined%}
    cfg->poly &= {%cfg_mask%};
{%endif%}
{%if $crc_xor_in == Undefined%}
    cfg->xor_in &= {%cfg_mask%};
{%endif%}
{%if $crc_xor_out == Undefined%}
    cfg->xor_out &= {%cfg_mask%};
{%endif%}
    return 0;
}\
"""


    # getTerminal
    ###############################################################################
    def getTerminal(self, id):
        """
        return the expanded terminal, if it exists or None otherwise
        """

        if id != None:
            if id == "":
                return ""
            if self.table.has_key(id):
                return self.table[id]
        raise LookupError

    # __pretty_str
    ###############################################################################
    def __pretty_str(self, value):
        """
        Return a value of width bits as a pretty string.
        """
        if value == None:
            return "Undefined"
        return str(value)

    # __pretty_hex
    ###############################################################################
    def __pretty_hex(self, value, width = None):
        """
        Return a value of width bits as a pretty hexadecimal formatted string.
        """
        if value == None:
            return "Undefined"
        if width == None:
            return "0x%x" % value
        width = (width + 3) / 4
        str = "0x%%0%dx" % width
        return str % value

    # __pretty_bool
    ###############################################################################
    def __pretty_bool(self, value):
        """
        Return a boolen value of width bits as a pretty formatted string.
        """
        if value == None:
            return "Undefined"
        if value:
            return "True"
        else:
            return "False"

    # __pretty_hdrprotection
    ###############################################################################
    def __pretty_hdrprotection(self):
        """
        Return the name of a C header protection (e.g. __CRC_IMPLEMENTATION_H__)
        """
        tr_str = ""
        for i in range(256):
            if chr(i).isalpha():
                tr_str += chr(i).upper()
            else:
                tr_str += '_'
        if self.opt.OutputFile == None:
            str = "stdout"
        else:
            str = self.opt.OutputFile
        str = os.path.basename(str)
        str = str.upper()
        str = str.translate(tr_str)
        return "__" + str + "__"

    # __get_init_value
    ###############################################################################
    def __get_init_value(self):
        """
        Return the init value of a C implementation, according to the selected algorithm and
        to the given options
        If no default option is given for a given parameter, value in the cfg_t structure must be used.
        """
        if self.opt.Algorithm != self.opt.Algo_Bit_by_Bit and self.opt.Algorithm != self.opt.Algo_Bit_by_Bit_Fast and self.opt.Algorithm != self.opt.Algo_Table_Driven:
            init = 0
        elif self.opt.Algorithm == self.opt.Algo_Bit_by_Bit:
            if self.opt.ReflectIn == None or self.opt.XorIn == None or self.opt.Width == None or self.opt.Poly == None:
                return None
            register = self.opt.XorIn
            for j in range(self.opt.Width):
                bit = register & 1
                if bit != 0:
                    register = ((register ^ self.opt.Poly) >> 1) | self.opt.MSB_Mask
                else:
                    register = register >> 1
            init = register & self.opt.Mask
        elif self.opt.Algorithm == self.opt.Algo_Bit_by_Bit_Fast:
            if self.opt.XorIn == None:
                return None
            init = self.opt.XorIn
        elif self.opt.Algorithm == self.opt.Algo_Table_Driven:
            if self.opt.ReflectIn == None or self.opt.XorIn == None or self.opt.Width == None:
                return None
            if self.opt.ReflectIn:
                crc = Crc(self.opt)
                init = crc.reflect(self.opt.XorIn, self.opt.Width)
            else:
                init = self.opt.XorIn
        else:
            init = 0
        return self.__pretty_hex(init, self.opt.Width)

    # __get_table_init
    ###############################################################################
    def __get_table_init(self):
        """
        Return the precalculated CRC table for the table_driven implementation
        """
        if self.opt.Algorithm != self.opt.Algo_Table_Driven:
            return "0"
        if self.opt.UndefinedCrcParameters:
            return "0"
        crc = Crc(self.opt)
        tbl = crc.gen_table()
        if self.opt.Width >= 32:
            values_per_line = 4
        elif self.opt.Width >= 16:
            values_per_line = 8
        else:
            values_per_line = 16
        out  = ""
        for i in range(self.opt.TableWidth):
            if i % values_per_line == 0:
                out += "    "
            if i == (self.opt.TableWidth - 1):
                out += "%s" % self.__pretty_hex(tbl[i], self.opt.Width)
            elif i % values_per_line == (values_per_line - 1):
                out += "%s,\n" % self.__pretty_hex(tbl[i], self.opt.Width)
            else:
                out += "%s, " % self.__pretty_hex(tbl[i], self.opt.Width)
        return out

