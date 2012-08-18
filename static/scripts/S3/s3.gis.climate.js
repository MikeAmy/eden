
// Workaround: see http://stackoverflow.com/questions/4728852/forcing-an-openlayers-markers-layer-to-draw-on-top-and-having-selectable-layers
// This fixes a problem whereby the marker layer doesn't 
// respond to click events

OpenLayers.Handler.Feature.prototype.activate = function() {
    var activated = false;
    if (OpenLayers.Handler.prototype.activate.apply(this, arguments)) {
        //this.moveLayerToTop();
        this.map.events.on({
            "removelayer": this.handleMapEvents,
            "changelayer": this.handleMapEvents,
            scope: this
        });
        activated = true;
    }
    return activated;
};

// Workaround:
// for some reason some features remain styled after being unselected
// so just unselect all features. Takes longer but doesn't confuse the user.
OpenLayers.Control.SelectFeature.prototype.unselectAll = function (options) {
    var layers = this.layers || [this.layer];
    var layer, feature;
    for(var l=0; l<layers.length; ++l) {
        layer = layers[l];
        for(var i=layer.features.length-1; i>=0; --i) {
            feature = layer.features[i];
            if(!options || options.except != feature) {
                this.unselect(feature);
            }
        }
    }
}

function each(array, fn) {
    if (!array) {
        throw new Error(
            ""+array+" is not an array"
        )
    }
    else {
        for (
            var i = 0;
            i < array.length;
            ++i
        ) {
            fn(array[i], i)
        }
    }
}

function walk(items, use_item) {
    if (
        items.constructor === Array
    ) {
        each(
            items,
            function (item) {
                walk(item, use_item)
            }
        )
    }
    else {
        use_item(items)
    }
}
function flatten(items) {
    var result = []
    walk(
        items,
        function (item) {
            result.push(item)
        }
    )
    return result
}

function node(tag_name, attrs, children) {
    var result = $(document.createElement(tag_name))
    for (var key in attrs) {
        if (attrs.hasOwnProperty(key)) {
            result.attr(key, attrs[key])
        }
    }
    result.append.apply(result, flatten(children))
    return result
}
function NodeGenerator(tag_name) {
    return function (/* attrs, child1... */) {
        var attrs = Array.prototype.shift.apply(arguments)
        arguments.constructor = Array
        return node(tag_name, attrs, arguments)
    }
}

INPUT = NodeGenerator('input')
DIV = NodeGenerator('div')
TABLE = NodeGenerator('table')
TR = NodeGenerator('tr')
TD = NodeGenerator('td')
SPAN = NodeGenerator('span')
IMG = NodeGenerator('img')
TEXTAREA = NodeGenerator('textarea')
A = NodeGenerator('a')

var power_pattern = new RegExp('\\^(-?\\d+)', 'g')
function replace_power_with_sup(string) {
    return string.replace(
        power_pattern,
        '<sup>$1</sup>'
    )
}

var ColourKey = OpenLayers.Class(OpenLayers.Control, {
    CLASS_NAME: 'ColourKey',
    /* The colour key is implemented as an OpenLayers control
       so that it gets rendered on the printed map
       attributes:
         plugin
    */
    destroy: function() {
        var colour_key = this
        colour_key.deactivate();
        OpenLayers.Control.prototype.destroy.apply(colour_key, arguments);
    },
    
    set_gradient: function (colour_gradient) {
        var colour_key = this
        colour_key.gradient = colour_gradient
        colour_gradient.manage_image(
            colour_key.$key_colour_key_img
        )
    },
    
    activate: function() {
        var colour_key = this
        if (
            OpenLayers.Control.prototype.activate.apply(colour_key, arguments)
        ) {
            // show colours
            colour_key.set_gradient(colour_key.gradients[0])
            // when the user changes limits, the map colours update instantly
            colour_key.use_callback = function () {
                if (!!colour_key.use_limits) {
                    colour_key.with_limits(colour_key.use_limits)
                }
            }
            colour_key.$lower_limit.change(colour_key.use_callback)
            colour_key.$upper_limit.change(colour_key.use_callback)
            return true;
        } else {
            return false;
        }
    },
    
    deactivate: function() {
        var colour_key = this
        if (
            OpenLayers.Control.prototype.deactivate.apply(colour_key, arguments)
        ) {
            return true;
        } else {
            return false;
        }
    },
    
    with_limits: function (use_limits) {
        // immediately use the limits
        var colour_key = this
        use_limits(
            parseFloat(colour_key.$lower_limit.attr('value')),
            parseFloat(colour_key.$upper_limit.attr('value'))
        )
    },
    
    on_change: function (use_limits) {
        // provide a callback for when the limits change
        // use_limits needs to accept min and max
        this.use_limits = use_limits
    },
    
    update_from: function (
        new_units,
        max_value,
        min_value
    ) {
        // Sets units, and limits (rounded sensibly) from supplied arguments.
        // If the limit lock checkbox is checked, doesn't change limits unless
        // the units change.
        // Calls the callback supplied in on_change with the limits.
        var colour_key = this
        
        var previous_units = colour_key.$units.html()
        colour_key.$units.html(
            replace_power_with_sup(
                new_units
            )
        )

        if (
            // user can lock limits
            !colour_key.$limit_lock.is(':checked')
            
            // but if units change, old limits become meaningless
            || previous_units != new_units
        ) {
            // sensible range
            var significant_digits = 1
            function scaling_factor(value) {
                return Math.pow(
                    10,
                    (
                        Math.floor(
                            Math.log(Math.abs(value)) / Math.LN10
                        ) - (significant_digits - 1)
                    )
                )
            }
            function sensible(value, round) {
                if (value == 0.0) {
                    return 0.0
                }
                else {
                    factor = scaling_factor(value)
                    return round(value/factor) * factor
                }
            }
            range_mag = scaling_factor(
                sensible(max_value, Math.ceil) - 
                sensible(min_value, Math.floor)
            )
            function to_significant_digits(number, sd){
                return parseFloat(number.toPrecision(sd))
            }
                
            // function set_scale(min_value, max_value) {
            min_value = Math.floor(min_value/range_mag) * range_mag
            // if min is near zero (relative to max), just use 0
            if (min_value > 0 && (min_value / max_value) < 0.5) {
                min_value = 0.0
            }
            else {
                min_value = to_significant_digits(min_value, 1)
            }
            max_value = to_significant_digits(
                Math.ceil(max_value/range_mag) * range_mag,
                1
            )
            
            function nice_number_string(number) {
                var result_string = number.toString()
                if (result_string.length > 6) {
                    result_string = number.toPrecision(significant_digits)
                }
                return result_string
            }
            min_value_string = nice_number_string(min_value)
            max_value_string = nice_number_string(max_value)
            colour_key.$lower_limit.attr('value', min_value_string)
            colour_key.$upper_limit.attr('value', max_value_string)
        }
        else {
            min_value = parseFloat(colour_key.$lower_limit.attr('value'))
            max_value = parseFloat(colour_key.$upper_limit.attr('value'))
        }
        colour_key.min_value = min_value
        colour_key.max_value = max_value
        colour_key.use_callback()
    },
            
    draw: function() {
        var colour_key = this
        OpenLayers.Control.prototype.draw.apply(colour_key, arguments);
        
        colour_key.$lower_limit = INPUT({
            size:5, value:'Min',
            style: 'background-color:#222; border:1px solid #888; color:white;'
        })
        colour_key.$upper_limit = INPUT({
            size:5, value:'Max',
            style:'text-align:right; background-color:#222; border:1px solid #888; color:white;'
        })
        colour_key.$limit_lock = INPUT({
            type:'checkbox',
            name:'key-lock',
            id:'key_lock'
        })
        colour_key.$limit_lock_label = $(
            '<label for="key_lock" style="color:white; padding:0.5em;">Lock limits between queries</label>'
        )
        
        var gradient_images = []
        function raise(x) {
            $(this).css('border-top', '1px solid #DDD')
            $(this).css('border-bottom', '1px solid #AAA')
        }
        function lower(x) {
            $(this).css('border-top', '1px solid black')
            $(this).css('border-bottom', '1px solid black')
        }
        each(
            colour_key.gradients,
            function (colour_gradient) {
                var gradient_image = IMG({
                    width:'100%',
                    height:'15px',
                    style:'border-top: 1px solid black; border-bottom: 1px solid black; margin-top: 1px;'
                })
                colour_gradient.manage_image(gradient_image)
                gradient_images.push(gradient_image)
                gradient_image.mouseover(raise)
                gradient_image.mouseout(lower)
                gradient_image.click(function () {
                    colour_key.set_gradient(colour_gradient)
                    colour_key.use_callback()
                })
            }
        )
        colour_key.$controls = DIV(
            {
                style: 'display: none; padding-top: 3px;'
            },
            gradient_images,
            DIV({style:'text-align:center;'},
                colour_key.$limit_lock,
                colour_key.$limit_lock_label
            )
        )
        
        colour_key.$key_colour_key_img = IMG({
            width:'100%',
            height:'15px',
            title:'Click to invert colour gradient'
        })
        colour_key.$gradient = DIV({},
            colour_key.$key_colour_key_img,
            colour_key.$controls
        )
        colour_key.$key_colour_key_img.click(
            function () {
                colour_key.gradient.invert()
                colour_key.use_callback()
            }
        )
        
        colour_key.$units = SPAN({}, 'Units')
        var $div = colour_key.$inner_div = DIV({
                style:'width: 240px; position:absolute; top: 10px; left:55px; background-color:#222; border-top:1px solid #EEE; padding: 4px; border-radius: 5px;color:white;'
            },
            TABLE({
                    width:'100%'
                },
                TR({},
                    TD({
                            style:'width:65px; max-width:60px; text-align:left;'
                        },
                        colour_key.$lower_limit
                    ),
                    TD({
                            style:'text-align:center;'
                        },
                        colour_key.$units
                    ),
                    TD({
                            style:'width:65px; max-width:60px; text-align:right;'
                        },
                        colour_key.$upper_limit
                    )
                )
                // key_scale_tr (unused)
            ),
            colour_key.$gradient
        )
        $div.mouseover(
            function () {
                colour_key.$controls.css('display', 'inline')
            }
        )
        $div.mouseout(
            function () {
                colour_key.$controls.css('display', 'none')
            }
        )
        /*
        // code that draws a scale on the colours as lines, to aid 
        // interpretation. Doesn't work well for some scales
        var scale_divisions = range/range_mag
        alert(''+range+' '+range_mag+' '+scale_divisions)
        
        var scale_html = '';
        for (
            var i = 0;
            i < scale_divisions-1;
            i++
        ) {
            scale_html += '<td style="border-left:1px solid black">&nbsp;</td>'
        }
        $('#id_key_scale_tr').html(
            scale_html+
            '<td style="border-left:1px solid black; border-right:1px solid black;">&nbsp;</td>'
        )
        */

        $(colour_key.div).append($div)
        $div.show()
        return colour_key.div
    },
    
    print_mode: function () {
        var colour_key = this
        colour_key.$limit_lock.hide()
        colour_key.$limit_lock_label.hide()
        colour_key.$inner_div.css('width', 300)
        colour_key.$inner_div.css('left', 10)
    }
});

