
ClimateDataPortal = local_import("ClimateDataPortal")
    
def show_usage():
    sys.stderr.write("""Usage:
    %(command)s table_name
    
""" % dict(
    command = "... add_table.py",
))

import sys

try:
    sample_type_name = sys.argv[1]
    assert sys.argv[2:] == [], "%s ??" % sys.argv
except:
    show_usage()
    #raise
else:  
    ClimateDataPortal.SampleTable.with_name(sample_type_name).create_indices()
 