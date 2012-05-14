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