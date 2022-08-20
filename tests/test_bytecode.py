import bytecode
from bytecode.symbols import *


def test_basic():
    @bytecode.bytecode(constants=["test"])
    def return_constant():
        LOAD_CONST, 1
        RETURN_VALUE

    assert return_constant() == "test"


def test_arg():
    @bytecode.bytecode()
    def return_arg(a):
        LOAD_FAST, 0
        RETURN_VALUE

    assert return_arg("test") == "test"
    assert return_arg(10) == 10


def test_sum():
    @bytecode.bytecode()
    def sum(a, b):
        LOAD_FAST, 0
        LOAD_FAST, 1
        BINARY_ADD
        RETURN_VALUE

    assert sum(5, 5) == 10
    assert sum("a", "b") == "ab"


def test_variable():
    @bytecode.bytecode(constants=[5])
    def return_variable():
        LOAD_CONST, 1
        STORE_FAST, 0

        LOAD_FAST, 0
        RETURN_VALUE

    assert return_variable() == 5

def test_extended():
    const_arg = 0x1234567
    constants = [None] * (const_arg + 1)
    constants[const_arg] = "foo"

    @bytecode.bytecode(constants=constants)
    def return_extended():
        EXTENDED_ARG, 0x1
        EXTENDED_ARG, 0x23
        EXTENDED_ARG, 0x45
        LOAD_CONST, 0x67
        RETURN_VALUE

    assert return_extended() == "foo"

def test_factorial():
    # This test is mostly just to do something a little more complex
    @bytecode.bytecode(constants=[1])
    def factorial(n):
        LOAD_CONST, 1
        LOAD_FAST, 0

        DUP_TOP
        ROT_THREE
        INPLACE_MULTIPLY
        ROT_TWO

        LOAD_CONST, 1
        INPLACE_SUBTRACT

        JUMP_IF_TRUE_OR_POP, 2

        RETURN_VALUE

    assert factorial(5) == 120

def test_names(capsys):
    @bytecode.bytecode(constants=["Hello, World!"], names=["print"])
    def print_hello():
        LOAD_GLOBAL, 0
        LOAD_CONST, 1
        CALL_FUNCTION, 1
        RETURN_VALUE

    print_hello()
    captured = capsys.readouterr()
    assert captured.out == "Hello, World!\n"
