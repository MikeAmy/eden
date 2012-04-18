# -*- coding: utf-8 -*-


from gluon.dal import Expression

from Cache import *
import gluon.contrib.simplejson as JSON
from . import SampleTable, units_in_out
from known_units import units_in_out
from DSL.Units import MeaninglessUnitsException
from DSL.GridSizing import MismatchedGridSize
from DSL import aggregations, grid_sizes

from math import log10, floor
def round_to_4_sd(x):
    if x == 0:
        return 0.0
    else:
        return round(x, -int(floor(log10(abs(x)))-3))
                    
def between(items, main, between, *a, **kw):
    # Loop with code that runs between main code
    generator = iter(items)
    try:
        item = generator.next()
    except StopIteration:
        return
    while True:
        main(item, *a, **kw)
        try:
            item = generator.next()
        except StopIteration:
            return
        else:
            between(item, *a, **kw)

import gluon.contrib.simplejson as JSON

import datetime
def serialiseDate(obj):
    if isinstance(
        obj,
        (
            datetime.date, 
            datetime.datetime, 
            datetime.time
        )
    ): 
        return obj.isoformat()[:19].replace("T"," ")
    else:
        raise TypeError("%r is not JSON serializable" % (obj,)) 

import md5


class MapPlugin(object):
    def __init__(
        map_plugin,
        env,
        year_min,
        year_max,
        place_table,
        client_config = {}
    ):
        """client_config (optional) passes configuration dict 
        through to the client-side map plugin.
        """
        map_plugin.env = env
        map_plugin.year_min = year_min 
        map_plugin.year_max = year_max
        map_plugin.place_table = place_table
        map_plugin.client_config = client_config

    def get_R(map_plugin):
        try:
            R = map_plugin.R
        except AttributeError:
            try:
                import rpy2
                import rpy2.robjects as robjects
            except ImportError:
                import logging
                logging.getLogger().error(
            """R is required by the climate data portal to generate charts

            To install R: refer to:
            http://cran.r-project.org/doc/manuals/R-admin.html


            rpy2 is required to interact with python.

            To install rpy2, refer to:
            http://rpy.sourceforge.net/rpy2/doc-dev/html/overview.html
            """)
                raise
            map_plugin.robjects = robjects
            R = map_plugin.R = robjects.r
            env = map_plugin.env
            env.DSL.init_R_interpreter(R, env.deployment_settings.database)
        return R

    def extend_gis_map(map_plugin, add_javascript, add_configuration):
        add_javascript("scripts/S3/s3.gis.climate.js")
        env = map_plugin.env
        SCRIPT = env.SCRIPT
        T = env.T
        import json

        application_name = env.request.application
        
        def climate_URL(url):
            return "/%s/climate/%s" % (application_name, url)
        
        config_dict = dict(
            map_plugin.client_config,
            
            year_min = map_plugin.year_min,
            year_max = map_plugin.year_max,
            
            overlay_data_URL = climate_URL("climate_overlay_data"),
            chart_URL = climate_URL("climate_chart"),
            places_URL = climate_URL("places"),
            chart_popup_URL = climate_URL("chart_popup.html"),
            buy_data_popup_URL = climate_URL("buy_data.html"),
            request_image_URL = climate_URL("request_image"),
            data_URL = climate_URL("data"),
            years_URL = climate_URL("get_years"),
            station_parameters_URL = climate_URL("station_parameter"),
            world_map_URL = climate_URL("../static/data/countries_compressible.json"),
            download_data_URL = climate_URL("download_data"),
            data_type_label = str(T("Data Type")),
            projected_option_type_label = str(
                T("Projection Type")
            ),
            aggregation_names = [
                Aggregation.__name__ for Aggregation in aggregations
            ],
        )
        SampleTable.add_to_client_config_dict(config_dict)
        add_configuration(
            SCRIPT(
                "\n".join((
                    "registerPlugin(",
                    "    new ClimateDataMapPlugin("+
                            json.dumps(
                                config_dict,
                                indent = 4
                            )+
                        ")",
                    ")",
                )),
                _type="text/javascript"
            )
        )

    def get_overlay_data(
        map_plugin,
        query_expression,
    ):
        env = map_plugin.env
        DSL = env.DSL
        expression = DSL.parse(query_expression)
        understood_expression_string = str(expression)        
        units = DSL.units(expression)()
        if units is None:
            analysis_strings = []
            def analysis_out(*things):
                analysis_strings.append("".join(map(str, things)))
            DSL.analysis(expression)(analysis_out)
            raise MeaninglessUnitsException(
                "\n".join(analysis_strings)
            )
        available_grid_sizes = grid_sizes(expression)()
        if len(available_grid_sizes) == 0:
            raise MismatchedGridSize(
                understood_expression_string + 
                "\n# These datasets do not refer to the same sets of places, "
                "so the result set will be empty."
            )
        
        highest_resolution_grid_size = min(available_grid_sizes)
        
        def generate_map_overlay_data(file_path):
            R = map_plugin.get_R()
            code = DSL.R_Code_for_values(expression, "place_id")
            values_by_place_data_frame = R(code)()
            # R willfully removes empty data frame columns 
            # which is ridiculous behaviour
            if isinstance(
                values_by_place_data_frame,
                map_plugin.robjects.vectors.StrVector
            ):
                raise Exception(str(values_by_place_data_frame))
            elif values_by_place_data_frame.ncol == 0:
                keys = []
                values = []
            else:
                keys = values_by_place_data_frame.rx2("key")
                values = values_by_place_data_frame.rx2("value")
            
            overlay_data_file = None
            try:
                overlay_data_file = open(file_path, "w")
                write = overlay_data_file.write
                write('{')
                # sent back for acknowledgement:
                write(
                    '"understood_expression":"%s",'.__mod__(
                        understood_expression_string.replace('"','\\"')
                    )
                )
                write('"units":"%s",' % units)
                write('"grid_size":%f,' % highest_resolution_grid_size)
                
                write('"keys":[')
                write(",".join(map(str, keys)))
                write('],')
                
                write('"values":[')
                write(",".
                    join(
                        map(
                            lambda value: str(round_to_4_sd(value)),
                            values
                        )
                    )
                )
                write(']')
                write('}')
            except:
                if overlay_data_file:
                    overlay_data_file.close()
                os.unlink(file_path)
                raise
            finally:
                overlay_data_file.close()
            
        import hashlib
        return get_cached_or_generated_file(
            map_plugin.env.request.application,
            hashlib.md5(understood_expression_string).hexdigest()+".json",
            generate_map_overlay_data
        )
    
    def get_csv_location_data(
        map_plugin,
        query_expression,
        place_ids
    ):
        env = map_plugin.env
        DSL = env.DSL
        expression = DSL.parse(query_expression)
        understood_expression_string = str(expression)        
        units = DSL.units(expression)()
        if units is None:
            analysis_strings = []
            def analysis_out(*things):
                analysis_strings.append("".join(map(str, things)))
            DSL.analysis(expression)(analysis_out)
            raise MeaninglessUnitsException(
                "\n".join(analysis_strings)
            )                
        
        def generate_map_csv_data(file_path):
            R = map_plugin.get_R()
            code = DSL.R_Code_for_values(expression, "place_id")
            if place_ids:
                code = DSL.R_Code_for_values(
                    expression,
                    "place_id",
                    "place_id IN (%s)" % ",".join(map(str, place_ids))
                )
            else:
                code = DSL.R_Code_for_values(
                    expression,
                    "place_id"
                )
            values_by_place_data_frame = R(code)()
            # R willfully removes empty data frame columns 
            # which is ridiculous behaviour
            if isinstance(
                values_by_place_data_frame,
                map_plugin.robjects.vectors.StrVector
            ):
                raise Exception(str(values_by_place_data_frame))
            elif values_by_place_data_frame.ncol == 0:
                keys = []
                values = []
            else:
                keys = values_by_place_data_frame.rx2("key")
                values = values_by_place_data_frame.rx2("value")
            db = map_plugin.env.db
            try:
                csv_data_file = open(file_path, "w")
                write = csv_data_file.write
                
                #min(grid_sizes(expression)())
                write("latitude,longitude,station_id,station_name,elevation,%s\n" % (units))
            
                if place_ids:
                    place_selection = db.climate_place.id.belongs(place_ids)
                else:
                    place_selection = (db.climate_place.id > 0)
                
                places = {}
                for place_row in db(
                    place_selection
                ).select(
                    db.climate_place.id,
                    db.climate_place.longitude,
                    db.climate_place.latitude,
                    db.climate_place_elevation.elevation_metres,
                    db.climate_place_station_id.station_id,
                    db.climate_place_station_name.name,
                    left = (
                        db.climate_place_elevation.on(
                            db.climate_place.id == db.climate_place_elevation.id
                        ),
                        db.climate_place_station_id.on(
                            db.climate_place.id == db.climate_place_station_id.id
                        ),
                        db.climate_place_station_name.on(
                            db.climate_place.id == db.climate_place_station_name.id
                        )
                    )
                ):
                    places[place_row.climate_place.id] = place_row

                for key, value in zip(keys, values):
                    place = places[key]
                    write(
                        ",".join(
                            map(
                                str, 
                                (
                                    place.climate_place.latitude,
                                    place.climate_place.longitude,
                                    place.climate_place_station_id.station_id or "",
                                    place.climate_place_station_name.name or "",
                                    place.climate_place_elevation.elevation_metres or "",
                                    round_to_4_sd(value)
                                )
                            )
                        )
                    )
                    write("\n")
            except:
                csv_data_file.close()
                os.unlink(file_path)
                raise
            finally:
                csv_data_file.close()
            
        import hashlib
        return get_cached_or_generated_file(
            hashlib.md5(JSON.dumps(
                [query_expression,place_ids]
            )).hexdigest()+".csv",
            generate_map_csv_data
        )

    def get_csv_timeseries_data(
        map_plugin,
        query_expression,
        place_ids,
        #label
    ):
        env = map_plugin.env
        DSL = env.DSL
        
        def get_csv_timeseries_data(file_path):
            time_serieses = []
                        
            R = map_plugin.R
            c = R("c")
            starts = []
            ends = []
            yearly = []
            expression = DSL.parse(query_expression)
            understood_expression_string = str(expression)
            units = DSL.units(expression)
            unit_string = str(units)
            if units is None:
                analysis_strings = []
                def analysis_out(*things):
                    analysis_strings.append("".join(map(str, things)))
                DSL.analysis(expression, analysis_out)
                raise MeaninglessUnitsException(
                    "\n".join(analysis_strings)
                )
            is_yearly_values = "Months(" in query_expression
            yearly.append(is_yearly_values)
            if is_yearly_values:
                if "Prev" in query_expression:
                    # PreviousDecember handling:
                    grouping_key = "(time_period - ((time_period + 1000008 + %i +1) %% 12))" % start_month_0_indexed
                else:
                    grouping_key = "(time_period - ((time_period + 1000008 + %i) %% 12))" % start_month_0_indexed
            else:
                grouping_key = "time_period"
            code = DSL.R_Code_for_values(
                expression, 
                grouping_key,
                "place_id IN (%s)" % ",".join(map(str, place_ids))
            )
            #print code
            values_by_time_period_data_frame = R(code)()
            data = {}
            if isinstance(
                values_by_time_period_data_frame,
                map_plugin.robjects.vectors.StrVector
            ):
                raise Exception(str(values_by_time_period_data_frame))
            elif values_by_time_period_data_frame.ncol == 0:
                pass
            else:
                keys = values_by_time_period_data_frame.rx2("key")
                values = values_by_time_period_data_frame.rx2("value")
                try:
                    display_units = {
                        "Kelvin": "Celsius",
                    }[unit_string]
                except KeyError:
                    converter = lambda x:x
                    display_units = unit_string
                else:
                    converter = units_in_out[display_units]["out"]

                previous_december_month_offset = [0,1][is_yearly_values and "Prev" in query_expression]
            
                def month_number_to_float_year(month_number):
                    year, month = month_number_to_year_month(month_number+previous_december_month_offset)
                    return year + (float(month-1) / 12)
                
                add = data.__setitem__
                for key, value in zip(keys, values):
                    #print key, value
                    add(key, value)
                # assume monthly values and monthly time_period
                start_month_number = min(data.iterkeys())
                starts.append(start_month_number)
                start_year, start_month = month_number_to_year_month(
                    start_month_number + previous_december_month_offset
                )

                end_month_number = max(data.iterkeys())
                ends.append(end_month_number)
                end_year, end_month = month_number_to_year_month(
                    end_month_number + previous_december_month_offset
                )
                
                values = []
                for month_number in range(
                    start_month_number,
                    end_month_number+1,
                    [1,12][is_yearly_values]
                ):
                    if not data.has_key(month_number):
                        values.append(None)
                    else:
                        values.append(converter(data[month_number]))
                
                if is_yearly_values:
                    time_series = zip(range(start_year, end_year), values)
                else:
                    time_series = list()
                    year = start_year
                    month = start_month
                    values = iter(values)
                    while (year, month) < (end_year, end_month):
                        time_series.append(
                            ("%i-%i" % (year, month), 
                            values.next())
                        )
                        month += 1
                        if month == 13:
                            month = 1
                            year += 1
            display_units = display_units.replace("Celsius", "\xc2\xb0Celsius")
            try:
                csv_data_file = open(file_path, "w")
                write = csv_data_file.write
                
                write("latitude,longitude,station_id,station_name,elevation,%s\n" % (units))
            
                if place_ids:
                    place_selection = db.climate_place.id.belongs(place_ids)
                else:
                    place_selection = (db.climate_place.id > 0)
                
                places = {}
                for place_row in db(
                    place_selection
                ).select(
                    db.climate_place.id,
                    db.climate_place.longitude,
                    db.climate_place.latitude,
                    db.climate_place_elevation.elevation_metres,
                    db.climate_place_station_id.station_id,
                    db.climate_place_station_name.name,
                    left = (
                        db.climate_place_elevation.on(
                            db.climate_place.id == db.climate_place_elevation.id
                        ),
                        db.climate_place_station_id.on(
                            db.climate_place.id == db.climate_place_station_id.id
                        ),
                        db.climate_place_station_name.on(
                            db.climate_place.id == db.climate_place_station_name.id
                        )
                    )
                ):
                    places[place_row.climate_place.id] = place_row

                for key, value in zip(keys, values):
                    place = places[key]
                    write(
                        ",".join(
                            map(
                                str, 
                                (
                                    place.climate_place.latitude,
                                    place.climate_place.longitude,
                                    place.climate_place_station_id.station_id or "",
                                    place.climate_place_station_name.name or "",
                                    place.climate_place_elevation.elevation_metres or "",
                                    round_to_4_sd(value)
                                )
                            )
                        )
                    )
                    write("\n")
            except:
                csv_data_file.close()
                os.unlink(file_path)
                raise
            finally:
                csv_data_file.close()

        return get_cached_or_generated_file(
            map_plugin.env.request.application,
            "".join((
                md5.md5(
                    JSON.dumps(
                        [query_expression, place_ids],
                        sort_keys=True,
                        default=serialiseDate,
                    )
                ).hexdigest(),
                ".csv"
            )),
            get_csv_timeseries_data
        )
        
    
    
    def place_data(map_plugin):
        def generate_places(file_path):
            "return all place data in JSON format"
            db = map_plugin.env.db
            
            class Attribute(object):
                def __init__(attribute, name, getter, convert, compressor):
                    def get(object, use):
                        value = getter(object)
                        if value is not None:
                            use(attribute, convert(value))
                    attribute.name = name
                    attribute.get = get
                    attribute.compressor = compressor
                    
                def __repr__(attribute):
                    return "@"+attribute.name
                    
                def compress(attribute, places, use_string):
                    attribute.compressor(attribute, places, use_string)
            
            def similar_numbers(attribute, places, out):
                out("[")
                last_value = [0]
                def write_value(value):
                    out(str(value - last_value[0]))
                    last_value[0] = value
                between(
                    (place[attribute] for place in places),
                    write_value,
                    lambda value: out(",")
                )
                out("]")

            def no_compression(attribute, places, out):
                out("[")
                between(
                    (place[attribute] for place in places),
                    lambda value: out(str(value)),
                    lambda value: out(",")
                )
                out("]")
                
            attributes = [
                Attribute(
                    "id",
                    lambda place: place.climate_place.id, 
                    int,
                    similar_numbers
                ),
                Attribute(
                    "longitude",
                    lambda place: place.climate_place.longitude, 
                    round_to_4_sd,
                    similar_numbers
                ),
                Attribute(
                    "latitude",
                    lambda place: place.climate_place.latitude, 
                    round_to_4_sd,
                    similar_numbers
                ),
                Attribute(
                    "elevation",
                    lambda place: place.climate_place_elevation.elevation_metres, 
                    int,
                    no_compression
                ),
                Attribute(
                    "station_id",
                    lambda place: place.climate_place_station_id.station_id, 
                    int,
                    similar_numbers
                ),
                Attribute(
                    "ISO_code",
                    lambda place: place.climate_place_iso3_code.iso3_code, 
                    '"%s"'.__mod__,
                    no_compression
                ),
                Attribute(
                    "station_name",
                    lambda place: place.climate_place_station_name.name, 
                    lambda name: '"%s"' % name.replace('"', '\\"'),
                    no_compression
                )
            ]
            
            places_by_attribute_groups = {}

            for place_row in db(
                db.climate_place.id > 0
            ).select(
                db.climate_place.id,
                db.climate_place.longitude,
                db.climate_place.latitude,
                db.climate_place_elevation.elevation_metres,
                db.climate_place_station_id.station_id,
                db.climate_place_iso3_code.iso3_code,
                db.climate_place_station_name.name,
                left = (
                    db.climate_place_elevation.on(
                        db.climate_place.id == db.climate_place_elevation.id
                    ),
                    db.climate_place_station_id.on(
                        db.climate_place.id == db.climate_place_station_id.id
                    ),
                    db.climate_place_iso3_code.on(
                        db.climate_place.id == db.climate_place_iso3_code.id
                    ),
                    db.climate_place_station_name.on(
                        db.climate_place.id == db.climate_place_station_name.id
                    )
                ),
                orderby = db.climate_place.id
            ):
                place_data = {}
                for attribute in attributes:
                    attribute.get(place_row, place_data.__setitem__)
                attributes_given = place_data.keys()
                attributes_given.sort(key = lambda attribute: attribute.name)
                attribute_group = tuple(attributes_given)
                try:
                    places_for_these_attributes = places_by_attribute_groups[attribute_group]
                except KeyError:
                    places_for_these_attributes = places_by_attribute_groups[attribute_group] = []
                places_for_these_attributes.append(place_data)
                
            places_strings = []
            out = places_strings.append
            out("[")

            def add_data_for_attribute_group((attribute_group, places)):
                out("{\"attributes\":[")
                double_quote = '"%s"'.__mod__
                between(
                    attribute_group,
                    lambda attribute: out(double_quote(attribute.name)),
                    lambda attribute: out(",")
                )
                out("],\"compression\":[")
                between(
                    attribute_group,
                    lambda attribute: out(double_quote(attribute.compressor.__name__)),
                    lambda attribute: out(",")
                )
                out("],\n\"places\":[")
                between(
                    attribute_group,
                    lambda attribute: attribute.compress(places, out),
                    lambda attribute: out(",")
                )
                out("]}")
            
            between(
                places_by_attribute_groups.iteritems(),
                add_data_for_attribute_group,
                lambda item: out(","),
            )
                    
            out("]")

            file = open(file_path, "w")
            file.write(
                "".join(places_strings)
            )
            file.close()
        
        return get_cached_or_generated_file(
            map_plugin.env.request.application,
            "places.json",
            generate_places
        )
    
    def printable_map_image_file(map_plugin, command, url_prefix, query_string, width, height):
        def generate_printable_map_image(file_path):
            import urllib
            url = url_prefix+"?"+query_string+"&display_mode=print"
                        
            # PyQT4 signals don't like not being run in the main thread
            # run in a subprocess to give it it's own thread
            
            if os.system("xvfb-run -help") == 0:
                command_prefix = (
                    "xvfb-run "+
                    '"--server-args=-screen 0, 640x480x24" '+
                    '--auto-servernum '
                )
            else:
                command_prefix = ""
            subprocess_args = (
                url,
                str(width),
                str(height),
                file_path
            )                
  
            command_string = (
                command_prefix + 
                command+" "+(
                    " ".join(
                        map("'%s'".__mod__, subprocess_args)
                    )
                )
            )
            os.system(command_string)
  
        return get_cached_or_generated_file(
            map_plugin.env.request.application,
            md5.md5(
                JSON.dumps(
                    [query_string, width, height],
                    sort_keys=True,
                )
            ).hexdigest()+".png",
            generate_printable_map_image
        )

    def get_available_years(map_plugin, sample_table_name):
        def generate_years_json(file_path):
            file = open(file_path, "w")
            years = list(SampleTable.with_name(sample_table_name).get_available_years())
            years.sort()
            file.write(str(years))
            file.close()
        
        import md5
        import gluon.contrib.simplejson as JSON
        return get_cached_or_generated_file(
            map_plugin.env.request.application,
            md5.md5(sample_table_name+" years").hexdigest()+".json",
            generate_years_json
        )
        
