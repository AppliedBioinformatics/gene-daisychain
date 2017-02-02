# Modify the annotation lines of a protein fasta file
# Final format: >|lcl|ID "Protein description"
import sys
for file in sys.argv[1:]:
    fasta_file = open(file, "r")
    fasta_file_corrected = open(file[:file.rfind(".")]+"_header_corrected.faa", "w")
    for line in fasta_file:
        if not line.startswith(">"):
            fasta_file_corrected.write(line)
        else:
            # Remove > and newline
            header = line[1:-1]
            id = header[:header.find(" ")]
            protein_description = header[header.find(" "):]
            fasta_file_corrected.write(">|lcl|"+id+protein_description+"\n")
    fasta_file.close()
    fasta_file_corrected.close()
