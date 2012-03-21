
same = lambda x: x
# keyed off the units field in the sample_table_spec table
standard_unit = {
    "in": same,
    "out": same
}
# be careful to use floats for all of these numbers
units_in_out = {
    "Celsius": {
        "in": lambda celsius: celsius + 273.15,
        "out": lambda kelvin: kelvin - 273.15
    },
    "Fahreinheit": {
        "in": lambda fahreinheit: (fahreinheit + 459.67) + (5.0/9.0),
        "out": lambda kelvin: (kelvin * (9.0/5.0)) - 459.67
    },
    "Kelvin": standard_unit,
    "hPa": standard_unit,
    "people": standard_unit,
    "Person": standard_unit,
    
    
    "Pa": {
        "in": lambda pascals: pascals / 100.0,
        "out": lambda hectopascals: hectopascals * 100.0
    },

    "mm": standard_unit,

    #"mm": standard_unit,
    "kg m-2 s-1": {
        "in": lambda precipitation_rate: precipitation_rate * 2592000.0,
        "out": lambda mm: mm / 2592000.0
    },
    
    "%": {
        "in": lambda x: x / 100.0,
        "out": lambda x: x * 100.0
    },
    "ratio": standard_unit,
    "m/s": standard_unit,
    "km^2": standard_unit,
    "tonne/km^2": standard_unit,
    "US$": standard_unit,
    "kWh": standard_unit,
    "tonne/US$": standard_unit,
    "tonne": standard_unit,
    "kWh/Person": standard_unit,
    "tonne/Person": standard_unit,
    "DRR Progress score": standard_unit,
    "km^3": standard_unit,
    "Business Ease": standard_unit,
    "CPIA Public sector score": standard_unit,
    "US$/Person": standard_unit,
}