from . import Method
from DateMapping import Monthly, Yearly, MultipleYearsByMonth
time_period_to_float_year = Method("time_period_to_float_year")

@time_period_to_float_year.implementation(Monthly)
def Monthly_time_period_to_float_year(date_mapper, month_number):
    year, month = date_mapper.to_date_tuple(month_number+previous_december_month_offset)
    return year + (float(month-1) / 12)

@time_period_to_float_year.implementation(Yearly)
def Yearly_time_period_to_float_year(date_mapper, year_number):
    return float(year_number + date_mapper.start_year)

@time_period_to_float_year.implementation(MultipleYearsByMonth)
def MultipleYearsByMonth_time_period_to_year(date_mapper, time_period):
    return float(date_mapper.to_date(time_period).year)



time_series_args = Method("time_series_args")
@time_series_args.implementation(Monthly)
def Monthly_time_series(date_mapper, is_yearly_values, use_kwargs):
    if is_yearly_values:
        use_kwargs(frequency = 1)
    else:
        use_kwargs(frequency = 12)

@time_series_args.implementation(Yearly)
def Monthly_time_series(date_mapper, is_yearly_values, use_kwargs):
    use_kwargs(frequency = 1)

@time_series_args.implementation(MultipleYearsByMonth)
def MultipleYearsByMonth_time_series_args(date_mapper, is_yearly_values, use_kwargs):
    use_kwargs(deltat = 20)
                

