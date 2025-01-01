from paramclass.common import UNDEFINED, object_dunder_methods, type_dunder_methods
from paramclass.linker import Linker, dunder_tracer_closed, get_linker

class Mask:
    def __init__(self, name, val):
        self._key = name
        self._val = val
        self._trace_type = get_linker(val)
        self._accessed = False

    def __call__(self, *args, **kwargs):
        self._accessed = True
        return self._trace_type(self._val)(*args, **kwargs)
    
    def __getattr__(self, name):
        self._accessed = True
        return getattr(self._trace_type(self._val), name)
    
    def __getitem__(self, key):
        self._accessed = True
        return self._trace_type(self._val)[key]
    
    def __repr__(self):
        return 'Shadowed ' + self._key + ': ' + str(self._key)

class TypeMaskMeta(type):
    def __new__(cls, name, bases, dct):
        dunders = {dunder_name:dunder_tracer_closed(dunder_name) for dunder_name in type_dunder_methods}
        dct.update(dunders)
        return super().__new__(cls, name, bases, dct)

class TypeMask(Mask, metaclass=TypeMaskMeta):
    def __getitem__(self, key):
        return self._val[key]

class ObjectMaskMeta(type):
    def __new__(cls, name, bases, dct):
        for func_name in object_dunder_methods:
            dct[func_name] = dunder_tracer_closed(func_name)
        
        return super().__new__(cls, name, bases, dct)

class ObjectMask(Mask, metaclass=ObjectMaskMeta):
    pass

class MaskDict(dict):
    whitelist = ('__name__', '__builtins__', '__doc__', '__package__', '__loader__', '__spec__', '__file__', '__cached__', 'classmethod', 'staticmethod', 'property')
    def __init__(self, frame, bases=None):
        super().__init__()
        self.shadow_dict = {**frame.f_locals, **frame.f_globals, **frame.f_builtins}
        if bases is None:
            bases = []
        for base in bases:
            self[base.__name__] = base

    def __setitem__(self, key, value):
        if isinstance(value, Linker):
            value.__close__(key)
        super().__setitem__(key, value)
    
    def __getitem__(self, key):
        if super().__contains__(key):
            return super().get(key)
        else:
            val = super().get(key, UNDEFINED)
            if val is not UNDEFINED:
                return val
            elif key.startswith('__') or key in MaskDict.whitelist:
                val = self.shadow_dict[key]
                self[key] = val
                return val
            elif key in self.shadow_dict:
                val = self.shadow_dict[key]
                if isinstance(val, type):
                    val = TypeMask(key, val)
                else:
                    val = ObjectMask(key, val)
                self[key] = val
                return val
            else:
                raise AttributeError(f'Attribute {key} not found')
    
    def __purge__(self):
        purge_list = []
        for key, value in self.items():
            if isinstance(value, TypeMask):
                purge_list.append(key)
        for key in purge_list:
            del self[key]
