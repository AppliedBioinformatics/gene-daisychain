function show_hide(assembly, show)
{
var cy= $('#cy').cytoscape('get'); // now we have a global reference to `cy`
if (typeof(cy) == 'undefined')
{
return;
}
cy.nodes().forEach(function( node )
    {
        if (node.data('species')==assembly)
        {
         if(show == 'True')
         {
         node.show();
         }
         else
         {
         node.hide();
         };
        };
    });
}
function is_visible(assembly)
{
return "show";
}