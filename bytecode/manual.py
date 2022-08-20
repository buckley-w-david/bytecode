__version__ = "0.1.0"

from enum import Enum, auto
from types import CodeType, FunctionType
import dis
import io

_LOAD_GLOBAL = dis.opname.index("LOAD_GLOBAL")
_LOAD_DEREF = dis.opname.index("LOAD_DEREF")
_LOAD_CONST = dis.opname.index("LOAD_CONST")
_POP_TOP = dis.opname.index("POP_TOP")
_BUILD_TUPLE = dis.opname.index("BUILD_TUPLE")


class State(Enum):
    SCAN_INSTRUCTION = auto()
    SCAN_ARGUMENT = auto()
    SKIP_TUPLE = auto()
    POP_TOP = auto()


_SENTINEL = object()

# TODO: Probably need to expose more arguments here for other properties
def bytecode(
    constants=_SENTINEL,
    names=_SENTINEL,
):
    def inner(f):
        bc = dis.Bytecode(f)
        instructions = list(bc)
        state = State.SCAN_INSTRUCTION
        ni = [None, 0]

        writer = io.BytesIO()
        linetable_writer = io.BytesIO()
        last_pos = 0
        current_pos = 0
        # We ignore the last two instructions because they will be the default return
        for instruction in instructions[:-2]:
            if state == State.SCAN_INSTRUCTION:
                if (
                    instruction.opcode == _LOAD_GLOBAL
                    or instruction.opcode == _LOAD_DEREF
                ):
                    ni[0] = dis.opname.index(instruction.argval)
                    state = State.SCAN_ARGUMENT
                else:
                    raise ValueError(
                        "Cannot parse instruction, expected an OPCODE, got %s"
                        % instruction.opname
                    )
            elif state == State.SCAN_ARGUMENT:
                if instruction.opcode == _LOAD_CONST:
                    ni[1] = instruction.argval
                    state = State.SKIP_TUPLE
                elif instruction.opcode == _POP_TOP:
                    state = State.SCAN_INSTRUCTION

                    # TODO: Look into how linetable actually works
                    # For now pulled logic from https://medium.com/@yonatanzunger/advanced-python-achieving-high-performance-with-code-generation-796b177ec79
                    current_pos = writer.tell()
                    linetable_writer.write(bytes([current_pos - last_pos, 1]))
                    last_pos = current_pos

                    writer.write(bytes(ni))
                    ni = [None, 0]
                else:
                    raise ValueError(
                        "Cannot parse instruction, expected an argument, got %s"
                        % instruction.opname
                    )
            elif state == State.SKIP_TUPLE:
                if instruction.opcode == _BUILD_TUPLE:
                    state = State.POP_TOP
                else:
                    raise ValueError(
                        "Cannot parse instruction, expected an TUPLE, got %s"
                        % instruction.opname
                    )
            elif state == State.POP_TOP:
                if instruction.opcode == _POP_TOP:
                    state = State.SCAN_INSTRUCTION

                    current_pos = writer.tell()
                    linetable_writer.write(bytes([current_pos - last_pos, 1]))
                    last_pos = current_pos

                    writer.write(bytes(ni))
                    ni = [None, 0]
                else:
                    raise ValueError(
                        "Cannot parse instruction, expected an argument, got %s"
                        % instruction.opname
                    )
            else:
                raise ValueError("This should be impossible")

        bytecode = writer.getvalue()
        linetable = linetable_writer.getvalue()

        co_consts = bc.codeobj.co_consts if constants is _SENTINEL else constants
        if co_consts[0] is not None:
            co_consts = (None, *constants)

        co_names = bc.codeobj.co_names if names is _SENTINEL else names

        code = bc.codeobj.replace(
            co_code=bytecode,
            co_linetable=linetable,
            co_consts=tuple(co_consts),
            co_names=tuple(co_names),
        )

        return FunctionType(
            code, f.__globals__, f.__name__, f.__defaults__, f.__closure__
        )

    return inner
