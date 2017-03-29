// Load list of available projects
         function LoadProjectList()
         {
            // Open websocket to retrieve list of projects
            var wsconn = new WebSocket("ws://146.118.99.190:7687/");
            // Request project list
            wsconn.onopen = function () {wsconn.send("PMINFO");};
            // Receive and process project list
            wsconn.onmessage = function (evt){SetProjectList(evt.data);};
         };
         // Fill select menu with available projects
         // Data comes from "PMINFO" command
         function SetProjectList(received_msg)
         {
            // Find select menu
            select_menu = document.getElementById("select_proj");
            // Each line of data contains one project
            // Each line has project name, project ID and project status
            // Only showing project name, the ID is the value internal associated with the selection
            project_items = received_msg.split("\n");
            // Iterate through project data
            for(var i = 0; i < project_items.length; i++)
            {
                 project_item = project_items[i].split("\t");
                 // Only list set-up and running projects
                 if (project_item[2] != "DB_RUNNING")
                 {continue;};
                 // Create a new select option
                 option = document.createElement("option");
                 // Fill select option with data:
                 option.innerHTML = project_item[0];
                 option.value = project_item[1];
                 // Add new option as child to select menu
                 select_menu.appendChild(option);
             };
             // Update global project ID variable
             changeProjectID();
         };
         // Update the global project ID in response to either
         // changing the value in the project select menu
         // or on initial loading of the page
         function changeProjectID()
         {
            // Find select menu and retrieve currently selected project
            var select_menu = document.getElementById("select_proj");
            // Change global variable
            project_id = select_menu.options[select_menu.selectedIndex].value;
            console.log("New PI: "+project_id);
            // Load project-specific list of species
            LoadSpeciesList();
            update_color_legend();
         };
         // Load list of species for this project
         function LoadSpeciesList()
         {
            // Open websocket to retrieve list of projects
            var wsconn = new WebSocket("ws://146.118.99.190:7687/");
            // Request species list
            wsconn.onopen = function () {wsconn.send("PAQURY_LIST_"+project_id+"_SPECIES");};
            // Receive and process project list
            wsconn.onmessage = function (evt){
                console.log("Recv species msg");
                SetSpeciesList(evt.data);
                };
         };
         // Load list of chromosomes for current species (global variable)
         function LoadChromosomeList()
         {
            // Open websocket to retrieve list of projects
            var wsconn = new WebSocket("ws://146.118.99.190:7687/");
            // Request chromosome list, replace underscores in species name with tabs
            wsconn.onopen = function () {wsconn.send("PAQURY_LIST_"+project_id+"_CONTIG_"+species.split("_").join("\t"));};
            // Receive and process project list
            wsconn.onmessage = function (evt){
                console.log("Recv chromosome msg");
                SetChromosomeList(evt.data);
                };
         };
         // Fill species select menu with available species
         // Data comes from websocket "SL" command
         function SetSpeciesList(received_msg)
         {
            console.log("SetSpeciesList");
            // Find select menu
            select_species_menu = document.getElementById("select_species");
            // Each line of data contains one species
            species_items = received_msg.split("\n");
            // Send species items list to color legend
            update_color_legend(species_items);
            // Delete old options
            while (select_species_menu.length > 0)
            {
            select_species_menu.remove(select_species_menu.length-1);
            }
            // Add default option: All species
            option = document.createElement("option");
            // Fill select option with data:
            option.innerHTML = "All assemblies";
            option.value = "*";
            // Add new option to select menu
            select_species_menu.add(option);
            // Iterate through project data
            for(var i = 0; i < species_items.length; i++)
            {
                 // Create a new select option
                 option = document.createElement("option");
                 // Fill select option with data:
                 option.innerHTML = species_items[i];
                 option.value = species_items[i];
                 // Add new option to select menu
                 select_species_menu.add(option);
             };
             // Call function changeSpecies() to update chromosome list
             changeSpecies();
         };
         // React to a change in species selection
         function changeSpecies()
         {
            // Find select menu and retrieve currently selected project
            var select_spec_menu = document.getElementById("select_species");
            // Change global variable
            species = select_spec_menu.options[select_spec_menu.selectedIndex].value;
            console.log("New Species selection: "+species);
            // Load species-specific list of chromosomes
            LoadChromosomeList();
         };
         // Fill species select menu with available species
         // Data comes from websocket "SL" command
         function SetChromosomeList(received_msg)
         {
            console.log("SetChromosomeList");
            // Find select menu
            select_chrom_menu = document.getElementById("select_chromosome");
            // Each line of data contains one chromosome
            chromosome_items = received_msg.split("\n");
            // Delete old options
            while (select_chrom_menu.length > 0)
            {
            select_chrom_menu.remove(select_chrom_menu.length-1);
            }
            // Add default option: All chromosomes
            option = document.createElement("option");
            // Fill select option with data:
            option.innerHTML = "All contigs";
            option.value = "*";
            // Add new option to select menu
            select_chrom_menu.add(option);
            // Iterate through contig data
            for(var i = 0; i < chromosome_items.length; i++)
            {
                 // Create a new select option
                 option = document.createElement("option");
                 // Fill select option with data:
                 option.innerHTML = chromosome_items[i];
                 option.value = chromosome_items[i];
                 // Add new option to select menu
                 select_chrom_menu.add(option);
             };
         };
         // Search for genes/proteins in the project database
         // Collects current settings in select menus and text field
         function searchKeyword()
         {
            search_button = $('#search_kwd_btm')
            // Deactivate search button until results are retrieved
            search_button.disabled = true;
            // Project ID and species selection are global variables,
            // retrieve chromosome selection and keyword
            var select_chrom_menu = document.getElementById("select_chromosome");
            var chromosome = select_chrom_menu.options[select_chrom_menu.selectedIndex].value;
            var keyword = document.getElementById("keyword").value;
            if(document.getElementById("radio_all").checked)
            {
            var type = "ALL";
            }
            else
            {
            var type = "ANY";
            };
            // Open websocket to send query to server
            var wsconn = new WebSocket("ws://146.118.99.190:7687/");
            // Replace underscores in queries with tabs
            wsconn.onopen = function () {wsconn.send("PAQURY_SEAR_"+project_id+"_WEB_"+species.split("_").join("\t")+"_"+
            chromosome.split("_").join("\t")+"_"+keyword.split("_").join("\t")+"_"+type);
            search_button.innerHTML = "Searching"};
            set_color_legend();
             // Receive and process query result
            wsconn.onmessage = function (evt){
                search_button.innerHTML = "Receiving data";
                $('#knet-maps-row').collapse("hide");
                $('#result-picker').collapse("show");
                search_result = JSON.parse(evt.data);
                showSearchResult();
                //graphJSON = JSON.parse(evt.data);
                //console.log(graphJSON);
            //initializeNetworkView();
            //search_button.innerHTML = "Building graph";
            //updateCyLegend();
            //changeSensitivity();
            //search_button.innerHTML = "Search!"
            //search_button.disabled = false;
                };
         };


         // Load search result into jstree
         function showSearchResult()
         {
         // Remove old instance of jstree
         $('#jstree_div').jstree("destroy").empty();
         // jsTree accepts node data in JSON format
         // Initialize an empty container for node data
         var jsdata = {'core': {'data': []}};
         // Retrieve node data from search results (edges are not filtered)
         node_data = search_result["nodes"];
         // Collect assembly ids and contig ids in a separate array
         // Make ids unique, they serve as parent nodes to gene nodes
         // Assembly->Contig-> Gene
         assembly_ids = [];
         contig_ids = []
         // Loop through found gene nodes
         for (var i = 0, len = node_data.length; i < len; i++){
         // Collect assembly and contig ids
         // contig id is stored as assembly_name$$$contig_name
         // to allow for similar contig names in different assemblies
         assembly_ids.push(node_data[i]['data']['species']);
         contig_ids.push(node_data[i]['data']['species']+"$$$"+node_data[i]['data']['contig']);
         console.log(node_data[i]);
         //jsdata['core']['data'].push({'id': node_data[i]['data']['species']+"$$$"+node_data[i]['data']['contig'], "parent":assembly_name, "text": contig_name});
         };

         assembly_ids = assembly_ids.filter( function(value,index,self){return self.indexOf(value) === index;} );
         contig_ids = contig_ids.filter( function(value,index,self){return self.indexOf(value) === index;} );

         for (var i = 0, len = assembly_ids.length; i < len; i++){
            jsdata['core']['data'].push({'id': assembly_ids[i], "parent":"#", "text": assembly_ids[i]});
         };
         for (var i = 0, len = contig_ids.length; i < len; i++){
            var contig_id = contig_ids[i].split("$$$");
            var assembly_name = contig_id[0];
            var contig_name = contig_id[1];
            jsdata['core']['data'].push({'id': contig_ids[i], "parent":assembly_name, "text": contig_name});
         };
         //jsdata['core']['data']={};
         $('#jstree_div').jstree(jsdata);
         }
         // Render json node/edge data into a visual representation
         function renderJSON()
         {
         // Set global graphJSON variable to new json_data
         graphJSON = search_result;
         console.log(graphJSON);
         initializeNetworkView();
         search_button = $('#search_kwd_btm')
         search_button.innerHTML = "Building graph";
         updateCyLegend();
         changeSensitivity();
         search_button.innerHTML = "Search!"
         search_button.disabled = false;
         $('#result-picker').collapse("hide");
         $('#knet-maps-row').collapse("show");
         }
