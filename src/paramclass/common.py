dunder_math = {
    '__add__', '__radd__', '__sub__', '__rsub__', '__eq__', '__ne__',
    '__lt__', '__gt__', '__le__', '__ge__',
    '__neg__', '__mod__', '__rmod__', '__pow__', '__rpow__',
    '__divmod__', '__rdivmod__',
    '__floordiv__', '__rfloordiv__', '__truediv__', '__rtruediv__'
}

dunder_collection = {
    '__getitem__', '__len__', '__contains__'
}

dunder_bitwise = {
    '__lshift__', '__rlshift__', '__rshift__', '__rrshift__',
    '__and__', '__rand__', '__xor__', '__rxor__', '__or__', '__ror__'
}

dunder_string = {
    '__str__', '__format__'
}

dunder_special = {
    '__bool__', '__hash__'
}

object_dunder_methods = dunder_math | dunder_collection | dunder_bitwise | dunder_string | dunder_special
type_dunder_methods = dunder_math | dunder_bitwise | dunder_string


def builtins_dict():
    if isinstance(__builtins__, dict):
        builtins_dict = __builtins__
    else:
        builtins_dict = __builtins__.__dict__

    return {k:v for k,v in builtins_dict.items()}

UNDEFINED = object()