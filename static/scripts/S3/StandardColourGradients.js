coarse_colour_steps = new ColourGradient([
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

blue_green_red_cosines = []
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

blue_green_red_cosines = new ColourGradient(blue_green_red_cosines)

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
smooth_blue_green_red = new ColourGradient(smooth_blue_green_red)

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

black_to_white = new ColourGradient(linear_gradient([0,0,0], [1,1,1]))
blue_to_yellow = new ColourGradient(linear_gradient([0,0,1], [1,1,0]))
red_to_green = new ColourGradient(linear_gradient([1,0,0], [0,1,0]))
red_to_blue = new ColourGradient(linear_gradient([1,0,0], [0,0,1]))
green_to_blue = new ColourGradient(linear_gradient([0,1,0], [0,0,1]))
