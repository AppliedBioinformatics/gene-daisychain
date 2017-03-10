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
from Bio.Seq import Seq
from Bio.Alphabet import IUPAC

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
        # Extract species name from file name
        self.species_name = os.path.splitext(os.path.basename(gff3_file_path))[0]
        self.sequence_file_path = sequence_file_path
        # Parse sequence file
        if seq_is_genome:
            self.sequence = Fasta(sequence_file_path)
        else:
            self.sequence = None
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
        # Input format: subfeat1,subfeat2,subfeat3
        self.subfeatures = subfeatures.split(",")
        # Attribute location is converted from feat:attr to a tuple
        self.name_attribute = name_attribute.split(":")
        self.descr_attribute = descr_attribute.split(":")
        # Load GFF3 file
        gffutils.create_db(self.gff3_file_path, "gff3utils.db", merge_strategy="create_unique", force=True)
        self.gff3_db = gffutils.FeatureDB('gff3utils.db', keep_order=False)

    # Reverse complement a nucleotide sequence
    def reverse_complement(self, sequence):
        rev_complement = {"A": "T", "T": "A", "C": "G", "G": "C"}
        try:
            sequence = "".join([rev_complement[nt] for nt in sequence])[::-1]
        # If non-nucleotide letters are found: return empty string
        except KeyError:
            sequence = ""
        return sequence

    # Translate a nucleotide sequence into protein sequence
    def translate_nt(self, nt_sequence):
        # Coding sequence should be in frame
        # If nucleotide sequence does not start with ATG, continuously remove 3 letters until sequence starts with ATG
        while nt_sequence:
            if nt_sequence[:3] == "ATG": break
            else:
                if len(nt_sequence) < 3: return ""
                else:
                    nt_sequence = nt_sequence[3:]
        # Biopython demands coding sequence lengths to be a multiple of three
        # Add trailing N to those sequences that fail this requirement
        while len(nt_sequence)%3 != 0:
            nt_sequence += "N"
        coding_seq = Seq(nt_sequence, IUPAC.ambiguous_dna)
        return str(coding_seq.translate(to_stop=True))


    def parse_gff3_file(self):
        print("Features as they arive")
        print(self.parent_feature_type)
        print(self.subfeatures)
        print(self.name_attribute)
        print(self.descr_attribute)
        output_nt = open(self.gff3_file_path+"_transcripts.fa", "w")
        output_prot = open(self.gff3_file_path+"_translations.fa", "w")
        gff3_db = self.gff3_db
        # Collect all gene annotations in a list
        gene_annotation_list = []
        # Iterate through all transcripts (identified by parent_feature_type)
        for transcript in gff3_db.iter_by_parent_childs(self.parent_feature_type):
            # Increase gene node ID by one
            self.gene_node_id += 1
            # Extract all "standard" attributes for this transcript:
            # name and description may be changed by name_attribute and descr_attribute
            gene_annotation = [self.gene_node_id, self.species_name, transcript[0].seqid, transcript[0].start,
                               transcript[0].stop, transcript[0].strand, transcript[0].id, ""]
            if self.name_attribute[0] == self.parent_feature_type:
                try:
                    gene_annotation[6]=transcript[0][self.name_attribute[1]][0]
                except KeyError:
                    gene_annotation[6] = "?"
                    print("KeyError for "+gene_annotation)
            if self.descr_attribute[0] == self.parent_feature_type:
                try:
                    gene_annotation[7]=transcript[0][self.descr_attribute[1]][0]
                except KeyError:
                    gene_annotation[7]= "?"
                    print("KeyError for " + gene_annotation)
            # Collect gene annotation in list
            gene_annotation_list.append(gene_annotation)
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
                    # Strandedness is therefore evaluated manually here
                    if self.seq_is_genome:
                        # Is sequence from a minus-strand feature?
                        antisense = subfeature.strand == "-"
                        # If antisense, reverse complement the sequence
                        seq_fragment = subfeature.sequence(self.sequence, False).seq.upper() if not antisense \
                            else self.reverse_complement(subfeature.sequence(self.sequence, False).seq.upper())
                        # Include the coding phase, phase is zero if phase field is empty:
                        phase = int(subfeature.frame) if subfeature.frame.isdigit() else 0
                        # If a gene consists of multiple segments they need to be sorted by their start index
                        # For antisense strand features the negative of the start index is used
                        start_index = int(subfeature.start) if not antisense else int(subfeature.start)*(-1)
                        # Store each gene sequence fragment in a tuple together with its start index
                        gene_sequence.append((start_index, seq_fragment[phase:]))
            # Join all sequence fragments together
            # First, sort by start_index
            gene_sequence = sorted(gene_sequence, key=lambda x: x[0])
            # Now join fragments into a single string
            gene_sequence = "".join([item[1] for item in gene_sequence])
            # Write sequence to file, except when no sequence could be retrieved
            if not gene_sequence:
                continue
            # The fasta annotation line is  '>lcl|' plus the gene node ID
            # 'lcl|' is required by blast+ to ensure correct parsing of the identifier
            output_nt.write(">lcl|"+str(gene_annotation[0])+"\n")
            output_nt.write(gene_sequence+"\n")
            protein_sequence = self.translate_nt(gene_sequence)
            if not protein_sequence:
                continue
            output_prot.write(">lcl|"+str(gene_annotation[0])+"\n")
            output_prot.write(protein_sequence + "\n")
        output_nt.close()
        output_prot.close()
        # Delete genome index file
        os.remove(self.sequence_file_path + ".fai")
        return gene_annotation_list

    # Retrieve a single nt transcript by FASTA header ID
    def get_nt_sequence(self, id):
        try:
            nt_transcripts = Fasta(self.gff3_file_path + "_transcripts.fa", as_raw=True)
            nt_transcript = str(nt_transcripts["lcl|" + str(id)])
        except (KeyError,UnboundLocalError):
            nt_transcript = ""
        os.remove(self.gff3_file_path+"_transcripts.fa" + ".fai")
        return nt_transcript

    # Retrieve a single prot translation by FASTA header ID
    def get_prot_sequence(self, id):
        try:
            prot_transcripts = Fasta(self.gff3_file_path + "_translations.fa", as_raw=True)
            prot_transcript = str(prot_transcripts["lcl|" + str(id)])
        except (KeyError, UnboundLocalError):
            prot_transcript = ""
        os.remove(self.gff3_file_path + "_translations.fa" + ".fai")
        return prot_transcript

    # Delete transcripts and translations
    def delete_transcripts_translations(self):
        os.remove(self.gff3_file_path + "_transcripts.fa")
        os.remove(self.gff3_file_path + "_translations.fa")











