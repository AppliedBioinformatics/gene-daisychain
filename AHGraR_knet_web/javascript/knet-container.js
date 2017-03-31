function load_reload_Network(network_json, network_style/*, runNetLayout*/) {

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
/** Add a Qtip message to all the nodes & edges using QTip displaying their Concept Type & value when a
 * node/ edge is clicked.
 * Note: Specify 'node' or 'edge' to bind an event to a specific type of element.
 * e.g, cy.elements('node').qtip({ }); or cy.elements('edge').qtip({ }); */
cy.elements().qtip({
  content: function() {
      var qtipMsg= "";
     try {
      if(this.isNode()) {
          if(this.data('type')=="Gene")
          {
         qtipMsg= "<b>Name:</b> "+ this.data('name') + "\n" +", <b>Type:</b> "+ this.data('type') + "\n"
         +", <b>Species:</b> "+ this.data('species')+ "\n"
         +", <b>Contig:</b> "+ this.data('contig');
        }
         else
         {
             qtipMsg= "<b>Name:</b> "+ this.data('name') +", <b>Type:</b> "+ this.data('type')
                    +", <b>Species:</b> "+ this.data('species')
          +", <b>Contig:</b> "+ this.data('contig');
        }
        }
      else if(this.isEdge()) {
              if(this.data('type')=="HOMOLOG")
              {
              qtipMsg= "<b>Identity:</b> "+ this.data('perc_match')+"%";
              }
             }
      }
      catch(err) { qtipMsg= "Selected element is neither a Concept nor a Relation"; }
      return qtipMsg;
     },
  style: {
    classes: 'qtip-bootstrap',
    tip: {
      width: 12,
      height: 6
    }
  }
});

 /** Popup (context) menu: a circular Context Menu for each Node (concept) & Edge (relation) using the 'cxtmenu' jQuery plugin. */
 var contextMenu= {
    menuRadius: 75, // the radius of the circular menu in pixels

    // Use selector: '*' to set this circular Context Menu on all the elements of the core.
    /** Note: Specify selector: 'node' or 'edge' to restrict the context menu to a specific type of element. e.g, 
     * selector: 'node', // to have context menu only for nodes.
     * selector: 'edge', // to have context menu only for edges. */
    selector: 'node',
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
             //this.hide(); // hide the selected 'node' or 'edge' element.
             console.log(this);
            cy.remove(this);
			 // Refresh network legend.
             updateCyLegend();
            }
        },
        {
         content: "Show 5'/3''",
         select: function()
            {
                addPath(this, "53NB");
            }
        },
        {
         content: "Show CODING",
         select: function()
            {
                addPath(this, "CODING");
            } 
        },
        {
         content: "Show HOMOLOG",
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
    fillColor: 'rgba(0, 0, 0, 0.75)', // the background colour of the menu
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

cy.cxtmenu(contextMenu); // set Context Menu for all the core elements.

 // Show the popup Info. dialog box.
 $('#infoDialog').click(function() {
   $('#infoDialog').slideToggle(300);
  });

}
