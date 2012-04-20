# -*- coding: utf-8 -*-

from ..Method import Method
date_mapping = Method("date_mapping")

class MismatchedDateMapping(Exception):
    pass

WhateverDateMappingIsNeeded = object()

from . import Addition, Subtraction, Multiplication, Division
@date_mapping.implementation(Addition, Subtraction, Multiplication, Division)
def operation_date_mapping(binop):
    left_date_mapping = date_mapping(binop.left)()
    right_date_mapping = date_mapping(binop.right)()
    if left_date_mapping != right_date_mapping:
        if right_date_mapping is WhateverDateMappingIsNeeded:
            binop.date_mapping = left_date_mapping
        elif left_date_mapping is WhateverDateMappingIsNeeded:
            binop.date_mapping = right_date_mapping
        else:
            binop.date_mapping_error = MismatchedDateMapping(
                (binop, left_date_mapping, right_date_mapping)
            )
    else:
        binop.date_mapping = right_date_mapping
    return binop.date_mapping

from . import Pow
@date_mapping.implementation(Pow)
def power_date_mapping(pow):
    pow.date_mapping = date_mapping(pow.left)()
    return pow.date_mapping

from . import aggregations
@date_mapping.implementation(*aggregations)
def aggregation_date_mapping(aggregation):
    return aggregation.sample_table.date_mapper

from . import Number
@date_mapping.implementation(Number, int, float)
def number_date_mapping(number):
    return WhateverDateMappingIsNeeded
