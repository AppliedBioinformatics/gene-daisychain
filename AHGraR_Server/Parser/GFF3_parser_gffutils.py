# GFF3-parser based on gffutils
# Input: GFF3 file, initial gene and protein id
# Output: Two lists
# 1. List describing gene nodes:
# [(gene_id, species_name, contig_name, start_index, stop_index, gene_name, chromosome, strand_orientation, coding_frame),...]
# 2. List describing protein nodes with a reference to coding gene id
# [(protein_id, protein_name, protein_description, gene_id),...]
# 3. Dict matching protein names to gene-ID and protein description
# dict[prot_name]=(protein_id, protein_desc, gene_id)
# Some annotation is mandatory, i.e. GFF3 file has to contain these fields, others are optional:
# Mandatory: Gene-name, Protein-name, contig-name, start-index, stop-index
# Optional: Protein-description, chromosome-name, strand-orientation, coding frame
import gffutils
import os


class GFF3Parser:

    def __init__(self, gff3_file_path, gene_node_id, protein_node_id):
        self.gff3_file_path = gff3_file_path
        # Organism/species name
        self.species_name = os.path.splitext(os.path.basename(gff3_file_path))[0]
        # Each protein and gene node gets an unique id
        self.gene_node_id = int(gene_node_id)
        self.protein_node_id = int(protein_node_id)
        # Gene annotations are stored in a list
        self.gene_list = []
        # Protein annotations and their reference to a gene node are stored in a list
        self.protein_list = []
        # Annotation mapper: Describes where each annotation field is found in the GFF3
        # Annotation fields are: Gene name, contig, start, stop, strand, phase, protein name, protein description
        # Annotation is either stored in columns 1-8 or in attribute column 9
        # To retrieve information from column 1-8, column index (starting at 1) needs to be specified
        # For retrieval from column 9 the key has to be specified
        # In addition, the feature name (e.g. Gene, mRNA etc.) needs to be specified
        # Example:
        # Gene::(Start:4),(Stop:5),(Contig:1),(Gene_name:Name),(Phase:8),(Strand:7);mRNA::(Protein_name:Name),(Protein_desc:Product)
        self.annotation_mapper = {}
        # GFF3-files contain a hierarchical structure, the ordering of the features looked at needs to be provided as well:
        # Example:
        # Gene,mRNA
        self.feature_hierarchy = []
        # Some features may not fit in the hierarchical structure, they are accessed separately
        self.non_hierarchic_features = []
        # gffutils parses GFF3-file into a dict-like structure
        self.gff3_db = []

    # Retrieve annotation data from columns 1-9 of a GFF3-file
    # 1-8 are found by their index, 9 by attribute key
    # col. index 0 means that this annotation field will not be used
    # (only possible for phase,strand,protein_desc)
    def column_index_2_field(self, feature, col_index):
        if col_index.isdigit():
            col_index = int(col_index)
            if col_index == 1: return (feature.seqid)
            if col_index == 2: return (feature.source)
            if col_index == 3: return (feature.featuretype)
            if col_index == 4: return (feature.start)
            if col_index == 5: return (feature.end)
            if col_index == 6: return (feature.score)
            if col_index == 7: return (feature.strand)
            if col_index == 8: return (feature.frame)
            else: return ("")
        else:
            return (feature[col_index][0])




    # Set annotation mapper
    # Mandatory fields: Start,Stop,Contig,Gene_name,Protein_name
    # Optional fields: Chromosome,Strand,Phase,Protein_desc
    # Input: String, example:
    # gene::(Start:4),(Stop:5),(Contig:1),(Gene_name:Name),(Phase:8),(Strand:7);CDS::(Protein_name:Name),(Protein_desc:product)
    def set_annotation_mapper(self, anno_map):
        # 0. Ensure that annotation mapping string has the right format
        # Ensure that there are no whitespaces in anno_map
        anno_map = "".join(anno_map.split(" "))
        # Check if annotation mapping contains all mandatory annotation fields:
        if "(Start:" not in anno_map: return(False)
        if "(Stop:" not in anno_map: return (False)
        if "(Contig:" not in anno_map: return (False)
        if "(Gene_name:" not in anno_map: return (False)
        if "(Protein_name:" not in anno_map: return (False)
        try:
            # 1. Separate by features
            anno_map = anno_map.strip().split(";")
            # 2. Split annotation mappings
            for feature_map in anno_map:
                feature_name = feature_map.split("::")[0]
                feature_fields = feature_map.split("::")[1].split(",")
                self.annotation_mapper[feature_name]=feature_fields
        except (IndexError, KeyError):
            return (False)
        return (True)

    # Set hierarchy of GFF3 features.
    # Input string, i.e. "Gene,CDS;region"
    # Can also be used to check the validity of the hierarchy definition
    # Returns True if feature hierarchy string is within the formal definitions
    def set_feature_hierarchy(self, features):
        # 0. Remove any whitespaces
        features = "".join(features.split(" "))
        try:
            # 1. Separate hierarchical features from non-hierarchical features
            self.feature_hierarchy = features.split(";")[0].split(",")
            # See if there are also non hierarchical features
            # If not, self.non_hierarchic_features points to empty list
            try:
                self.non_hierarchic_features = features.split(";")[1].split(",")
            except IndexError:
                self.non_hierarchic_features = []
        except IndexError:
            return (False)
        # Test if a feature hierarchy was defined
        if self.feature_hierarchy != ['']:
            return (True)
        else:
            return (False)


    def traverse_gff3(self, parent_node, level, anno_dict):
        # Check if lowest hierarchical level is reached:
        if level < len(self.feature_hierarchy)-1:
            # If not, travel through child nodes first
            for child_node in self.gff3_db.children(parent_node, featuretype=self.feature_hierarchy[level+1]):
                self.traverse_gff3(child_node, level+1, anno_dict)
        for attribute in self.annotation_mapper[self.feature_hierarchy[level]]:
            try:
                attribute = attribute[1:-1].split(":")
                if not attribute[0] in anno_dict.keys():
                    anno_dict[attribute[0]] = []
                anno_dict[attribute[0]].append(self.column_index_2_field(parent_node, attribute[1]))
            except (KeyError, IndexError):
                continue


    def parse_gff3_file(self):
        gffutils.create_db(self.gff3_file_path, "gff3utils.db", merge_strategy="create_unique", force=True)
        self.gff3_db = gffutils.FeatureDB('gff3utils.db', keep_order=False)
        # Collect all gene annotations in a list
        gene_annotation_list = []
        # Traverse through GFF3-file, starting with the highest-rank feature
        # For each highest-rank feature, collect all annotation fields in a dict
        gene_annotation = {}
        # 1. Enter database at the highest ranked hierarchical feature (most likely gene or something similar)
        for upper_level_feature in self.gff3_db.all_features(featuretype=self.feature_hierarchy[0]):
            # 2. Store all annotations for this particular gene in a dict
            gene_annotation = {}
            # 3. Travel down the defined feature-tree, depth-first-search
            self.traverse_gff3(upper_level_feature, 0, gene_annotation)
            # 4. Collection annotation data for this gene in list
            gene_annotation_list.append(gene_annotation)
        # 5. Scan all non-hierarchical features, add attributes to annotation in gene_annotation_list
        # based in start/stop indices and contig-id
        for feature_type in self.non_hierarchic_features:
            for feature in self.gff3_db.all_features(featuretype=feature_type):
                try:
                    for attribute in self.annotation_mapper[feature_type]:
                        attribute = attribute[1:-1].split(":")
                        attribute_value = self.column_index_2_field(feature, attribute[1])
                        attribute_start = feature.start
                        attribute_stop = feature.stop
                        attribute_seq = feature.seqid
                        # Add attribute to genes in gene_annotation list
                        # Attribute can either be parent to gene feature (i.e. indices surround gene feature)
                        # or attribute is a child to gene feature (i.e. gene feature indices surround attribute)
                        for gene_annotation_dict in gene_annotation_list:
                            if gene_annotation_dict["Contig"][0] == attribute_seq and\
                                    ((attribute_start <= gene_annotation_dict["Start"][0] and gene_annotation_dict["Stop"][0] <= attribute_stop) or \
                                    (attribute_start >= gene_annotation_dict["Start"][0] and gene_annotation_dict["Stop"][
                                        0] >= attribute_stop)):
                                if not attribute[0] in gene_annotation_dict.keys():
                                    gene_annotation_dict[attribute[0]] = []
                                gene_annotation_dict[attribute[0]].append(attribute_value)
                except (KeyError, IndexError):
                        continue

        # 6.Convert annotation_dicts into lists.
        #  Final format:
        # [(Gene_id, Species,Contig,Start_index,End_index, Strand_orientation, Chromosome, Gene_name),...]
        # [(Protein_name, Protein_desc, Gene_id),...]
        #  Most features should/are supposed to have only one value,
        # e.g. a gene has only one start index, one chromosome etc. A gene can however code for multiple proteins (e.g. isoforms).
        print(gene_annotation_dict)
        for gene_annotation_dict in gene_annotation_list:
            try:
                self.gene_node_id +=1
                # Retrieve the mandatory fields from the gene_annotation dict:
                # Contig name, start+stop indices, Gene name
                gene_node =[gene_annotation_dict[key][0] for key in ["Contig","Start","Stop", "Gene_name"]]
                # Add unique gene_node_id
                gene_node.insert(0, self.gene_node_id)
                # Add species name derived from GFF3 filename
                gene_node.insert(1, self.species_name)
                # Add non-mandatory fields
                gene_node.append(gene_annotation_dict.get("Chromosome", "?")[0])
                gene_node.append(gene_annotation_dict.get("Strand", "?")[0])
                gene_node.append(gene_annotation_dict.get("Phase", "?")[0])
                # Add this gene node annotation to overall list of gene nodes
                self.gene_list.append(tuple(gene_node))
                # Create protein node annotation
                # Each gene node can be associated with multiple proteins
                protein_names = gene_annotation_dict["Protein_name"]
                try:
                    protein_descriptions = gene_annotation_dict["Protein_desc"]
                except KeyError:
                    protein_descriptions = len(protein_names)*["?"]
                # Zip a protein description to each protein name
                protein_nodes = list(set((zip(protein_names, protein_descriptions))))
                # Create protein node annotations for one specific gene node id
                for protein_node in protein_nodes:
                    self.protein_node_id+=1
                    protein_node = (self.protein_node_id, protein_node[0],protein_node[1], self.gene_node_id)
                    self.protein_list.append(protein_node)
            # In case annotation data for one gene node could not be retrieved, continue with the next annotation data set
            except (KeyError, IndexError):
                continue
        # Ensure that gene and protein list contain only unique entries
        self.gene_list = list(set(self.gene_list))
        self.protein_list = list(set(self.protein_list))
        # Sort the gene_list by contig, start and stop. Only one species per file, so no need to sort by species
        self.gene_list = sorted(self.gene_list, key=lambda x: (x[2], x[3], x[4]))
        # Sort the protein_list by protein_id
        self.protein_list = sorted(self.protein_list, key=lambda x: x[0])
        # Clean up: Remove the temporary database created by gffutils
        os.remove("gff3utils.db")

    # Retrieve the sorted gene list
    def get_gene_list(self):
        return (self.gene_list)

    # Retrieve the protein list
    def get_protein_list(self):
        return (self.protein_list)

    # Retrieve protein nodes as dict
    # dict[prot_name] = (protein_id, protein_desc, gene_id)
    def get_protein_dict(self):
        protein_dict = {}
        for protein in self.protein_list:
            protein_dict[protein[1]]=(protein[0],protein[2],protein[3])
        return (protein_dict)

    # Retrieve current gene_node id
    def get_gene_node_id(self):
        return (self.gene_node_id)

    # Retrieve current protein_node id
    def get_protein_node_id(self):
        return (self.protein_node_id)
