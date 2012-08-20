import datetime

from ..Method import Method
from . import *

# check methods check expressions that have been parsed
# this makes sure that all parts of the expressions make sense
# this is before building
check = Method("check")
# checks arguments are correct type and in range only.

def month_number_from_arg(month, error):
    if not isinstance(month, int):     
        error("Month should be a whole number")
    else:
        try:
            month_number = Months.options[month]
        except KeyError:
            error(
                "Months should be e.g. Jan/January or numbers "
                "in range 1 (January) to 12 (Dec), not %s" % month
            )
            return 1
        else:
            return month_number

def month_filter_number_from_arg(month, error):
    try:
        month_number = Months.options[month]
    except KeyError:
        error(
            "Months should be e.g. PrevDec/PreviousDecember/Jan/January or numbers "
            "in range 0 (PreviousDecember) to 12 (Dec), not %s" % month
        )
        return 1
    else:
        return month_number

# specialist check for month specifications
check_months = Method("check_months")

from ..DateMapping import Yearly, Monthly, MultipleYearsByMonth, Daily

@check_months.implementation(Yearly)
def Yearly_check_months(yearly, add_error):
    add_error("Yearly data sets cannot have Months specified, so remove the Months(...).")

@check_months.implementation(Monthly)
def Monthly_check_months(yearly, error, month_numbers):
    if (
        Months.options["PreviousDecember"] - 1 in month_numbers and 
        Months.options["December"] - 1 in month_numbers
    ):
        error(
            "It doesn't make sense to aggregate with both PreviousDecember and "
            "December. Please choose one or the other."
        )

@check_months.implementation(MultipleYearsByMonth)
def MultipleYearsByMonth_check_months(date_mapper, error, months, month_numbers):
    if (
        Months.options["PreviousDecember"] - 1 in month_numbers
    ):
        error(
            "PreviousDecember doesn't mean anything with this dataset's "
            "concept of dates. Please choose December instead."
        )



@check.implementation(Months)
def Months_check(month_filter, date_mapper):
    month_filter.errors = set()
    error = month_filter.errors.add
    month_filter.month_numbers = month_numbers = list()
    months = month_filter.months
    for month in months:                
        month_number_or_null = month_filter_number_from_arg(month, error)
        if month_number_or_null is not None:
            month_number = month_number_or_null - 1
            if month_number in month_numbers:
                error(
                    "%s was added more than once" % Months.sequence[month_number]
                )
            month_numbers.append(month_number)
    check_months(
        date_mapper
    )(
        error = error,
        month_numbers = month_filter.month_numbers
    )
    return month_filter.errors



check_from = Method("check_from")   
check_to = Method("check_to")

def checked_year(year, error):
    if not isinstance(year, int):
        error("Year should be a whole number")
    if not (1900 <= year <= 2100):
        error("Year should be in range 1900 to 2100, not %i" % year)
    return (year,)

def checked_year_month(year, month, error):
    return checked_year(year, error) + (month_filter_number_from_arg(month, error),)

import calendar
def checked_year_month_day(year, month, day, error):
    if not isinstance(day, int):
        error("Day should be a whole number")    
    year, month_number = checked_year_month(year, month, error)
    if day is -1:
        # use last day of month
        _, day = calendar.monthrange(year, month_number)
    try:
        datetime.date(year, month_number, day)
    except:
        error("Invalid date: datetime.date(%i, %i, %i)" % (year, month_number, day))
    return (year, month_number, day)

@check_from.implementation(Monthly)
def Monthly_check_from(yearly, error, year, month, day):
    if month is None:
        month = 1
    if day is not None:
        error("Monthly datasets cannot use days in time ranges")
    return checked_year_month(year, month, error)

@check_to.implementation(Monthly)
def Monthly_check_to(yearly, error, year, month, day):
    if month is None:
        month = 12
    if day is not None:
        error("Monthly datasets cannot use days in time ranges")
    return checked_year_month(year, month, error)

@check_to.implementation(MultipleYearsByMonth, Yearly)
@check_from.implementation(MultipleYearsByMonth, Yearly)
def Yearly_check_from_to(date_mapper, error, year, month, day):
    if month is not None:
        error("Yearly datasets cannot use months in time ranges")
    if day is not None:
        error("Yearly datasets cannot use days in time ranges")
    if not isinstance(year, int):
        error("Year should be a whole number")
    return checked_year(year, error)

@check_from.implementation(Daily)
def Daily_check_from(date_mapper, error, year, month, day):
    if month is None:
        month = 1
    if day is None:
        day = 1
    return checked_year_month_day(year, month, day, error)

@check_to.implementation(Daily)
def Daily_check_to(date_mapper, error, year, month, day):
    if month is None:
        month = 12
    if day is None:
        day = -1
    return checked_year_month_day(year, month, day, error)

@check.implementation(From)
def From_check(from_date, date_mapper):
    from_date.errors = set()
    error = from_date.errors.add
    year = from_date.year
    from_date.date = check_from(
        date_mapper
    )(
        error, 
        from_date.year,
        from_date.month,
        from_date.day
    )
    return from_date.errors