get_grouping_key = Method("get_grouping_key")

@get_grouping_key.implementation(Monthly)
def Monthly_grouping_key(date_mapper, is_yearly_values):
    if is_yearly_values:
        if "Prev" in query_expression:
            # PreviousDecember handling:
            return "(time_period - ((time_period + 1000008 + %i +1) %% 12))" % date_mapper.start_month_0_indexed
        else:
            return "(time_period - ((time_period + 1000008 + %i) %% 12))" % date_mapper.start_month_0_indexed
    else:
        return "time_period"

@get_grouping_key.implementation(Yearly)
def Yearly_grouping_key(date_mapper, is_yearly_values):
    return "time_period"

@get_grouping_key.implementation(MultipleYearsByMonth)
def MultipleYearsByMonth_grouping_key(date_mapper, is_yearly_values):
    return "(time_period - ((time_period + 1000008) % 12))"


get_axis_labels = Method("get_axis_labels")
@get_axis_labels.implementation(Monthly)
def Monthly_get_axis_labels(
    date_mapper,
    min_start_time_period,
    max_end_time_period,
    axis_points,
    axis_labels,
    show_months
):
    if show_months:
        # label_step spaces out the x-axis marks sensibly based on
        # width by not marking all of them.
        ticks = (max_end_time_period - min_start_time_period) + 1
        # ticks should be made at 1,2,3,4,6,12 month intervals 
        # or 1, 2, 5, 10, 20, 50 year intervals
        # depending on the usable width and the number of ticks
        # ticks should be at least 15 pixels apart
        usable_width = width - 100
        max_ticks = usable_width / 15.0
        Y = 12
        for step in [1,2,3,4,6,12,2*Y, 5*Y, 10*Y, 20*Y, 50*Y]:
            if ticks/step <= max_ticks:
                break
        month_names = (
            "Jan Feb Mar Apr May Jun "
            "Jul Aug Sep Oct Nov Dec"
        ).split(" ")
        for month_number in range(
            min_start_time_period,
            max_end_time_period+1,
            step
        ):
            year, month = date_mapper.to_date_tuple(month_number)
            month -= 1
            axis_points.append(
                year + (month / 12.0)
            )
            axis_labels.append(
                "%s %i" % (month_names[month], year)
            )
    else:
        start_year, start_month = date_mapper.to_date_tuple(min_start_time_period)
        end_year, end_month = date_mapper.to_date_tuple(max_end_time_period)
        for year in range(start_year, end_year+1):
            axis_points.append(year)
            axis_labels.append(year)

