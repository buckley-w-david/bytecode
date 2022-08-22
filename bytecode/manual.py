__version__ = "0.2.0"

from types import FunctionType
import dis
import io

_SYMBOLS = {name: i for i, name in enumerate(dis.opname)}
_LOAD_GLOBAL = _SYMBOLS["LOAD_GLOBAL"]
_LOAD_DEREF = _SYMBOLS["LOAD_DEREF"]
_LOAD_CONST = _SYMBOLS["LOAD_CONST"]
_POP_TOP = _SYMBOLS["POP_TOP"]
_BUILD_TUPLE = _SYMBOLS["BUILD_TUPLE"]
_SENTINEL = object()


# TODO: Probably need to expose more arguments here for other properties
def bytecode(
    constants=_SENTINEL,
    names=_SENTINEL,
):
    def inner(f):
        bc = dis.Bytecode(f)
        instructions = list(bc)
        state = 0
        ni = [None, 0]

        writer = io.BytesIO()
        linetable_writer = io.BytesIO()
        last_pos = 0
        current_pos = 0
        # We ignore the last two instructions because they will be the default return
        for instruction in instructions[:-2]:
            if state == 0:
                if (
                    instruction.opcode == _LOAD_GLOBAL
                    or instruction.opcode == _LOAD_DEREF
                ):
                    ni[0] = _SYMBOLS[instruction.argval]
                    state = 1
                else:
                    raise ValueError(
                        "Cannot parse instruction, expected an OPCODE, got %s"
                        % instruction.opname
                    )
            elif state == 1:
                if instruction.opcode == _LOAD_CONST:
                    ni[1] = instruction.argval
                    state = 2
                elif instruction.opcode == _POP_TOP:
                    state = 0

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
            elif state == 2:
                if instruction.opcode == _BUILD_TUPLE:
                    state = 3
                else:
                    raise ValueError(
                        "Cannot parse instruction, expected an TUPLE, got %s"
                        % instruction.opname
                    )
            elif state == 3:
                if instruction.opcode == _POP_TOP:
                    state = 0

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


def mixed_bytecode(f):
    bc = dis.Bytecode(f)
    instructions = list(bc)
    ni = [None, 0]

    writer = io.BytesIO()
    state = 0

    for instruction in instructions:
        if state == 0:
            if (
                instruction.opcode == _LOAD_GLOBAL or instruction.opcode == _LOAD_DEREF
            ) and instruction.argval in _SYMBOLS:
                ni[0] = _SYMBOLS[instruction.argval]
                state = 1
            else:
                writer.write(bytes([instruction.opcode, instruction.arg or 0]))
        elif state == 1:
            if instruction.opcode == _POP_TOP:
                writer.write(bytes(ni))
                state = 0
            else:
                ni[1] = instruction.argval
                state = 2
        elif state == 2:
            state = 3
        elif state == 3:
            writer.write(bytes(ni))
            state = 0
        else:
            raise Exception("Impossible")

    bytecode = writer.getvalue()

    code = bc.codeobj.replace(
        co_code=bytecode,
    )

    return FunctionType(code, f.__globals__, f.__name__, f.__defaults__, f.__closure__)
