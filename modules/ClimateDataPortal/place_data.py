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
    lambda place, use: get("station_name", str, place.climate_place_station_name.name, use),
]

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
        features = []
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
            properties = {}
            set_attribute = properties.__setitem__
            for attribute in attributes:
                attribute(place_row, set_attribute)
            features.append({
                "type": "Feature",
                "geometry": JSON.loads(place_row.geojson),
                "properties": properties
            })

        file = open(file_path, "w")
        file.write(
            "".join(
                JSON.dumps(
                    {
                        "type": "FeatureCollection",
                        "features": features
                    }
                )
            )
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
