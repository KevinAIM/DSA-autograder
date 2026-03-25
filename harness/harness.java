package harness;

import M6.RodCut;
import M6.LCS;

public class Harness {
    public static void main(String[] args) {
        
int result1 = LCS.lcs_length("ABCBDAB", "BDCABA");
if (result1 != 4) {
    System.out.println("{\"status\":\"fail\",\"class\":\"LCS\",\"reason\":\"lcs_length(ABCBDAB, BDCABA) wrong answer\"}");
    return;
}

int result2 = LCS.lcs_length("ACCGGTCGAGTGCGCGGAAGCCGGCCGAA", "GTCGTTCGGAATGCCGTTGCTCTGTAAA");
if (result2 != 20) {
    System.out.println("{\"status\":\"fail\",\"class\":\"LCS\",\"reason\":\"lcs_length second test wrong answer\"}");
    return;
}

System.out.println("{\"status\":\"pass\",\"class\":\"LCS\"}");

    }
}
