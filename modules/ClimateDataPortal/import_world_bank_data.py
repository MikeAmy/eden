# -*- coding: utf-8 -*-

if __name__ == "__main__":
    import sys
    print sys.argv[2:]
    statistic_arg, variable_arg, scenario_arg = sys.argv[2:]
    
    if statistic_arg.endswith("anom") and scenario_arg == "20c3m":
        raise Exception("No anomaly data for past years")
    
    import simplejson
    import urllib2
    ClimateDataPortal = local_import("ClimateDataPortal")
    units_in_out = ClimateDataPortal.units_in_out

    years = (
        (1920, 1939),
        (1940, 1959),
        (1960, 1979),
        (1980, 1999),
        
        (2020, 2039),
        (2040, 2059),
        (2060, 2079),
        (2080, 2099)
    )

    future = (
        (2020, 2039),
        (2040, 2059),
        (2060, 2079),
        (2080, 2099)
    )

    past = (
        (1920, 1939),
        (1940, 1959),
        (1960, 1979),
        (1980, 1999),
    )


    anom_years = (    
        (2020, 2039),
        (2040, 2059),
        (2060, 2079),
        (2080, 2099)
    )


    statistic = []
    for s in [
        ("mavg", ("Monthly Avg.", years)),
        ("annualavg", ("Annual Average", years)),
        ("manom", ("Monthly Anomaly", anom_years)),
        ("annualanom", ("Annual Anomaly", anom_years))
    ]:
        name = s[0]
        if name == statistic_arg:
            statistic.append(s)

    variables = {}
    for k, v in {
        "pr": ("Precip.", "Precipitation mm", "Precipitation mm"),
        "tas": ("Temp.",  "Celsius", "Kelvin"),
    }.iteritems():
        if k == variable_arg:
            variables[k] = v

    # get all of these back each response
    gcms = {
        "bccr_bcm2_0": "BCM 2.0",
        "csiro_mk3_5": "CSIRO Mark 3.5",
        "ingv_echam4": "ECHAM 4.6",
        "cccma_cgcm3_1": "CGCM 3.1 (T47)",
        "cnrm_cm3": "CNRM CM3",
        "gfdl_cm2_0": "GFDL CM2.0",
        "gfdl_cm2_1": "GFDL CM2.1",
        "ipsl_cm4": "IPSL-CM4",
        "miroc3_2_medres": "MIROC 3.2 (medres)",
        "miub_echo_g": "ECHO-G",
        "mpi_echam5": "ECHAM5/MPI-OM",
        "mri_cgcm2_3_2a": "MRI-CGCM2.3.2",
        "inmcm3_0": "INMCM3.0",
        "ukmo_hadcm3": "UKMO HadCM3",
        "ukmo_hadgem1": "UKMO HadGEM1"
    }


    scenarios = {}
    for k, v in {
        "a2":    ("Scen. A2", future),
        "b1":    ("Scen. B1", future),
        "20c3m": ("Baseline", past)
    }.iteritems():
        if k == scenario_arg:
            scenarios[k] = v

    InsertChunksWithoutCheckingForExistingReadings = local_import(
        "ClimateDataPortal.InsertChunksWithoutCheckingForExistingReadings"
    ).InsertChunksWithoutCheckingForExistingReadings

    sample_tables = []
    Projected = ClimateDataPortal.Projected
    SampleTable = ClimateDataPortal.SampleTable

    importers = {}
    def setup_sample_tables():
        for variable, (variable_name, units_name, standard_unit) in variables.iteritems():
            for gcm, gcm_name in gcms.iteritems():
                for sres_code, (scenario, _) in scenarios.iteritems():
                    for statistic_code, (statistic_name, years) in statistic:
                        key = (statistic_code, variable, gcm, sres_code)
                        parameter_name = " ".join(
                            (statistic_name, variable_name, gcm_name, scenario)
                        )
                        field_type = "real"
                        sample_table = SampleTable.matching(
                            parameter_name,
                            Projected.code
                        )
                        if sample_table is None:
                            def write_message(sample_table_name):
                                print "Added", sample_table_name, "Projected", parameter_name
                                print "  containing", units_name, "values of type", field_type

                            sample_table = SampleTable(
                                name = parameter_name,
                                sample_type = Projected,
                                units_name = standard_unit,
                                field_type = field_type,
                                date_mapping_name = "twenty_years_by_month",
                                grid_size = 0,
                                db = db
                            )
                            sample_table.create(write_message)
                        else:
                            sample_table.clear()
                        if statistic_code.endswith("anom") and scenario_arg == "20c3m":
                            def write(sample_table_name):
                                print "Dropping", sample_table_name
                            sample_table.drop(write)
                        sample_tables.append(sample_table)
                        importers[key] = (
                            InsertChunksWithoutCheckingForExistingReadings(
                                sample_table
                            ),
                            units_in_out[units_name]["in"]
                        )
        db.commit()

    setup_sample_tables()

    places = {}
    def setup_places():
        for place_row in db(
            db.climate_place.id > 0
        ).select(
            db.climate_place.id,
            db.climate_place.longitude,
            db.climate_place.latitude,
            db.climate_place_iso3_code.iso3_code,
            left = (
                db.climate_place_iso3_code.on(
                    db.climate_place_iso3_code.id == db.climate_place.id
                ),
            )
        ):
            places[place_row.climate_place_iso3_code.iso3_code] = place_row.climate_place.id
    setup_places()

    def import_model_data(
        iso3_code, statistic_code, gcm, fromYear, 
        toYear, monthVals, variable, 
        sres_code,
        scenario = "20c3m"
    ):
        assert scenario == sres_code
        sample_table_name = gcm+" "+variable
        key = (statistic_code, variable, gcm, sres_code)
        for month, value in zip(range(1,13), monthVals):
            importer, converter = importers[key]
            importer(
                importer.sample_table.date_mapper.year_month_day_to_time_period(
                    fromYear, month, None
                ),
                places[iso3_code],
                converter(value)
            )

    def import_all_data():
        import operator
        print reduce(operator.mul, map(len, (scenarios, statistic, variables, past, places)))
        for sres_code, (scenario, years) in scenarios.iteritems():
            for statistic_code, (statistic_name, _) in statistic:
                for var in variables.keys():
                    for (start_year, end_year) in years:
                        for iso3_code in places.keys():
                            url = (
                                "http://climatedataapi.worldbank.org/climateweb/rest/v1/country/"
                                "%(statistic_code)s/%(sres_code)s/%(var)s/%(start_year)i/%(end_year)i/%(iso3_code)s.json" % locals()
                            )
                            print url
                            response = urllib2.urlopen(url)
                            response_string = response.read()
                            if response_string != "Invalid country code. Three letters are required":
                                data = simplejson.loads(response_string)
                                for model_data in data:
                                    import_model_data(
                                        iso3_code = iso3_code, 
                                        statistic_code = statistic_code,
                                        sres_code = sres_code,
                                        **model_data
                                    )
                            else:
                                print response_string
        for importer, converter in importers.itervalues():
            importer.done()
    import_all_data()
                    