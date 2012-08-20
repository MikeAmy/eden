  
from . import *

def Months__unicode__(month_filter):
    return u"Months(%s)" % (
        u", ".join(
            Months.sequence[month_number + 1] 
            for month_number in month_filter.month_numbers
        )
    )
Months.__unicode__ = Months__unicode__


def From__unicode__(from_date):
    original_args = [from_date.year]
    if from_date.month is not None:
        original_args.append(from_date.month)
    if from_date.day is not None:
        original_args.append(from_date.day)
    return u"From(%s)" % ", ".join(map(unicode, original_args))
From.__unicode__ = From__unicode__
    

def To__unicode__(to_date):
    original_args = [to_date.year]
    if to_date.month is not None:
        original_args.append(to_date.month)
    if to_date.day is not None:
        original_args.append(to_date.day)
    return u"To(%s)" % ", ".join(map(unicode,original_args))
To.__unicode__ = To__unicode__

def Date_Offset__unicode__(date_offset):
    original_args = [date_offset.years]
    if date_offset.months is not 0:
        original_args.append(date_offset.months)
    return u"Date_Offset(%s)" % ", ".join(map(unicode,original_args))
Date_Offset.__unicode__ = Date_Offset__unicode__

def Number__unicode__(number):
    units_name = unicode(number.units)
    if units_name:
        return u"%s %s" % (number.value, number.units)
    else:
        return unicode(number.value)
Number.__unicode__ = Number__unicode__

def AggregationNode__unicode__(aggregation):
    return u"".join((
        type(aggregation).__name__, u"(\"",
            aggregation.dataset_name, u"\", ",
            u", ".join(
                map(unicode, aggregation.specification)
            ),
        u")"
    ))
AggregationNode.__unicode__ = AggregationNode__unicode__

def BinaryOperator__unicode__(binop):
    return u"("+unicode(binop.left)+u" "+binop.op+u" "+unicode(binop.right)+u")"
BinaryOperator.__unicode__ = BinaryOperator__unicode__
