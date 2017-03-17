function show_hide(species, show)
{
var cy= $('#cy').cytoscape('get'); // now we have a global reference to `cy`
for (var ele in cy.elements())
{
console.log(ele);
}
}