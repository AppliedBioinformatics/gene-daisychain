// Export graph data in csv format
// First part contains one gene description per row, last column contains ID(s) of homologs
// Next part is the same for proteins
// Function export_Table is called from saveCSV (former saveJSON) button
function export_table(){
console.log("Export table");
var cy= $('#cy').cytoscape('get'); // now we have a global reference to `cy`
// Collect all visible genes
var gene_nodes = cy.filter(function(i,ele){
            if (ele.isNode() && ele.data('type') == "Gene" && ele.visible())
            {return true;}
            else {return false;}
            });
// Collect all visible proteins
var protein_nodes = cy.filter(function(i,ele){
            if (ele.isNode() && ele.data('type') == "Protein" && ele.visible())
            {return true;}
            else {return false;}
            });
// Collect all visible homolog edges
var homolog_edges = cy.filter(function(i,ele){
            if (ele.isEdge() &&  ele.data('type') == "HOMOLOG" && ele.visible())
            {return true;}
            else {return false;}
            });
// Extract gene node data from gene nodes
// Dict-like format of object: "id":["id","name","assembly","contig","start","stop","annotation"]
var gene_nodes_data = {};
for (i = 0; i < gene_nodes.length; ++i){
gene_nodes_data[gene_nodes[i].data("id")]=[gene_nodes[i].data("id"), gene_nodes[i].data("name"),
gene_nodes[i].data("species"),gene_nodes[i].data("contig"),gene_nodes[i].data("start"),
gene_nodes[i].data("stop"), gene_nodes[i].data("description")];
};
console.log(gene_nodes_data);
// Extract protein node data from protein nodes
// Dict-like format of object: "id":["id","name","assembly"]
var protein_nodes_data = {};
for (i = 0; i < protein_nodes.length; ++i){
protein_nodes_data[protein_nodes[i].data("id")]=[protein_nodes[i].data("id"),protein_nodes[i].data("name"),
protein_nodes[i].data("species")]
};
// Create another dict-like structure storing for each gene or protein ID all homologs (as ID and percentage match)
var hmlg_dict = {};
// Scan through all HOMOLOG edges, for each source add the target node to its list of homolog nodes
for (i = 0; i < homolog_edges.length; ++i){
source_id = homolog_edges[i].data("source");
target_id = homolog_edges[i].data("target");
perc_match = homolog_edges[i].data("perc_match")+"%";
if ("undefined" == typeof source_id || "undefined" == typeof target_id){continue;};
// Distinguish between gene and protein nodes via the first letter of the ID (g or p)
if (source_id.startsWith("g"))
{
var source = gene_nodes_data[source_id][0];
var target = gene_nodes_data[target_id][0];
}
else
{
var source = protein_nodes_data[source_id][0];
var target = protein_nodes_data[target_id][0];
};
// Add this edge to hmlg_dict:
// Source-ID gets target-ID + perc-match as new homolog
// Then target-ID gets source-ID + perc-match as new homolog
// That is because homolog relations are displayed by only one edge although they
// are in principal bidirectional (cytoscape.js does not support bidirectional edges, yet)
if(source in hmlg_dict)
{
// If source is already in hmlg_dict, add target_id to the array list
hmlg_dict[source].push(target+":"+perc_match);
}
else
{
// If source is not in hmlg_dict, create a  new entry with a new array containing target-id
hmlg_dict[source] = [target+":"+perc_match];
};
if(target in hmlg_dict)
{
// If target is already in hmlg_dict, add source_id to the array list
hmlg_dict[target].push(source+":"+perc_match);
}
else
{
// If target is not in hmlg_dict, create a  new entry with a new array containing source-id
hmlg_dict[target] = [source+":"+perc_match];
};
};
// Start to build the CSV file
// Start with genes and their homologs
// Header for genes
csv_file = "";
csv_file += "### Gene data ###\n"
csv_file += ["id","name","assembly","contig","start","stop","annotation","homologs"].join(",")+"\n";
// Convert each gene_nodes_data into a row
// First, convert the gene_node_data object into an array
gene_nodes_data = $.map(gene_nodes_data, function(val, key){return [val]});
// Sort array by gene id
gene_nodes_data.sort(function(a,b){return parseInt(a[0].substr(1))-parseInt(b[0].substr(1))});
// Add node data to csv_file_string
for (i = 0; i < gene_nodes_data.length; ++i)
{
// If there are no homologs, hmlg_dict[id] is undefined
// State "None" in csv output if no homologs
hmlg_nodes = hmlg_dict[gene_nodes_data[i][0]];
if (typeof(hmlg_nodes) == "undefined"){hmlg_nodes="None"};
csv_file += gene_nodes_data[i].join(",")+","+hmlg_nodes+"\n";
};
// Next add genes and their homologs
// Header for genes
csv_file += "### Protein data ###\n"
csv_file += ["id","name","assembly","homologs"].join(",")+"\n";
// Convert each protein_nodes_data into a row
// First, convert the protein_nodes_data object into an array
protein_nodes_data = $.map(protein_nodes_data, function(val, key){return [val]});
// Sort array by protein id
protein_nodes_data.sort(function(a,b){return parseInt(a[0].substr(1))-parseInt(b[0].substr(1))});
for (i = 0; i < protein_nodes_data.length; ++i)
{
// If there are no homologs, hmlg_dict[id] is undefined
// State "None" in csv output if no homologs
hmlg_nodes = hmlg_dict[protein_nodes_data[i][0]];
if (typeof(hmlg_nodes) == "undefined"){hmlg_nodes="None"};
csv_file += protein_nodes_data[i].join(",")+","+hmlg_nodes+"\n";
};
// Open csv string as file
window.open("data:text/csv;charset=utf-8,"+escape(csv_file));
}

