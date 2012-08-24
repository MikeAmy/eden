
from datetime import date, timedelta

"""
class DateMapping(object):
        assert from_date(to_date(0)) == 0,  from_date(to_date(0))
        assert from_date(to_date(-1)) == -1
        assert from_date(to_date(1)) == 1
        assert from_date(to_date(-1000)) == -1000
        assert from_date(to_date(1000)) == 1000
"""

class Daily(object):
    def __init__(date_mapper, start_date):
        date_mapper.start_ordinal = start_date.toordinal()
       
    def to_date_tuple(date_mapper, day_number):
        date = date_mapper.to_date(day_number)
        return date.year, date.month, date.day

    def to_time_period(date_mapper, year, month, day):
        return date(year, month, day).toordinal() - date_mapper.start_ordinal
    
    def date_to_time_period(date_mapper, date):
        return date_mapper.to_time_period(date.year, date.month, date.day)
    
    def to_date(date_mapper, time_period):
        return date.fromordinal(
            date_mapper.start_ordinal + time_period
        )
        
    def __repr__(date_mapper):
        return "Daily(start_date=%(start_date)s)" % date_mapper.start_date

    def SQL_query(date_mapper, start_date, end_date, use):
        use(
            from_start = "time_period >= %i" % date_mapper.to_time_period(*start_date),
            until_end = "time_period <= %i " % date_mapper.to_time_period(*end_date),
            ordering_specification = "time_period ASC",
            format_time_period = (
                lambda time_period: 
                    date_mapper.to_date(time_period).strftime("%Y-%m-%d")
            )
        )

    
from math import floor
from calendar import isleap

class Monthly(object):
    def __init__(monthly, start_year, start_month_0_indexed):
        monthly.start_year = start_year
        monthly.start_month_0_indexed = start_month_0_indexed
        
    def to_time_period(monthly, year, month):
        """Time periods are integers representing months in years, 
        from 1960 onwards.
        
        e.g. 0 = Jan 1960, 1 = Feb 1960, 12 = Jan 1961
        
        This function converts a year and month to a month number.
        """
        return (
            ((year - monthly.start_year) * 12) + 
            (month - 1) 
        ) - monthly.start_month_0_indexed
   
    def to_date(monthly, month_number):
        year, month = monthly.to_date_tuple(month_number)
        return date(year, month, 1)

    def to_date_tuple(monthly, month_number):
        month_number += monthly.start_month_0_indexed
        return (month_number / 12) + monthly.start_year, ((month_number % 12) + 1)

    def date_to_time_period(monthly, date):
        return monthly.to_time_period(date.year, date.month)
    
    def __repr__(monthly):
        return "Monthly(start_date=%(start_date)s)" % monthly.start_date

    def SQL_query(monthly, start_date, end_date, use):
        use(
            from_start = "time_period >= %i" % monthly.to_time_period(*start_date),
            until_end = "time_period <= %i " % monthly.to_time_period(*end_date),
            ordering_specification = "time_period ASC",
            format_time_period = (
                lambda time_period: 
                    "%i-%i" % monthly.to_date_tuple(
                        time_period
                    )
            )
        )
 
    def floored_twelfth_of_a_360_day_year(monthly, date):
        """This function converts a date to a month number by flooring
        to the nearest 12th of a 360 day year. Used by PRECIS projection.
        """
        timetuple = date.timetuple()
        year = timetuple.tm_year
        day_of_year = timetuple.tm_yday
        month0 = floor((day_of_year / 360) * 12)
        return ((year-start_year) * 12) + (month0 - monthly.start_month_0_indexed)

    def rounded_date_to_month_number(monthly, date):
        """This function converts a date to a month number by rounding
        to the nearest 12th of a year.
        
        See also date_to_month_number(year, month)
        """
        timetuple = date.timetuple()
        year = timetuple.tm_year
        day_of_year = timetuple.tm_yday
        month0 = floor(((day_of_year / (isleap(year) and 366.0 or 365.0)) * 12) + 0.5)
        return ((year-start_year) * 12) + (month0 - monthly.start_month_0_indexed)

    def floored_twelfth_of_a_year(monthly, date):
        """This function converts a date to a month number by flooring
        to the nearest 12th of a year.
        """
        timetuple = date.timetuple()
        year = timetuple.tm_year
        day_of_year = timetuple.tm_yday
        month0 = floor((day_of_year / (isleap(year) and 366.0 or 365.0)) * 12)
        return ((year-start_year) * 12) + (month0 - monthly.start_month_0_indexed)


class MultipleYearsByMonth(object):
    """Month refers to a discontiguous slice through the twenty year
    period, for that month, which fundamentally affects calculations 
    and behaviour of interfaces, etc.
    """
    def __init__(date_mapper, start_year, year_step):
        date_mapper.start_year = start_year
        date_mapper.year_step = year_step
        
    # twenty_years_by_month date mapping should show charts without years,
    # only months?
    def to_date(date_mapper, time_period):
        year, month_1_indexed = date_mapper.to_date_tuple(time_period)
        return date(year, month_1_indexed, 1)

    def to_date_tuple(date_mapper, time_period):
        month = time_period % 12
        year = (
            (
                (time_period - month) / 12
            ) * date_mapper.year_step
        ) + date_mapper.start_year
        return year, month+1

    def to_time_period(date_mapper, year):
        return int(
            ((year - date_mapper.start_year) / date_mapper.year_step) * 12
        )

    def SQL_query(date_mapper, start_date, end_date, use):
        months = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(" ")
        def format_time_period(time_period):
            month_number = time_period % 12
            start_year = (
                ((time_period - month_number) / 12) * date_mapper.year_step
            ) + date_mapper.start_year
            end_year = start_year + date_mapper.year_step - 1
            return "%i-%i %s" % (
                start_year,
                end_year,
                months[month_number]
            )
        use(
            from_start = "time_period >= %i" % date_mapper.to_time_period(*start_date),
            until_end = "time_period >= %i " % date_mapper.to_time_period(*end_date),
            ordering_specification = "time_period ASC",
            format_time_period = format_time_period
        )

class Yearly(object):
    def __init__(date_mapper, start_year):
        date_mapper.start_year = start_year
    
    def to_date(date_mapper, time_period):
        (year,) = date_mapper.to_date_tuple(time_period)
        return date(year, 1, 1)

    def to_date_tuple(date_mapper, time_period):
        return (time_period+date_mapper.start_year,)
        
    def to_time_period(date_mapper, year):
        return year-date_mapper.start_year
    
    def SQL_query(date_mapper, start_date, end_date, use):
        use(
            from_start = "time_period >= %i" % date_mapper.to_time_period(*start_date),
            until_end = "time_period <= %i " % date_mapper.to_time_period(*end_date),
            ordering_specification = "time_period ASC",
            format_time_period = lambda time_period: str(time_period + date_mapper.start_year)# not unicode
        )

