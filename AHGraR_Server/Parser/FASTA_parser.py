# Prepare the protein FASTA files for homolog search
# BLAST requires a certain format to parse the ID, therefore
# the annotation lines of the FASTA files are modified to this format:
# Final format: >|lcl|ID
# The ID is defined as everything following the > until the first whitespace
# ID must match protein name in csv/gff3 annotation file
# Additionally, one large FASTA file consisting of all individual FASTA sequences of
# all species is created. This is used later to build the BLAST database.
import os


class FastaParser:
    def __init__(self, proj_id):
        self.file_path = os.path.join("Projects", proj_id, "Files")
        self.CSV_path = os.path.join("Projects", proj_id, "CSV")
        self.BlastDB_path = os.path.join("Projects", proj_id, "BlastDB")
        self.combined_fasta_file = open(os.path.join(self.BlastDB_path, "combined_prot_fasta.faa"), "w")

    def parse_fasta(self, file_name):
        with open(os.path.join(self.file_path, file_name),"r") as input_fasta_file:
            with open(os.path.join(self.file_path, file_name+"_header_corrected.faa"),"w") as output_fasta_file:
                for line in input_fasta_file:
                    # If line is not a fasta-header or an already corrected fasta header
                    # write line to new file and to combined file
                    if not line.startswith(">") or line.startswith(">lcl|"):
                        output_fasta_file.write(line)
                        self.combined_fasta_file.write(line)
                        continue
                    else:
                        # Else modify header line to match required format
                        # Remove > and newline
                        header = line[1:-1]
                        id = header.split(" ")[0]
                        output_fasta_file.write(">lcl|" + id + "\n")
                        self.combined_fasta_file.write(">lcl|" + id + "\n")
        # Delete original FASTA file
        os.remove(os.path.join(self.file_path, file_name))
        # Rename modified FASTA file to original file name
        os.rename(os.path.join(self.file_path, file_name+"_header_corrected.faa"),
                  os.path.join(self.file_path, file_name))
    def close_combined_fasta(self):
        self.combined_fasta_file.close()

