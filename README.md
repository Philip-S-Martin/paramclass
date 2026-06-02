# paramclass

`paramclass` is a small Python library for making imperative construction APIs
usable from declarative, class-body designs.

Many modeling libraries are built around imperative Python calls: create an
object, attach components, call helper functions, mutate state. That is
flexible, but it can make reusable model definitions harder to lint, statically
analyze, compare, and package. `paramclass` lets you keep those ordinary Python
calls while presenting the model definition as a compact class.

It lets you write dependencies once:

```python
from paramclass import ParamClass


class Demo(ParamClass):
    x = 2
    y = x + 3


assert Demo().y == 5
assert Demo(x=10).y == 13
```

The goal is to make reusable object construction feel lightweight and
inspectable: public class attributes become overrideable parameters, and
expressions that reference those parameters are evaluated when an instance is
built.

## Project Timeline

`paramclass` was developed during 2023-2024 and has been used in production
workflows since 2023. Public packaging was added in 2025, and public
documentation was added in 2026 to make the project easier to evaluate, install,
and reuse outside its original environment.

## Install

```bash
pip install paramclass
```

For local development:

```bash
uv sync --extra dev
uv run --extra dev pytest
```

## Why

Python classes are a natural place to describe reusable structure. They give
linters, type checkers, code search, review tools, and documentation generators
a stable surface to inspect.

But normal class attributes are evaluated immediately. That makes dependent
defaults hard to override cleanly:

```python
class Normal:
    x = 2
    y = x + 3


normal = Normal()
normal.x = 10
assert normal.y == 5
```

`ParamClass` keeps the class-body syntax, but defers parameter expressions until
instance construction. That creates a bridge between two useful styles:

- declarative definitions that are easy to read, lint, review, and analyze
- imperative constructors and modeling APIs that already exist in the Python
  ecosystem

This is especially useful for libraries such as Pyomo or neural network modeling
toolkits, where model pieces are often assembled through Python calls but teams
still want code that can be scanned, checked, and reused consistently.

## Examples

### Literal Parameters

```python
class Config(ParamClass):
    width = 128
    height = 64
    size = width * height


assert Config().size == 8192
assert Config(width=256).size == 16384
```

### Function Calls

```python
def label(name, version):
    return f"{name}:{version}"


class Job(ParamClass):
    name = "trainer"
    version = 1
    tag = label(name, version)


assert Job().tag == "trainer:1"
assert Job(version=2).tag == "trainer:2"
```

### Collections

Links can be nested inside lists, tuples, and dictionaries.

```python
class Batch(ParamClass):
    size = 32
    settings = {
        "train": [size, size * 2],
        "eval": (size // 2),
    }


assert Batch(size=64).settings == {
    "train": [64, 128],
    "eval": 32,
}
```

### Nested ParamClasses

`ParamClass` instances can be nested and referenced by later parameters.

```python
class Layer(ParamClass):
    width = 128
    params = width * 4


class Model(ParamClass):
    layer = Layer()
    total_params = layer.params + 10


assert Model().total_params == 522
assert Model(layer=Layer(width=256)).total_params == 1034
```

### Methods Stay Methods

Normal methods, properties, static methods, and class methods are not treated as
parameters.

```python
class Counter(ParamClass):
    value = 2

    @property
    def doubled(self):
        return self.value * 2


assert Counter(value=5).doubled == 10
```

## How It Works

`ParamClass` uses a custom class namespace while the class body is being
defined. Public assignments are captured as deferred parameter definitions.
References between parameters become links that are resolved during instance
construction, after any keyword overrides have been applied.

The result is a declarative class definition backed by ordinary Python execution
at build time.

This means:

- public class-body assignments define instance parameters
- keyword arguments override those parameters
- dependent expressions are rebuilt from the final parameter values
- methods and descriptors remain normal class members

## Current Limitations

Some Python language constructs cannot be deferred because they require an
immediate truth value during class creation. In particular, `and`, `or`, and
`not` are not traceable in the same way as arithmetic and comparison operators.

Use explicit comparisons or helper functions when you need deferred boolean
logic.

## Testing

```bash
uv run --extra dev pytest
```
