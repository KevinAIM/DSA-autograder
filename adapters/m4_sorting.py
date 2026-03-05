from pathlib import Path
from adapters.base import Adapter


class M4InsertionSortAdapter(Adapter):
    method_name: str = "insertionSort"   # change if your skeleton uses a different name

    def harness_main_class(self) -> str:
        # Run: java harness.Harness (if we put it in package harness)
        return "harness.Harness"

    def write_harness(self, harness_path: Path) -> None:
        # A harness that:
        # 1) runs multiple tests
        # 2) compares to Arrays.sort on a copy (oracle)
        # 3) prints a single JSON line with pass/fail + first failing case
        code = f"""\
package harness;

import java.util.Arrays;
import {self.package}.{self.student_class};
import java.io.StringWriter;
import java.io.PrintWriter;

public class Harness {{

    static boolean arraysEqual(int[] a, int[] b) {{
        return Arrays.equals(a, b);
    }}

    static String arrToString(int[] a) {{
        return Arrays.toString(a);
    }}

    public static void main(String[] args) {{
        // Define a small but useful test set (can expand later)
        int[][] tests = new int[][] {{
            new int[] {{}},
            new int[] {{1}},
            new int[] {{2, 1}},
            new int[] {{3, 2, 1}},
            new int[] {{1, 2, 3}},
            new int[] {{5, 1, 4, 2, 8}},
            new int[] {{2, 2, 1, 1}},
            new int[] {{0, -1, 5, -3, 2}}
        }};

        for (int i = 0; i < tests.length; i++) {{
            int[] input = Arrays.copyOf(tests[i], tests[i].length);
            int[] expected = Arrays.copyOf(tests[i], tests[i].length);
            Arrays.sort(expected);

            int[] actual = Arrays.copyOf(tests[i], tests[i].length);

            try {{
                // call student method (assumes static void insertionSort(int[]))
                {self.student_class}.{self.method_name}(actual);
            }} catch (Throwable t) {{
                StringWriter sw = new StringWriter();
                PrintWriter pw = new PrintWriter(sw);
                t.printStackTrace(pw);

                String stack = sw.toString();
                String where = "";
                String[] lines = stack.split("\\\\r?\\\\n");
                for (String line : lines) {{
                    if (line.contains("Sort.java:")) {{
                        where = line.trim();
                        break;
                    }}
                }}
                where = where.replace("\\\\", "\\\\\\\\").replace("\\"", "\\\\\\"");

                System.out.println("{{\\"status\\":\\"error\\",\\"type\\":\\"exception\\",\\"testIndex\\":" + i
                    + ",\\"input\\":\\"" + arrToString(input) + "\\"," 
                    + "\\"exception\\":\\"" + t.toString().replace("\\"", "\\\\\\"") + "\\"," 
                    + "\\"where\\":\\"" + where + "\\"}}");
                return;
            }}



            if (!arraysEqual(actual, expected)) {{
                System.out.println("{{\\"status\\":\\"fail\\",\\"testIndex\\":" + i
                    + ",\\"input\\":\\"" + arrToString(input) + "\\","
                    + "\\"expected\\":\\"" + arrToString(expected) + "\\","
                    + "\\"actual\\":\\"" + arrToString(actual) + "\\"}}");
                return;
            }}
        }}

        System.out.println("{{\\"status\\":\\"pass\\",\\"tests\\":" + tests.length + "}}");
    }}
}}
"""
        harness_path.parent.mkdir(parents=True, exist_ok=True)
        harness_path.write_text(code, encoding="utf-8")
