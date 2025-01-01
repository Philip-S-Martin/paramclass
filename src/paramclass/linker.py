from paramclass.common import UNDEFINED, object_dunder_methods

def resolve_values(value, parent):
    if isinstance(value, Linker):
        if getattr(value, '_name', None) != None:
            return getattr(parent, value._name)
        else:
            return value.__execute__(parent)
    elif isinstance(value, tuple):
        return tuple(resolve_values(v, parent) for v in value)
    elif isinstance(value, list):
        return [resolve_values(v, parent) for v in value]
    elif isinstance(value, dict):
        return {k:resolve_values(v, parent) for k,v in value.items()}
    else:
        return value

def close_values(value):
    if isinstance(value, Linker):
        value.__close__(None)
    elif isinstance(value, tuple) or isinstance(value, list):
        for v in value:
            close_values(v)
    elif isinstance(value, dict):
        for v in value.values():
            close_values(v)

class LinkAttr:
    def __init__(self, name):
        self._name = name
        
    def do(self, val, parent):
        return getattr(val, self._name)

class LinkFunc:
    def __init__(self, *args, **kwargs):
        close_values(args)
        close_values(kwargs)
        self._args = args
        self._kwargs = kwargs
    
    def do(self, val, parent):
        return val(*resolve_values(self._args, parent), **resolve_values(self._kwargs, parent))

def dunder_tracer_open(method_name):
    def handler(self, *args, **kwargs):
        if self._closed:
            return getattr(Linker(self), method_name)(*args, **kwargs)
        self._links.append(LinkAttr(method_name))
        self._links.append(LinkFunc(*args, **kwargs))
        return self
    return handler

def dunder_tracer_closed(method_name):
    def handler(self, *args, **kwargs):
        if self._closed:
            raise RuntimeError(f'Attempted to use closed {self.__class__.__name__}')
        return getattr(self._val, method_name)(*args, **kwargs)
    return handler

class LinkerMeta(type):
    def __new__(cls, name, bases, dct):
        dunders = {dunder_name:dunder_tracer_open(dunder_name) for dunder_name in object_dunder_methods}
        dct.update(dunders)
        return super().__new__(cls, name, bases, dct)

def closed_func(name):
    def call(self:Linker, *args, **kwargs):
        return getattr(Linker(self), name)
    return call

class Linker(metaclass=LinkerMeta):
    def __init__(self, base):
        self._links = []
        self._base = base
        self._closed = False
        
    def __call__(self, *args, **kwargs):
        self._links.append(LinkFunc(*args, **kwargs))
        return self
    
    def __getattr__(self, name):
        if (not isinstance(self._base, Linker) 
            and len(self._links) == 0 
            and isinstance(val := getattr(self._base, name), type)):
            return get_linker(val)(val)
        else:
            self._links.append(LinkAttr(name))
        return self
    
    def __close__(self, name):
        if self._closed:
            return
        self._name = name
        self._closed = True
        self.__call__ = closed_func('__call__')
        self.__getattr__ = closed_func('__getattr__')
    
    def __execute__(self, parent):
        val = self._base
        if isinstance(val, Linker):
            val = getattr(parent, val._name)
        for step in self._links:
            val = step.do(val, parent)
        return val

__supported_linkers__ = dict()
def add_linker(base, tracer):
    if __supported_linkers__.get(base, UNDEFINED) is not UNDEFINED:
        raise RuntimeError(f'Attempted to register tracer for {base} twice')
    __supported_linkers__[base] = tracer
def get_linker(base):
    return __supported_linkers__.get(base, Linker)
