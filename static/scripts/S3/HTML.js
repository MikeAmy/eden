function walk(items, use_item) {
    if (items === undefined) {
        throw new Error("items are undefined, should be a list")
    }
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