var TextAreaAutoResizer = function(
    $text_area,
    min_height,
    max_height
) {
    var resizer = this
    resizer.min_height = min_height || 0
    resizer.max_height = max_height || Infinity

    function resize(force) {
        var value_length = $text_area.val().length,
            $text_area_width = $text_area.width
        if (
            force || (
                value_length != resizer.previous_value_length || 
                $text_area_width != resizer.previous_width
            )
        ) {
            $text_area.height(0)
            var height = Math.max(
                resizer.min_height,
                Math.min(
                    $text_area[0].scrollHeight,
                    resizer.max_height
                )
            )
            $text_area.css('overflow',
                $text_area.height() > height ? 'auto' : 'hidden'
            )
            $text_area.height(height)

            resizer.previous_value_length = value_length
            resizer.previous_width = $text_area_width
        }
        return true;
    }
    resizer.resize = resize
    resize()
    $text_area.css('padding-top', 0)
    $text_area.css('padding-bottom', 0)
    $text_area.bind('keyup', resize)
    $text_area.bind('focus', resize)
    return resizer
}

var QueryBox = OpenLayers.Class(OpenLayers.Control, {
    CLASS_NAME: 'QueryBox',
    destroy: function() {
        var query_box = this
        query_box.deactivate()
        query_box.resizer.destroy()
        delete query_box.resizer
        OpenLayers.Control.prototype.destroy.apply(query_box, arguments)
    },
    
    activate: function() {
        var query_box = this
        if (OpenLayers.Control.prototype.activate.apply(query_box, arguments)) {
            return true
        } else {
            return false
        }
    },
    
    deactivate: function() {
        var query_box = this
        if (OpenLayers.Control.prototype.deactivate.apply(query_box, arguments)) {
            
            return true
        } else {
            return false
        }
    },
    
    update: function (
        query_expression
    ) {
        var query_box = this
        $(query_box.div).css('background-color', 'white')
        query_box.$text_area.val(query_expression)
        query_box.$update_button.hide()
        query_box.previous_query = query_expression
        query_box.resizer.resize()
    },

    error: function (
        position
    ) {
        // inform the query box that there is an error,
        var query_box = this
        var text = query_box.$text_area.val()
        var message = '# Syntax error (highlighted):\n'
        if (text.substr(0, message.length) == message) {
            message = ''
        }
        // highlight where it starts
        var following_text = text.substr(position)
        var selection_size = following_text.search(new RegExp('\\s|$'))
        if (
            selection_size + message.length <= 0
        ) {
            selection_size = following_text.search(new RegExp('\n|$'))
        }
        query_box.$text_area.blur()
        
        query_box.$text_area.val(message + text)
        
        var textarea = query_box.$text_area[0]
        textarea.setSelectionRange(
            position + message.length,
            position + message.length + selection_size
        )
        $(query_box.div).css('background-color', 'red')
    },

    draw: function() {
        var query_box = this
        OpenLayers.Control.prototype.draw.apply(query_box, arguments);
        var $query_box_div = $(query_box.div)
        var $text_area = query_box.$text_area = TEXTAREA({
            style: (
                'border: none;'+
                'width: 100%;'+
                'font-family: Monaco, Lucida Console, Courier New, monospace;'+
                'font-size: 0.9em;'
            )
        },
            'Query'
        )
        
        var $update_button = query_box.$update_button = INPUT({
            type:'button',
            value:'Compute and show on map',
            style:'margin-top:5px;'
        })
        $update_button.hide()
        $update_button.click(function () {
            query_box.updated(query_box.$text_area.val())
        })
        $query_box_div.append($text_area)
        $query_box_div.append(
            DIV({
                    style:'text-align: center;'
                },
                $update_button
            )
        )
        
        function show_update_button() {
            $update_button.show()
            //$update_button.toggle($text_area.html() != query_box.previous_query)
        }

        $text_area.bind('keyup', show_update_button)

        $text_area.show()
        query_box.resizer = new TextAreaAutoResizer(
            $text_area,
            15
        )
        $query_box_div.css({
            position: 'absolute',
            bottom: '10px',
            left: '120px',
            right: '160px',
            backgroundColor: 'white',
            border: '1px solid black',
            padding: '0.5em'
        })
        return query_box.div
    },

    print_mode: function () {
        var query_box = this
        query_box.$text_area.css('text-align', 'center')
    }
});

function base64_encode(s) {
    var base64chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'.split("");
    var r = ''
    var p = ''
    var c = s.length % 3
    if (c > 0) { 
        for (; c < 3; c++) { 
            p += '='
            s += '\0'
        } 
    }
    for (c = 0;
        c < s.length;
        c += 3
    ) {
        if (c > 0 && (c / 3 * 4) % 76 == 0) { 
            r += '\r\n'; 
        }
        var n = (
            (s.charCodeAt(c) << 16) + 
            (s.charCodeAt(c+1) << 8) + 
            s.charCodeAt(c+2)
        )
        n = [
            (n >>> 18) & 63,
            (n >>> 12) & 63,
            (n >>> 6) & 63,
            n & 63
        ]
        r += (
            base64chars[n[0]] + 
            base64chars[n[1]] + 
            base64chars[n[2]] + 
            base64chars[n[3]]
        )
    }
    return r.substring(0, r.length - p.length) + p
}
function ColourGradient(
    rgb_values
) {
    var colour_gradient = this
    var rgb_values = rgb_values
    var bitmap_string = null
    function bitmap_data() {
        if (bitmap_string != null) {
            return bitmap_string
        }
        else {
            function encode(number, bytes) {
                var oldbase = 1
                var string = ''
                for (var x = 0; x < bytes; x++) {
                    var byte = 0
                    if (number != 0) {
                        var base = oldbase * 256
                        byte = number % base
                        number = number - byte
                        byte = byte / oldbase
                        oldbase = base
                    }
                    string += String.fromCharCode(byte)
                }
                return string
            }
            var width = rgb_values.length

            var data = []
            for (var x = 0; x < width; x++) {
                var value = rgb_values[Math.floor((x/width) * rgb_values.length)]
                data.push(
                    String.fromCharCode(
                        value[2],
                        value[1],
                        value[0]
                    )
                )
            }
            padding = (
                width % 4 ? 
                '\0\0\0'.substr((width % 4) - 1, 3):
                ''
            )
            data.push(padding + padding + padding)
            var data_bytes = data.join('')

            var info_header = (
                encode(40, 4) + // Number of bytes in the DIB header (from this point)
                encode(width, 4) + // Width of the bitmap in pixels
                encode(1, 4) + // Height of the bitmap in pixels
                '\x01\0' + // Number of color planes being used
                encode(24, 2) + // Number of bits per pixel
                '\0\0\0\0'+ // BI_RGB, no Pixel Array compression used
                encode(data_bytes.length, 4)+ // Size of the raw data in the Pixel Array (including padding)
                encode(2835, 4)+ //Horizontal resolution of the image
                encode(2835, 4)+ // Vertical resolution of the image
                '\0\0\0\0\0\0\0\0'
            )

            var header_length = 14 + info_header.length
            bitmap_string = (
                'BM'+
                encode(header_length + data_bytes.length, 4)+
                '\0\0\0\0'+
                encode(header_length, 4)
            ) + info_header + data_bytes
            return bitmap_string
        }
    }

    var fill_image = function (image) {
        $(image).attr(
            'src',
            'data:image/bmp;base64,'+
            base64_encode(bitmap_data())
        )
    }
    var images = []
    colour_gradient.manage_image = function (image) {
        images.push(image)
        fill_image(image)
    }
    colour_gradient.invert = function () {
        rgb_values = rgb_values.reverse()
        bitmap_string = null
        each(images, fill_image)
    }
    colour_gradient.colour_for_value = function (
        normalised_value // must be between 0 and 1
    ) {
        return rgb_values[
            Math.floor(
                normalised_value * (rgb_values.length-1)
            )
        ]
    }
}

var course_colour_steps = new ColourGradient([
    [240, 10, 135],
	[255, 62, 62],
    [240, 130, 40],
    [230, 220, 50],
    [160, 230, 55],
    [10, 210, 140],
    [10, 200, 200],
    [30, 60, 255],
    [130, 0, 220],
    [160, 0, 200]
])

var blue_green_red_cosines = []
with (Math) {
    var i;
    for (i = -900; i < 900; i++) {
        var x = i/1000 * PI
        var red = floor((1- (2 * abs(PI/2-x))/PI) * 255) //floor(sin(x) * 255)
        var green = floor((1- (2 * abs(x))/PI) * 255) //floor(cos(x) *255)
        var blue = floor((1- (2 * abs(PI/2+x))/PI) * 255) //floor(-sin(x) *255)
        blue_green_red_cosines.push([
            red < 0 ? 0 : red,
            green < 0 ? 0 : green,
            blue < 0 ? 0 : blue
        ])
    }
}

var blue_green_red_cosines = new ColourGradient(blue_green_red_cosines)

var smooth_blue_green_red = []
with (Math) {
    var i;
    for (i = -400; i < 800; i++) {
        var x = i/1000 * PI
        var red = floor(sin(x) * 255)
        var green = floor(sin(x + (PI/3)) *255)
        var blue = floor(sin(x + (2 * PI/3)) *255)
        smooth_blue_green_red.push([
            red < 0 ? 0 : red,
            green < 0 ? 0 : green,
            blue < 0 ? 0 : blue
        ])
    }
}
var smooth_blue_green_red = new ColourGradient(smooth_blue_green_red)

function linear_gradient(start_colour, end_colour, steps) {
    steps = steps || 100
    var start_red = start_colour[0],
        start_green = start_colour[1],
        start_blue = start_colour[2]
    var range_red = end_colour[0] - start_red,
        range_green = end_colour[1] - start_green,
        range_blue = end_colour[2] - start_blue
    var colours = []
    var floor = Math.floor
    for (
        var i = 0;
        i < steps;
        ++i
    ) {
        var value = i / steps
        colours.push([
            floor((start_red + value * range_red) * 255),
            floor((start_green + value * range_green) * 255),
            floor((start_blue + value * range_blue) * 255),
        ])
    }
    return colours
}

var black_to_white = new ColourGradient(linear_gradient([0,0,0], [1,1,1])),
    blue_to_yellow = new ColourGradient(linear_gradient([0,0,1], [1,1,0])),
    red_to_green = new ColourGradient(linear_gradient([1,0,0], [0,1,0])),
    red_to_blue = new ColourGradient(linear_gradient([1,0,0], [0,0,1])),
    green_to_blue = new ColourGradient(linear_gradient([0,1,0], [0,0,1]))

