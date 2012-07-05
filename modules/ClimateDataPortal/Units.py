# -*- coding: utf-8 -*-

class MeaninglessUnitsException(Exception):
    pass

class DimensionError(Exception):
    pass

class Units(object):
    __slots__ = ("_dimensions", "_positive")
    delta_strings = ("delta", "Δ")
    @staticmethod
    def parsed_from(string, positive=None):
        if positive is None:
            positive = True
            for delta_string in Units.delta_strings:
                if string.startswith(delta_string):
                    string = string[len(delta_string)+1:]
                    positive = False
                    break
        return Units(
            Dimensions.parsed_from(string),
            positive
        )
            
    def __init__(units, dimensions, positive):
        """Example:
        >>> u = Dimensions({"a": 4, "b": 2}, False)

        """
        units._dimensions = dimensions
        units._positive = bool(positive)

    def __repr__(units):
        return "%s(%s, %s)" % (
            units.__class__.__name__,
            repr(units._dimensions),
            units._positive
        )

    def __str__(units):
        return ["Δ ", ""][units._positive]+str(units._dimensions)

    def __eq__(units, other_units):
        return (
            units.dimensions == other_units.dimensions 
            and dimensions._positive == other_dimensions._positive
        )
    
    def __ne__(units, other_units):
        return not units.__eq__(other_units)

    def __add__(units, other_units):
        # signed + signed = signed
        # positive + signed = positive
        # signed + positive = positive
        # positive + positive = positive, but nonsense (but used in average)
        return Units(
            units._dimensions + other_units._dimensions,
            units._positive or other_units._positive
        )
    
    def __sub__(units, other_units):
        # signed - signed = signed
        # positive - signed = positive
        # signed - positive = signed, but nonsense
        # positive - positive = signed
        return Units(
            units._dimensions - other_units._dimensions,
            units._positive and not other_units._positive
        )

    def __mul__(units, other_units):
        # positive * positive = positive
        # positive * signed = signed
        # signed * positive = signed
        # signed * signed = signed, but nonsense
        return Units(
            units._dimensions.mul(other_units._dimensions, 1), 
            units._positive and other_units._positive     
        )    

    def __div__(units, other_units):
        # positive / positive = positive
        # positive / signed = signed
        # signed / positive = signed
        # signed / signed = signed 
        return Units(
            units._dimensions.mul(other_units._dimensions, -1), 
            units._positive and other_units._positive     
        )
    
    def __pow__(units, factor):
        return Units(
            units._dimensions ** factor,
            units._positive
        )

    def commensurable_with(units, other_units):
        return units._dimensions.commensurable_with(other_units._dimensions)

import re
counted_dimension_pattern = re.compile(
    r"(?:\w[^\^\/ ]*)(?:\^[0-9])?"
)

class Dimensions(object):
    """Used for dimensional analysis."""
    __slots__ = ("_counts", "_positive")
    @staticmethod
    def parsed_from(unit_string):
        "format example: m Kg^2 / s^2"
        dimension_counts = {}
        for factor, dimension_count_string in zip((1,-1), unit_string.split("/")):
            for match in counted_dimension_pattern.finditer(dimension_count_string):
                dimension_spec = match.group()
                if "^" in dimension_spec:
                    dimension, count = dimension_spec.split("^")
                else:
                    dimension = dimension_spec
                    count = 1
                count = factor * int(count)
                try:
                    existing_count = dimension_counts[dimension]
                except KeyError:
                    dimension_counts[dimension] = count
                else:
                    dimension_counts[dimension] += count
        return Dimensions(dimension_counts)

    def __init__(dimensions, dimension_counts):
        """Example:
        >>> u = Dimensions({"a": 4, "b": 2})

        """
        for dimension, count in dimension_counts.iteritems():
            if not isinstance(count, int):
                raise DimensionError(
                    "%s dimension count must be a whole number" % dimension
                )
        dimensions._counts = dimension_counts.copy()
    
    def iteritems(dimensions):
        return dimensions._counts.iteritems()

    def __repr__(dimensions):
        return "{%s}" % (
            dimensions.__class__.__name__,
            ", ".join(
                map("%r: %r".__mod__, dimensions._counts.iteritems())
            )
        )
        
    def __str__(dimensions):
        if not dimensions._counts:
            return "(dimensionless)"
        else:
            negative_dimension_counts = []
            positive_dimension_counts = []
            for dimension, count in dimensions._counts.iteritems():
                if count < 0:
                    negative_dimension_counts.append((dimension, -count))
                else:
                    positive_dimension_counts.append((dimension, count))
            
            dimension_strings = []
            def dimension_group(group):
                for dimension, count in group:
                    if " " in dimension:
                        dimension_name = "(%s)" % dimension
                    else:
                        dimension_name = dimension
                    if count == 1:
                        dimension_strings.append(dimension_name)
                    else:
                        dimension_strings.append(
                            "%s^%s" % (
                                dimension_name, 
                                #"²³⁴⁵⁶⁷⁸⁹"[count-2]
                                count
                            )
                        )
            dimension_group(positive_dimension_counts)
            if negative_dimension_counts:
                dimension_strings.append("/")
                dimension_group(negative_dimension_counts)
            return " ".join(dimension_strings)
    
    def commensurable_with(dimensions, other_dimensions):
        return (
            isinstance(other_dimensions, WhateverDimensionsAreNeeded) or
            dimensions._counts == other_dimensions._counts
        )
    
    def __eq__(dimensions, other_dimensions):
        return dimensions._counts == other_dimensions._counts
            
    def __ne__(dimensions, other_dimensions):
        return not dimensions.__eq__(other_dimensions)

    def mul(dimensions, other_dimensions, multiplier):
        result = dimensions._counts.copy()
        get = dimensions._counts.get
        if not isinstance(other_dimensions, WhateverDimensionsAreNeeded):
            for dimension, count in other_dimensions.iteritems():
                result[dimension] = get(dimension, 0) + multiplier * count
                if result[dimension] == 0:
                    del result[dimension]
        return Dimensions(result)

    def __pow__(dimensions, factor):
        # even = positive
        # odd = signed
        # zero is not allowed
        result = {}
        for dimension, count in dimensions._counts.iteritems():
            new_count = int(count * factor)
            if new_count != float(count) * float(factor):
                raise DimensionError(
                    "Non-integral %s dimension encountered." % dimension
                )
            result[dimension] = new_count
            if result[dimension] == 0:
                del result[dimension]
        return Dimensions(result)

