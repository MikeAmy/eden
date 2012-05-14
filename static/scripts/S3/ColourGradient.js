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