var FilterBox = OpenLayers.Class(OpenLayers.Control, {
    CLASS_NAME: 'FilterBox',
    // updated(filter_function): callback
    // example: object with example attributes, should match places
    title: (
        'Enter filter expressions here to filter the map overlay. '+
        '"unfiltered" means the map overlay is not being filtered. '+
        'You can use any attribute shown in the overlay '+
        'popup box, and logical operators "and", "not" and "or". \n'+
        'within("Region name") and within_Nepal() filter by region.'
    ),
    destroy: function() {
        var filter_box = this
        filter_box.deactivate()
        filter_box.resizer.destroy()
        OpenLayers.Control.prototype.destroy.apply(filter_box, arguments)
    },
    
    activate: function() {
        var filter_box = this
        if (OpenLayers.Control.prototype.activate.apply(filter_box, arguments)) {
            return true
        } else {
            return false
        }
    },
    
    deactivate: function() {
        var filter_box = this
        if (OpenLayers.Control.prototype.deactivate.apply(filter_box, arguments)) {
            
            return true
        } else {
            return false
        }
    },

    set_filter_no_update: function(filter_expression) {
        var filter_box = this
        filter_box.$text_area.val(filter_expression)
    },
    
    set_filter: function(filter_expression) {
        var filter_box = this
        filter_box.$text_area.val(filter_expression)
        filter_box.update_plugin()
    },
    
    update_plugin: function () {
        var filter_box = this
        var $text_area = filter_box.$text_area
        var filter_expression = $text_area.val()
        if (new RegExp('^\\s*$').test(filter_expression)) {
            var filter_function = function () { return true }
            $text_area.val('unfiltered')
        }
        else {
            try {
                filter_function = filter_box.plugin.create_filter_function(
                    filter_expression
                )
                // test it a bit
                filter_function(filter_box.example, 0)
            }
            catch (error) {
                $(filter_box.div).css('background-color', 'red')
                var error_name = error.name
                $(filter_box.div).attr('title', error.message)
                if (
                    error_name == 'ReferenceError'
                ) {
                    var bad_ref = error.message.substr(
                        error.message.lastIndexOf(':') + 2
                    )
                    var bad_ref_first_pos = filter_expression.indexOf(bad_ref)
                    $text_area[0].setSelectionRange(
                        bad_ref_first_pos,
                        bad_ref_first_pos + bad_ref.length
                    )
                    return
                }
                else {
                    throw error
                }
                return
            }
        }
        filter_box.updated(filter_function)
        filter_box.$update_button.hide()
        $(filter_box.div).css('background-color', 'white')
    },
    
    draw: function() {
        var filter_box = this
        OpenLayers.Control.prototype.draw.apply(filter_box, arguments);
        var $filter_box_div = $(filter_box.div)
        var $text_area = filter_box.$text_area = TEXTAREA({
            style: (
                'border: none;'+
                'width: 100%;'+
                'font-family: Monaco, Lucida Console, Courier New, monospace;'+
                'font-size: 0.9em;'+
                'text-align: center;'+
                'overflow: scroll;'
            )
        },
            filter_box.initial_filter || 'unfiltered'
        )
        
        $filter_box_div.append($text_area)
        
        var $update_button = filter_box.$update_button = INPUT({
            type:'button',
            value:'Filter map overlay',
            style:'margin-top:5px;'
        })
        $update_button.hide()
        $update_button.click(
            function () {
                filter_box.update_plugin()
            }
        )
        $filter_box_div.append($text_area)
        $filter_box_div.append(
            DIV({
                    style:'text-align: center;'
                },
                $update_button
            )
        )
        
        function show_update_button() {
            $update_button.show()
        }

        $text_area.bind('keyup', show_update_button)

        $text_area.show()
        filter_box.resizer = new TextAreaAutoResizer(
            $text_area,
            15
        )

        $filter_box_div.css({
            position: 'absolute',
            top: '10px',
            right: '10px',
            width: '200px',
            backgroundColor: 'white',
            border: '1px solid black',
            padding: '0.5em'
        })
        return filter_box.div
    }
});



// Shapes on the map
function Vector(geometry, attributes, style) {
    style.strokeColor = 'none'
    style.fillOpacity = 0.8
    style.strokeWidth = 1
    return new OpenLayers.Feature.Vector(
        geometry, attributes, style
    )
}
function Polygon(components) {
    return new OpenLayers.Geometry.Polygon(components)
}
function Point(lon, lat) {
    var point = new OpenLayers.Geometry.Point(lon, lat)
    return point.transform(
        S3.gis.proj4326,
        S3.gis.projection_current
    )
}
function LinearRing(point_list) {
    point_list.push(point_list[0])
    return new OpenLayers.Geometry.LinearRing(point_list)
}

function Place(data) {
    var place = this
    place.data = data
    place.data.latitude = Math.round(place.data.latitude * 1000000) / 1000000
    place.data.longitude = Math.round(place.data.longitude * 1000000) / 1000000
    
    place.spaces = []
    var point = place.point = new OpenLayers.Geometry.Point(
        data.longitude,
        data.latitude
    ).transform(
        S3.gis.proj4326,
        S3.gis.projection_current
    )
    var lonlat = place.lonlat = new OpenLayers.LonLat(
        point.x,
        point.y
    )
}
var station_marker_icon_size = new OpenLayers.Size(21,25)
var station_marker_icon = new OpenLayers.Icon(
    'static/img/gis/openlayers/marker-blue.png',
    station_marker_icon_size,
    new OpenLayers.Pixel(
        -(station_marker_icon_size.w/2),
        -station_marker_icon_size.h
    )
)
Place.prototype = {
    within: function () {
        for (var i = 0; i < arguments.length; i++) {
            if (this.spaces.indexOf(arguments[i]) != -1) {
                return true
            }
        }
        return false
    },
    within_Nepal: function () {
        return this.spaces.length > 0
    },
    matches: function (match_value) {
        var data = this.data
        if (data.station_id == match_value) {
            return true
        }
        lowercase_name = match_value.toLowerCase()
        if (data.station_name.toLowerCase().indexOf(lowercase_name) != -1) {
            return true
        }
        var spaces = this.spaces
        for (var i = 0; i < spaces.length; i++) {
            if (spaces[i].indexOf(match_value) != -1) {
                return true
            }
        }
        return false
    },
    generate_marker: function (use_marker) {
        // only for stations
        var place = this
        if (place.data.station_id) {
            var station_marker = new OpenLayers.Marker(
                place.lonlat,
                station_marker_icon.clone()
            )
            station_marker.place = place
            var show_place_info_popup = function (event) { 
                var marker = this
                var place = marker.place
                var info = [
                    // popup is styled with div.olPopup
                    '<div class="place_info_popup">',
                ]
                function add_attribute(attribute) {
                    var value = place.data[attribute]
                    if (!!value) {
                        info.push(
                            attribute.replace('_',' '),': ', value,
                            '<br />'
                        )
                    }
                }
                add_attribute('station_id')
                add_attribute('station_name')
                add_attribute('latitude')
                add_attribute('longitude')
                add_attribute('elevation')
                
                info.push('</div>')

                var popup = new OpenLayers.Popup(
                    null,
                    marker.lonlat,
                    new OpenLayers.Size(170, 125),
                    info.join(''),
                    true
                )
                marker.popup = popup
                map.addPopup(popup)
                function remove_place_info_popup() {
                    map.removePopup(marker.popup);
                    marker.popup.destroy();
                    marker.popup = null;
                }
                marker.events.register('mouseup', marker,
                    remove_place_info_popup
                )
                marker.events.register('mouseout', marker,
                    remove_place_info_popup
                )
                OpenLayers.Event.stop(event);
            }
            station_marker.events.register(
                'mousedown',
                station_marker,
                show_place_info_popup
            )
            use_marker(station_marker)
        }
    },
    add_space: function(space) {
        this.spaces.push(space.name)
    },
    popup: function(feature, value, use_popup, event) {
        var place = this
        var info = [
            // popup is styled with div.olPopup
            '<div class="place_info_popup">',
            '<div style="text-align:center; font-size:1.5em;">',
                value,
            '</div><br />'
        ]
        var data = place.data
        for (var p in data) {
            if (data.hasOwnProperty(p)) {
                value = data[p]
                if (!!value) {
                    info.push(
                        p.replace('_',' '),': ', value,
                        '<br />'
                    )
                }
            }
        }
        info.push('</div>')
        OpenLayers.Popup.COLOR = ''
        var popup = new OpenLayers.Popup(
            null,
            map.getLonLatFromPixel({x:event.layerX, y:event.layerY}),
            new OpenLayers.Size(170, 150),
            info.join(''),
            true
        )
        use_popup(popup)
    }
}


