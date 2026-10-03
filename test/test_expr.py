#!/usr/bin/env python3

from pycrc import expr


def test_sub_simplify():
    # A subtraction of two integers is folded into a constant.
    assert str(expr.Sub(5, 3).simplify()) == "2"
    # Subtracting zero leaves the operand unchanged.
    assert str(expr.Sub("x", 0).simplify()) == "x"
    # 0 - x must NOT be simplified to x (this would change the value).
    assert str(expr.Sub(0, "x").simplify()) == "0 - x"


def test_other_simplifications():
    assert str(expr.Add("x", 0).simplify()) == "x"
    assert str(expr.Mul("x", 0).simplify()) == "0"
    assert str(expr.Mul("x", 1).simplify()) == "x"
    assert str(expr.Xor("x", 0).simplify()) == "x"
    assert str(expr.And("x", 0).simplify()) == "0"
    assert str(expr.Shl("x", 0).simplify()) == "x"
    assert str(expr.Shr("x", 0).simplify()) == "x"
