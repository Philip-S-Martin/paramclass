from paramclass.mask import MaskDict
from paramclass.linker import Linker
from paramclass.common import UNDEFINED
from typing import TypeVar, Generic
import inspect

class ParamClassMeta(type):
    @classmethod
    def __prepare__(metacls, name, bases, **kwds):
        for base in bases:
            if not (issubclass(base, ParamClass) or base is object or base is Generic):
                raise RuntimeError(f'ParamClass {name} is a subclass of {base.__name__}, which is not a ParamClass')
        return MaskDict(inspect.currentframe().f_back, bases)

    def __new__(cls, name, bases, build_namespace:MaskDict, **kwds):
        build_namespace.__purge__()
        namespace = dict(build_namespace)
        namespace['__build_order__'] = tuple(k for k,v in build_namespace.items() if isinstance(v, Linker))
        return super().__new__(cls, name, bases, namespace, **kwds)
    
    def __init__(cls_self, name, bases, namespace, **kwds):
        if namespace.get('__build_order__', UNDEFINED) is not UNDEFINED:
            raise RuntimeError(f'ParamClass __build_order__ attribute is already defined. This is reserved for ParamClass __init__ behavior.')
        
        def __init__(self, *args, **kwargs):
            outer_class = kwargs.pop('__outer_class__', True)
            self._autobuild = True
            if outer_class and getattr(cls_self, '__setup__', UNDEFINED) is not UNDEFINED:
                cls_self.__setup__(self, *args, **kwargs)
            
            self._overrides = kwargs
            if outer_class and self._autobuild:
                self.__build__()
            
        def __build__(self):
            for base in bases:
                if issubclass(base, ParamClass):
                    base.__build__(self)
            for key in getattr(cls_self, '__build_order__'):
                res = self.__dict__.get(key, UNDEFINED)
                if res is UNDEFINED:
                    res = self.__build_param__(key)
        
        setattr(cls_self, '__init__', __init__)
        setattr(cls_self, '__build__', __build__)
        
        super().__init__(name, bases, namespace, **kwds)

C = TypeVar('C', bound='ParamClass')

class ParamClass(metaclass=ParamClassMeta):    
    def __build_param__(self, key):
        res = self._overrides.get(key, UNDEFINED)
        if res is UNDEFINED:
            res = getattr(type(self), key).__execute__(self)
        setattr(self, key, res)