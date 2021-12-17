// AHGraR-specific function
// Adds example data into search field
function addExampleQuery()
{
    // Get currently selected cluster size value
    // Find select menu and retrieve currently selected cluster size
    var query_window = document.getElementById("keyword");
    document.getElementById('radio_all').checked = false;
    document.getElementById('radio_any').checked = true;
    if (project_id == 689) {
        query_window.value = "BnaA01g00070D";
    } else if (project_id == 580 ){
        query_window.value = "YP_006776737";
    } else {
        alert('Current project has no example data.');
    }
    var blast_window = document.getElementById("tbfasta");
    blast_window.value = "";
};


// Adds data for BLAST
function addExampleBlast()
{
    var query_window = document.getElementById("keyword");
    query_window.value = "";
    document.getElementById('radio_all').checked = true;
    document.getElementById('radio_any').checked = false;
    var blast_window = document.getElementById("tbfasta");
    if (project_id == 689) {
        blast_window.value = "ATGGAGTCCGGGTCGGGTTTGGATCCGAGTAAGAGCAAAGGAAGCGGCAGTGGCGAGGGGAAGTTCGGTGCTTTCTTGAAGAGAGTAGAACCCTTCTTACCGAGAAAGGAGCTGAACCCGGTAGAGCTAAGATCTTGGGCCAAGAAAACCGGTTTTGTCTCCGACTACTCCGGCGAAACCAGCGCCAAGCTCGGTGAGACTGAGAGCTCTGCTTTTGATTTGCCAAAAGGTAGAGATCATCATCAAATAGATCGAGCGTCGTCACGTCAAACCGACCTCGACCCGATTCTTGGCCGAAGCAGACGATCCGATATCGGATCTGATCCCGGGTCTAAACCGGGCTCTATAGAGGAAGAGAGAGGATCAAACGCTGAGACACCGTTGGAGAATGAAGGAGGGAAGATCAGCAGAGATTTGGAGAATGGGTGTTACTATCCAGGAGGTGGAGAAGGAGAAGGTGGAGGTTGGCCTAAGCCCATTGTAATGAAGTATGGTCTCAGAGACAATCCTCCTGGCTTCGTCCACTTGTATACTACGGTTTGCAACACTATCTATCACTTGCCGGTTCACTTGTCTTTATACCTCTTGTCATTGTCCCAGCCATGGATGGTTCCGATAAAGATACCGCCGCAGTGATTTCAACAATGCTGCTTCTTACTGGAATTACAACCATACTTCACTGTTATTTTGGTACTCGGCTTCCTTTAGTGCAAGGAAGCTCCTTTGTTTACTTAGCCCCGGCTTTGGTTGTCATCAACTCAGAGGAGTTTAGGAACCTCACTGAGCATAAATTTCGGGAGATAATGAGAGAACTACAAGGAGCTATAATCGTTGGTTCATTGTTCCAGTGCATACTGGGATCCACTGGTCTCATGTCTCTCCTTCTTAGTTATTAATCCTGTTGTAGTAGCACCAACCGTAGCTGCAGTAGGATTAGCATTCTTTAGCTATGGATTTCCACAGGCCGGGACTTGTGTTGAGATCAGCATTCCTGTAATAGTCATGCTTCTCATTTGCACATTGTATCTCCGTGGAGTTTCAATCTTTGGTCATCGCATATTCCGAATTTATGCGGTGCCGCTTAGTGCTCTGATCGTCTGGACATACGCATTCTTTCTAACAGTTGGTGGTGCATATGACTATAAAGGCTGCAACGCCGACATACCAAGCTCTAACATATTAATAAACGAATGTAAGAAACACGCGTACACCATGAAGCATTGCAGAACAGATGCTTCCAACGCTTGGGCGACTTCTCCTTGGCTCAGAATCCCTTATCCATTTCAATGGGGGTTTCCGTATTTTCACATGAGAACTTGTATCATTATGATCTTCACGTCTTTGGTTACATCGGTGGACTCGGTTGGAACATACCATGCCACGTCTATGTTAGTGAATGCTAAGCGACCTACACGTGGTGTTGTGAGCAGAGGTGTTGCGTTAGAAGGCTTTTGTAGTTTGTTAGCTGGAATATGGGGTTCCGGTACCGGTTCAACCACGTTAACCGAAAATATTCATACAATTAATATCACTAAGGTGGCTAACCGAAGAGCTTTGGCAATAGGAGCTTTGTTCTTGATATTTTTCTCATTTGTGGGAAAATTAGGTGCAATTCTTGCTTCAATACCACAGGCTTTGGCTGCTTCAGTGTTATGCTTTATATGGGCACTTACAGTGGCTCTAGGTCTATCGAATCTCCGGTACACACAAACAGCGAGTTTTAGGAACATAACCATAGTTGGGGTCTCACTGTTTCTTGGATTATCCATCCCTGCTTATTTCCAGCAGTATCAACCACTATCTAGTCTGATACTACCGAGCTATTACCTATCCTTTGGAGCCGCTTCAAGTGGACCGTTCCAAACGGGCATCATGCAGTTGGATTTTGCGATGAATGCTGTGATGTCGATGAATATGGTTGTAACGTTTCTACTGGCTTTCGTGTTGGACAACACTGTACCGGGTAGTAAGGAAGAGAGGGGAGTCTATGTGTGGTCACGAGCTGAGGACATGGAGTTGGACCCTGCAATGCAAGCTGATTACTCCTTGCCAAGAAGAGTTGCTCAGTTTTTCGGTTGCAGATGTTGCTAG";
    } else if (project_id == 580 ) {
        blast_window.value = "GTGTCACTTTCGCTTTGGCAGCAGTGTCTTGCCCGATTGCAGGATGAGTTACCAGCCACAGAATTCAGTATGTGGATACGCCCATTGCAGGCGGAACTGAGCGATAACACGCTGGCCCTGTACGCGCCAAACCGTTTTGTCCTCGATTGGGTACGGGACAAGTACCTTAATAATATCAATGGACTGCTAACCAGTTTCTGCGGAGCGGATGCCCCACAGCTGCGTTTTGAAGTCGGCACCAAACCGGTGACGCAAACGCCACAAGCGGCAGTGACGAGCAACGTCGCGGCCCCTGCACAGGTGGCGCAAACGCAGCCGCAACGTGCTGCGCCTTCTACGCGCTCAGGTTGGGATAACGTCCCGGCCCCGGCAGAACCGACCTATCGTTCTAACGTAAACGTCAAACACACGTTTGATAACTTCGTTGAAGGTAAATCTAACCAACTGGCGCGCGCGGCGGCTCGCCAGGTGGCGGATAACCCTGGCGGTGCCTATAACCCGTTGTTCCTTTATGGCGGCACGGGTCTGGGTAAAACTCACCTGCTGCATGCGGTGGGTAACGGCATTATGGCGCGCAAGCCGAATGCCAAAGTGGTTTATATGCACTCCGAGCGCTTTGTTCAGGACATGGTTAAAGCCCTGCAAAACAACGCGATCGAAGAGTTTAAACGCTACTACCGTTCCGTAGATGCACTGCTGATCGACGATATTCAGTTTTTTGCTAATAAAGAACGATCTCAGGAAGAGTTTTTCCACACCTTCAACGCCCTGCTGGAAGGTAATCAACAGATCATTCTCACCTCGGATCGCTATCCGAAAGAGATCAACGGCGTTGAGGATCGTTTGAAATCCCGCTTCGGTTGGGGACTGACTGTGGCGATCGAACCGCCAGAGCTGGAAACCCGTGTGGCGATCCTGATGAAAAAGGCCGACGAAAACGACATTCGTTTGCCGGGTGAAGTGGCGTTCTTTATCGCCAAGCGTCTAC";
    } else {
        alert('Current project has no example data.');
    }
};