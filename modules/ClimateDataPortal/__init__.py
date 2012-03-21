# -*- coding: utf-8 -*-

"""
    Climate Data Module

    @author: Mike Amy
"""

# This could be moved somewhere else
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
    
    def __call__(method, target, *args, **kwargs):
        try:
            return method.implementations[type(target)](target, *args, **kwargs)
        except KeyError:
            raise TypeError(
                "No %s implementation for %s" % (method.name, type(target))
            )

    def implemented_by(method, target):
        return type(target) in method.implementations


from SampleTable import SampleTable
from known_units import units_in_out
from MapPlugin import MapPlugin

__all__ = ["SampleTable", "MapPlugin", "Observed", "Gridded", "Projected"]