@check.implementation(To)
def To_check(to_date, date_mapper):
    to_date.errors = set()
    error = to_date.errors.add
    year = to_date.year
    to_date.date = check_to(
        date_mapper
    )(
        error, 
        to_date.year,
        to_date.month,
        to_date.day
    )
    return to_date.errors

@check.implementation(Date_Offset)
def date_offset_check(date_offset, date_mapper):
    """Check Date offsets are given in numbers"""
    date_offset.errors = set()
    error = date_offset.errors.add
    years = date_offset.years
    months = date_offset.months
    if not isinstance(years, int):
        error("Offset years should be a whole number")
    if not isinstance(months, int):
        error("Offset months should be a whole number")
    return date_offset.errors

@check.implementation(Addition, Subtraction, Multiplication, Division)
def Binop_check(binop):
    """Check both sides of arithmetic expressions"""
    binop.errors = set()
    left = check(binop.left)()
    right = check(binop.right)()
    return left or right

@check.implementation(Pow)
def PowRoot_check(binop):
    """Check power expression have positive exponents"""
    binop.errors = set()
    error = binop.errors.add
    exponent = binop.right
    if not isinstance(exponent, int) or exponent == 0:
        error("Exponent should be a positive, non-zero number.")
    return check(binop.left)() or binop.errors

@check.implementation(*aggregations)
def Aggregation_check(aggregation):
    aggregation.errors = set()
    error = aggregation.errors.add
    # check a dataset is specified
    if not isinstance(aggregation.dataset_name, basestring):
        error(
            "First argument should be the name of a data set enclosed in "
            "quotes. "
        )
    else:
        # check the dataset exists - this peforms error handlng if not
        if SampleTable.name_exists(aggregation.dataset_name, error):
            aggregation.sample_table = SampleTable.with_name(aggregation.dataset_name)
            # check only date specs are given
            allowed_specifications = (To, From, Months, Date_Offset)
            specification_errors = False
            date_mapper = aggregation.sample_table.date_mapper
            used_specifications = set()
            for specification in aggregation.specification:
                if isinstance(specification, allowed_specifications):
                    specification_type = type(specification)
                    # check no date spec is used more than once
                    if specification_type in used_specifications:
                        error(specification_type.__name__+" should only be used once.")
                    else:
                        used_specifications.add(specification_type)
                        # check the date spec 
                        specification_errors |= bool(
                            check(specification)(date_mapper)
                        )
                else:
                    error(
                        "%(specification)s should not be used inside "
                        "%(aggregation_name)s(...).\n"
                        "The dataset name is required.\n"
                        "Optional arguments are %(possibilities)s." % dict(
                            specification = specification,
                            aggregation_name = aggregation.__class__.__name__,
                            possibilities = ", ".join(
                                Class.__name__+"(...)" for Class in allowed_specifications
                            )
                        )
                    )
    # TODO: check that aggregation from date >= to date? More a warning?
    # problem is those dates are locked inside the specs until Build phase
    return aggregation.errors or specification_errors

from .. import Units, WhateverUnitsAreNeeded
def Units_check_number(units, value, error):
    """Check for ambiguous numbers"""
    if units._positive and value < 0:
        error(
            "Can't guess whether negative numbers without 'delta' are deltas. "
            "Specify the number as a delta e.g. '%s delta mm', "
            "make it positive, or rearrange the expression "
            "(e.g. to multiply by -1, subtract from 0)." % value
        )
Units.check_number = WhateverUnitsAreNeeded.check_number = Units_check_number

@check.implementation(Number)
def Number_check(number):
    number.errors = set()
    number.units.check_number(
        number.value,
        number.errors.add
    )
    return number.errors

check_analysis = Method("check_analysis")

@check_analysis.implementation(Number)
def Number_check_analysis(number, out):
    out(number.value)
    if number.errors:
        out("# ^ ", ", ".join(number.errors))

@check_analysis.implementation(From, To, Months, Date_Offset)
def Date_check_analysis(date_spec, out):
    out("%s," % date_spec)
    if hasattr(date_spec, "errors") and date_spec.errors:
        out("# ^ ", ", ".join(date_spec.errors))


@check_analysis.implementation(*operations)
def Binop_check_analysis(binop, out):
    def indent(*strings):
        out("    ", *strings)

    out("(")
    check_analysis(binop.left)(indent)

    indent(binop.op)
    
    check_analysis(binop.right)(indent)
    out(")")
    if binop.errors:
        out("# ^ ", ", ".join(binop.errors))


@check_analysis.implementation(*aggregations)
def aggregation_check_analysis(aggregation, out):
    out(type(aggregation).__name__, "(")
    def indent(*strings):
        out("    ", *strings)
    indent('"%s"' % aggregation.dataset_name, ",")
    
    for specification in aggregation.specification:
        check_analysis(specification)(indent)
    out(")")
    if aggregation.errors:
        out("# ^ ", ", ".join(aggregation.errors))

@check_analysis.implementation(int, float)
def primitive_number_check_analysis(number, out):
    out(number)

        