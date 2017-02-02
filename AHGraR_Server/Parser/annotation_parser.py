# Accept various types of gene annotation files
# Currently supported: GFF3
# Return a list of genes in this format:
# [(Organism,Chromosome,Strand_orientation,Start_index,End_index, Gene_name),...]
from os.path import splitext,basename

import Outdated.GFF3_Parser_NCBI as GFF3_ncbi


class AnnotationParser:

    # Sort genes for Organism -> Chromosome -> Start_Index
    def sort_gene_list(self, gene_list):
        gene_list_ordered = sorted(gene_list, key=lambda x: (x[0], x[1], int(x[3])))
        return gene_list_ordered

    # Interface, keyword decides about the file format and the parsing routine
    def parse_annotation(self, format, file):
        switch = {"NCBI_refseq": self.parse_ncbi_refseq}
        gene_list = switch[format](file)
        # Order genes before returning list
        return self.sort_gene_list(gene_list)

    # Parser for NCBI refseq GFF3 files
    # GFF3_parser returns a dict assigning a gene to each protein name referenced in the GFF3 file
    def parse_ncbi_refseq(self, annotation_file_path):
        gff3_parser = GFF3_ncbi.GFF3ParserSimple()
        gff3_parser.add_file(annotation_file_path)
        organism_name = splitext(basename(annotation_file_path))[0]
        protein_DB = gff3_parser.match_protein_id_to_gene_id_db("protein_id")
        gene_list = []
        # Collect all genes by iterating over all proteins
        for protein in protein_DB.keys():
            gene_props = gff3_parser.protein_db[protein]
            gene = (organism_name, gene_props.get("seqid", "NA"), gene_props.get("strand", "NA"), gene_props.get("start", "NA"), gene_props["end"],
                    gene_props["Name"])
            gene_list.append(gene)
        # Multiple protein entries may be linked to the same gene
        # Make gene list unique
        # gene_list contains no information about proteins
        return list(set(gene_list))
