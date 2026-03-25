from pathlib import Path
from adapters.base import Adapter


class M6DynamicProgrammingAdapter(Adapter):

    def harness_main_class(self) -> str:
        return "harness.Harness"

    def methods(self) -> list:
        return [
            {"class_name": "RodCut", "harness_type": "rodcut", "pseudo_code": """
ROD-CUT MEMOIZED (top-down):
    Initialize r[0..n] = -infinity         // memo table
    return MEMOIZED-CUT-ROD-AUX(p, n, r)

MEMOIZED-CUT-ROD-AUX(p, n, r):
    if r[n] >= 0: return r[n]              // return cached result
    if n == 0: q = 0
    else:
        q = -infinity
        for i = 1 to n:                    // try all cut positions
            q = max(q, p[i] + MEMOIZED-CUT-ROD-AUX(p, n-i, r))
    r[n] = q                               // cache result
    return q

BOTTOM-UP-CUT-ROD(p, n):
    r[0] = 0
    for j = 1 to n:                        // solve each subproblem
        q = -infinity
        for i = 1 to j:                    // try all cuts
            q = max(q, p[i] + r[j-i])
        r[j] = q                           // store optimal value
    return r[n]

EXTENDED-BOTTOM-UP-CUT-ROD(p, n):
    same as BOTTOM-UP but also track s[j] = best first cut for rod of length j
"""},
            {"class_name": "LCS", "harness_type": "lcs", "pseudo_code": """
LCS-LENGTH(X, Y):
    m = X.length, n = Y.length
    c[0..m][0..n] = 0                      // base cases
    for i = 1 to m:
        for j = 1 to n:
            if X[i] == Y[j]:               // characters match
                c[i][j] = c[i-1][j-1] + 1
            else:
                c[i][j] = max(c[i-1][j], c[i][j-1])
    return c[m][n]                         // length of LCS
"""}
        ]

    def write_harness(self, harness_path: Path, method: dict) -> None:
        harness_type = method.get("harness_type")

        if harness_type == "rodcut":
            main_body = self._rodcut_main(method)
        elif harness_type == "lcs":
            main_body = self._lcs_main(method)

        code = f"""\
package harness;

import M6.RodCut;
import M6.LCS;

public class Harness {{
    public static void main(String[] args) {{
        {main_body}
    }}
}}
"""
        harness_path.parent.mkdir(parents=True, exist_ok=True)
        harness_path.write_text(code, encoding="utf-8")

    def _rodcut_main(self, method):
        return f"""
RodCut rc = new RodCut();

int memo = rc.memoized_cut_rod();
if (memo != 30) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"RodCut\\",\\"reason\\":\\"memoized_cut_rod() wrong answer\\"}}");
    return;
}}

int bottom = rc.bottom_up_cut_rod();
if (bottom != 30) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"RodCut\\",\\"reason\\":\\"bottom_up_cut_rod() wrong answer\\"}}");
    return;
}}

rc.extended_bottom_up_cut_rod();
if (rc.r == null || rc.s == null) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"RodCut\\",\\"reason\\":\\"extended_bottom_up_cut_rod() did not populate r and s arrays\\"}}");
    return;
}}

if (rc.r[10] != 30) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"RodCut\\",\\"reason\\":\\"extended_bottom_up_cut_rod() r[10] wrong answer\\"}}");
    return;
}}

System.out.println("{{\\"status\\":\\"pass\\",\\"class\\":\\"RodCut\\"}}");
"""

    def _lcs_main(self, method):
        return f"""
int result1 = LCS.lcs_length("ABCBDAB", "BDCABA");
if (result1 != 4) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"LCS\\",\\"reason\\":\\"lcs_length(ABCBDAB, BDCABA) wrong answer\\"}}");
    return;
}}

int result2 = LCS.lcs_length("ACCGGTCGAGTGCGCGGAAGCCGGCCGAA", "GTCGTTCGGAATGCCGTTGCTCTGTAAA");
if (result2 != 20) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"LCS\\",\\"reason\\":\\"lcs_length second test wrong answer\\"}}");
    return;
}}

System.out.println("{{\\"status\\":\\"pass\\",\\"class\\":\\"LCS\\"}}");
"""