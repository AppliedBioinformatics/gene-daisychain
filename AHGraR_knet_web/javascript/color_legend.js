function update_color_legend(species_list)
{
//$('#colorLegend span').text("Huhu");
var colorLegend = document.getElementById('colorLegend');
console.log("Update color legend");
console.log(species_list);
// Remove old elements
while (colorLegend.firstChild) {
    colorLegend.removeChild(colorLegend.firstChild);
}
for(var i = 0; i < species_list.length; i++)
            {
                 // Create a new select option
                 var btn = document.createElement("button");
                 btn.setAttribute('type', 'button');
                 btn.setAttribute('show', 'True')
                 btn.setAttribute('id', 'show_hide' + "_"+species_list[i]);
                 btn.setAttribute('onclick', function(species_list[i]){
                 console.log("click :-)");});
                 // Fill select option with data:
                 btn.innerHTML = species_list[i];
                 btn.value = species_list[i];
                 btn.style.border="2px solid "+color_node(species_list[i], "")
                 //btn.style.background=color_node(species_list[i], "");
                 colorLegend.appendChild(btn);
             };

//btn.setAttribute('onclick', functions[i]);


}