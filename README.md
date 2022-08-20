# bytecode

Write python functions directly with bytecode

```python
>>> import bytecode
>>> @bytecode.bytecode()
... def sum(a, b):
...     LOAD_FAST, 0
...     LOAD_FAST, 1
...     BINARY_ADD
...     RETURN_VALUE

>>> sum(5, 6)
11
```
