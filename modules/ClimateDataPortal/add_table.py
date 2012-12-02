
ClimateDataPortal = local_import("ClimateDataPortal")
    
def show_usage():
    sys.stderr.write("""Usage:
    %(command)s sample_type parameter_name units field_type date_mapping gridsize
    
parameter_name: a unique name for the table e.g. "Rainfall" "Max Temp"
field_type: any postgres numeric field type e.g. real, integer, "double precision".
units: mm, Kelvin (displayed units may be different)
sample_type: Observed, Gridded or Projected
date_mapping: daily or monthly
gridsize: 0 for no grid, otherwise, spacing in km

e.g. .../add_table.py Observed "Min Temp" Kelvin real daily 25

""" % dict(
    command = "... add_table.py",
))

import sys

try:
    sample_type_name = sys.argv[1]
    if sample_type_name == "Interpolated":
        sample_type_name = "Gridded"
    allowed_sample_type_names = ("Observed", "Gridded", "Projected")
    if sample_type_name not in allowed_sample_type_names:
        print "sample_type_name (argument 1) must be one of:"+ allowed_sample_type_names
    parameter_name = sys.argv[2]
    units_name = sys.argv[3]
    field_type = sys.argv[4]
    allowed_field_types = ("real", "integer", "double precision")
    if field_type not in allowed_field_types:
        print "field_type (argument 4) must be one of:"+ allowed_sample_type_names
    date_mapping_name = sys.argv[5]
    allowed_date_mappings = ("daily", "monthly")
    if date_mapping_name not in allowed_date_mappings:
        print "date_mapping_name (argument 5) must be one of:"+ allowed_date_mappings
    grid_size = sys.argv[6]
    assert sys.argv[7:] == [], "%s <- don't understand this extra argument" % sys.argv
except:
    show_usage()
    #raise
else:
    def write_message(sample_table_name):
        print "Added", sample_table_name, sample_type_name, parameter_name
        print "  containing", units_name, "values of type", field_type
        
    try:       
        ClimateDataPortal.SampleTable(
            db = db
            name = parameter_name,
            date_mapping_name = date_mapping_name,
            field_type = field_type,
            units_name = units_name,
            sample_type = getattr(ClimateDataPortal, sample_type_name),
            grid_size = float(grid_size),
        ).create(write_message)
    except:
        show_usage()
        raise
