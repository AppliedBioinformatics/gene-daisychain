# GFF3-parser based on gffutils
# Extracts gene transcript information from a GFF3 file
# In addition to the GFF3 annotation the genomic sequence or the transcript sequences are needed
# to retrieve the transcript sequences,
# Some information is required to correctly parse the GFF3 file:
# Is the sequence format genome or transcripts?
# How is the transcript feature called (e.g. Gene or mRNA)
# Which subfeatures of the transcript should be included (e.g. CDS, UTR, exons)
# Returns a list of gene annotations in this format:
#(gene_id, species_name, contig_name, start_index, stop_index, strand_orientation, gene_name, gene_description)
import gffutils
import os
from pyfaidx import Fasta

class GFF3Parser_v2:
    # Path to GFF3
    # Next gene node ID
    # Name of transcript feature (e.g. gene or mRNA)
    # Names of transcript subfeatures to include (list), e.g. [CDS,UTR]
    # Feature containing "Name" attribute plus name of attribute. e.g. gene:name
    # Feature containing "Description" attribute plus name of attribute e.g. CDS:product
    # Both attributes are NOT mandatory. If name attribute is not set, the transcript ID will be used as name
    # If description is missing, this attribute will not be included in the database
    def __init__(self, gff3_file_path, sequence_file_path, seq_is_genome, gene_node_id, parent_feature_type,subfeatures, name_attribute, descr_attribute):
        # Path to GFF3 file
        self.gff3_file_path = gff3_file_path
        # Parse sequence file
        self.sequence = Fasta(sequence_file_path)
        # Is sequence the genome (true) or already spliced transcripts (false)
        self.seq_is_genome = seq_is_genome
        # Organism/species name
        self.species_name = os.path.splitext(os.path.basename(gff3_file_path))[0]
        # Each gene node gets an unique id
        self.gene_node_id = int(gene_node_id)
        # Gene annotations are stored in a list
        self.gene_list = []
        # Set the name of the uppermost gene/transcript feature type (e.g. gene or mRNA)
        self.parent_feature_type = parent_feature_type
        # Set the list of all subfeatures of parent_feature that can be included in the final transcript
        self.subfeatures = subfeatures
        # Convert attribute location into a tuple
        self.name_attribute = [item.strip() for item in name_attribute.split(":")]
        self.descr_attribute = [item.strip() for item in descr_attribute.split(":")]

    def reverse_complement(self, sequence):
        # First ensure that all letters are uppercase
        sequence = sequence.upper()
        rev_complement = {"A": "T", "T": "A", "C": "G", "G": "C"}
        sequence = "".join([rev_complement[nt] for nt in sequence])[::-1]
        return sequence

    def parse_gff3_file(self):
        output = open("transcripts.fa", "w")
        gffutils.create_db(self.gff3_file_path, "gff3utils.db", merge_strategy="create_unique", force=True)
        gff3_db = gffutils.FeatureDB('gff3utils.db', keep_order=False)
        # Collect all gene annotations in a list
        gene_annotation_list = []
        # Iterate through all transcripts (identified by parent_feature_type)
        for transcript in gff3_db.iter_by_parent_childs(self.parent_feature_type):
            # Increase gene node ID by one
            self.gene_node_id += 1
            # Extract all "standard" attributes for this transcript:
            # name and description may be changed by name_attribute and descr_attribute
            gene_annotation = [self.gene_node_id, self.species_name, transcript[0].seqid, transcript[0].start, transcript[0].stop, transcript[0].strand, transcript[0].id, ""]
            if self.name_attribute[0] == self.parent_feature_type:
                gene_annotation[6]=transcript[0][self.name_attribute[1]][0]
            if self.descr_attribute[0] == self.parent_feature_type:
                gene_annotation[7]=transcript[0][self.descr_attribute[1]][0]
            gene_sequence = []
            # Iterate through all subfeatures of this transcript
            # Two tasks are performed here: Look for name or descr attributes
            # Build the sequence of this transcript
            for subfeature in transcript[1:]:
                # Check if feature type is in the list of selected subfeatures
                if subfeature.featuretype in self.subfeatures:
                    # Check if name or description attribute can be found in this subfeature
                    if self.name_attribute[0] == subfeature.featuretype:
                        try:
                            gene_annotation[6] = subfeature[self.name_attribute[1]][0]
                        except KeyError:
                            pass
                    if self.descr_attribute[0] == subfeature.featuretype:
                        try:
                            gene_annotation[7] = subfeature[self.descr_attribute[1]][0]
                        except KeyError:
                            pass
                    # Collect sequence of this subfeature if nucleotide sequence is the genome
                    # Important: Current version of GFFutils has a bug preventing the automatic reverse-complement
                    # of minus-strand features
                    # Strandedness is evaluated manually here
                    if self.seq_is_genome:
                        antisense = subfeature.strand == "-"
                        # If antisense, reverse complement the sequence
                        seq_fragment = subfeature.sequence(self.sequence, False).seq if not antisense else self.reverse_complement(subfeature.sequence(self.sequence, False).seq)
                        # Include the phase:
                        phase = int(subfeature.frame) if subfeature.frame.isdigit() else 0
                        start_index = int(subfeature.start) if not antisense else int(subfeature.start)*(-1)
                        gene_sequence.append((start_index, seq_fragment[phase:]))
            # Join all sequence fragments together
            # First, sort by start_index
            gene_sequence = sorted(gene_sequence, key=lambda x: x[0])
            gene_sequence = "".join([item[1] for item in gene_sequence])
            if not gene_sequence:
                continue
            output.write(">"+str(gene_annotation[0])+"_"+gene_annotation[6]+"\n")
            output.write(gene_sequence+"\n")
        output.close()






