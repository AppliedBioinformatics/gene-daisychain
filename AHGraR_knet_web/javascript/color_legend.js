function set_color_legend()
{
console.log("Retrieve  color legend");
buttons = document.getElementById('colorLegend').childNodes;
for (var but in buttons)
{
console.log(buttons[but].species);
//show_hide(buttons[but].getAttribute('species'), buttons[but].getAttribute('show'));
}
}
function update_color_legend(species_list)
{

var colorLegend = document.getElementById('colorLegend');
console.log("Set color legend");
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
                 show_hide(this.getAttribute('species'), 'False');
                 this.setAttribute('show', 'False');
                 this.style.background = "#ff9263";}
                 else
                 {console.log("showing now");
                 this.setAttribute('show', 'True');
                 show_hide(this.getAttribute('species'), 'True');
                 this.style.background = "#91ffd4";};
                console.log(this.getAttribute('species'));
                   });
                 // Fill select option with data:
                 btn.innerHTML = species_list[i];
                 btn.value = species_list[i];
                 btn.style.border="4px solid "+color_node(species_list[i], "")
                 btn.style.background = "#91ffd4";
                 //btn.style.background=color_node(species_list[i], "");
                 colorLegend.appendChild(btn);
             };

//btn.setAttribute('onclick', functions[i]);


}