class WhateverUnitsAreNeeded(object):
    __slots__ = ("_positive", "_dimensions")
    def __init__(units, positive = None):
        if positive is None:
            positive = True
        units._positive = positive
        units._dimensions = WhateverDimensionsAreNeeded()
    
    def __repr__(units):
        return "(Whatever units are needed)"
     
    def __str__(units):
        return ""
        
    __add__ = __sub__= \
        lambda units, other_units: other_units

    def __eq__(units, other_units):
        return True


class WhateverDimensionsAreNeeded(object):
    __slots__ = ()
    def __repr__(dimensions):
        return "(Whatever dimensions are needed)"
     
    def __str__(dimensions):
        return ""
        
    def commensurable_with(dimensions, other_dimensions):
        return True
            
    def __eq__(dimensions, other_dimensions):
        return True

Dimensionless = Dimensions({})


same = lambda x: x

units_in_out = {}
class Measure(object):
    def __init__(measure, dimensions, name, factor = 1.0, offset = 0.0):
        measure.name = name
        measure.dimensions = dimensions
        measure.factor = factor
        measure.offset = offset
        
        if factor == 1.0:
            if offset:
                to_standard = (lambda number: number - offset)
                from_standard = (lambda number: number + offset)
            else:
                to_standard = same
                from_standard = same
        else:
            if offset != 0.0:
                to_standard = (lambda number: (number * factor) - offset)
                from_standard = (lambda number: (number + offset) / factor)
            else:
                to_standard = (lambda number: number * factor)
                from_standard = (lambda number: number / factor)

        measure.to_standard = to_standard
        measure.from_standard = from_standard
        units_in_out[name] = measure

# There should be some distinction introduced "standard" and "preferred" units.
# E.g. in meteorology, degrees Celsius is the preferred unit but Kelvin 
# should be the standard because it simplifies certain calculations.
# There should only be one standard unit.
# preferred units differ by application, locale and user.

# It would be good to handle prefixes correctly.
# prefixes also have abbreviations which could cause ambiguity.

# Some units are merely abbreviations of other units with longer names.

# Some units have different names in different contexts, e.g.:
# 1,000,000 people vs. 1 tonne / person

# It would be useful to be able to generate Javascript objects from these 
# units in order to perform manipulations in the client.

measures_dict = dict(
    # units => dict((factor, offset) -> set(Measure))
)

def register(measure, measures_dict):
    definition = (measure.factor, measure.offset)
    try:
        measure_set = measures_dict[definition]
    except KeyError:
        measure_set = measures_dict[definition] = set()
    measure_set.add(measure)

Measure.register = register
standard_measure = {}

def group(dimensions, standard_name, *alternatives):
    base_dimensions = Dimensions.parsed_from(dimensions)
    standard_measure[base_dimensions] = Measure(base_dimensions, standard_name)
    try:
        compatible_measures = measures_dict[base_dimensions]
    except KeyError:
        compatible_measures = measures_dict[base_dimensions] = dict()
    for alternative in alternatives:
        Measure(base_dimensions, *alternative).register(compatible_measures)

Dimensions.group = staticmethod(group)
