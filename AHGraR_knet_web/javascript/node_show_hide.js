function show_hide(species, show)
{
var cy= $('#cy').cytoscape('get'); // now we have a global reference to `cy`
cy.nodes().forEach(function( node )
    {
        console.log(node.data('species'));
        node.hide();

    });
}