@get_axis_labels.implementation(Yearly)
def Monthly_get_axis_labels(
    date_mapper,
    min_start_time_period,
    max_end_time_period,
    axis_points,
    axis_labels,
    show_months
):
    start_year, = date_mapper.to_date_tuple(min_start_time_period)
    end_year, = date_mapper.to_date_tuple(max_end_time_period)
    for year in range(start_year, end_year+1):
        axis_points.append(year)
        axis_labels.append(year)

@get_axis_labels.implementation(MultipleYearsByMonth)
def MultipleYearsByMonth_axis_labels(
    date_mapper,
    min_start_time_period,
    max_end_time_period, 
    axis_points,
    axis_labels,
    show_months
):
    start_year = date_mapper.to_date_tuple(min_start_time_period)[0]
    end_year = date_mapper.to_date_tuple(max_end_time_period)[0]
    for year in range(start_year, end_year+1, 20):
        axis_points.append(year)
        axis_labels.append("%i - %i" % (year, year+19))

get_chart_values = Method("get_chart_values")

@get_chart_values.implementation(MultipleYearsByMonth)
@get_chart_values.implementation(Monthly)
def get_NonYearly_chart_values(
    date_mapper,
    start_time_period,
    end_time_period,
    is_yearly_values,
    use
):
    for time_period in range(
        start_time_period,
        end_time_period+1,
        [1,12][is_yearly_values]
    ):
        use(time_period)

