// Generate an interactive color legend
// Each assembly has one color assigned
// Clicking the respective button in the legend shows/hides all nodes of that assembly

// Generate color legend: Generate clickable buttons
function update_color_legend(species_list)
{
// Get reference to div
var colorLegend = document.getElementById('colorLegend');
// Remove all previous buttons
while (colorLegend.firstChild) {colorLegend.removeChild(colorLegend.firstChild);}
// Loop through assembly list, generate a button for each assembly
for(var i = 0; i < species_list.length; i++)
            {
                 // Create a new button option and set its attributes
                 var btn = document.createElement("button");
                 btn.setAttribute('type', 'button');
                 // Default: Show nodes
                 btn.setAttribute('show', 'True')
                 btn.setAttribute('species', species_list[i])
                 btn.setAttribute('id', 'show_hide' + "_"+species_list[i]);
                 btn.innerHTML = species_list[i];
                 btn.value = species_list[i];
                 btn.style.border="4px solid "+color_node(species_list[i], "")
                 btn.style.background = "#91ffd4";
                 // On click, change state of button and show or hide nodes for this assembly
                 btn.addEventListener("click", function(){
                 // If currently showing nodes, hide them now
                 if (this.getAttribute('show')=='True')
                 {
                 show_hide(this.getAttribute('species'), 'False');
                 this.setAttribute('show', 'False');
                 // Give button a red background color
                 this.style.background = "#ff9263";
                 }
                 // If currently hiding nodes, show them now
                 else
                 {
                 this.setAttribute('show', 'True');
                 show_hide(this.getAttribute('species'), 'True');
                 // Remove red background from button
                 this.style.background = "#91ffd4";
                 };});
                 // Add button to color legend div
                 colorLegend.appendChild(btn);
             };
}

// Reset color legend: Show all assemblies
function reset_color_legend()
{
// Get reference to div
var colorLegend_buttons = document.getElementById('colorLegend').children;
for (var i = 0; i < colorLegend_buttons.length; i++){
console.log(colorLegend_buttons[i]);
}

}