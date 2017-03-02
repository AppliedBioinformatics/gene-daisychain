// AHGraR-specific function
// Hides or shows HOMOLOG edges depending on selected sensitivity value
function changeSensitivity()
{
    // Get currently selected cluster size value
    // Find select menu and retrieve currently selected cluster size
    var select_sen_menu = document.getElementById("select_sensitivity");
    cluster_size = select_sen_menu.options[select_sen_menu.selectedIndex].value;
    // Get global reference to `cy`
    var cy= $('#cy').cytoscape('get'); 
    // Iterate through all HOMOLOG edges
   cy.edges().forEach(function( edge ) {
       if (edge.data("type")=="HOMOLOG")
       {
           // Set hide/show depending on edge sensitivity value
           if (edge.data("sensitivity")!=cluster_size)
           {
               edge.hide();
        }
        else
            {
             edge.show();   
            }
    }
      });
};
