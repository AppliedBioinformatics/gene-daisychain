// Set unique and distinguishable colors to each species node
// Within a species, variate color slightly to distinguish between individual chromosomes
function color_node(species, chromosome)
{
   colors = {
        0: "#a9a9a9", //darkgrey
        1: "#0000ff", //blue
        2: "#a52a2a", //brown
        3: "#ff8c00", //darkorange
        4: "#ff00ff", //fuchsia
        5: "#ffd700", //gold
        6: "#008000", //green
        7: "#4b0082", //indigo
        8: "#f0e68c", //khaki
        9: "#00ff00", //lime
        10: "#ff00ff", //magenta
        11: "#800000", //maroon
        12: "#000080", //navy
        13: "#808000", //olive
        14: "#ffa500", //orange
        15: "#ffc0cb", //pink
        16: "#800080", //purple
        17: "#800080", //violet
        18: "#ff0000", //red
        19: "#9400d3", //darkviolet
        20: "#ffff00", //yellow
        21: "#00008b", //darkblue
        22: "#008b8b", //darkcyan
        23: "#00ffff", //aqua
        24: "#006400", //darkgreen
        25: "#bdb76b", //darkkhaki
        26: "#8b008b", //darkmagenta
        27: "#556b2f", //darkolivegreen
        28: "#e9967a", //darksalmon
        29: "#9932cc", //darkorchid
        30: "#8b0000" //darkred
 

    };
    if(color_map[species])
    {
        console.log("Found color: "+ color_map[species]);    
        return color_map[species];
    }
    else
    {
        color_map[species]=colors[Object.keys(color_map).length%30];
        console.log("New color: "+color_map[species]);
        return color_map[species]; 
    };
};
