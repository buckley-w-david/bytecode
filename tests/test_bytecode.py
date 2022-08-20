import bytecode
from bytecode.symbols import *


@bytecode.bytecode(constants=["test"])
def return_constant():
    LOAD_CONST, 1
    RETURN_VALUE


def test_basic():
    assert return_constant() == "test"


@bytecode.bytecode()
def return_arg(a):
    LOAD_FAST, 0
    RETURN_VALUE


def test_arg():
    assert return_arg("test") == "test"
    assert return_arg(10) == 10


@bytecode.bytecode()
def sum(a, b):
    LOAD_FAST, 0
    LOAD_FAST, 1
    BINARY_ADD
    RETURN_VALUE


def test_sum():
    assert sum(5, 5) == 10
    assert sum("a", "b") == "ab"


@bytecode.bytecode(constants=[5])
def return_variable():
    LOAD_CONST, 1
    STORE_FAST, 0

    LOAD_FAST, 0
    RETURN_VALUE


def test_variable():
    assert return_variable() == 5
