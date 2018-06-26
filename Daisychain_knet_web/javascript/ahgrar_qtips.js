// Defines the tooltips shown on nodes and edges
// Based on qtip
// Function is called when loading search results or manually extending graph
// qtip may be added to an element that has already a qtip, By default, qtip()
// overrides existing qtips.

function add_qtips(){
var cy= $('#cy').cytoscape('get'); // now we have a global reference to `cy`
// Add a qtip message for all nodes
cy.elements('node').qtip({
  content: function() {
  var qtipMsg= "";
  if(this.data('type')=="Gene"){
    qtipMsg= "<b>Name:</b> "+ this.data('name')  + " [Gene]<br>"
    +"<b>Assembly:</b> "+ this.data('species')+ "<br>"
    +"<b>Contig:</b> "+ this.data('contig');}

  else if(this.data('type')=="Protein"){
    qtipMsg= "<b>Name:</b> "+ this.data('name')  + " [Protein]<br>"
    +"<b>Assembly:</b> "+ this.data('species')+ "<br>";}
    return qtipMsg;},

  style: {
    classes: 'qtip-bootstrap',
    tip: {
      width: 12,
      height: 6
    }
  }
});

// Add a qtip message for all edges
cy.elements('edge').qtip({
  content: function() {
      var qtipMsg= "";
      if(this.data('type')=="HOMOLOG"){
        perc_match = this.data('perc_match');
        if (isNaN(perc_match)){perc_match = 0;};
        qtipMsg= "<b>Identity:</b> "+ perc_match+"%";}
      if(this.data('type')=="CODING"){
        qtipMsg= "Gene coding for a protein";}
      if(this.data('type')=="5_NB"){
        qtipMsg= "Located upstream on contig";}
      if(this.data('type')=="3_NB"){
        qtipMsg= "Located downstream on contig";}
      return qtipMsg;},
  style: {
    classes: 'qtip-bootstrap',
    tip: {
      width: 12,
      height: 6
    }
  }
});

}