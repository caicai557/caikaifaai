"""Contract tests - executable API contract enforcement.

These tests serve as the machine-readable gate for API contracts.
If a contract test fails, the contract has been violated.

See: .council/CONTRACTS.md for human-readable contract documentation.
"""

import pytest
from src.calculator import add, subtract, multiply, divide


class TestDivideContract:
    """Contract: divide(a, b) raises ZeroDivisionError when b == 0."""

    def test_contract_divide_by_zero_raises_zero_division_error(self):
        """Enforce: b == 0 → ZeroDivisionError."""
        with pytest.raises(ZeroDivisionError):
            divide(1, 0)

    def test_contract_divide_by_zero_any_numerator(self):
        """Enforce: any a with b == 0 → ZeroDivisionError."""
        with pytest.raises(ZeroDivisionError):
            divide(0, 0)
        with pytest.raises(ZeroDivisionError):
            divide(-1, 0)
        with pytest.raises(ZeroDivisionError):
            divide(1.5, 0)

    def test_contract_divide_returns_float(self):
        """Enforce: divide() returns float."""
        result = divide(10, 3)
        assert isinstance(result, float)

    def test_contract_divide_accepts_numeric_types(self):
        """Enforce: divide() accepts int and float."""
        assert divide(10, 2) == 5.0  # int, int
        assert divide(10.0, 2) == 5.0  # float, int
        assert divide(10, 2.0) == 5.0  # int, float
        assert divide(10.0, 2.0) == 5.0  # float, float


class TestAddContract:
    """Contract: add(a, b) returns a + b."""

    def test_contract_add_returns_sum(self):
        assert add(1, 2) == 3

    def test_contract_add_negative_numbers(self):
        """Enforce: add() handles negative numbers correctly."""
        assert add(-1, -2) == -3
        assert add(-5, 3) == -2
        assert add(5, -3) == 2

    def test_contract_add_zero(self):
        """Enforce: add(a, 0) == a and add(0, b) == b."""
        assert add(5, 0) == 5
        assert add(0, 5) == 5
        assert add(0, 0) == 0

    def test_contract_add_floats(self):
        """Enforce: add() accepts and returns floats."""
        assert add(1.5, 2.5) == 4.0
        assert add(0.1, 0.2) == pytest.approx(0.3)


class TestSubtractContract:
    """Contract: subtract(a, b) returns a - b."""

    def test_contract_subtract_returns_difference(self):
        assert subtract(5, 3) == 2

    def test_contract_subtract_negative_numbers(self):
        """Enforce: subtract() handles negative numbers correctly."""
        assert subtract(-5, -3) == -2
        assert subtract(-5, 3) == -8
        assert subtract(5, -3) == 8

    def test_contract_subtract_zero(self):
        """Enforce: subtract(a, 0) == a and subtract(0, b) == -b."""
        assert subtract(5, 0) == 5
        assert subtract(0, 5) == -5
        assert subtract(0, 0) == 0

    def test_contract_subtract_floats(self):
        """Enforce: subtract() accepts and returns floats."""
        assert subtract(5.5, 2.5) == 3.0
        assert subtract(0.3, 0.1) == pytest.approx(0.2)


class TestMultiplyContract:
    """Contract: multiply(a, b) returns a * b."""

    def test_contract_multiply_returns_product(self):
        assert multiply(3, 4) == 12

    def test_contract_multiply_by_zero(self):
        """Enforce: multiply(a, 0) == 0 and multiply(0, b) == 0."""
        assert multiply(5, 0) == 0
        assert multiply(0, 5) == 0
        assert multiply(0, 0) == 0

    def test_contract_multiply_negative_numbers(self):
        """Enforce: multiply() handles negative numbers correctly."""
        assert multiply(-3, 4) == -12
        assert multiply(3, -4) == -12
        assert multiply(-3, -4) == 12

    def test_contract_multiply_floats(self):
        """Enforce: multiply() accepts and returns floats."""
        assert multiply(2.5, 4) == 10.0
        assert multiply(0.1, 0.1) == pytest.approx(0.01)
