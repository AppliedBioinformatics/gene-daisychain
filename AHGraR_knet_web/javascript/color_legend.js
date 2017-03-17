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
                 btn.setAttribute('species', species_list[i])
                 btn.setAttribute('id', 'show_hide' + "_"+species_list[i]);
                 btn.addEventListener("click", function(){
                 if (this.getAttribute('show')=='True')
                 {console.log("hiding now");
                 this.setAttribute('show', 'False');}
                 else
                 {console.log("showing now");
                 this.setAttribute('show', 'True');
                 this.style.background-color = "#4CAF50"};
                console.log(this.getAttribute('species'));
                   });
                 // Fill select option with data:
                 btn.innerHTML = species_list[i];
                 btn.value = species_list[i];
                 btn.style.border="2px solid "+color_node(species_list[i], "")
                 //btn.style.background=color_node(species_list[i], "");
                 colorLegend.appendChild(btn);
             };

//btn.setAttribute('onclick', functions[i]);


}