function PointInLinearRingDetector(linear_ring) {
    /* Cache line information to speed up queries when we have many
    points to test.
    */
    var detector = this
    var steps = linear_ring.components
    var bounds = detector.bounds = linear_ring.getBounds()
    var top = bounds.top
    var bottom = bounds.bottom
    // sort polygon edges into horizontal parallel strips
    // any line that has either end inside or crosses a strip
    // gets added to the set of lines for that strip
    // The aim is to have as few lines as possible per strip
    // without having too many strips duplicating lots of lines
    // containsPoint test can now be orders of magnitude faster, as far fewer
    // lines need consideration.
    var strips_count = parseInt(steps.length / 2)
    var strips = detector.strips = new Array(strips_count+1) // up and down again
    for (
        var i = 0;
        i< strips.length;
        i++
    ) {
        strips[i] = []
    }

    // strips run from bottom (0) to top
    var latitude_range = top - bottom
    var acos = Math.acos
    var floor = Math.floor, max = Math.max, min = Math.min
    var strips_count_over_pi = strips_count / Math.PI
    var strip_selector = detector.strip_selector = function (latitude) {
        // for efficient strip sizes, assume polygons approximate a circle
        // i.e. the top lines are much more likely to run horizontally,
        // and the side lines vertically. Strip sizes reflect this.
        return floor(
            acos(
                // Some loss of floating point precision seems to have been 
                // introduced by OpenLayers (getBounds?)
                1 - (2 * max(min(((latitude - bottom) / latitude_range), 1.0), 0.0))
            ) * strips_count_over_pi
        )
    }
    
    var start_point = steps[0]
    var start_y = start_point.y
    var start_coords = [start_point.x, start_y]
    var start_strip = strip_selector(start_y)
    var end_point, end_y, end_coords, end_strip
    var line, direction, strip_number
    for(
        var i = 1,
            len = steps.length;
        i < len;
        ++i
    ) {
        end_point = steps[i]
        end_y = end_point.y
        end_coords = [end_point.x, end_y]
        end_strip = strip_selector(end_y)
        
        line = [start_coords, end_coords]
        direction = parseInt((end_y-start_y) / Math.abs(end_y-start_y) || 0)
        strip_number = start_strip
        strips[strip_number].push(line)
        while (strip_number != end_strip) {
            strip_number += direction
            strips[strip_number].push(line)
        }  
        start_coords = end_coords
        start_y = end_y
        start_strip = end_strip
    }
}
PointInLinearRingDetector.prototype = {
    containsPoint: function (point, is_contained) {
        if (this.bounds.contains(point.x, point.y)) {
            var digs = 14;
            var px = point.x
            var py = point.y
            function getX(y, x1, y1, x2, y2) {
                // this should be commited to OpenLayers source
                var y1_ = y1-y, y2_ = y2-y
                return (((x2 * y1_) - (x1 * y2_))) / (y1_ - y2_);
            }
            var lines_to_test = this.strips[this.strip_selector(py)]
            var line, x1, y1, x2, y2, cx, cy;
            var crosses = 0;
            for(
                var i=0, len = lines_to_test.length;
                i < len;
                ++i
            ) {
                line = lines_to_test[i]
                x1 = line[0][0]
                y1 = line[0][1]
                x2 = line[1][0]
                y2 = line[1][1]
                
                /**
                 * The following conditions enforce five edge-crossing rules:
                 *    1. points coincident with edges are considered contained;
                 *    2. an upward edge includes its starting endpoint, and
                 *    excludes its final endpoint;
                 *    3. a downward edge excludes its starting endpoint, and
                 *    includes its final endpoint;
                 *    4. horizontal edges are excluded; and
                 *    5. the edge-ray intersection point must be strictly right
                 *    of the point P.
                 */
                if(y1 == y2) {
                    // horizontal edge
                    if(py == y1) {
                        // point on horizontal line
                        if(x1 <= x2 && (px >= x1 && px <= x2) || // right or vert
                           x1 >= x2 && (px <= x1 && px >= x2)) { // left or vert
                            // point on edge
                            crosses = -1;
                            break;
                        }
                    }
                    // ignore other horizontal edges
                    continue;
                }
                cx = getX(py, x1, y1, x2, y2);
                if(cx == px) {
                    // point on line
                    if(y1 < y2 && (py >= y1 && py <= y2) || // upward
                       y1 > y2 && (py <= y1 && py >= y2)) { // downward
                        // point on edge
                        crosses = -1;
                        break;
                    }
                }
                if(cx <= px) {
                    // no crossing to the right
                    continue;
                }
                
                if(x1 != x2 && (cx < Math.min(x1, x2) || cx > Math.max(x1, x2))) {
                    // no crossing                
                    continue;
                }
                
                if(y1 < y2 && (py >= y1 && py < y2) || // upward
                   y1 > y2 && (py < y1 && py >= y2)) { // downward
                   ++crosses;
                }
            }
            if (
                (crosses == -1) ?
                // on edge
                1 :
                // even (out) or odd (in)
                !!(crosses & 1)
            ) {
                is_contained()
            }
        }
    }
}

VariableResolutionVectorLayer = OpenLayers.Class(
    OpenLayers.Layer.Vector,
    {
        CLASS_NAME: 'VariableResolutionVectorLayer',
        drawFeature: function (feature) {
            var map = this.map
            var zoom = map.zoom
            OpenLayers.Layer.Vector.prototype.drawFeature.call(
                this,
                feature.atZoom(zoom, map)
            )
        },
        moveTo: function(bounds, zoomChanged, dragging) {
            OpenLayers.Layer.prototype.moveTo.apply(this, arguments);
            
            var ng = (OpenLayers.Renderer.NG && this.renderer instanceof OpenLayers.Renderer.NG);
            if (ng) {
                if (zoomChanged) {
                    this.renderer.updateDimensions();
                }
            } else {
                var coordSysUnchanged = true;

                if (!dragging) {
                    this.renderer.root.style.visibility = "hidden";
                
                    this.div.style.left = -parseInt(this.map.layerContainerDiv.style.left) + "px";
                    this.div.style.top = -parseInt(this.map.layerContainerDiv.style.top) + "px";
                    var extent = this.map.getExtent();
                    coordSysUnchanged = this.renderer.setExtent(extent, zoomChanged);
                
                    this.renderer.root.style.visibility = "visible";

                    // Force a reflow on gecko based browsers to prevent jump/flicker.
                    // This seems to happen on only certain configurations; it was originally
                    // noticed in FF 2.0 and Linux.
                    if (OpenLayers.IS_GECKO === true) {
                        this.div.scrollLeft = this.div.scrollLeft;
                    }
                    if(!zoomChanged && coordSysUnchanged) {
                        for(var i in this.unrenderedFeatures) {
                            var feature = this.unrenderedFeatures[i];
                            this.drawFeature(feature);
                        }
                    }
                }
            }
            if (!this.drawn || (!ng && (zoomChanged || !coordSysUnchanged))) {
                this.drawn = true;
                this.renderer.clear()
                this.unrenderedFeatures = {}
                var features = this.features
                for(var i=0, len=features.length; i<len; i++) {
                    this.renderer.locked = (i !== (len - 1))
                    this.drawFeature(
                        features[i]
                    )
                }
            }    
        }
    }
)
OpenLayers.Feature.prototype.atZoom = function (zoom, map) {
    return this
}
OpenLayers.Feature.Vector.prototype.atZoom = function (zoom, map) {
    var feature = this
    var by_zoom = feature.by_zoom
    if (!by_zoom) {
        by_zoom = feature.by_zoom = []
    }
    var simplified_feature = by_zoom[zoom]
    if (!simplified_feature) {
        // ToDo: there are more accurate ways to get a decent 
        // tolerance, but this is fast, which is the whole point
        // of simplifying the vectors
        var centre_lonlat = map.getCenter()
        var offset_lonlat = map.getLonLatFromPixel(
            map.getPixelFromLonLat(centre_lonlat).offset(
                new OpenLayers.Pixel(1,1)
            )
        )
        max_x_diff = Math.abs(offset_lonlat.lon - centre_lonlat.lon)
        max_y_diff = Math.abs(centre_lonlat.lat - offset_lonlat.lat)
        var simplified_feature = new OpenLayers.Feature.Vector(
            feature.geometry ? feature.geometry.atZoom(max_x_diff, max_y_diff) : null,
            feature.attributes,
            feature.style
        )
        delete simplified_feature.state
        simplified_feature.prototype = feature
        by_zoom[zoom] = simplified_feature
    }
    return simplified_feature
}
// It is safe not to simplify the feature in all cases, also we cannot 
// simplify the following:
// Rectangle
// Point
// Surface
OpenLayers.Geometry.prototype.atZoom = function () { return this }

// simplifying a Collection is like cloning its simplified components:

// Multipolygon,
// Polygon,
// MultiLineString

OpenLayers.Geometry.Collection.prototype.atZoom = function (max_x_diff, max_y_diff) {
    var geometry = eval("new " + this.CLASS_NAME + "()")
    for(var i=0, len=this.components.length; i<len; i++) {
        geometry.addComponent(
            this.components[i].atZoom(max_x_diff, max_y_diff)
        )
    }
    OpenLayers.Util.applyDefaults(geometry, this)
    return geometry
}

// Geometries that use Points are the ones we need to simplify:

//Multipoint
// Curve
//  LineString
//   LinearRing
OpenLayers.Geometry.MultiPoint.prototype.atZoom = function (max_x_diff, max_y_diff) {
    var geometry = eval("new " + this.CLASS_NAME + "()")
    var points = this.components
    var points_length = points.length
    if (points_length > 0) {
        var previous_point = points[0]
        var previous_x = previous_point.x
        var previous_y = previous_point.y
        
        // Always add the first point if there are any
        geometry.addComponent(previous_point)
        
        if (points_length > 1) {
            var i = 1 // we added the first point already
            var abs = Math.abs
            while (i < points_length - 1) {
                var point = points[i]
                if (
                    abs(point.x - previous_x) > max_x_diff ||
                    abs(point.y - previous_y) > max_y_diff
                ) {
                    // the point is far away enough from the previous point
                    // such that the difference is discernible on a pixel basis
                    geometry.addComponent(point.clone())
                    previous_point = point
                    previous_x = previous_point.x
                    previous_y = previous_point.y
                }
                i++
            }
            // Always add the last point if there is one
            geometry.addComponent(points[points_length -1])
        }
    }
    OpenLayers.Util.applyDefaults(geometry, this);
    return geometry;
}

load_layer_and_locate_places_in_spaces = function (
    name, layer_URL, format, label_colour, label_size
) {
    var vector_layer = new VariableResolutionVectorLayer(
        name,
        {
            projection: map.displayProjection,
            strategies: [new OpenLayers.Strategy.Fixed()],
            protocol: new OpenLayers.Protocol.HTTP({
                url: layer_URL,
                format: format
            })
        }
    )
    map.addLayer(vector_layer)
  
    var region_names_layer = new OpenLayers.Layer.Vector(
        name+" names",
        {
            projection: map.displayProjection,
            styleMap: new OpenLayers.StyleMap({'default':{
                label : "${name}",
                
                fontColor: label_colour || "black",
                fontSize: label_size || "10px",
                //fontFamily: "Courier New, monospace",
                fontWeight: "bold",
                labelAlign: "cm",
                labelOutlineColor: "white",
                labelOutlineWidth: 1
            }}),
            renderers: ["Canvas"]
        }
    )
    map.addLayer(region_names_layer)
    vector_layer.events.register(
        'loadend',
        vector_layer,
        function () {
            region_names_layer.setZIndex(109)
            each(
                vector_layer.features,
                function (feature) {
                    var geometry = feature.geometry
                    var polygon = geometry.components[0]
                    var district = feature.data.District || feature.data.DISTRICT
                    var pointFeature = new OpenLayers.Feature.Vector(geometry.getCentroid());
                    pointFeature.attributes = {
                        name: district.value ? district.value : district
                    }
                    region_names_layer.addFeatures([pointFeature])
                }
            )
        }
    )
    map.panDuration = 0
    vector_layer.events.register(
        'loadend',
        vector_layer,
        function () {
            vector_layer.setVisibility(false)
            setTimeout(
                function () {
                    vector_layer.setZIndex(
                        110
                    )
                    var linear_rings = []
                    
                    function find_linear_rings(geometry, name) {
                        if (
                            geometry.CLASS_NAME == "OpenLayers.Geometry.LinearRing"
                        ) {
                            var linear_ring = geometry
                            linear_ring.name = name
                            plugin.spaces.push([name, name])
                            linear_rings.push(linear_ring)
                        }
                        else {
                            if (geometry.components) {
                                each(
                                    geometry.components,
                                    function (geometry) {
                                        find_linear_rings(geometry, name)
                                    }
                                )
                            }
                        }
                    }
                    
                    each(
                        vector_layer.features,
                        function (feature) {
                            var data = feature.data
                            if (data) {
                                var district = data.District || data.DISTRICT
                                if (district.value) {
                                    name = district.value
                                }
                                else {
                                    name = district
                                }
                            }
                            find_linear_rings(feature.geometry, name)
                        }
                    )
                    each(linear_rings,
                        function (linear_ring) {
                            plugin.when_places_loaded(
                                function (places) {
                                    var detector = new PointInLinearRingDetector(
                                        linear_ring
                                    )
                                    for (p in places) {
                                        if (places.hasOwnProperty(p)) {
                                            var place = places[p]
                                            detector.containsPoint(
                                                place.point,
                                                function () {
                                                    place.add_space(linear_ring)
                                                }
                                            )
                                        }
                                    }
                                }
                            )
                        }
                    )
                    
                    plugin.quick_filter_data_store.loadData(
                        ([["(All)",""], ["Nepal", "within_Nepal()"]]).concat(plugin.spaces)
                    )
                    plugin.quick_filter_data_store.sort('name', 'ASC')
                    //vector_layer.redraw()
                },
                1
            )
        }
    )
}

