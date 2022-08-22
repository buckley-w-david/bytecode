import bytecode
from bytecode.symbols import *


def test_basic():
    """
    def return_constant():
        return "test"
    """

    @bytecode.bytecode(constants=["test"])
    def return_constant():
        LOAD_CONST, 1
        RETURN_VALUE

    assert return_constant() == "test"


def test_arg():
    """
    def return_arg(a):
        return a
    """

    @bytecode.bytecode()
    def return_arg(a):
        LOAD_FAST, 0
        RETURN_VALUE

    assert return_arg("test") == "test"
    assert return_arg(10) == 10


def test_sum():
    """
    def sum(a, b):
        return a + b
    """

    @bytecode.bytecode()
    def sum(a, b):
        LOAD_FAST, 0
        LOAD_FAST, 1
        BINARY_ADD
        RETURN_VALUE

    assert sum(5, 5) == 10
    assert sum("a", "b") == "ab"


def test_variable():
    """
    def return_variable():
        a = 5
        return a
    """

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

    """
    def return_extended():
        { Somehow define more than 19,000,000 constants }
        return { the last of those constants }
    """

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
    """
    Similar to this, but not exactly, since the bytecode version does it all on the stack
    def factorial(n):
        result = 1
        while n:
            result *= n
            n -= 1
        return result
    """

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
    """
    def print_hello():
        print("Hello, World!")
    """

    @bytecode.bytecode(constants=["Hello, World!"], names=["print"])
    def print_hello():
        LOAD_GLOBAL, 0
        LOAD_CONST, 1
        CALL_FUNCTION, 1
        RETURN_VALUE

    print_hello()
    captured = capsys.readouterr()
    assert captured.out == "Hello, World!\n"


def test_mixed(capsys):
    """
    def f(a):
        while a:
            print(a)
            a -= 1
        return a
    """

    @bytecode.mixed_bytecode
    def f(a):
        print(a)
        a -= 1
        LOAD_FAST, 0
        POP_JUMP_IF_TRUE, 0
        LOAD_FAST, 0
        RETURN_VALUE

    assert f(5) == 0
    captured = capsys.readouterr()
    assert captured.out == "5\n4\n3\n2\n1\n"
