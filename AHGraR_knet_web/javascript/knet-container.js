// This function is used to convert search results (keyword or blast) into a graph visualization
// A graph can then be extended via the context menu
// Those functions are provided by extend_graph

function load_reload_Network(network_json, network_style) {
// Initialise a cytoscape container instance on the HTML DOM using JQuery.
$('#cy').cytoscape({
  container: document.getElementById('cy')/*$('#cy')*/,
  style: network_style,
  // Using the JSON data to create the nodes.
  elements: network_json,
  // this is an alternative that uses a bitmap during interaction.
  textureOnViewport: false, // true,
  // interpolate on high density displays instead of increasing resolution.
  pixelRatio: 1,
  // Zoom settings
  zoomingEnabled: true, // zooming: both by user and programmatically.
  zoom: 1, // the initial zoom level of the graph before the layout is set.
  wheelSensitivity: 0.05,
  panningEnabled: true, // panning: both by user and programmatically.
  touchTapThreshold: 8,
  desktopTapThreshold: 4,
  autolock: false,
  autoungrabify: false,
  autounselectify: false,
  // a "motion blur" effect that increases perceived performance for little or no cost.
  motionBlur: true,
  ready: function() {
      rerunLayout(); // reset current layout.
   window.cy= this;
  }
});

// Get the cytoscape instance as a Javascript object from JQuery.
var cy= $('#cy').cytoscape('get'); // now we have a global reference to `cy`
cy.boxSelectionEnabled(true); // enable box selection (highlight & select multiple elements for moving via mouse click and drag).

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
        qtipMsg= "<b>Identity:</b> "+ this.data('perc_match')+"%";}
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


 //Popup (context) menu: a circular Context Menu for each Node (concept) & Edge (relation) using the 'cxtmenu' jQuery plugin.
 // Define indidivual ctxt menus for genes, proteins and edges

 // Context menu for genes
 var ctxt_menu_gene= {
    menuRadius: 75, // the radius of the circular menu in pixels
    selector: 'node[type="Gene"]',
    commands: [ // an array of commands to list in the menu
        {
         content: 'Show Info',
         select: function() {
             // Show Item Info Pane.
             openItemInfoPane();
             // Display Item Info.
             showItemInfo(this);
            }
        },
        {
         content: 'Delete',
         select: function() {
            cy.remove(this);
			 // Refresh network legend.
             updateCyLegend();
            }
        },
        {
         content: "Show 5'/3'",
         select: function()
            {
                addPath(this, "53NB");
            }
        },
        {
         content: "Show protein",
         select: function()
            {
                addPath(this, "CODING");
            } 
        },
        {
         content: "Show homologs",
         select: function()
            {
                addPath(this, "HOMOLOG");
            } 
        },
        {
         content: 'Label on/ off',
         select: function() {
             if(this.style('text-opacity') === '0') {
                this.style({'text-opacity': '1'}); // show the concept/ relation Label.
               }
               else {
                this.style({'text-opacity': '0'}); // hide the concept/ relation Label.
               }
            }
        }
    ], 
    fillColor: 'rgba(0, 37, 96, 0.75)', // the background colour of the menu
    activeFillColor: 'rgba(92, 194, 237, 0.75)', // the colour used to indicate the selected command
    activePadding: 2, // 20, // additional size in pixels for the active command
    indicatorSize: 15, // 24, // the size in pixels of the pointer to the active command
    separatorWidth: 3, // the empty spacing in pixels between successive commands
    spotlightPadding: 3, // extra spacing in pixels between the element and the spotlight
    minSpotlightRadius: 5, // 24, // the minimum radius in pixels of the spotlight
    maxSpotlightRadius: 10, // 38, // the maximum radius in pixels of the spotlight
    itemColor: 'white', // the colour of text in the command's content
    itemTextShadowColor: 'black', // the text shadow colour of the command's content
    zIndex: 9999 // the z-index of the ui div
 };

// Context menu for proteins
 var ctxt_menu_protein= {
    menuRadius: 75, // the radius of the circular menu in pixels
    selector: 'node[type="Protein"]',
    commands: [ // an array of commands to list in the menu
        {
         content: 'Show Info',
         select: function() {
             // Show Item Info Pane.
             openItemInfoPane();
             // Display Item Info.
             showItemInfo(this);
            }
        },
        {
         content: 'Delete',
         select: function() {
            cy.remove(this);
			 // Refresh network legend.
             updateCyLegend();
            }
        },
        {
         content: "Show gene",
         select: function()
            {
                addPath(this, "CODING");
            }
        },
        {
         content: "Show homologs",
         select: function()
            {
                addPath(this, "HOMOLOG");
            }
        },
        {
         content: 'Label on/ off',
         select: function() {
             if(this.style('text-opacity') === '0') {
                this.style({'text-opacity': '1'}); // show the concept/ relation Label.
               }
               else {
                this.style({'text-opacity': '0'}); // hide the concept/ relation Label.
               }
            }
        }
    ],
    fillColor: 'rgba(135, 0, 0, 0.75)', // the background colour of the menu
    activeFillColor: 'rgba(92, 194, 237, 0.75)', // the colour used to indicate the selected command
    activePadding: 2, // 20, // additional size in pixels for the active command
    indicatorSize: 15, // 24, // the size in pixels of the pointer to the active command
    separatorWidth: 3, // the empty spacing in pixels between successive commands
    spotlightPadding: 3, // extra spacing in pixels between the element and the spotlight
    minSpotlightRadius: 5, // 24, // the minimum radius in pixels of the spotlight
    maxSpotlightRadius: 10, // 38, // the maximum radius in pixels of the spotlight
    itemColor: 'white', // the colour of text in the command's content
    itemTextShadowColor: 'black', // the text shadow colour of the command's content
    zIndex: 9999 // the z-index of the ui div
 };

 // Context menu for edges
 var ctxt_menu_edge= {
    menuRadius: 75, // the radius of the circular menu in pixels
    selector: 'edge',
    commands: [ // an array of commands to list in the menu
        {
         content: 'Label on/ off',
         select: function() {
             if(this.style('text-opacity') === '0') {
                this.style({'text-opacity': '1'}); // show the concept/ relation Label.
               }
               else {
                this.style({'text-opacity': '0'}); // hide the concept/ relation Label.
               }
            }
        },
        {
         content: 'Delete',
         select: function() {
            cy.remove(this);
            }
        }
    ],
    fillColor: 'rgba(188, 249, 57, 0.75)', // the background colour of the menu
    activeFillColor: 'rgba(133, 204, 130, 0.75)', // the colour used to indicate the selected command
    activePadding: 2, // 20, // additional size in pixels for the active command
    indicatorSize: 15, // 24, // the size in pixels of the pointer to the active command
    separatorWidth: 3, // the empty spacing in pixels between successive commands
    spotlightPadding: 3, // extra spacing in pixels between the element and the spotlight
    minSpotlightRadius: 5, // 24, // the minimum radius in pixels of the spotlight
    maxSpotlightRadius: 10, // 38, // the maximum radius in pixels of the spotlight
    itemColor: 'black', // the colour of text in the command's content
    itemTextShadowColor: 'green', // the text shadow colour of the command's content
    zIndex: 9999 // the z-index of the ui div
 };


cy.cxtmenu(ctxt_menu_gene); // set Context Menu for all the core elements.
cy.cxtmenu(ctxt_menu_protein); // set Context Menu for all the core elements.
//cy.cxtmenu(ctxt_menu_edge); // set Context Menu for all the core elements.
 // Show the popup Info. dialog box.
 $('#infoDialog').click(function() {
   $('#infoDialog').slideToggle(300);
  });

}
