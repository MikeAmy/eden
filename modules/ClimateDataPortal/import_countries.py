# -*- coding: utf-8 -*-

import simplejson

import urllib2

countries = {
    'AFG': (4, "Afghanistan"), 
    'ALA': (248, "Åland Islands"), 
    'ALB': (8, "Albania"), 
    'DZA': (12, "Algeria"), 
    'ASM': (16, "American Samoa"), 
    'AND': (20, "Andorra"), 
    'AGO': (24, "Angola"), 
    'AIA': (660, "Anguilla"), 
    'ATG': (28, "Antigua and Barbuda"), 
    'ARG': (32, "Argentina"), 
    'ARM': (51, "Armenia"), 
    'ABW': (533, "Aruba"), 
    'AUS': (36, "Australia"), 
    'AUT': (40, "Austria"), 
    'AZE': (31, "Azerbaijan"), 
    'BHS': (44, "Bahamas"), 
    'BHR': (48, "Bahrain"), 
    'BGD': (50, "Bangladesh"), 
    'BRB': (52, "Barbados"), 
    'BLR': (112, "Belarus"), 
    'BEL': (56, "Belgium"), 
    'BLZ': (84, "Belize"), 
    'BEN': (204, "Benin"), 
    'BMU': (60, "Bermuda"), 
    'BTN': (64, "Bhutan"), 
    'BOL': (68, "Bolivia (Plurinational State of)"), 
    'BES': (535, "Bonaire, Saint Eustatius and Saba"), 
    'BIH': (70, "Bosnia and Herzegovina"), 
    'BWA': (72, "Botswana"), 
    'BRA': (76, "Brazil"), 
    'VGB': (92, "British Virgin Islands"), 
    'BRN': (96, "Brunei Darussalam"), 
    'BGR': (100, "Bulgaria"), 
    'BFA': (854, "Burkina Faso"), 
    'BDI': (108, "Burundi"), 
    'KHM': (116, "Cambodia"), 
    'CMR': (120, "Cameroon"), 
    'CAN': (124, "Canada"), 
    'CPV': (132, "Cape Verde"), 
    'CYM': (136, "Cayman Islands"), 
    'CAF': (140, "Central African Republic"), 
    'TCD': (148, "Chad"), 
    #830, Channel Islands	

    'CHL': (152, "Chile"), 
    'CHN': (156, "China"), 
    'HKG': (344, "China, Hong Kong Special Administrative Region"), 
    'MAC': (446, "China, Macao Special Administrative Region"), 
    'COL': (170, "Colombia"), 
    'COM': (174, "Comoros"), 
    'COG': (178, "Congo"), 
    'COK': (184, "Cook Islands"), 
    'CRI': (188, "Costa Rica"), 
    'CIV': (384, "Côte d'Ivoire"), 
    'HRV': (191, "Croatia"), 
    'CUB': (192, "Cuba"), 
    'CUW': (531, "Curaçao"), 
    'CYP': (196, "Cyprus"), 
    'CZE': (203, "Czech Republic"), 
    'PRK': (408, "Democratic People's Republic of Korea"), 
    'COD': (180, "Democratic Republic of the Congo"), 
    'DNK': (208, "Denmark"), 
    'DJI': (262, "Djibouti"), 
    'DMA': (212, "Dominica"), 
    'DOM': (214, "Dominican Republic"), 
    'ECU': (218, "Ecuador"), 
    'EGY': (818, "Egypt"), 
    'SLV': (222, "El Salvador"), 
    'GNQ': (226, "Equatorial Guinea"), 
    'ERI': (232, "Eritrea"), 
    'EST': (233, "Estonia"), 
    'ETH': (231, "Ethiopia"), 
    'FRO': (234, "Faeroe Islands"), 
    'FLK': (238, "Falkland Islands (Malvinas)"), 
    'FJI': (242, "Fiji"), 
    'FIN': (246, "Finland"), 
    'FRA': (250, "France"), 
    'GUF': (254, "French Guiana"), 
    'PYF': (258, "French Polynesia"), 
    'GAB': (266, "Gabon"), 
    'GMB': (270, "Gambia"), 
    'GEO': (268, "Georgia"), 
    'DEU': (276, "Germany"), 
    'GHA': (288, "Ghana"), 
    'GIB': (292, "Gibraltar"), 
    'GRC': (300, "Greece"), 
    'GRL': (304, "Greenland"), 
    'GRD': (308, "Grenada"), 
    'GLP': (312, "Guadeloupe"), 
    'GUM': (316, "Guam"), 
    'GTM': (320, "Guatemala"), 
    'GGY': (831, "Guernsey"), 
    'GIN': (324, "Guinea"), 
    'GNB': (624, "Guinea-Bissau"), 
    'GUY': (328, "Guyana"), 
    'HTI': (332, "Haiti"), 
    'VAT': (336, "Holy See"), 
    'HND': (340, "Honduras"), 
    'HUN': (348, "Hungary"), 
    'ISL': (352, "Iceland"), 
    'IND': (356, "India"), 
    'IDN': (360, "Indonesia"), 
    'IRN': (364, "Iran (Islamic Republic of)"), 
    'IRQ': (368, "Iraq"), 
    'IRL': (372, "Ireland"), 
    'IMN': (833, "Isle of Man"), 
    'ISR': (376, "Israel"), 
    'ITA': (380, "Italy"), 
    'JAM': (388, "Jamaica"), 
    'JPN': (392, "Japan"), 
    # 832, Jersey	JEY

    'JOR': (400, "Jordan"), 
    'KAZ': (398, "Kazakhstan"), 
    'KEN': (404, "Kenya"), 
    'KIR': (296, "Kiribati"), 
    'KWT': (414, "Kuwait"), 
    'KGZ': (417, "Kyrgyzstan"), 
    'LAO': (418, "Lao People's Democratic Republic"), 
    'LVA': (428, "Latvia"), 
    'LBN': (422, "Lebanon"), 
    'LSO': (426, "Lesotho"), 
    'LBR': (430, "Liberia"), 
    'LBY': (434, "Libya"), 
    'LIE': (438, "Liechtenstein"), 
    'LTU': (440, "Lithuania"), 
    'LUX': (442, "Luxembourg"), 
    'MDG': (450, "Madagascar"), 
    'MWI': (454, "Malawi"), 
    'MYS': (458, "Malaysia"), 
    'MDV': (462, "Maldives"), 
    'MLI': (466, "Mali"), 
    'MLT': (470, "Malta"), 
    'MHL': (584, "Marshall Islands"), 
    'MTQ': (474, "Martinique"), 
    'MRT': (478, "Mauritania"), 
    'MUS': (480, "Mauritius"), 
    'MYT': (175, "Mayotte"),
    'MEX': (484, "Mexico"), 
    'FSM': (583, "Micronesia (Federated States of)"), 
    'MCO': (492, "Monaco"), 
    'MNG': (496, "Mongolia"), 
    'MNE': (499, "Montenegro"), 
    'MSR': (500, "Montserrat"), 
    'MAR': (504, "Morocco"), 
    'MOZ': (508, "Mozambique"), 
    'MMR': (104, "Myanmar"), 
    'NAM': (516, "Namibia"), 
    'NRU': (520, "Nauru"), 
    'NPL': (524, "Nepal"), 
    'NLD': (528, "Netherlands"), 
    'NCL': (540, "New Caledonia"), 
    'NZL': (554, "New Zealand"), 
    'NIC': (558, "Nicaragua"), 
    'NER': (562, "Niger"), 
    'NGA': (566, "Nigeria"), 
    'NIU': (570, "Niue"), 
    'NFK': (574, "Norfolk Island"), 
    'MNP': (580, "Northern Mariana Islands"), 
    'NOR': (578, "Norway"), 
    'PSE': (275, "Occupied Palestinian Territory"), 
    'OMN': (512, "Oman"), 
    'PAK': (586, "Pakistan"), 
    'PLW': (585, "Palau"), 
    'PAN': (591, "Panama"), 
    'PNG': (598, "Papua New Guinea"), 
    'PRY': (600, "Paraguay"), 
    'PER': (604, "Peru"), 
    'PHL': (608, "Philippines"), 
    'PCN': (612, "Pitcairn"), 
    'POL': (616, "Poland"), 
    'PRT': (620, "Portugal"), 
    'PRI': (630, "Puerto Rico"), 
    'QAT': (634, "Qatar"), 
    'KOR': (410, "Republic of Korea"), 
    'MDA': (498, "Republic of Moldova"), 
    'REU': (638, "Réunion"), 
    'ROU': (642, "Romania"), 
    'RUS': (643, "Russian Federation"), 
    'RWA': (646, "Rwanda"), 
    'BLM': (652, "Saint-Barthélemy"), 
    'SHN': (654, "Saint Helena"), 
    'KNA': (659, "Saint Kitts and Nevis"), 
    'LCA': (662, "Saint Lucia"), 
    'MAF': (663, "Saint-Martin (French part)"),

    'SPM': (666, "Saint Pierre and Miquelon"), 
    'VCT': (670, "Saint Vincent and the Grenadines"), 
    'WSM': (882, "Samoa"), 
    'SMR': (674, "San Marino"), 
    'STP': (678, "Sao Tome and Principe"), 
    #680, Sark,  , 
    'SAU': (682, "Saudi Arabia"), 
    'SEN': (686, "Senegal"), 
    'SRB': (688, "Serbia"), 
    'SYC': (690, "Seychelles"), 
    'SLE': (694, "Sierra Leone"), 
    'SGP': (702, "Singapore"), 
    'SXM': (534, "Sint Maarten (Dutch part)"),

    'SVK': (703, "Slovakia"), 
    'SVN': (705, "Slovenia"), 
    'SLB': (90, "Solomon Islands"), 
    'SOM': (706, "Somalia"), 
    'ZAF': (710, "South Africa"), 
    'SSD': (728, "South Sudan"), 
    'ESP': (724, "Spain"), 
    'LKA': (144, "Sri Lanka"), 
    'SDN': (729, "Sudan"), 
    'SUR': (740, "Suriname"), 
    'SJM': (744, "Svalbard and Jan Mayen Islands"), 
    'SWZ': (748, "Swaziland"), 
    'SWE': (752, "Sweden"), 
    'CHE': (756, "Switzerland"), 
    'SYR': (760, "Syrian Arab Republic"), 
    'TJK': (762, "Tajikistan"), 
    'THA': (764, "Thailand"), 
    'MKD': (807, "The former Yugoslav Republic of Macedonia"), 
    'TLS': (626, "Timor-Leste"), 
    'TGO': (768, "Togo"), 
    'TKL': (772, "Tokelau"), 
    'TON': (776, "Tonga"), 
    'TTO': (780, "Trinidad and Tobago"), 
    'TUN': (788, "Tunisia"), 
    'TUR': (792, "Turkey"), 
    'TKM': (795, "Turkmenistan"), 
    'TCA': (796, "Turks and Caicos Islands"), 
    'TUV': (798, "Tuvalu"), 
    'UGA': (800, "Uganda"), 
    'UKR': (804, "Ukraine"), 
    'ARE': (784, "United Arab Emirates"), 
    'GBR': (826, "United Kingdom of Great Britain and Northern Ireland"), 
    'TZA': (834, "United Republic of Tanzania"), 
    'USA': (840, "United States of America"), 
    'VIR': (850, "United States Virgin Islands"), 
    'URY': (858, "Uruguay"), 
    'UZB': (860, "Uzbekistan"), 
    'VUT': (548, "Vanuatu"), 
    'VEN': (862, "Venezuela (Bolivarian Republic of)"), 
    'VNM': (704, "Viet Nam"), 
    'WLF': (876, "Wallis and Futuna Islands"), 
    'ESH': (732, "Western Sahara"), 
    'YEM': (887, "Yemen"), 
    'ZMB': (894, "Zambia"), 
    'ZWE': (716, "Zimbabwe"),
}

