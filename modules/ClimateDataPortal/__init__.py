# -*- coding: utf-8 -*-

"""
    Climate Data Module

    @author: Mike Amy
"""

from SampleTable import (
    SampleTable,
    Observed,
    Gridded,
    Projected,
    sample_table_types_by_code
)
from Units import (
    Units,
    Dimensions,
    units_in_out, 
    WhateverUnitsAreNeeded,
    DimensionError,
    MeaninglessUnitsException
)
from MapPlugin import MapPlugin, Disallowed



# This shouldn't be here, it should be in the application,
# however, can't see a good place to put it.

# Take care to use floats for all numbers in conversion calculations:

Dimensions.group("", 
    "ratio", 
    ("%", 100.0,)
)

temperature = Dimensions.parsed_from("Kelvin")
Dimensions.group("Kelvin", 
    "Kelvin",
    ("Celsius", 1.0, 273.15),
    ("Fahreinheit", (9.0/5.0), 459.67),
)

pressure = Dimensions.parsed_from("kg / m s^2")
Dimensions.group("kg / m s^2", 
    "Pascal",
    ("hPa", 100.0)
)

Dimensions.group("person", "person",
    ("capita",),
    ("people",),
)

length = Dimensions.parsed_from("m")
Dimensions.group("m", "metre",
    ("km", 1000.0),
    ("cm", 1/100.0),
    ("mm", 1/1000.0),
)

mass = Dimensions.parsed_from("kg")
Dimensions.group("kg", "kilogram",
    ("tonne", 1000.0),
    ("kilotonne", 1000000.0),
)

time = Dimensions.parsed_from("s")
Dimensions.group("s", "second",
    ("minute", 60),
    ("hour", 60 * 60),
    ("day", 60 * 60 * 24),
    ("week", 60 * 60 * 24),
)

rainfall = Dimensions.parsed_from("precipitation mm")
Dimensions.group("precipitation mm", "precipitation mm")

# in case someone types it this way around:
mm_precipitation = Dimensions.parsed_from("mm precipitation")
Dimensions.group("precipitation mm", "mm precipitation")

velocity = Dimensions.parsed_from("m/s")
Dimensions.group("m/s", "m/s")

preferred_units = {
    pressure: "hPa",
    time: "day",
    temperature: "Kelvin",
    rainfall: "precipitation mm",
    velocity: "m/s",
}

SampleTable.init_SampleTables()