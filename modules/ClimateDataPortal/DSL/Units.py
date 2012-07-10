# -*- coding: utf-8 -*-

from ..Method import Method
from .. import Units
from ..Units import Dimensionless

units = Method("units")


from . import (
    Addition, Subtraction, Multiplication, Division, Pow,
    operations, aggregations,
    BinaryOperator,
    Average, Sum, Minimum, Maximum, Count, 
    StandardDeviation, Count, Number
)

def binop_units(binop, use_units):
    left_units = units(binop.left)()
    right_units = units(binop.right)()
    if left_units is not None and right_units is not None:
        use_units(left_units, right_units)
    else:
        binop.units = None

@units.implementation(Addition)
def addition_units(operation):
    def determine_units(left_units, right_units):
        if not left_units.commensurable_with(right_units):
            operation.units_error = MismatchedUnits(
                (operation, left_units, right_units)
            )
            operation.units = None
        else:
            operation.units = left_units + right_units
    binop_units(operation, determine_units)
    return operation.units
                
@units.implementation(Subtraction)
def subtract_units(operation):
    def determine_units(left_units, right_units):
        if not left_units.commensurable_with(right_units):
            operation.units_error = (
                "Incompatible units: %(left_units)s and %(right_units)s" % locals()
            )
            operation.units = None
        else:
            operation.units = left_units - right_units
    binop_units(operation, determine_units)
    return operation.units

@units.implementation(Multiplication)
def multiply_units(operation):
    binop_units(operation,
        lambda left_units, right_units:
            setattr(operation, "units", left_units * right_units)
    )
    return operation.units

@units.implementation(Division)
def divide_units(operation):
    binop_units(operation,
        lambda left_units, right_units:
            setattr(operation, "units", left_units / right_units)
    )
    return operation.units

@units.implementation(Pow)
def raise_units_to_power(operation):
    def determine_units(left_units, right_units):
        if right_units is WhateverUnitsAreNeeded:
            operation.right_units = right_units = Dimensionless
        if right_units == Dimensionless:
            operation.units = left_units ** operation.right
        else:
            operation.units_error = "Exponents must be dimensionless, of the form n or 1/n"
            operation.units = None

    binop_units(operation, determine_units)
    return operation.units

@units.implementation(Average, Sum, Minimum, Maximum)
def aggregation_units(aggregation):
    aggregation.units = Units.parsed_from(
        aggregation.sample_table.units_name
    )
    return aggregation.units
    
@units.implementation(StandardDeviation)
def stddev_determine_units(aggregation):
    aggregation.units = Units.parsed_from(
        aggregation.sample_table.units_name,
        False # displacement
    )
    return aggregation.units

@units.implementation(Count)
def count_units(count):
    count.units = Dimensionless
    return count.units

@units.implementation(Number)
def number_units(number):
    return number.units # set in constructor

@units.implementation(int, float)
def primitive_number_units(number):
    return WhateverUnitsAreNeeded




analysis = Method("analysis")

@analysis.implementation(Number)
def Number_analysis(number, out):
    out(number.value, " ", number.units)

@analysis.implementation(*operations)
def Binop_analysis(binop, out):
    def indent(*strings):
        out("    ", *strings)

    out("(")
    analysis(binop.left)(indent)

    indent(binop.op)
    
    analysis(binop.right)(indent)
    out(")    # ", binop.units or "???")
    if hasattr(binop, "units_error"):
        out("# ", binop.units_error)


@analysis.implementation(*aggregations)
def aggregation_analysis(aggregation, out):
    out(type(aggregation).__name__, "(    # ", aggregation.units or "???")
    def indent(*strings):
        out("    ", *strings)
    indent(str(aggregation.sample_table), ",")
    
    for specification in aggregation.specification:
        indent(specification, ",")
    out(")")

@analysis.implementation(int, float)
def primitive_number_analysis(number, out):
    out(number)
