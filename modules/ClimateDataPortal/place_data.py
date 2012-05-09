from MapPlugin import *

__all__ = ()
import gluon.contrib.simplejson as JSON

def get(attribute, convert, value, use):
    if value is not None:
        use(attribute, convert(value))

class Attribute(object):
    def __init__(attribute, name, getter, compressor):
        attribute.name = name
        attribute.get = getter
        attribute.compressor = compressor
        
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

def similar_lists_of_numbers(attribute, places, out):
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
    lambda place, use: get("id", int, place.climate_place.id, use),
    lambda place, use: get("elevation", int, place.climate_place_elevation.elevation_metres, use),
    lambda place, use: get("station_id", int, place.climate_place_station_id.station_id, use),
    (
        lambda place, use: 
            get(
                "station_name", 
                (lambda name: '"%s"' % name.replace('"', '\\"')),
                place.climate_place_station_name.name,
                use
            )
    )
]
def get_geojson_attributes(place, use):
    geojson = JSON.loads(place.geojson)
    if geojson["type"] == "Point":
        latitude, longitude = geojson["coordinates"]
        use("latitude", latitude)
        use("longitude", longitude)
    elif geojson["type"] == "Polygon":
        latitudes = []
        longitudes = []
        for linear_ring in geojson["coordinates"]:
            for latitude, longitude in linear_ring:
                latitudes.append(latitude)
                longitudes.append(longitude)
        use("latitudes", latitudes)
        use("longitudes", longitudes)

attributes.append(get_geojson_attributes)

compressor = {
    "id": similar_numbers,
    "elevation": no_compression,
    "station_id": similar_numbers,
    "station_name": no_compression,
    "latitude": similar_numbers,
    "longitude": similar_numbers,
    "latitudes": similar_lists_of_numbers,
    "longitudes": similar_lists_of_numbers
}

def place_data(map_plugin, bounding_box):
    def generate_places(file_path):
        "return all place data in JSON format"
        db = map_plugin.env.db
                    
        places_by_attribute_groups = {}
        west, south, east, north = bounding_box
        
        bounding_box_geometry = (
            "POLYGON (("
                "%(west)f %(north)f, "
                "%(east)f %(north)f, "
                "%(east)f %(south)f, "
                "%(west)f %(south)f, "
                "%(west)f %(north)f"
            "))" % locals()
        )
        for place_row in db(
            db.climate_place.wkt.st_intersects(bounding_box_geometry)
        ).select(
            db.climate_place.id,
            db.climate_place.wkt.st_asgeojson().with_alias("geojson"),
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
            ),
            orderby = db.climate_place.id
        ):
            place_data = {}
            set_attribute = place_data.__setitem__
            for attribute in attributes:
                attribute(place_row, set_attribute)
            attributes_given = place_data.keys()
            attributes_given.sort()
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
                lambda attribute: out(double_quote(attribute)),
                lambda attribute: out(",")
            )
            out("],\"compression\":[")
            between(
                attribute_group,
                lambda attribute: out(double_quote(compressor[attribute].__name__)),
                lambda attribute: out(",")
            )
            out("],\n\"places\":[")
            between(
                attribute_group,
                lambda attribute: compressor[attribute](attribute, places, out),
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
        JSON.dumps(dict(
            bbox = bounding_box,
            data = "places"
        ))+".json",
        generate_places
    )

MapPlugin.feature_data = place_data
