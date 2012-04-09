
from types import MethodType

class Method(object):
    """Allows better functional cohesion in the source.
    Removes possibility of method name conflicts.
    """
    def __init__(method, name):
        method.implementations = {}
        method.name = name
    
    def implementation(method, *classes):
        def accept_implementation(impl):
            for Class in classes:
                method.implementations[Class] = impl
            return impl
        return accept_implementation
    
    def __call__(method, target):
        key = type(target)
        try:
            return MethodType(
                method.implementations[key],
                target,
                key
            )
        except KeyError:
            raise TypeError(
                "No %s implementation for %s" % (method.name, key)
            )

    def implemented_by(method, target):
        return type(target) in method.implementations
