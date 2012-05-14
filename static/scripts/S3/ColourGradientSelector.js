
var ColourGradientSelector = OpenLayers.Class(OpenLayers.Control, {
    CLASS_NAME: 'ColourGradientSelector',
/*    initialize: function () {
        var colour_gradient_selector = this
        console.log(colour_gradient_selector.gradients)
        colour_gradient_selector.gradients = colour_gradient_selector.gradients || []
        if (colour_gradient_selector.gradients.length > 0) {
            colour_gradient_selector.set_gradient(colour_gradient_selector.gradients[0])
        }
    },*/
    destroy: function() {
        var colour_gradient_selector = this
        colour_gradient_selector.deactivate();
        OpenLayers.Control.prototype.destroy.apply(
            colour_gradient_selector,
            arguments
        );
    },
    set_gradient: function (colour_gradient) {
        var colour_gradient_selector = this
        colour_gradient_selector.gradient = colour_gradient
        colour_gradient.manage_image(
            colour_gradient_selector.$key_colour_gradient_selector_img
        )
    },    
    on_change: function (use_limits_and_gradient) {
        // provide a callback for when the limits change
        // use_limits needs to accept min and max
        this.use_limits_and_gradient = use_limits_and_gradient
    },
    use_callback: function () {
        if (colour_gradient_selector.use_limits_and_gradient != null) {
            colour_gradient_selector.use_limits_and_gradient(
                parseFloat(colour_gradient_selector.$lower_limit.attr('value')),
                parseFloat(colour_gradient_selector.$upper_limit.attr('value')),
                colour_gradient_selector.gradient
            )
        }
    },    
    activate: function() {
        var colour_gradient_selector = this
        if (
            OpenLayers.Control.prototype.activate.apply(colour_gradient_selector, arguments)
        ) {
            colour_gradient_selector.set_gradient(colour_gradient_selector.gradients[0])
            // when the user changes limits, the map colours update instantly
            var bound_use_callback = function () { colour_gradient_selector.use_callback() }
            colour_gradient_selector.$lower_limit.change(bound_use_callback)
            colour_gradient_selector.$upper_limit.change(bound_use_callback)
            return true;
        } else {
            return false;
        }
    },
    deactivate: function() {
        var colour_gradient_selector = this
        if (
            OpenLayers.Control.prototype.deactivate.apply(colour_gradient_selector, arguments)
        ) {
            return true;
        } else {
            return false;
        }
    },
    draw: function() {
        var colour_gradient_selector = this
        OpenLayers.Control.prototype.draw.apply(colour_gradient_selector, arguments);
        
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
            colour_gradient_selector.gradients,
            function (colour_gradient) {
                var gradient_image = IMG({
                    width:'100%',
                    height:'15px',
                    style:'border-top: 1px solid black; border-bottom: 1px solid black; margin-top: 1px;',
                    title:'click to use this gradient'
                })
                colour_gradient.manage_image(gradient_image)
                gradient_images.push(gradient_image)
                gradient_image.mouseover(raise)
                gradient_image.mouseout(lower)
                gradient_image.click(function () {
                    colour_gradient_selector.set_gradient(colour_gradient)
                    colour_gradient_selector.use_callback()
                })
            }
        )
        colour_gradient_selector.$controls = DIV(
            {
                style: 'display: none; padding-top: 3px;'
            },
            SPAN({}, 'Click to select gradient:'),
            gradient_images
        )
        
        colour_gradient_selector.$key_colour_gradient_selector_img = IMG({
            width:'100%',
            height:'15px',
            title:'Click to invert colour gradient'
        })
        colour_gradient_selector.$gradient = DIV({},
            colour_gradient_selector.$key_colour_gradient_selector_img,
            colour_gradient_selector.$controls
        )
        colour_gradient_selector.$key_colour_gradient_selector_img.click(
            function () {
                colour_gradient_selector.gradient.invert()
                colour_gradient_selector.use_callback()
            }
        )
        var $div = colour_gradient_selector.$inner_div = DIV({
                style:'width: 240px; position:absolute; top: 10px; left:55px; background-color:#222; border-top:1px solid #EEE; padding: 4px; border-radius: 5px;color:white;'
            },
            colour_gradient_selector.$gradient
        )
        $div.mouseover(
            function () {
                colour_gradient_selector.$controls.css('display', 'inline')
            }
        )
        $div.mouseout(
            function () {
                colour_gradient_selector.$controls.css('display', 'none')
            }
        )
        $(colour_gradient_selector.div).append($div)
        $div.show()
        return colour_gradient_selector.div
    }
})
    