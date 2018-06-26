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
                 btn.setAttribute('assembly', species_list[i])
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
                 show_hide(this.getAttribute('assembly'), 'False');
                 this.setAttribute('show', 'False');
                 // Give button a red background color
                 this.style.background = "#ff9263";
                 }
                 // If currently hiding nodes, show them now
                 else
                 {
                 this.setAttribute('show', 'True');
                 show_hide(this.getAttribute('assembly'), 'True');
                 // Remove red background from button
                 this.style.background = "#91ffd4";
                 };updateCyLegend();});
                 // Add button to color legend div
                 colorLegend.appendChild(btn);
             };}

// Reset color legend: Show all assemblies
function reset_color_legend()
{
// Get reference to buttons
var colorLegend_buttons = document.getElementById('colorLegend').children;
for (var i = 0; i < colorLegend_buttons.length; i++){
colorLegend_buttons[i].setAttribute('show', 'True');
colorLegend_buttons[i].style.background = "#91ffd4";
};
}

// For each assembly, show/hide nodes according to current button state
// Used when the graph is extended (e.g. show neighbors, coding etc.)
function show_hide_refresh()
{
// Get reference to buttons
var colorLegend_buttons = document.getElementById('colorLegend').children;
// Itterate through buttons, each represents an assembly
// Call show_hide to set visibility according to current status
for (var i = 0; i < colorLegend_buttons.length; i++){
show_hide(colorLegend_buttons[i].getAttribute('assembly'), colorLegend_buttons[i].getAttribute('show'));
};
}

// Show or hide nodes of one assembly
function show_hide(assembly, show)
{
var cy= $('#cy').cytoscape('get'); // now we have a global reference to `cy`
// If cytoscape has not been initialized yet, return
if (typeof(cy) == 'undefined')
{
return;
}

// Else, run through each node and if node belongs to assembly set state
cy.nodes().forEach(function( node )
    {
        if (node.data('species')==assembly)
        {
         if(show == 'True') {node.show();}
         else{node.hide();};
        };
    });
}
