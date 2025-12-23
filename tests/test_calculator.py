"""Tests for calculator module."""

import pytest
from src.calculator import add, subtract, multiply, divide


class TestCalculator:
    """Test suite for calculator functions."""

    def test_add(self):
        assert add(2, 3) == 5
        assert add(-1, 1) == 0
        assert add(0, 0) == 0

    def test_subtract(self):
        assert subtract(5, 3) == 2
        assert subtract(1, 1) == 0
        assert subtract(0, 5) == -5

    def test_multiply(self):
        assert multiply(3, 4) == 12
        assert multiply(-2, 3) == -6
        assert multiply(0, 100) == 0

    def test_divide(self):
        assert divide(10, 2) == 5
        assert divide(7, 2) == 3.5
        assert divide(0, 5) == 0

    def test_divide_by_zero(self):
        """Test that dividing by zero raises ZeroDivisionError.

        Contract: divide(a, b) raises ZeroDivisionError when b==0.
        """
        with pytest.raises(ZeroDivisionError):
            divide(5, 0)
        with pytest.raises(ZeroDivisionError):
            divide(-5, 0)
        with pytest.raises(ZeroDivisionError):
            divide(0, 0)

    def test_divide_zero_numerator(self):
        """Test divide(0, b) returns 0 when b != 0."""
        assert divide(0, 5) == 0
        assert divide(0, -5) == 0
        assert divide(0, 0.5) == 0

    def test_divide_negative_numbers(self):
        """Test sign correctness for negative operands."""
        assert divide(-10, 2) == -5  # -a / b = negative
        assert divide(10, -2) == -5  # a / -b = negative
        assert divide(-10, -2) == 5  # -a / -b = positive

    def test_divide_floats(self):
        """Test float inputs and precision.

        Contract: divide() accepts float inputs and returns float.
        """
        assert divide(1.5, 0.5) == 3.0
        assert divide(0.1, 0.1) == pytest.approx(1.0)  # 浮点精度
        assert divide(1, 3) == pytest.approx(0.333333, rel=1e-5)
