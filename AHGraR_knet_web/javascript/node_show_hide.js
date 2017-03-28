function show_hide(species, show)
{
var cy= $('#cy').cytoscape('get'); // now we have a global reference to `cy`
if (typeof(cy) == 'undefined')
{
return;
}
cy.nodes().forEach(function( node )
    {
        console.log(node.data('species'));
        if (node.data('species')==species)
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