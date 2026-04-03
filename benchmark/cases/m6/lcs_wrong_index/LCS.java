package M6;

public class LCS {
	
    public static int lcs_length(String X, String Y) {
        int m = X.length();
        int n = Y.length();
        int[][] c = new int[m + 1][n + 1];
        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (X.charAt(i) == Y.charAt(j))  // should be X.charAt(i-1) == Y.charAt(j-1)
                    c[i][j] = c[i-1][j-1] + 1;
                else
                    c[i][j] = Math.max(c[i - 1][j], c[i][j - 1]);
            }
        }
        return c[m][n];
    }

	public static void main(String[] args) {
		System.out.println(LCS.lcs_length("ABCBDAB", "BDCABA"));
		System.out.println(LCS.lcs_length("ACCGGTCGAGTGCGCGGAAGCCGGCCGAA", "GTCGTTCGGAATGCCGTTGCTCTGTAAA"));
	}
}