example = {
    "id":"ABW",
    "iso2Code":"AW",
    "name":"Aruba",
    "region":{
        "id":"LCN",
        "value":"Latin America & Caribbean (all income levels)"
    },
    "adminregion":{
        "id":"",
        "value":""
    },
    "incomeLevel":{
        "id":"NOC",
        "value":"High income: nonOECD"
    },
    "lendingType":{
        "id":"LNX",
        "value":"Not classified"
    },
    "capitalCity":"Oranjestad",
    "longitude":"-70.0167",
    "latitude":"12.5167"
}


ClimateDataPortal = local_import("ClimateDataPortal")

def import_country(
    id, iso2Code, name, longitude, latitude,
    **other #region, adminregion, incomeLevel, lendingType, capitalCity, 
):
    existing_country = db(
        db.climate_place_iso3_code.iso3_code == id
    ).select().first()
    longitude, latitude = map(float, (longitude, latitude))
    if existing_country is None:
        place_id = climate_place.insert(
            longitude = longitude,
            latitude = latitude                
        )
    else:
        print "Update:"
        place_id = existing_country.id                    
        db(climate_place.id == place_id).update(
            longitude = longitude,
            latitude = latitude                
        )
    def insert_or_update(
        table,
        place_id,
        attribute,
        format,
        value
    ):
        table_name = table._tablename
        if db(table.id == place_id).count() == 0:
            formatted_value = format(value)
            db.executesql(
                "INSERT INTO %(table_name)s "
                "(id, %(attribute)s) "
                "VALUES (%(place_id)i, %(formatted_value)s);" % locals()
            )
        else:
            db(table.id == place_id).update(
                **{attribute: value}
            )
    
    insert_or_update(
        db.climate_place_station_name,
        place_id,
        "name",
        (lambda value: "'%s'" % (value.replace("\'", "''"))),
        name
    )
    try:
        country_iso_number = countries[id][0]
    except KeyError:
        country_iso_number = None
    else:
        insert_or_update(
            db.climate_place_country_iso_number,
            place_id,
            "country_iso_number",
            "'%0.3i'".__mod__,
            country_iso_number
        )        
    insert_or_update(
        db.climate_place_iso3_code,
        place_id,
        "iso3_code",
        repr,
        id
    )
    print place_id, country_iso_number, name, latitude, longitude

if __name__ == "__main__":
    for page in range(1,6):
        for country_data in (
            simplejson.loads(
                urllib2.urlopen(
                    "http://api.worldbank.org/countries?format=json&page=%i" % page
                ).read()
            )[1]
        ):
            if country_data["longitude"] != "":
                import_country(**country_data)
