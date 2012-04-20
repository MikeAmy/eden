# -*- coding: utf-8 -*-

from DateMapping import Daily, Monthly, Yearly, MultipleYearsByMonth

class Observed(object):
    code = "O"

class Gridded(object):
    code = "G"
Gridded.__name__ = "Interpolated"
    
class Projected(object):
    code = "P"

from simplejson import OrderedDict
sample_table_types = (Observed, Gridded, Projected)
sample_table_types_by_code = OrderedDict()
for SampleTableType in sample_table_types:
    sample_table_types_by_code[SampleTableType.code] = SampleTableType


from gluon import current
db = current.db

from datetime import date
from Units import units_in_out

class SampleTable(object):
    # Samples always have places and time (periods)
    # This format is used for daily data and monthly aggregated data.
    
    # Performance matters, and we have lots of data, 
    # so unnecessary bytes are shaved as follows: 

    # 1. Sample tables don't need an id - the time and place is the key
    # 2. The meaning of dates may vary. 
    #    The smallest interval is one day, so time_period as smallint (65536)
    #    instead of int, allows a 179 year range. 
    #    Normally we'll be dealing with months however, where this is 
    #    even less of an issue.
    # 3. The value field type can be real, int, smallint, decimal etc. 
    #    Double is overkill for climate data.
    #    Take care with decimal though - calculations may be slower.
    
    # These tables are not web2py tables as we don't want web2py messing with 
    # them. The database IO is done directly to postgres for speed. 
    # We don't want web2py messing with or complaining about the schemas.
    # It is likely we will need spatial database extensions i.e. PostGIS.
    # May be better to cluster places by region.
        
    __date_mapper = {
        "daily": Daily(
            start_date = date(2011,11,11) # Nepal specific dates
        ),
        "monthly": Monthly(
            start_year = 2011, # Nepal specific dates
            start_month_0_indexed = 11
        ),
        "yearly": Yearly(
            start_year = 2000
        ),
        "twenty_years_by_month": MultipleYearsByMonth(
            start_year = 1900,
            year_step = 20
        ),
    }
    __objects = {}
    __names = OrderedDict()

    @staticmethod
    def with_name(name):
        return SampleTable.__names[name]

    __by_ids = {}
    @staticmethod
    def with_id(id):
        SampleTable_by_ids = SampleTable.__by_ids
        return SampleTable_by_ids[id]
    
    @staticmethod
    def name_exists(name, error):
        if name in SampleTable.__names:
            return True
        else:
            error(
                "Can't find dataset \"%s\"" % name
            )
            return False

    @staticmethod
    def matching(
        parameter_name,
        sample_type_code
    ):
        return SampleTable.__objects[(parameter_name, sample_type_code)]

    @staticmethod
    def add_to_client_config_dict(config_dict):
        data_type_option_names = []
        for SampleTableType in sample_table_types:
            data_type_option_names.append(SampleTableType.__name__)                

        parameter_names = []
        for name, sample_table in SampleTable.__names.iteritems():
            # Nepal-specific (only monthly are allowed):
            if sample_table.date_mapping_name == "monthly":
                parameter_names.append(name)
        config_dict.update(
            data_type_option_names = data_type_option_names,
            parameter_names = parameter_names
        )
    
    def __init__(
        sample_table, 
        db, 
        name, # please change to parameter_name
        date_mapping_name,
        field_type,
        units_name,
        grid_size,
        sample_type = None,
        sample_type_code = None,
        id = None
    ):
        parameter_name = name
        assert units_name in units_in_out.keys(), \
            "units must be one of %s, not %s" % (units_in_out.keys(), units_name)
        assert sample_type is None or sample_type in sample_table_types
        assert (sample_type is not None) ^ (sample_type_code is not None), \
            "either parameters sample_type or sample_type_code must be set"
        sample_table_type = sample_type or sample_table_types_by_code[sample_type_code]

        if id is not None:
            if id in SampleTable.__by_ids:
                # other code shouldn't be creating SampleTables that already
                # exist. Or, worse, different ones with the same id.
                raise Exception(
                    "SampleTable %i already exists. "
                    "Use SampleTable.with_id(%i) instead." % (id, id)
                )
                #return SampleTable.__by_ids[id]
            else:
                sample_table.set_id(id)
                SampleTable.__by_ids[id] = sample_table

        sample_table.type = sample_table_type
        sample_table.units_name = units_name
        sample_table.parameter_name = parameter_name
        sample_table.date_mapping_name = date_mapping_name
        sample_table.date_mapper = SampleTable.__date_mapper[date_mapping_name]
        sample_table.field_type = field_type
        sample_table.grid_size = grid_size
        sample_table.db = db

        SampleTable.__objects[
            (parameter_name, sample_table.type.code)
        ] = sample_table
        SampleTable.__names["%s %s" % (
            sample_table.type.__name__, 
            parameter_name
        )] = sample_table
    
    def __repr__(sample_table):
        return '%s %s' % (
            sample_table.type.__name__,
            sample_table.parameter_name
        )

    def __str__(sample_table):
        return '"%s"' % repr(sample_table)
    
    @staticmethod
    def table_name(id): # name conflict with attribute
        return "climate_sample_table_%i" % id
    
    def set_id(sample_table,id):
        sample_table.id = id
        sample_table.table_name = SampleTable.table_name(id)

    def find(
        sample_table,
        found,
        not_found 
    ):
        db = sample_table.db
        existing_table_query = db(
            (db.climate_sample_table_spec.name == sample_table.parameter_name) &
            (db.climate_sample_table_spec.sample_type_code == sample_table.type.code)      
        )
        existing_table = existing_table_query.select().first()
        if existing_table is None:
            not_found()
        else:
            found(
                existing_table_query,
                SampleTable.table_name(existing_table.id),
            )
    
    def create(sample_table, use_table_name):
        def create_table():
            db = sample_table.db
            sample_table.set_id(
                db.climate_sample_table_spec.insert(
                    sample_type_code = sample_table.type.code,
                    name = sample_table.parameter_name,
                    units = sample_table.units_name,
                    field_type = sample_table.field_type,
                    date_mapping = sample_table.date_mapping_name,
                    grid_size = sample_table.grid_size
                )
            )
            db.executesql(
                """
                CREATE TABLE %(table_name)s
                (
                  place_id integer NOT NULL,
                  time_period smallint NOT NULL,
                  value %(field_type)s NOT NULL,
                  CONSTRAINT %(table_name)s_primary_key 
                      PRIMARY KEY (place_id, time_period),
                  CONSTRAINT %(table_name)s_place_id_fkey 
                      FOREIGN KEY (place_id)
                      REFERENCES climate_place (id) MATCH SIMPLE
                      ON UPDATE NO ACTION ON DELETE CASCADE
                );
                """ % sample_table.__dict__
            )
            use_table_name(sample_table.table_name)

        def complain_that_table_already_exists(
            query, 
            existing_table_name
        ):
            raise Exception(
                "Table for %s %s already exists as '%s'" % (
                    sample_table.type.__name__,
                    sample_table.parameter_name, 
                    existing_table_name
                )
            )
        return sample_table.find(
            not_found = create_table,
            found = complain_that_table_already_exists
        )
        
    def create_indices(sample_table):
        db = sample_table.db
        for field in (
            "time_period",
            "place_id",
            "value"
        ):
            db.executesql(
                "CREATE INDEX %(table_name)s_%(field)s__idx "
                "on %(table_name)s(%(field)s);" % dict(
                    sample_table.__dict__,
                    field = field
                )
            )

    def drop(sample_table, use_table_name):
        db = sample_table.db
        def complain_that_table_does_not_exist():
            raise Exception(
                "%s %s table not found" % (
                    sample_table.sample_type_name,
                    sample_table.parameter_name,
                )
            ) 
        
        def delete_table(
            existing_table_query, 
            existing_table_name,
        ):
            existing_table_query.delete()
            db.executesql(
                "DROP TABLE %s;" % existing_table_name
            )
            use_table_name(existing_table_name)
        
        return sample_table.find(
            not_found = complain_that_table_does_not_exist,
            found = delete_table
        )

    def clear(sample_table):
        sample_table.db.executesql(
            "TRUNCATE TABLE %s;" % sample_table.table_name
        )

    def insert_values(sample_table, values):
        sql = "INSERT INTO %s (time_period, place_id, value) VALUES %s;" % (
            sample_table.table_name,
            ",".join(values)
        )
        try:
            sample_table.db.executesql(sql)
        except:
            print sql
            raise
    
    def pull_real_time_data(sample_table):
        import_sql = (
            "SELECT AVG(value), station_id, obstime "
            "FROM weather_data_nepal "
            "WHERE parameter = 'T' "
            "GROUP BY station_id, obstime"
            "ORDER BY station_id, obstime;"
        )
        sample_table.cldb.executesql(
            import_sql
        )

    def csv_data(
        sample_table, 
        place_id,
        date_from, # tuple (year[, month[, day]])
        date_to # tuple (year[, month[, day]])
    ):
        data = ["date,"+sample_table.units_name]
        def request_data(
            from_start,
            until_end,
            ordering_specification,
            format_time_period
        ):
            for record in db.executesql(
                "SELECT * "
                "FROM climate_sample_table_%(sample_table_id)i "
                "WHERE place_id = %(place_id)i "
                "AND %(from_start)s "
                "AND %(until_end)s "
                "ORDER BY %(ordering_specification)s;" % dict(
                    sample_table_id = sample_table.id,
                    from_start = from_start,
                    until_end = until_end,
                    ordering_specification = ordering_specification
                )
            ):
                place_id, time_period, value = record
                data.append(
                    ",".join((
                        format_time_period(time_period),
                        str(value)
                    ))
                )
        sample_table.date_mapper.SQL_query(
            start_date = date_from,
            end_date = date_to,
            use = request_data
        )
        data.append("")
        return "\n".join(data)
        
    def get_available_years(
        sample_table
    ):
        years = set()
        for (time_period,) in db.executesql(
            "SELECT DISTINCT time_period "
            "FROM climate_sample_table_%(sample_table_id)i;" % dict(
                sample_table_id = sample_table.id
            )
        ):
            years.add(
                sample_table.date_mapper.to_date(time_period).year
            )
        return years

def init_SampleTables():    
    for SampleTableType in sample_table_types:
        for sample_table_spec in db(
            (db.climate_sample_table_spec.sample_type_code == SampleTableType.code) 
        ).select(
            orderby = db.climate_sample_table_spec.name
        ):
            sample_type_code = sample_table_spec.sample_type_code
            parameter_name = sample_table_spec.name
            sample_type = sample_table_types_by_code[
                sample_table_spec.sample_type_code
            ]
            date_mapper = SampleTable._SampleTable__date_mapper
            SampleTable(
                name = sample_table_spec.name,
                id = sample_table_spec.id,
                units_name = sample_table_spec.units,
                field_type = sample_table_spec.field_type,
                date_mapping_name = sample_table_spec.date_mapping,
                sample_type = sample_type,
                grid_size = sample_table_spec.grid_size,
                db = db
            )

SampleTable.init_SampleTables = staticmethod(init_SampleTables)
