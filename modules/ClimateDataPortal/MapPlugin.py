# -*- coding: utf-8 -*-

import codecs
from gluon.dal import Expression

from Cache import *
import gluon.contrib.simplejson as JSON
from SampleTable import SampleTable, init_SampleTables
from Units import units_in_out, MeaninglessUnitsException
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
            # Nepal specific
            station_parameters_URL = climate_URL("station_parameter"),
            download_data_URL = climate_URL("download_data"),
            download_timeseries_URL = climate_URL("download_timeseries"),
            
            data_type_label = str(T("Data Type")),# not unicode
            projected_option_type_label = str(# not unicode
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
        understood_expression_string = unicode(expression)        
        units = DSL.units(expression)()
        if units is None:
            analysis_strings = []
            def analysis_out(*things):
                analysis_strings.append(u"".join(map(unicode, things)))
            DSL.analysis(expression)(analysis_out)
            raise MeaninglessUnitsException(
                u"\n".join(analysis_strings)
            )                
        
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
                raise Exception(unicode(values_by_place_data_frame))
            elif values_by_place_data_frame.ncol == 0:
                keys = []
                values = []
            else:
                keys = values_by_place_data_frame.rx2("key")
                values = values_by_place_data_frame.rx2("value")
            
            overlay_data_file = None
            try:
                overlay_data_file = codecs.open(file_path, "w", encoding="utf-8")
                write = overlay_data_file.write
                write(u'{')
                # sent back for acknowledgement:
                write(
                    u'"understood_expression":"'+understood_expression_string.replace(u'"',u'\\"')+u'",'
                )
                write(u'"units":"')
                write(unicode(units))
                write(u'",')
                write(u'"grid_size":%f,' % min(grid_sizes(expression)()))
                
                write(u'"keys":[')
                write(u",".join(map(unicode, keys)))
                write(u'],')
                
                write(u'"values":[')
                write(u",".
                    join(
                        map(
                            lambda value: str(round_to_4_sd(value)),# not unicode
                            values
                        )
                    )
                )
                write(u']')
                write(u'}')
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
            hashlib.md5(understood_expression_string.encode("UTF8")).hexdigest()+".json",
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
        understood_expression_string = unicode(expression)        
        units = DSL.units(expression)()
        if units is None:
            analysis_strings = []
            def analysis_out(*things):
                analysis_strings.append("".join(map(unicode, things)))
            DSL.analysis(expression)(analysis_out)
            raise MeaninglessUnitsException(
                "\n".join(analysis_strings)
            )                
        
        def generate_map_csv_data(file_path):
            R = map_plugin.get_R()
            if place_ids:
                code = DSL.R_Code_for_values(
                    expression,
                    "place_id",
                    "place_id IN (%s)" % ",".join(map(str, place_ids))# not unicode
                )
            else:
                code = DSL.R_Code_for_values(
                    expression,
                    "place_id"
               )
            values_by_place_data_frame = R(code)()
            # R unhelpfully removes empty data frame columns 
            if isinstance(
                values_by_place_data_frame,
                map_plugin.robjects.vectors.StrVector
            ):
                raise Exception(unicode(values_by_place_data_frame))
            elif values_by_place_data_frame.ncol == 0:
                keys = []
                values = []
            else:
                keys = values_by_place_data_frame.rx2("key")
                values = values_by_place_data_frame.rx2("value")
            db = map_plugin.env.db
            try:
                csv_data_file = codecs.open(file_path, "w", encoding="utf-8")

                write = csv_data_file.write
                
                write(u"latitude,longitude,station_id,station_name,elevation,")
                write(unicode(units))
                write("\n"
            
                if place_ids:
                    place_selection = db.climate_place.id.belongs(place_ids)
                else:
                    place_selection = (db.climate_place.id > 0)
                
                places_by_id = {}
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
                    places_by_id[place_row.climate_place.id] = place_row

                for place_id, value in zip(keys, values):
                    place = places_by_id[place_id]
                    write(
                        u",".join(
                            map(
                                unicode, 
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
                    write(u"\n")
            except:
                csv_data_file.close()
                os.unlink(file_path)
                raise
            finally:
                csv_data_file.close()
            
        import hashlib
        return get_cached_or_generated_file(
            map_plugin.env.request.application,
            hashlib.md5(JSON.dumps(
                 [query_expression,place_ids]
            ).encode("UTF8")).hexdigest()+".csv",
            generate_map_csv_data
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
                str(width),# not unicode
                str(height),# not unicode
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

        import md5
        import gluon.contrib.simplejson as JSON
        return get_cached_or_generated_file(
            map_plugin.env.request.application,
            md5.md5(
                JSON.dumps(
                    [query_string, width, height],
                    sort_keys=True,
                ).encode("UTF8")
            ).hexdigest()+".png",
            generate_printable_map_image
        )

    def get_available_years(map_plugin, sample_table_name):
        def generate_years_json(file_path):
            years = list(SampleTable.with_name(sample_table_name).get_available_years())
            years.sort()
            file = open(file_path, "w")
            file.write(str(years))# not unicode
            file.close()
        import md5
        import gluon.contrib.simplejson as JSON
        return get_cached_or_generated_file(
            map_plugin.env.request.application,
            md5.md5(unicode(sample_table_name+u" years").encode("UTF8")).hexdigest()+".json",
            generate_years_json
        )
        

from Method import Method
from DateMapping import Monthly, Yearly, MultipleYearsByMonth
time_period_to_float_year = Method("time_period_to_float_year")

@time_period_to_float_year.implementation(Monthly)
def Monthly_time_period_to_float_year(date_mapper, month_number, offset=0):
    year, month = date_mapper.to_date_tuple(month_number+offset)
    return year + (float(month-1) / 12)

@time_period_to_float_year.implementation(Yearly)
def Yearly_time_period_to_float_year(date_mapper, year_number, **kwargs):
    return float(year_number + date_mapper.start_year)

@time_period_to_float_year.implementation(MultipleYearsByMonth)
def MultipleYearsByMonth_time_period_to_year(date_mapper, time_period, **kwargs):
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
def Monthly_grouping_key(date_mapper, is_yearly_values, previous_december = False):
    if is_yearly_values:
        if previous_december:
            # PreviousDecember handling:
            return "(time_period - ((time_period + 1000008 + %i +1) %% 12))" % date_mapper.start_month_0_indexed
        else:
            # the 1000008 is to add a large enough month offset so that PostgreSQL's
            # modulo function doesn't ever return negatives
            return "(time_period - ((time_period + 1000008 + %i) %% 12))" % date_mapper.start_month_0_indexed
    else:
        return "time_period"

@get_grouping_key.implementation(Yearly)
def Yearly_grouping_key(date_mapper, is_yearly_values, **kwargs):
    return "time_period"

@get_grouping_key.implementation(MultipleYearsByMonth)
def MultipleYearsByMonth_grouping_key(date_mapper, is_yearly_values, **kwargs):
    return "(time_period - ((time_period + 1000008) % 12))"


get_axis_labels = Method("get_axis_labels")
@get_axis_labels.implementation(Monthly)
def Monthly_get_axis_labels(
    date_mapper,
    min_start_time_period,
    max_end_time_period,
    axis_points,
    axis_labels,
    show_months,
    width
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
    show_months,
    width
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
    show_months,
    width
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
        # need to make sure spec_index matches 
        # because the regression lines will be coloured the same
        # as the timeseries lines
        regression_lines = {} # spec_index (int) -> regression
        
        R = map_plugin.get_R()
        c = R("c")
        # TODO: this would all be better in a class
        spec_labels = []
        start_time_periods = []
        end_time_periods = []
        yearly = []
        for (label, spec), spec_index in zip(specs, range(len(specs))):
            query_expression = spec["query_expression"]
            expression = DSL.parse(query_expression)
            understood_expression_string = unicode(expression)
            spec_labels.append(label.encode("UTF8"))
            
            units = DSL.units(expression)()
            unit_string = unicode(units)
            if units is None:
                analysis_strings = []
                def analysis_out(*things):
                    analysis_strings.append(u"".join(map(unicode, things)))
                DSL.analysis(expression)(analysis_out)
                raise MeaninglessUnitsException(
                    u"\n".join(analysis_strings)
                )
            
            date_mapper = DSL.date_mapping(expression)()
            
            is_yearly_values = "Months(" in query_expression
            yearly.append(is_yearly_values)
            grouping_key = get_grouping_key(date_mapper)(
                is_yearly_values,
                previous_december = "Prev" in query_expression
            )
            code = DSL.R_Code_for_values(
                expression, 
                grouping_key,
                "place_id IN (%s)" % ",".join(map(str, spec["place_ids"])) # not unicode
            )
            values_by_time_period_data_frame = R(code)()
            data = {}
            if isinstance(
                values_by_time_period_data_frame,
                map_plugin.robjects.vectors.StrVector
            ):
                raise Exception(unicode(values_by_time_period_data_frame))
            elif not hasattr(values_by_time_period_data_frame, "ncol"):
                # TODO: stop empty place_ids getting in (bug in the JS mapping code)
                import logging
                logging.error((
                        u"Don't understand R object %s:"
                        "\nresulting from %s"
                    ) % (
                        unicode(values_by_time_period_data_frame),
                        code
                    )
                )                
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
                    converter = units_in_out[display_units].to_standard
                                    
                linear_regression = R("{}")
                
                # TODO: Hacky way to do this
                # alternative involves changing the parser
                # Will break if Prev in a dataset name
                previous_december_month_offset = [0,1][
                    is_yearly_values and "Prev" in query_expression
                ]
            
                converted_keys = map(
                    (
                        lambda time_period: 
                            time_period_to_float_year(date_mapper)(
                                time_period,
                                offset = previous_december_month_offset
                            )
                    ),
                    keys
                )
                converted_values = map(converter, values)
                if len(converted_keys) > 0:
                    regression = stats.linregress(converted_keys, converted_values)
                else:
                    # it's possible that there will be no linear regression
                    # if the data is of zero length
                    regression = None
                regression_lines[spec_index] = regression
                
                add = data.__setitem__
                for key, value in zip(keys, values):
                    add(key, value)
                if len(data) > 0:
                    # Date Mapping
                    # TODO: currently assumes monthly values and monthly time_period
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
                        """Add time periods in if they are not in the data
                        so that R generates a meaningful chart (missing values
                        show as white space). Otherwise, missing values shift 
                        other data forward, and the chart will be incorrect.
                        """
                        if not data.has_key(time_period):
                            add_value(None)
                        else:
                            # similar to above (conversion is done twice)
                            add_value(converter(data[time_period]))

                    get_chart_values(date_mapper)(
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
        
        # What happens if there is no data at all?
        min_start_time_period = min(start_time_periods) if len(start_time_periods) > 0 else 1940
        max_end_time_period = max(end_time_periods) if len(end_time_periods) >0 else 2100
        
        show_months = any(not is_yearly for is_yearly in yearly)

        # show only years
        axis_points = []
        axis_labels = []
        
        get_axis_labels(date_mapper)(
            min_start_time_period,
            max_end_time_period,
            axis_points,
            axis_labels,
            show_months,
            width
        )

        R.png(
            filename = file_path,
            width = width,
            height = height
        )
        
        plot_chart = R("""
function (
    n, names, 
    width, height, 
    total_margin_height,
    line_interspacing,
    
    xlab, ylab, 
    plot_type,
    axis_points, 
    axis_labels, axis_orientation,
    ...
) {
    if (n > 0) {
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
    }
    else {
        plot.new()
        text(0.5, 0.5, "(No time series data to display)")
    }
}""" )
        from math import log10, floor, isnan
        for i, regression_line in regression_lines.iteritems():
            if regression_line is None:
                spec_labels[i] += "   (no data)"                
            else:
                slope, intercept, r, p, stderr = regression_line
                if isnan(slope) or isnan(intercept):
                    spec_labels[i] += "   (cannot calculate linear regression)"
                else:
                    if isnan(p):
                        p_str = "NaN"
                    else:
                        p_str = str(round_to_4_sd(p)) # not unicode
                    if isnan(stderr):
                        stderr_str = "NaN"
                    else:
                        stderr_str = str(round_to_4_sd(p)) # not unicode
                        
                    slope_str, intercept_str, r_str = map(
                        str, # not unicode
                        map(round_to_4_sd, (slope, intercept, r))
                    )
                
                    spec_labels[i] += (
                        "   {"
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
            n = len(time_serieses),
            names = spec_labels, # BUG: if unicode query, only first char shows (!!)
            width = width,
            height = height,
            # R uses Normalised Display coordinates.
            # these have been found by recursive improvement 
            # they place the legend legibly. tested up to 8 lines
            total_margin_height = 150,
            line_interspacing = 1.8,
            xlab = "",
            ylab = display_units.encode("UTF8").replace(
                # HACK for Celsius degrees symbol display in R
                "Celsius",
                "\xc2\xb0Celsius"
            ),
            plot_type= "lo"[is_yearly_values],               
            axis_points = axis_points,
            axis_labels = axis_labels,
            axis_orientation = [0,2][show_months], 
            *time_serieses
        )
        
        # R's colour number is the spec index
        for colour_number, regression_line in regression_lines.iteritems():
            if regression_line is not None:
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
        map_plugin.env.request.application,
        "".join((
            md5.md5(
                JSON.dumps(
                    [specs, width, height],
                    sort_keys=True,
                    default=serialiseDate,
                ).encode("UTF8")
            ).hexdigest(),
            ".png"
        )),
        generate_chart
    )

MapPlugin.render_plots = render_plots

def get_csv_timeseries_data(
    map_plugin,
    query_expression,
    place_ids
):
    env = map_plugin.env
    DSL = env.DSL
    
    def generate_csv_data(file_path):        
        R = map_plugin.get_R()
        c = R("c")
        yearly = []

        expression = DSL.parse(query_expression)
        understood_expression_string = unicode(expression)
        
        units = DSL.units(expression)()
        if units is None:
            analysis_strings = []
            def analysis_out(*things):
                analysis_strings.append("".join(map(unicode, things)))
            DSL.analysis(expression)(analysis_out)
            raise MeaninglessUnitsException(
                u"\n".join(analysis_strings)
            )
        else:
            unit_string = unicode(units)
            try:
                display_units = {
                    "Kelvin": "Celsius",
                }[unit_string]
            except KeyError:
                converter = lambda x:x
                display_units = unit_string
            else:
                converter = units_in_out[display_units].to_standard

        date_mapper = DSL.date_mapping(expression)()
        
        is_yearly_values = "Months(" in query_expression
        yearly.append(is_yearly_values)
        grouping_key = get_grouping_key(date_mapper)(
            is_yearly_values,
            previous_december = "Prev" in query_expression
        )
        code = DSL.R_Code_for_values(
            expression, 
            grouping_key,
            "place_id IN (%s)" % ",".join(map(str, place_ids)) # not unicode
        )
        values_by_time_period_data_frame = R(code)()

        display_units = display_units.replace("Celsius", "\xc2\xb0Celsius")
        file = open(file_path, 'w')
        file.write(u'year,month,"%s"\n' % display_units)

        if isinstance(
            values_by_time_period_data_frame,
            map_plugin.robjects.vectors.StrVector
        ):
            raise Exception(unicode(values_by_time_period_data_frame))
        elif not hasattr(values_by_time_period_data_frame, "ncol"):
            # TODO: stop empty place_ids getting in (bug in the JS mapping code)
            import logging
            logging.error((
                    u"Don't understand R object %s:"
                    "\nresulting from %s"
                ) % (
                    unicode(values_by_time_period_data_frame),
                    code
                )
            )                
        elif values_by_time_period_data_frame.ncol == 0:
            pass
        else:
            keys = values_by_time_period_data_frame.rx2("key")
            values = values_by_time_period_data_frame.rx2("value")
            previous_december_month_offset = [0,1][
                is_yearly_values and "Prev" in query_expression
            ]
                        
            data = {}
            add = data.__setitem__
            for time_period, value in zip(keys, values):
                add(time_period + previous_december_month_offset, value)
            time_periods = data.keys()
            time_periods.sort()
            for time_period in time_periods:
                file.write("%s,%s\n" % (
                    ",".join(map(str, date_mapper.to_date_tuple(time_period))), # not unicode
                    round_to_4_sd(converter(data[time_period])))
                )
        file.close()
                
    import md5
    import gluon.contrib.simplejson as JSON
    
    return get_cached_or_generated_file(
        map_plugin.env.request.application,
        "".join((
            md5.md5(
                JSON.dumps(
                    ["timeseries",query_expression,place_ids],
                ).encode("UTF8")
            ).hexdigest(),
            ".csv"
        )),
        generate_csv_data
    )

MapPlugin.get_csv_timeseries_data = get_csv_timeseries_data


import place_data