@get_chart_values.implementation(Yearly)
def get_Yearly_chart_values(
    date_mapper,
    start_time_period,
    end_time_period,
    is_yearly_values,
    use
):
    for time_period in range(
        start_time_period,
        end_time_period+1
    ):
        use(time_period)

def render_plots(
    map_plugin,
    specs,
    width,
    height
):
    env = map_plugin.env
    DSL = env.DSL
    
    def generate_chart(file_path):
        time_serieses = []
        
        from scipy import stats
        regression_lines = []
        
        R = map_plugin.get_R()
        c = R("c")
        spec_names = []
        start_time_periods = []
        end_time_periods = []
        yearly = []
        for label, spec in specs:
            query_expression = spec["query_expression"]
            expression = DSL.parse(query_expression)
            understood_expression_string = str(expression)
            spec_names.append(label)
            
            units = DSL.units(expression)()
            unit_string = str(units)
            if units is None:
                analysis_strings = []
                def analysis_out(*things):
                    analysis_strings.append("".join(map(str, things)))
                DSL.analysis(expression)(analysis_out)
                raise MeaninglessUnitsException(
                    "\n".join(analysis_strings)
                )
            
            date_mapper = DSL.date_mapping(expression)()
            
            is_yearly_values = True #"Months(" in query_expression
            yearly.append(is_yearly_values)
            grouping_key = get_grouping_key(date_mapper)(is_yearly_values)
            code = DSL.R_Code_for_values(
                expression, 
                grouping_key,
                "place_id IN (%s)" % ",".join(map(str, spec["place_ids"]))
            )
            #print code
            values_by_time_period_data_frame = R(code)()
            data = {}
            if isinstance(
                values_by_time_period_data_frame,
                map_plugin.robjects.vectors.StrVector
            ):
                raise Exception(str(values_by_time_period_data_frame))
            elif values_by_time_period_data_frame.ncol == 0:
                pass
            else:
                keys = values_by_time_period_data_frame.rx2("key")
                values = values_by_time_period_data_frame.rx2("value")
                try:
                    display_units = {
                        "Kelvin": "Celsius",
                    }[unit_string]
                except KeyError:
                    converter = lambda x:x
                    display_units = unit_string
                else:
                    converter = units_in_out[display_units]["out"]
                                    
                linear_regression = R("{}")
                
                previous_december_month_offset = [0,1][
                    is_yearly_values and "Prev" in query_expression
                ]
            
                converted_keys = map(
                    (
                        lambda time_period: 
                            time_period_to_float_year(date_mapper)(time_period)
                    ),
                    keys
                )
                converted_values = map(converter, values) 
                regression_lines.append(
                    stats.linregress(converted_keys, converted_values)
                )
                
                add = data.__setitem__
                for key, value in zip(keys, values):
                    add(key, value)
                # Date Mapping
                # currently assumes monthly values and monthly time_period
                start_time_period = min(data.iterkeys())
                start_time_periods.append(start_time_period)
                start = date_mapper.to_date_tuple(
                    start_time_period + previous_december_month_offset
                )

                end_time_period = max(data.iterkeys())
                end_time_periods.append(end_time_period)
                end = date_mapper.to_date_tuple(
                    end_time_period + previous_december_month_offset
                )

                values = []
                add_value = values.append
                def use_time_period(time_period):
                    if not data.has_key(time_period):
                        add_value(None)
                    else:
                        add_value(converter(data[time_period]))

                get_chart_values(
                    date_mapper
                )(
                    start_time_period,
                    end_time_period,
                    is_yearly_values,
                    use_time_period
                )
                                
                def append_time_series(**kwargs):
                    time_serieses.append(
                        R("ts")(
                            map_plugin.robjects.FloatVector(values),
                            start = c(*start),
                            end = c(*end),
                            **kwargs
                        )
                    )
                time_series_args(date_mapper)(is_yearly_values, append_time_series)

        min_start_time_period = min(start_time_periods)
        max_end_time_period = max(end_time_periods)
        
        show_months = any(not is_yearly for is_yearly in yearly)

        # show only years
        axis_points = []
        axis_labels = []
        
        get_axis_labels(
            date_mapper
        )(
            min_start_time_period,
            max_end_time_period,
            axis_points,
            axis_labels,
            show_months
        )

        display_units = display_units.replace("Celsius", "\xc2\xb0Celsius")

        R.png(
            filename = file_path,
            width = width,
            height = height
        )
        
        plot_chart = R("""
function (
xlab, ylab, n, names, axis_points, 
axis_labels, axis_orientation, 
plot_type,
width, height, 
total_margin_height,
line_interspacing,
...
) {
split_names <- lapply(
    names,
    strwrap, width=(width - 100)/5
)
wrapped_names <- lapply(
    split_names,
    paste, collapse='\n'
)
legend_line_count = sum(sapply(split_names, length))
legend_height_inches <- grconvertY(
    -(
        (legend_line_count * 11) + 
        (length(wrapped_names) * 6) + 30
    ),
    "device",
    "inches"
) - grconvertY(0, "device", "inches")
par(
    xpd = T,
    mai = (par()$mai + c(legend_height_inches , 0, 0, 0))
)
ts.plot(...,
    gpars = list(
        xlab = xlab,
        ylab = ylab,
        col = c(1:n),
        pch = c(21:25),
        type = plot_type,
        xaxt = 'n'
    )
)
axis(
    1, 
    at = axis_points,
    labels = axis_labels,
    las = axis_orientation
)
legend(
    par()$usr[1],
    par()$usr[3] - (
        grconvertY(0, "device", "user") -
        grconvertY(70, "device", "user")
    ),
    wrapped_names,
    cex = 0.8,
    pt.bg = c(1:n),
    pch = c(21:25),
    bty = 'n',
    y.intersp = line_interspacing,
    text.width = 3
)
}""" )
        from math import log10, floor, isnan
        for regression_line, i in zip(
            regression_lines,
            range(len(time_serieses))
        ):
            slope, intercept, r, p, stderr = regression_line
            if isnan(slope) or isnan(intercept):
                spec_names[i] += "   {cannot calculate linear regression}"
            else:
                if isnan(p):
                    p_str = "NaN"
                else:
                    p_str = str(round_to_4_sd(p))
                if isnan(stderr):
                    stderr_str = "NaN"
                else:
                    stderr_str = str(round_to_4_sd(p))
                    
                slope_str, intercept_str, r_str = map(
                    str,
                    map(round_to_4_sd, (slope, intercept, r))
                )
            
                spec_names[i] += (
                    u"   {"
                        "y=%(slope_str)s x year %(add)s%(intercept_str)s, "
                        "r= %(r_str)s, "
                        "p= %(p_str)s, "
                        "S.E.= %(stderr_str)s"
                    "}"
                ) % dict(
                    locals(),
                    add = [u"+ ",u""][intercept_str.startswith("-")]
                )
                
        plot_chart(
            xlab = "",
            ylab = display_units,
            n = len(time_serieses),
            names = spec_names,
            axis_points = axis_points,
            axis_labels = axis_labels,
            axis_orientation = [0,2][show_months], 
            plot_type= "lo"[is_yearly_values],               
            width = width,
            height = height,
            # R uses Normalised Display coordinates.
            # these have been found by recursive improvement 
            # they place the legend legibly. tested up to 8 lines
            total_margin_height = 150,
            line_interspacing = 1.8,
            *time_serieses
        )
        
        for regression_line, colour_number in zip(
            regression_lines,
            range(len(time_serieses))
        ):
            slope = regression_line[0]
            intercept = regression_line[1]
            if isnan(slope) or isnan(intercept):
                pass
            else:
                R.par(xpd = False)
                R.abline(
                    intercept,
                    slope,
                    col = colour_number+1
                )
        R("dev.off()")
        
        import Image, ImageEnhance

        RGBA = "RGBA"
        def reduce_opacity(image, opacity):
            """Returns an image with reduced opacity."""
            assert opacity >= 0 and opacity <= 1
            if image.mode != RGBA:
                image = image.convert(RGBA)
            else:
                image = image.copy()
            alpha = image.split()[3]
            alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
            image.putalpha(alpha)
            return image
            
        def scale_preserving_aspect_ratio(image, ratio):
            return image.resize(
                map(int, map(ratio.__mul__, image.size))
            )

        def watermark(image, mark, position, opacity=1):
            """Adds a watermark to an image."""
            if opacity < 1:
                mark = reduce_opacity(mark, opacity)
            if image.mode != RGBA:
                image = image.convert(RGBA)
            # create a transparent layer the size of the 
            # image and draw the watermark in that layer.
            layer = Image.new(RGBA, image.size, (0,0,0,0))
            if position == 'tile':
                for y in range(0, image.size[1], mark.size[1]):
                    for x in range(0, image.size[0], mark.size[0]):
                        layer.paste(mark, (x, y))
            elif position == 'scale':
                # scale, but preserve the aspect ratio
                ratio = min(
                    float(image.size[0]) / mark.size[0],
                    float(image.size[1]) / mark.size[1]
                )
                w = int(mark.size[0] * ratio)
                h = int(mark.size[1] * ratio)
                mark = mark.resize((w, h))
                layer.paste(
                    mark,
                    (
                        (image.size[0] - w) / 2,
                        (image.size[1] - h) / 2
                    )
                )
            else:
                layer.paste(mark, position)
            # composite the watermark with the layer
            return Image.composite(layer, image, layer)

        image = Image.open(file_path)
        watermark_image_path = os.path.join(
            os.path.realpath("."),
            "applications",
            map_plugin.env.request.application, 
            "static", "img", 
            "Nepal-Government-Logo.png"
        )
        watermark_image = Image.open(watermark_image_path)
        #watermark_image = scale_preserving_aspect_ratio(watermark_image, 0.5)
        watermark(image, watermark_image, 'scale', 0.05).save(file_path)

    import md5
    import gluon.contrib.simplejson as JSON

    import datetime
    def serialiseDate(obj):
        if isinstance(
            obj,
            (
                datetime.date, 
                datetime.datetime, 
                datetime.time
            )
        ): 
            return obj.isoformat()[:19].replace("T"," ")
        else:
            raise TypeError("%r is not JSON serializable" % (obj,)) 
    
    return get_cached_or_generated_file(
        "".join((
            md5.md5(
                JSON.dumps(
                    [specs, width, height],
                    sort_keys=True,
                    default=serialiseDate,
                )
            ).hexdigest(),
            ".png"
        )),
        generate_chart
    )

MapPlugin.render_plots = render_plots