var Logo = OpenLayers.Class(OpenLayers.Control, {
    draw: function () {
        return (
            DIV({
                    style:'width: 120px; position:absolute; left: 5px; bottom:60px;'
                },
                IMG({
                    src:'static/img/Nepal-Government-Logo.png',
                    width: '120px'
                })
            )
        )[0]
    }
})

function load_world_map(plugin) {
    if (!Ext.isIE || Ext.isIE9 || display_mode == 'print') { 
        $.ajax({
            url: plugin.world_map_URL,
            format: 'json',
            success: function (delta_polygon_feature_collection) {
                var format = new OpenLayers.Format.GeoJSON({
                    ignoreExtraDims: true
                })
                
                function decompressiblize_GeometryCollection(geometry_collection) {
                    each(
                        geometry_collection["geometries"],
                        function (geometry) {
                            decompressiblize[geometry["type"]](geometry)
                        }
                    )
                }
                    
                function decompressiblize_Polygon(polygon) {
                    var new_linear_rings = []
                    each(
                        polygon["coordinates"],
                        function(linear_ring) {
                            var longitude_deltas = linear_ring[0]
                            var latitude_deltas = linear_ring[1]
                            var new_linear_ring = []
                            var previous_longitude = 0, previous_latitude = 0
                            for (
                                var i = 0, 
                                    len = longitude_deltas.length; 
                                i < len;
                                i++
                            ) {
                                var longitude_delta = longitude_deltas[i]
                                var latitude_delta = latitude_deltas[i]
                                new_linear_ring.push(
                                    [
                                        (previous_longitude + longitude_delta)*1000,
                                        (previous_latitude + latitude_delta)*1000,
                                    ]
                                )
                                previous_longitude = previous_longitude + longitude_delta
                                previous_latitude = previous_latitude + latitude_delta
                            }
                            new_linear_rings.push(new_linear_ring)
                        }
                    )
                    polygon["coordinates"] = new_linear_rings
                }

                var decompressiblize = {
                    GeometryCollection: decompressiblize_GeometryCollection,
                    Polygon: decompressiblize_Polygon,
                    Point: function () {}
                }
                
                window.delta_polygon_feature_collection = delta_polygon_feature_collection
                each(
                    delta_polygon_feature_collection.features,
                    function (delta_polygon_feature) {
                        var geometry = delta_polygon_feature.geometry
                        decompressiblize[geometry["type"]](geometry)
                        // feature is no longer in delta format
                        var feature_json = delta_polygon_feature
                        delete delta_polygon_feature
                        var feature = format.parseFeature(feature_json)
                        if (!!feature.data.ISO3) {
                            plugin.countries[feature.data.ISO3] = feature
                        }
                    }
                )
                plugin.when_places_loaded(
                    function () {
                        plugin.colour_key.with_limits(
                            plugin.render_map_layer
                        )
                    }
                )
            },
            failure: function () {
                plugin.set_status(
                    'Could not load world map!'
                )
            }
        })
    }
    else {
        plugin.set_status(
            'Sorry, Internet Explorer < 9 is not performant '+
            'enough to show detailed vector maps. Countries will '+
            'be represented by circles at their capital cities'
        )
    }
    each(
        plugin.month_selector_ids,
        function (id) {
            Ext.getCmp(id).hide()
        }
    )
}

