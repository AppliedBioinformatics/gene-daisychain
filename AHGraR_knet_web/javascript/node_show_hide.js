function show_hide(species, show)
{
var cy= $('#cy').cytoscape('get'); // now we have a global reference to `cy`
var x = cy.elements();
console.log(x);
}