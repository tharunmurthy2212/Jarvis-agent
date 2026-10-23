import pytest
from app.tools.calculator import SafeCalculator


def test_basic_arithmetic():
    res = SafeCalculator.evaluate("2 + 3 * 4")
    assert res["result"] == 14

    res2 = SafeCalculator.evaluate("(100 - 25) / 5")
    assert res2["result"] == 15


def test_advanced_math_functions():
    res = SafeCalculator.evaluate("sqrt(64) + sin(0) + cos(0)")
    assert res["result"] == 9

    res_pi = SafeCalculator.evaluate("round(pi, 4)")
    assert res_pi["result"] == 3.1416


def test_power_and_factorial():
    res = SafeCalculator.evaluate("2^8")
    assert res["result"] == 256

    res_fact = SafeCalculator.evaluate("factorial(5)")
    assert res_fact["result"] == 120


def test_division_by_zero():
    res = SafeCalculator.evaluate("10 / 0")
    assert "error" in res
    assert "Division by zero" in res["error"]


def test_unsafe_expression_rejection():
    # Attempt import
    res1 = SafeCalculator.evaluate("__import__('os').system('dir')")
    assert "error" in res1

    # Attempt builtins
    res2 = SafeCalculator.evaluate("open('file.txt')")
    assert "error" in res2

    # Attempt exec
    res3 = SafeCalculator.evaluate("exec('x = 1')")
    assert "error" in res3