ClimateDataMapPlugin = function (config) {
    var plugin = this // let's be explicit!
    window.plugin = plugin
    plugin.data_type_option_names = config.data_type_option_names
    plugin.parameter_names = config.parameter_names
    plugin.aggregation_names = config.aggregation_names
    plugin.year_min = config.year_min 
    plugin.year_max = config.year_max

    plugin.data_type_label = config.data_type_label
    plugin.overlay_data_URL = config.overlay_data_URL
    plugin.places_URL = config.places_URL
    plugin.chart_URL = config.chart_URL
    plugin.data_URL = config.data_URL
    plugin.station_parameters_URL = config.station_parameters_URL
    plugin.years_URL = config.years_URL
    
    plugin.chart_popup_URL = config.chart_popup_URL
    plugin.request_image_URL = config.request_image_URL
    plugin.download_data_URL = config.download_data_URL
    plugin.download_timeseries_URL = config.download_timeseries_URL
    
    var display_mode = config.display_mode
    plugin.set_status = function (html_message) {
        $('#error_div').html(html_message)
    }
    if (config.expression) {
        var initial_query_expression = decodeURI(
            config.expression
        )
    }
    else {
        var initial_query_expression = (
            plugin.aggregation_names[0]+'('+
                '"'+ //form_values.data_type+' '+
                plugin.parameter_names[0].replace(
                    new RegExp('\\+','g'),
                    ' '
                )+'", '+
                'From('+plugin.year_min+'), '+
                'To('+plugin.year_max+')'+
            ')'
        )
    }
    var initial_filter = decodeURI(config.filter || 'unfiltered')
    
    delete config
    
    plugin.last_query_expression = null
    
    plugin.places = {}
    plugin.spaces = []
    
    plugin.places_events = []
    plugin.when_places_loaded = function (places_function) {
        places_function(plugin.places)
        plugin.places_events.push(places_function)
    }
    plugin.month_selector_ids = []
    plugin.create_filter_function = function (filter_expression) {
        var replacements = {
            '(\\W)and(\\W)': '$1&&$2',
            '(^|\\W)not(\\W)': '$1!$2',
            '(\\W)or(\\W)': '$1||$2',
            '([^=<>])=([^\\=])': '$1==$2'
        }
        for (var pattern in replacements) {
            if (replacements.hasOwnProperty(pattern)) {
                var reg_exp = new RegExp(pattern, 'g')
                filter_expression = filter_expression.replace(
                    reg_exp, replacements[pattern]
                )
            }
        }
        /* Special cases */
        if (filter_expression == "Nepal" ||
            filter_expression == "'Nepal'" ||
            filter_expression == '"Nepal"'
        ) {
            filter_expression = "within_Nepal()"
        }
        // Simple strings can be used to search for a place or area name
        try {
            if (typeof eval(filter_expression) == "string") {
                filter_expression = "matches("+filter_expression+")"
                plugin.filter_box.set_filter_no_update(filter_expression)
            }
        }
        catch (exception) {}

        var function_string = (
            'unfiltered = true\n'+
            'with (Math) {'+
                'with (place) {' +
                    'with (place.data) { '+
                        'return '+ filter_expression +
                    '}'+
                '}'+
            '}'
        )
        var filter_function = new Function(
            'place',
            'value',
            function_string
        )
        return filter_function
    }
    if (initial_filter) {
        plugin.filter = plugin.create_filter_function(initial_filter)
    }
    
    var tooltips = []
    function add_tooltip(config) {
        tooltips.push(config)
    }

    function init_tooltips() {
        each(tooltips,
            function (config) {
                new Ext.ToolTip(config)
            }
        )
        //Ext.QuickTips.init(); // done by gis
    }

    plugin.overlay_layer = new OpenLayers.Layer.Vector(
        'Query result values',
        {
            isBaseLayer:false                                
        }
    )
    plugin.setup = function () {
        var overlay_layer = plugin.overlay_layer
        map.addLayer(overlay_layer)
        // hovering over a feature pops up a box showing details
        // subsequently moving to another feature pops up another box instantly
        // not hovering for a while resets the hover delay
        var hover_timeout = null,
            hover_delay = 1000,
            hover_delay_clear_timeout = null
        function onFeatureSelect(feature) {
            if (hover_delay_clear_timeout != null) {
                clearTimeout(hover_delay_clear_timeout)
                hover_delay_clear_timeout = null
            }
            if (hover_timeout == null) {
                hover_timeout = setTimeout(
                    function () {
                        hover_delay = 0
                        var data = feature.data
                        var place = plugin.places[data.place_id]
                        if (!!place) {
                            place.popup(
                                feature,
                                data.value,
                                function (popup) {
                                    feature.popup = popup
                                    map.addPopup(popup)
                                    feature.unselect_timeout = setTimeout(
                                        function () {
                                            onFeatureUnselect(feature)
                                        },
                                        10000
                                    )
                                },
                                hover_control.handlers.feature.evt
                            )
                        }
                    },
                    hover_delay
                )
            }
        }
        function onFeatureUnselect(feature) {
            if (hover_timeout != null) {
                clearTimeout(hover_timeout)
                hover_timeout = null
            }
            if (feature.popup && feature.popup.div) {
                map.removePopup(feature.popup)
                feature.popup.destroy()
                feature.popup = null
            }
            if (feature.unselect_timeout) {
                clearTimeout(feature.unselect_timeout)
            }
            clearTimeout(hover_delay_clear_timeout)
            hover_delay_clear_timeout = setTimeout(
                function () {
                    hover_delay = 1000
                },
                1000
            )
        }
        var hover_control = new OpenLayers.Control.SelectFeature(
            overlay_layer,
            {
                title: 'Show detail by hovering over a square',
                hover: true,
                onSelect: onFeatureSelect,
                onUnselect: onFeatureUnselect
            }
        )
        map.addControl(hover_control)
        hover_control.activate()
        
        $.ajax({
            url: plugin.places_URL,
            dataType: 'json',
            success: function (rearranged_places_data) {
                // add marker layer for places
                var station_markers_layer = new OpenLayers.Layer.Markers(
                    "Observation stations"
                )
                places_data = {}
                each(
                    rearranged_places_data,
                    function (places_by_attribute_group) {
                        var attributes = places_by_attribute_group.attributes
                        var compression = places_by_attribute_group.compression
                        var places = places_by_attribute_group.places
                        var id_index = attributes.indexOf('id')
                        var id_attribute = places[id_index]
                        var previous_id = 0
                        each(id_attribute,
                            function (id_offset, position) {
                                var place_id = id_offset + previous_id
                                if (places_data[place_id] == undefined) {
                                    places_data[place_id] = {}
                                }
                                id_attribute[position] = previous_id = place_id
                            }
                        )
                        attributes.splice(id_index, 1)
                        places.splice(id_index, 1)
                        compression.splice(id_index, 1)
                        each(
                            attributes,
                            function (attribute_name, index) {
                                if (compression[index] == "similar_numbers") {
                                    var previous = 0
                                    each(
                                        places[index],
                                        function (value, position) {
                                            var place_id = id_attribute[position]
                                            var place_data = places_data[place_id]
                                            previous = place_data[attribute_name] = previous + value 
                                        }
                                    )
                                }
                                else {
                                    // no compression
                                    each(
                                        places[index],
                                        function (value, position) {
                                            var place_id = id_attribute[position]
                                            var place_data = places_data[place_id]
                                            place_data[attribute_name] = value
                                        }
                                    )
                                }
                            }
                        )
                    }
                )
                var new_places = []
                for (var place_id in places_data) {
                    if (places_data.hasOwnProperty(place_id)) {
                        var place_data = places_data[place_id]
                        // store place data
                        var place = new Place(place_data)
                        new_places.push(place)
                        plugin.places[place_id] = place
                        // add marker
                        place.generate_marker(
                            function (marker) { 
                                station_markers_layer.addMarker(marker) 
                            }
                        )
                    }
                }
                each(
                    plugin.places_events,
                    function (places_function) {
                        places_function(new_places)
                    }
                )
                station_markers_layer.setVisibility(false)
                map.addLayer(station_markers_layer)
                plugin.station_markers_layer = station_markers_layer

                plugin.update_map_layer(initial_query_expression)
                plugin.filter_box = new FilterBox({
                    updated: function (filter_function) {
                        plugin.filter = filter_function
                        plugin.colour_key.with_limits(
                            plugin.render_map_layer
                        )
                    },
                    example: new Place(places_data[place_id]),
                    initial_filter: initial_filter,
                    plugin: plugin
                })
                map.addControl(plugin.filter_box)
                plugin.filter_box.activate()
                if (initial_filter == 'unfiltered') {
                    // don't update as no data loaded
                    plugin.filter_box.set_filter_no_update('Nepal')
                }
                plugin.logo = new Logo()
                plugin.logo.activate()
                map.addControl(plugin.logo)
            },
            error: function (jqXHR, textStatus, errorThrown) {
                plugin.set_status(
                    '<a target= "_blank" href="climate/places">Could not load place data!</a>'
                )
            }
        })
        var print_window = function() {
            // this breaks event handling in the widgets, but that's ok for printing
            var map_div = map.div
            var $map_div = $(map_div)
            $(map_div).remove()
            var body = $('body')
            body.remove()
            var new_body = $('<body></body>')
            new_body.css({position:'absolute', top:0, bottom:0, left:0, right:0})
            new_body.append($map_div)
            $('html').append(new_body)
            $map_div.css('width', '100%')
            $map_div.css('height', '100%')
            map.updateSize()
        }
        
        plugin.expand_to_full_window = function() {
            // this makes the map use the full browser window,
            // events still work, but it leaves a scroll bar
            S3.gis.mapPanel.autoWidth = true
            S3.gis.mapPanel.autoHeight = true
            $(map.div).css({
                position:'fixed',
                top:0, bottom:0, left:0, right:0,
                width:'100%', height:'100%',
                zIndex: 10000
            })
            $('body').children().css('display', 'none')
            $('div.fullpage').css('display', '')
            $('html').css('overflow', 'hidden')
            map.updateSize()
        }

        setTimeout(
            function () {
                //load_world_map()
                load_layer_and_locate_places_in_spaces(
                    "Nepal development regions",
                    "/eden/static/data/Development_Region.geojson",
                    new OpenLayers.Format.GeoJSON(),
                    "black",
                    "11px"
                )
                init_tooltips()
            },
            1000
            // this is waiting for OpenLayers to render everything 
            // and Ext to render all components
        )
    }
    
    var conversion_functions = {
        'Kelvin': function (value) {
            return value - 273.16
        }
    }
    var display_units_conversions = {
        'Kelvin': '&#176;C',
        // Delta
        '\u0394 Kelvin': '&#916; &#176;C'
    }
    
    plugin.render_map_layer = function(min_value, max_value) {
        plugin.overlay_layer.destroyFeatures()
        // Law of Demeter violation:
        var colour_gradient = plugin.colour_key.gradient
        var feature_data = plugin.feature_data
        var place_ids = feature_data.keys
        var values = feature_data.values
        var units = feature_data.units
        var grid_size = feature_data.grid_size
        
        var converter = plugin.converter
        var display_units = replace_power_with_sup(plugin.display_units)
        
        var range = max_value - min_value
        var features = []
        var filter = plugin.filter || function () { return true }
        var exponent_pattern = new RegExp('e(-?\\d+)')
        for (
            var i = 0;
            i < place_ids.length;
            i++
        ) {
            var place_id = place_ids[i]
            var place = plugin.places[place_id]
            if (place == undefined) {
                // some places outside of nepal may be filtered out.
                continue
            }
            var value = values[i]
            if (place == undefined) {
                console.log(i)
                console.log(place)
                console.log(place_id)
            }
            var converted_value = converter(value)
            if (
                filter(place, converted_value)
            ) {
                if (range) {
                    var normalised_value = (converted_value - min_value) / range
                }
                else {
                    var normalised_value = 0
                }
                if (
                    (0.0 <= normalised_value) && 
                    (normalised_value <= 1.0)
                ) {
                    var colour_value = colour_gradient.colour_for_value(
                        normalised_value
                    )
                    function hexFF(value) {
                        return (256+value).toString(16).substr(1)
                    }
                    var colour_string = (
                        '#'+
                        hexFF(colour_value[0]) + 
                        hexFF(colour_value[1]) + 
                        hexFF(colour_value[2])
                    )
                    var data = place.data
                    var lat = data.latitude
                    var lon = data.longitude
                    var attributes = {}
                    if (grid_size == 0) {
                        /*
                        var feature = plugin.places[data.station_id]
                        if (!!feature) {
                            feature = feature.clone()
                            features.push(feature)
                            feature.style = {
                                fillColor: colour_string,
                                pointRadius: 6,
                                strokeWidth: 1
                            }
                            attributes = feature.attributes
                        }
                        else {*/
                            features.push(
                                Vector(
                                    Point(lon, lat),
                                    attributes,
                                    {
                                        fillColor: colour_string,
                                        pointRadius: 6
                                    }
                                )
                            )
                        //}
                    }
                    else {
                        var border = grid_size / 220
                        
                        north = lat + border
                        south = lat - border
                        east = lon + border
                        west = lon - border
                        features.push(
                            Vector(
                                Polygon([
                                    LinearRing([
                                        Point(west, north),
                                        Point(east, north),
                                        Point(east, south),
                                        Point(west, south)
                                    ])
                                ]),
                                attributes,
                                {
                                    fillColor: colour_string
                                }
                            )
                        )
                    }
                    var pre_rounding_factor = Math.pow(
                        10, 
                        7-Math.floor(Math.log(Math.abs(converted_value)) / Math.LN10)
                    )
                    var attribute_string = (
                        Math.round(
                            converted_value * pre_rounding_factor
                        ) / pre_rounding_factor
                    ).toString()
                    if (exponent_pattern.test(attribute_string)) {
                        attribute_string = attribute_string.replace(
                            exponent_pattern,
                            '\u00d710<sup>$1</sup>'
                        )
                    }
                    else {
                        attribute_string = attribute_string.replace(
                            new RegExp('(\\d+)(\\.\\d+)?', 'g'), 
                            function (_, integer_part, fractional_part) {
                                var number_string = integer_part.reverse().replace(
                                    new RegExp('(\\d{3})(?!$)', 'g'),
                                    '$1,'
                                ).reverse()
                                if (fractional_part) {
                                    number_string += fractional_part
                                }
                                return number_string
                            }
                        )
                    }
                    attributes.value = attribute_string+' '+display_units
                    attributes.id = id
                    attributes.place_id = place_id
                }                        
            }
        }
        plugin.overlay_layer.addFeatures(features)
        
        plugin.request_image = function () {
            var coords = map.getCenter().transform(
                S3.gis.projection_current,
                S3.gis.proj4326
            )
            window.location.href = encodeURI([
                plugin.request_image_URL,
                '?expression=', plugin.last_query_expression ,
                '&filter=', plugin.filter_box.$text_area.val() ,
                '&width=', $(window).width() || 1024, 
                '&height=', $(window).height() || 768,
                '&zoom=', map.zoom,
                '&coords=', coords.lon, ',', coords.lat
            ].join(''))
        }
        plugin.print_button.enable()
        if (display_mode == 'print') {
            //console.log('print requested')
            plugin.expand_to_full_window()
            setTimeout(
                // this setTimeout is to allow the map to expand.
                // otherwise some map tiles might be missed
                function () { 
                    var allowed_control_class_names = [
                        "OpenLayers.Control.Attribution",
                        "OpenLayers.Control.ScaleLine",
                        "ColourKey",
                        "FilterBox",
                        "QueryBox"
                    ]
                    each(map.controls,
                        function (control) {
                            if (    
                                allowed_control_class_names.indexOf(
                                    control.__proto__.CLASS_NAME
                                ) == -1
                            ) {
                                $(control.div).hide()
                            }
                            else {
                                if (control.print_mode) {
                                    control.print_mode()
                                }
                            }
                        }
                    )
                    
                    var images_waiting = []
                    function print_if_no_more_images() {
                        if (images_waiting.length == 0) {
//                            console.log('All images loaded, now printing.')
                            setTimeout(function () {
                                window.print()
                            }, 0)
                        }
                    }
                    
                    function image_done(img) {
                        var image_pos = images_waiting.indexOf(img)
                        images_waiting.splice(image_pos, 1)
                        print_if_no_more_images()
                    }
                    each(
                        document.getElementsByTagName('img'),
                        function (img) {
                            if (!img.complete) {
                                images_waiting.push(img)
                                $(img).load(image_done).error(image_done)
                                if (img.complete) {
                                    image_done.call(img)
                                }
                            }
                        }
                    )
                    print_if_no_more_images()
                    
                    // 10 sec max wait
                    setTimeout(
                        function () { 
//                            console.log('Could not load all images in time.')
                            window.print()
                        },
                        20000
                    )
                },
                0
            )
        }
    }
    
    plugin.update_query = function (query_expression) {
        plugin.query_box.update(query_expression)
        plugin.last_query_expression = query_expression
    }
    
    plugin.update_map_layer = function (
        query_expression
    ) {
        // request new features
        plugin.overlay_layer.destroyFeatures()
        plugin.set_status('Updating...')
        plugin.query_box.update(query_expression)
        plugin.show_chart_button.disable()
//        console.log(plugin.overlay_data_URL)
        $.ajax({
            url: plugin.overlay_data_URL,
            dataType: 'json',
            data: {
                query_expression: query_expression
            },
            //timeout: 1000 * 20, // timeout doesn't seem to work
            success: function(feature_data, status_code) {
                if (feature_data.values.length == 0) {
                    plugin.set_status(
                        'Query was successful but contains no data. '+
                        'Data might be unavailable for this time range. '+
                        'Gridded data runs from 1971 to 2009. '+
                        'For Observed data please refer to '+
                        '<a href="'+plugin.station_parameters_URL+
                        '">Station Parameters</a>. '+
                        'Projected data depends on the dataset.'
                    )
                } else {
                    plugin.feature_data = feature_data
                    var units = feature_data.units
                    var converter = plugin.converter = (
                        conversion_functions[units] || 
                        function (x) { 
                            return x 
                        }
                    )
                    var display_units = plugin.display_units = display_units_conversions[units] || units
                    var values = feature_data.values
                    var place_ids = feature_data.keys
                    var usable_values = []
                    for (
                        var i = 0;
                        i < place_ids.length;
                        i++
                    ) {
                        if (plugin.places[place_ids[i]]) {
                            usable_values.push(values[i])
                        }
                    }
                    plugin.colour_key.update_from(
                        display_units,
                        converter(Math.max.apply(null, usable_values)), 
                        converter(Math.min.apply(null, usable_values))
                    )
                    plugin.update_query(feature_data.understood_expression)
                    // not right place for this:
                    plugin.filter_box.resizer.resize(true)
                    plugin.set_status('')
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                plugin.set_status(
                    'An error occurred: ' + (
                        jqXHR.statusText == 'error' ? 
                            'Is the connection OK?'
                            : jqXHR.statusText
                    )
                )
                var responseText = jqXHR.responseText
                var error_message = responseText.substr(
                    0,
                    responseText.indexOf('<!--')
                )
                var error = $.parseJSON(error_message)
                if (error.error == 'SyntaxError') {
                    // don't update the last expression if it's invalid
                    plugin.query_box.update(error.understood_expression)
                    plugin.query_box.error(error.offset)
                    plugin.set_status('')
                }
                else {
                    if (
                        error.error == 'MeaninglessUnitsException' ||
                        error.error == 'DSLTypeError' || 
                        error.error == 'DimensionError' ||
                        error.error == 'MismatchedGridSize'
                    ) {
                        window.analysis = error.analysis
                        plugin.query_box.update(error.analysis)
                    }
                    else {
                        plugin.set_status(
                            '<a target= "_blank" href="'+
                                plugin.overlay_data_URL+'?'+
                                $.param(query_expression)+
                            '">Error</a>'
                        )
                    }
                }
            },
            complete: function (jqXHR, status) {
                if (status != 'success' && status != 'error') {
                    plugin.set_status(status)
                }
            }
        });
    }
    var months = [
        '', 'Jan', 'Feb', 'Mar', 'Apr', 'May',
        'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ]

    function SpecPanel(
        panel_id, panel_title, collapsed
    ) {
        function make_combo_box(
            data,
            fieldLabel,
            hiddenName,
            combo_box_size
        ) {
            var options = []
            each(
                data,
                function (option) {
                    options.push([option, option])
                }
            )
            var combo_box = new Ext.form.ComboBox({
                id: panel_id+hiddenName,
                fieldLabel: fieldLabel,
                hiddenName: hiddenName,
                store: new Ext.data.SimpleStore({
                    fields: ['name', 'option'],
                    data: options
                }),
                displayField: 'name',
                typeAhead: true,
                mode: 'local',
                triggerAction: 'all',
                emptyText:'',
                selectOnFocus: true,
                forceSelection: true
            })
            combo_box.setSize(combo_box_size)
            if (!!options[0]) {
                combo_box.setValue(options[0][0])
            }
            return combo_box
        }

        /*
        var data_type_combo_box = make_combo_box(
            plugin.data_type_option_names,
            'Data type',
            'data_type',
            {
                width: 115,
                heigth: 25
            }
        )*/

        var variable_combo_box = make_combo_box(
            plugin.parameter_names,
            'Parameter',
            'parameter',
            {
                width: 310,
                heigth: 25
            }
        )
        // add tooltips to ease selection of datasets with long names
        variable_combo_box.tpl = new Ext.XTemplate(
            '<tpl for=".">'+
                '<div ext:qtip="{name}" class="x-combo-list-item">'+
                    '{name}'+
                '</div>'+
            '</tpl>'
        )
        
        var statistic_combo_box = make_combo_box(
            plugin.aggregation_names,
            'Statistic',
            'statistic',
            {
                width: 115,
                heigth: 25
            }
        )
        
        function inclusive_range(start, end) {
            var values = []
            for (
                var i = start;
                i <= end;
                i++
            ) {
                values.push(i)
            }
            return values
        }
        var years = inclusive_range(plugin.year_min, plugin.year_max)
        
        var from_year_combo_box = make_combo_box(
            years,
            null,
            'from_year',
            {width:60, height:25}
        )
        from_year_combo_box.setValue(plugin.year_min)
        
        var to_year_combo_box = make_combo_box(
            years,
            null,
            'to_year',
            {width:60, height:25}
        )
        to_year_combo_box.setValue(plugin.year_max)
        
        variable_combo_box.years = []
        // when a dataset is selected, request the years.
        function update_years(dataset_name) {
            $.ajax({
                url: plugin.years_URL+'?dataset_name='+dataset_name,
                dataType: 'json',
                success: function (years) {
                    variable_combo_box.years = years
                    if (years.length) {
                        from_year_combo_box.setValue(years[0])
                        to_year_combo_box.setValue(years[years.length-1])
                    }
                }
            })
        }
        variable_combo_box.on(
            'select',
            function (a, value) {
                update_years(value.json[0])
            }
        )
        update_years(plugin.parameter_names[0])
        // grey out (but don't disable) any years in the from and to year
        // combo boxes if no data is available for those years
        each(
            [from_year_combo_box, to_year_combo_box],
            function (combo_box) {
                combo_box.on(
                    'expand',
                    function () {
                        $(combo_box.list.dom).find(
                            '.x-combo-list-item'
                        ).each(
                            function (i, option_div) {
                                $option_div = $(option_div)
                                $option_div.css('display', 'block')
                                if (
                                    variable_combo_box.years.indexOf(
                                        parseInt($option_div.text())
                                    ) == -1
                                ) {
                                    $option_div.css('display', 'none')
                                }
                            }
                        )
                    }
                )
            }
        )
        
        var from_month_combo_box = make_combo_box(
            months,
            null,
            'from_month',
            {width:50, height:25}
        )
        plugin.month_selector_ids.push(from_month_combo_box.id)

        var to_month_combo_box = make_combo_box(
            months,
            null,
            'to_month',
            {width:50, height:25}
        )
        add_tooltip({
            target: to_year_combo_box.id,
            html: 'If month is not specified, the end of the year will be used.'
        })
        add_tooltip({
            target: to_month_combo_box.id,
            html: 'If month is not specified, the end of the year will be used.'
        })
        plugin.month_selector_ids.push(to_month_combo_box.id)
        
        var month_letters = []
        var month_checkboxes = []
        // if none are picked, don't do annual aggregation
        // if some are picked, aggregate those months
        // if all are picked, aggregate for whole year
        each('DJFMAMJJASOND',
            function (
                month_letter,
                month_index
            ) {
                month_letters.push(
                    {
                        html: month_letter,
                        border: false
                    }
                )
                var name = 'month-'+month_index
                month_checkboxes.push(
                    new Ext.form.Checkbox({
                        id: panel_id+'_'+name,
                        name: name,
                        checked: (month_index > 0)
                    })
                )
            }
        )
        add_tooltip({
            target: panel_id+'_month-0',
            html: 'Include Previous December. Years will also start in Previous December and end in November.'
        })
        month_checkboxes[0].on('check', function(a, value) {
            if (value && month_checkboxes[12].checked) {
                month_checkboxes[12].setValue(false)
            }
        })
        month_checkboxes[12].on('check', function(a, value) {
            if (value && month_checkboxes[0].checked) {
                month_checkboxes[0].setValue(false)
            }
        })
        var month_filter = month_letters.concat(month_checkboxes)
        var annual_aggregation_check_box_id = panel_id+'_annual_aggregation_checkbox'
        var annual_aggregation_check_box = new Ext.form.Checkbox({
            id: annual_aggregation_check_box_id,
            name: 'annual_aggregation',
            checked: true,
            fieldLabel: 'Annual aggregation'
        })
        plugin.month_selector_ids.push(annual_aggregation_check_box_id)
        add_tooltip({
            target: panel_id+'_annual_aggregation_checkbox',
            html: 'Aggregate monthly values into yearly values. Only affects charts.'
        })
        var month_checkboxes_id = panel_id+'_month_checkboxes'
        annual_aggregation_check_box.on('check', function(a, value) {
            var month_checkboxes = $('#'+month_checkboxes_id)
            if (value) {
                month_checkboxes.show(300)
            }
            else {
                month_checkboxes.hide(300)
            }
        })
        plugin.month_selector_ids.push(month_checkboxes_id)

        var form_panel = new Ext.FormPanel({
            id: panel_id,
            title: panel_title,
            collapsible: true,
            collapseMode: 'mini',
            collapsed: collapsed,
            labelWidth: 55,
            items: [{
                region: 'center',
                items: [
                    new Ext.form.FieldSet({
                        style: 'margin: 0px; border: none;',
                        items: [
                            //data_type_combo_box,
                            variable_combo_box,
                            statistic_combo_box,
                            annual_aggregation_check_box,
                            // month filter checkboxes
                            {
                                id: month_checkboxes_id,
                                border: false,
                                layout: {
                                    type: 'table',
                                    columns: (month_filter.length / 2)
                                },
                                defaults: {
                                    width: '15px',
                                    height: '1.3em',
                                    style: 'margin: 0.1em;'
                                },
                                items: month_filter
                            },
                            new Ext.form.CompositeField(
                                {
                                    fieldLabel: 'From',
                                    items:[
                                        from_year_combo_box,
                                        from_month_combo_box
                                    ]
                                }
                            ),
                            new Ext.form.CompositeField(
                                {
                                    fieldLabel: 'To',
                                    items:[
                                        to_year_combo_box,
                                        to_month_combo_box
                                    ]
                                }
                            )
                        ]
                    })
                ]
            }]
        })
        add_tooltip({
            target: month_checkboxes_id,
            html: 'Select months that will be used in the aggregation.'
        })
        return form_panel
    }
    var filter_months = [
        'PrevDec', 'Jan', 'Feb', 'Mar', 'Apr', 'May',
        'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ]

    function form_query_expression(ext_form) {
        form_values = ext_form.getValues()
        var month_names = []
        each(
            [0,1,2,3,4,5,6,7,8,9,10,11,12],
            function (
                month_number
            ) {
                if (
                    form_values['month-'+month_number] == 'on'
                ) {
                    month_names.push(
                        filter_months[month_number]
                    )
                }
            }
        )
        return (
            [
                form_values.statistic,
                '(',
                    '"', form_values.parameter.replace(new RegExp('\\+','g'),' '), '", ',
                    'From(',
                        form_values.from_year ,
                        (form_values.from_month?', '+form_values.from_month:''),
                    '), ',
                    'To(',
                        form_values.to_year ,
                        (form_values.to_month?', '+form_values.to_month:''),
                    ')',
                    (
                        form_values.annual_aggregation ?
                        (', Months('+month_names.join(', ')+')'):''
                    ),
                ')'
            ].join('')
        )
    }

    plugin.addToMapWindow = function (items) {
        // create the panels
        var climate_data_panel = SpecPanel(
            'climate_data_panel',
            'Select data: (A)',
            false
        )
        // This button does the simplest "show me data" overlay
        plugin.update_map_layer_from_form = function () {
            plugin.update_map_layer(
                form_query_expression(climate_data_panel.getForm())
            )
        }
        var update_map_layer_button = new Ext.Button({
            text: 'Show on map (A)',
            disabled: false,
            handler: plugin.update_map_layer_from_form
        });
        climate_data_panel.addButton(update_map_layer_button)
        items.push(climate_data_panel)
        
        var comparison_panel = SpecPanel(
            'comparison_panel',
            'Compare with data (B)',
            true
        )
        // This button does the comparison overlay
        plugin.update_map_layer_from_comparison = function () {
            plugin.update_map_layer(
                
                form_query_expression(comparison_panel.getForm()) + ' - ' +
                form_query_expression(climate_data_panel.getForm())
            )
        }
        var update_map_layer_comparison_button = new Ext.Button({
            text: 'Compare on map (B - A)',
            disabled: false,
            handler: plugin.update_map_layer_from_comparison
        });
        comparison_panel.addButton(update_map_layer_comparison_button)
        items.push(comparison_panel)
        
        
        var quick_filter_data_store = plugin.quick_filter_data_store = new Ext.data.SimpleStore({
            fields: ['name', 'option']
        })
        var quick_filter_combo_box = new Ext.form.ComboBox({
            fieldLabel: 'Region',
            hiddenName: 'region',
            store: quick_filter_data_store,
            displayField: 'name',
            typeAhead: true,
            mode: 'local',
            triggerAction: 'all',
            emptyText: '',
            selectOnFocus: true,
            forceSelection: true
        })
        var quick_filter_panel = new Ext.Panel({
            id: 'quick_filter_panel',
            title: 'Region filter',
            collapsible: true,
            collapseMode: 'mini',
            collapsed: false,
            items: [
                quick_filter_combo_box
            ]
        })
        quick_filter_combo_box.on(
            'select',
            function (combo_box, record, index) {
                var region_name = record.data.name
                if (region_name == "(All)") {
                    plugin.filter_box.set_filter('')
                } 
                else {
                    if (region_name == "Nepal") {
                        plugin.filter_box.set_filter('Nepal')
                    } 
                    else {
                        plugin.filter_box.set_filter('within("'+region_name+'")')
                    }
                }
            }
        )
        items.push(quick_filter_panel)
        
        function get_selected_place_ids() {
            var place_ids = []
            each(
                plugin.overlay_layer.selectedFeatures,
                function (feature) {
                    place_ids.push(feature.data.place_id)
                }
            )
            return place_ids
        }
        var show_chart_button = new Ext.Button({
            text: 'Show chart for selected places',
            disabled: true,
            handler: function() {
                // create URL
                var place_ids = get_selected_place_ids()
                var place_names = []
                each(
                    place_ids,
                    function (place_id) {
                        var place = plugin.places[place_id]
                        var place_data = place.data
                        if (place_data.station_name != undefined) {
                            place_names.push(place_data.station_name)
                        }
                        else {
                            place_names.push(
                                '('+place_data.latitude+'N,'+place_data.longitude+'E)'
                            )
                        }
                    }
                )
                if (place_ids.length == 0) {
                    // there is bug in the selection
                    // sometimes places look selected but aren't
                    // deselect all, disable and give up
                    plugin.show_chart_button.disable()
                    plugin.selectCtrl.unselectAll()
                }
                else {
                    var query_expression = plugin.last_query_expression
                    var spec = JSON.stringify({
                        place_ids: place_ids,
                        query_expression: query_expression
                    })
                    
                    if (place_names.length > 7) {
                        var place_names_string = "many places"
                    } else {
                        var place_names_string = place_names.join(', ')
                    }
                    var chart_name = [
                        query_expression.replace(
                            new RegExp('[",]', 'g'), ''
                        ).replace(
                            new RegExp('[()]', 'g'), ' '
                        ),
                        'for '+place_names_string
                    ].join(' ').replace(
                        new RegExp('\\s+', 'g'), ' '
                    )

                    // get hold of a chart manager instance
                    if (
                        !plugin.chart_window ||
                        typeof plugin.chart_window.chart_manager == 'undefined'
                    ) {
                        var chart_window = plugin.chart_window = window.open(
                            plugin.chart_popup_URL,
                            'chart',
                            'width=660,height=600,toolbar=0,resizable=0'
                        )
                        chart_window.onload = function () {
                            chart_window.chart_manager = new chart_window.ChartManager(plugin.chart_URL)
                            chart_window.chart_manager.addChartSpec(
                                spec,

                                chart_name
                            )
                        }
                        chart_window.onbeforeunload = function () {
                            delete plugin.chart_window
                        }
                    } else {
                        // some duplication here:
                        plugin.chart_window.chart_manager.addChartSpec(spec, chart_name)
                    }
                }
            }
        })
        plugin.show_chart_button = show_chart_button
         
        items.push(show_chart_button)
 
        var download_data_button = new Ext.Button({
            text: 'Download CSV map data for selected places',
            disabled: false,
            handler: function() {
                var place_ids = get_selected_place_ids()
                var spec = JSON.stringify({
                    place_ids: place_ids,
                    query_expression: plugin.last_query_expression
                })
                window.location.href = plugin.download_data_URL+'?spec='+encodeURI(spec)
            }
        })
        plugin.download_data_button = download_data_button
        items.push(download_data_button)

        var download_time_series_button = new Ext.Button({
            text: 'Download CSV time series for selected places',
            disabled: false,
            handler: function() {
                var place_ids = get_selected_place_ids()
                var spec = JSON.stringify({
                    place_ids: place_ids,
                    query_expression: plugin.last_query_expression
                })
                window.location.href = plugin.download_timeseries_URL+'?spec='+encodeURI(spec)
            }
        })
        plugin.download_time_series_button = download_time_series_button
        items.push(download_time_series_button)

        var print_button = new Ext.Button({
            text: 'Download printable map image',
            disabled: false,
            handler: function() {
                // make the map use the full window
                // plugin.full_window()
                // add a button on the map "Download image"
                plugin.request_image()
                print_button.disable()
            }
        })
        plugin.print_button = print_button
        print_button.disable()
        items.push(print_button)
        
        items.push({
            autoEl: {
                    tag: 'div',
                    id: 'error_div'
                }                
            }
        )
        plugin.set_status = function (html_message) {
            $('#error_div').html(html_message)
        }
        
        plugin.colour_key = new ColourKey({
            gradients: [
                course_colour_steps,
                smooth_blue_green_red,
                blue_green_red_cosines,
                black_to_white,
                blue_to_yellow,
                red_to_green,
                red_to_blue,
                green_to_blue
            ]
        })
        plugin.colour_key.on_change(plugin.render_map_layer)
        map.addControl(plugin.colour_key)
        plugin.colour_key.activate()

        plugin.query_box = new QueryBox({
            updated: plugin.update_map_layer
        })
        map.addControl(plugin.query_box)
                
        plugin.query_box.activate()
        
        // with a lot of data, things can get slow, animations make it worse
        map.panDuration = 0
    }
    
    function apply_attributes(object, attributes) {
        for (var name in attributes) {
            if (attributes.hasOwnProperty(name)) {
                object[name] = attributes[name]
            }
        }
    }
    
    plugin.setupToolbar = function (toolbar) {
        var SelectDragHandler = OpenLayers.Class(OpenLayers.Handler.Drag, {
            // Ensure that we propagate clicks (so we can still use other controls)
            down: function() {
                OpenLayers.Handler.Drag.prototype.down.apply(arguments)
                //OpenLayers.Event.stop(evt);
                return true;
            },
            CLASS_NAME: 'SelectHandler'
        });
        // selection of overlay squares
        OpenLayers.Feature.Vector.style['default']['strokeWidth'] = '2'
        var selectCtrl = plugin.selectCtrl = new OpenLayers.Control.SelectFeature(
            plugin.overlay_layer,
            {
                clickout: true,
                toggle: false,
                toggleKey: 'altKey',
                multiple: false,
                multipleKey: 'shiftKey',
                hover: false,
                box: true,
                onSelect: function (feature) {
                    apply_attributes(
                        feature.style,
                        {
                            strokeColor: 'black',
                            strokeDashstyle: 'dash',
                            strokeWidth: 1
                        }
                    )
                    plugin.overlay_layer.drawFeature(feature)
                    plugin.show_chart_button.enable()
                },
                onUnselect: function (feature) {
                    apply_attributes(
                        feature.style,
                        {
                            strokeColor: '',
                            strokeDashstyle: '',
                            strokeWidth: 1
                        }
                    )
                    plugin.overlay_layer.drawFeature(feature)
                    if (plugin.overlay_layer.selectedFeatures.length == 0) {
                        plugin.show_chart_button.disable()
                    }
                }
            }
        )
        
        // workaround: is this a bug in OpenLayers?
        //selectCtrl.handlers.box.dragHandler.dragstart
        OpenLayers.Handler.Drag.prototype.dragstart = function (evt) {
            var propagate = true;
            this.dragging = false;
            if (this.checkModifiers(evt) &&
                   (OpenLayers.Event.isLeftClick(evt) ||
                    OpenLayers.Event.isSingleTouch(evt))) {
                this.started = true;
                this.start = evt.xy;
                this.last = evt.xy;
                OpenLayers.Element.addClass(
                    this.map.viewPortDiv, "olDragDown"
                );
                this.down(evt);
                this.callback("down", [evt.xy]);

                //OpenLayers.Event.stop(evt);

                if (!this.oldOnselectstart) {
                    this.oldOnselectstart = document.onselectstart ?
                        document.onselectstart : OpenLayers.Function.True;
                }
                document.onselectstart = OpenLayers.Function.False;

                propagate = !this.stopDown;
            } else {
                this.started = false;
                this.start = null;
                this.last = null;
            }
            return true;
        }
        
        

        toolbar.add(
            new GeoExt.Action({
                control: selectCtrl,
                map: map,
                iconCls: 'select_places',
                // button options
                tooltip: 'Select places by dragging a box',
                toggleGroup: 'controls',
                allowDepress: true,
                pressed: false
            })
        )
        map.controls[0].deactivate()
    }
}
