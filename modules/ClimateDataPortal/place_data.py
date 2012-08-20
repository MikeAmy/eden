from MapPlugin import *

__all__ = ()

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
        out(str(value - last_value[0]))# not unicode
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
        lambda value: out(unicode(value)),
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
        "station_name",
        lambda place: place.climate_place_station_name.name, 
        lambda name: '"%s"' % name.replace('"', '\\"'),
        no_compression
    )
]

def place_data(map_plugin):
    def generate_places(file_path):
        "return all place data in JSON format"
        db = map_plugin.env.db
                    
        places_by_attribute_groups = {}

        for place_row in db(
            # only show Nepal
            (db.climate_place.longitude > 79.5) & 
            (db.climate_place.longitude < 88.5) & 
            (db.climate_place.latitude > 26.0) & 
            (db.climate_place.latitude < 30.7)
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

MapPlugin.place_data = place_data
