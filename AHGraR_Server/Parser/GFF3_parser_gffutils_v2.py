# GFF3-parser based on gffutils
# Extracts gene transcript information from a GFF3 file
# In addition to the GFF3 annotation the genomic sequence or the transcript sequences are needed
# to retrieve the transcript sequences,
# Some information is required to correctly parse the GFF3 file:
# Is the sequence format genome or transcripts?
# How is the transcript feature called (e.g. Gene or mRNA)
# Which subfeatures of the transcript should be included (e.g. CDS, UTR, exons)
# Returns a list of gene annotations in this format:
#(gene_id, species_name, contig_name, start_index, stop_index, strand_orientation, gene_name, gene_description,
# nt_sequence, prot_sequence)
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
    def __init__(self, transcript_output, translate_output):
        self.output_path_nt_transcript = transcript_output
        self.output_path_prot_translation = translate_output
        # Ensure that output files are empty
        with open(self.output_path_nt_transcript, "w") as nt_out:
            with open(self.output_path_prot_translation, "w") as prot_out:
                pass
        # Each gene node gets an unique id, starting with zero
        self.gene_node_id = 0


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

    def parse_gff3_file(self, gff3_file_path, sequence_file_path, seq_is_genome,  parent_feature_type,
                 subfeatures, name_attribute, descr_attribute):
        species_name = os.path.splitext(os.path.basename(gff3_file_path))[0]
        # Load GFF3 file
        gffutils.create_db(gff3_file_path, "gff3utils.db", merge_strategy="create_unique", force=True)
        gff3_db = gffutils.FeatureDB('gff3utils.db', keep_order=False)
        # Parse sequence file
        # Is sequence the genome (true) or already spliced transcripts (false)
        if seq_is_genome:
            sequence = Fasta(sequence_file_path, sequence_always_upper=True)
        else:
            sequence = None

        # Set the list of all subfeatures of parent_feature that can be included in the final transcript
        # Input format: subfeat1,subfeat2,subfeat3
        subfeatures = subfeatures.split(",")
        # Attribute location is converted from feat:attr to a tuple
        name_attribute = name_attribute.split(":")
        descr_attribute = descr_attribute.split(":")
        # Collect all gene annotations in a list
        gene_annotation_list = []
        # Iterate through all transcripts (identified by parent_feature_type)
        for transcript in gff3_db.iter_by_parent_childs(parent_feature_type):
            # Increase gene node ID by one
            self.gene_node_id += 1
            # Extract all "standard" attributes for this transcript:
            # name and description may be changed by name_attribute and descr_attribute
            gene_annotation = [self.gene_node_id, species_name, transcript[0].seqid, transcript[0].start,
                               transcript[0].stop, transcript[0].strand, transcript[0].id, ""]
            if name_attribute[0] == parent_feature_type:
                try:
                    gene_annotation[6]=transcript[0][name_attribute[1]][0]
                except KeyError:
                    gene_annotation[6] = ""
            if descr_attribute[0] == parent_feature_type:
                try:
                    gene_annotation[7]=transcript[0][descr_attribute[1]][0]
                except KeyError:
                    gene_annotation[7]= ""
            # Collect gene annotation in list
            gene_sequence = []
            # Iterate through all subfeatures of this transcript
            # Two tasks are performed here: Look for name or descr attributes
            # Build the sequence of this transcript
            for subfeature in transcript[1:]:
                # Check if feature type is in the list of selected subfeatures
                if subfeature.featuretype in subfeatures:
                    # Check if name or description attribute can be found in this subfeature
                    if name_attribute[0] == subfeature.featuretype:
                        try:
                            gene_annotation[6] = subfeature[name_attribute[1]][0]
                        except KeyError:
                            pass
                    if descr_attribute[0] == subfeature.featuretype:
                        try:
                            gene_annotation[7] = subfeature[descr_attribute[1]][0]
                        except KeyError:
                            pass
                    # Collect sequence of this subfeature if nucleotide sequence is the genome
                    # Important: Current version of GFFutils has a bug preventing the automatic reverse-complement
                    # of minus-strand features
                    # Strandedness is therefore evaluated manually here
                    if seq_is_genome:
                        # Is sequence from a minus-strand feature?
                        antisense = subfeature.strand == "-"
                        # If antisense, reverse complement the sequence
                        #seq_fragment = subfeature.sequence(sequence, False).seq if not antisense \
                            #else self.reverse_complement(subfeature.sequence(sequence, False).seq)
                        seq_fragment = subfeature.sequence(sequence, False) if not antisense \
                            else self.reverse_complement(subfeature.sequence(sequence, False))
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
            # Translate gene sequence into protein sequence
            if gene_sequence:
                protein_sequence = self.translate_nt(gene_sequence)
            else:
                protein_sequence = ""
            # Append gene and protein sequence to gene annotation list
            gene_annotation.append(gene_sequence)
            gene_annotation.append(protein_sequence)
            gene_annotation_list.append(gene_annotation)
            # Write sequence to file, except when no sequence could be retrieved
            if not gene_sequence:
                continue
            # The fasta annotation line is  '>lcl|' plus the gene node ID
            # 'lcl|' is required by blast+ to ensure correct parsing of the identifier
            with open(self.output_path_nt_transcript, "a") as output_nt:
                output_nt.write(">lcl|"+str(gene_annotation[0])+"\n")
                output_nt.write(gene_sequence+"\n")
            if not protein_sequence:
                continue
            with open(self.output_path_prot_translation, "a") as output_prot:
                output_prot.write(">lcl|"+str(gene_annotation[0])+"\n")
                output_prot.write(protein_sequence + "\n")
        # Sort the gene_list by contig, start and stop. Only one species per file, so no need to sort by species
        gene_annotation_list = sorted(gene_annotation_list, key=lambda x: (x[2], int(x[3]), int(x[4])))
        # Delete genome index file
        os.remove(sequence_file_path + ".fai")
        return gene_annotation_list

    # # Retrieve a single nt transcript by FASTA header ID
    # def get_nt_sequence(self, id):
    #     try:
    #         nt_transcripts = Fasta(self.gff3_file_path + "_transcripts.fa", as_raw=True)
    #         nt_transcript = str(nt_transcripts["lcl|" + str(id)])
    #     except (KeyError,UnboundLocalError):
    #         nt_transcript = ""
    #     os.remove(self.gff3_file_path+"_transcripts.fa" + ".fai")
    #     return nt_transcript
    #
    # # Retrieve a single prot translation by FASTA header ID
    # def get_prot_sequence(self, id):
    #     try:
    #         prot_transcripts = Fasta(self.gff3_file_path + "_translations.fa", as_raw=True)
    #         prot_transcript = str(prot_transcripts["lcl|" + str(id)])
    #     except (KeyError, UnboundLocalError):
    #         prot_transcript = ""
    #     os.remove(self.gff3_file_path + "_translations.fa" + ".fai")
       # return prot_transcript

    # Delete transcripts and translations
    def delete_transcripts_translations(self):
        os.remove(self.output_path_nt_transcript)
        os.remove(self.output_path_prot_translation)











