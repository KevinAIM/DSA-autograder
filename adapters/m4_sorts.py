from pathlib import Path
from adapters.base import Adapter


class M4SortsAdapter(Adapter):
    def harness_main_class(self) -> str:
        # Run: java harness.Harness (if we put it in package harness)
        return "harness.Harness"

    def methods(self) -> list:
        return [{"method_name": "insertionSort", "pseudo_code": """
INSERTION-SORT(A):
    for j = 2 to A.length:              // iterate through each element starting from second
        key = A[j]                      // current element to insert into sorted left side
        // insert A[j] into the sorted sequence A[1..j-1]
        i = j - 1                       // index of last element in sorted portion
        while i > 0 and A[i] > key:    // shift elements right while greater than key
            A[i + 1] = A[i]            // shift element one position right
            i = i - 1                   // move left in sorted portion
        A[i + 1] = key                 // insert key into correct position
""", "call_args" : "actual"},
                {"method_name": "merge_sort", "pseudo_code": """
MERGE-SORT(A, p, r):
    if p < r:                        // base case: array of size 1 is already sorted
        q = (p + r) / 2              // find the midpoint
        MERGE-SORT(A, p, q)          // recursively sort left half
        MERGE-SORT(A, q + 1, r)      // recursively sort right half
        MERGE(A, p, q, r)            // merge the two sorted halves
""", "call_args" : "actual, 0, actual.length - 1"},
                {"method_name": "merge", "harness_type": "merge", "pseudo_code": """
MERGE(A, p, q, r):
    copy elements A[p..q] into left array L    // copy left subarray
    copy elements A[q+1..r] into right array R // copy right subarray
    iteratively compare L and R element by element  // merge step
    copy the smaller element back into A            // build sorted result
""", "call_args" : "actual, 0, actual.length / 2, actual.length - 1"},
                {"method_name": "quick_sort", "pseudo_code": """
QUICKSORT(A, p, r):
    if p < r:                            // base case: one or zero elements already sorted
        q = PARTITION(A, p, r)           // partition and get pivot index
        QUICKSORT(A, p, q - 1)           // recursively sort left of pivot
        QUICKSORT(A, q + 1, r)           // recursively sort right of pivot
""", "call_args" : "actual, 0, actual.length - 1"},
                {"method_name": "partition", "harness_type": "partition", "pseudo_code": """
PARTITION(A, p, r):
    x = A[r]                     // choose last element as pivot
    i = p - 1                    // i tracks boundary of elements <= pivot
    for j = p to r - 1:          // scan through array
        if A[j] <= x:            // if current element belongs on left side
            i = i + 1            // expand left partition
            exchange A[i] with A[j]  // move element to left side
    exchange A[i+1] with A[r]    // place pivot in correct position
    return i + 1                 // return pivot index
""", "call_args" : "actual, 0, actual.length - 1"}]

    def write_harness(self, harness_path: Path, method: dict) -> None:
        harness_type = method.get("harness_type", "sort")

        if harness_type == "partition":
            main_body = self._partition_main(method)
        elif harness_type == "merge":
            main_body = self._merge_main(method)
        else:
            main_body = self._sort_main(method)

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
        {main_body}
    }}
}}
"""
    
        harness_path.parent.mkdir(parents=True, exist_ok=True)
        harness_path.write_text(code, encoding="utf-8")

    
    def _partition_main(self, method):
        return f"""\
            {self.student_class} obj = new {self.student_class}();
            int[][] tests = new int[][] {{
                new int[] {{2, 1}},
                new int[] {{3, 2, 1}},
                new int[] {{1, 2, 3}},
                new int[] {{5, 1, 4, 2, 8}},
                new int[] {{2, 2, 1, 1}},
                new int[] {{0, -1, 5, -3, 2}}
            }};

            for (int i = 0; i < tests.length; i++) {{
                int[] input = Arrays.copyOf(tests[i], tests[i].length);
                int[] actual = Arrays.copyOf(tests[i], tests[i].length);

                try {{
                    int q = obj.partition(actual, 0, actual.length - 1);

                    // check left side <= pivot
                    for (int k = 0; k < q; k++) {{
                        if (actual[k] > actual[q]) {{
                            System.out.println("{{\\"status\\":\\"fail\\",\\"testIndex\\":" + i
                                + ",\\"reason\\":\\"left element > pivot\\""
                                + ",\\"input\\":\\"" + Arrays.toString(input) + "\\"}}");
                            return;
                        }}
                    }}
                    // check right side >= pivot
                    for (int k = q + 1; k < actual.length; k++) {{
                        if (actual[k] < actual[q]) {{
                            System.out.println("{{\\"status\\":\\"fail\\",\\"testIndex\\":" + i
                                + ",\\"reason\\":\\"right element < pivot\\""
                                + ",\\"input\\":\\"" + Arrays.toString(input) + "\\"}}");
                            return;
                        }}
                    }}

                }} catch (Throwable t) {{
                    System.out.println("{{\\"status\\":\\"error\\",\\"testIndex\\":" + i
                        + ",\\"exception\\":\\"" + t.toString().replace("\\"", "\\\\\\"") + "\\"}}");
                    return;
                }}
            }}
            System.out.println("{{\\"status\\":\\"pass\\",\\"tests\\":" + tests.length + "}}");"""

    def _merge_main(self, method):
        return f"""\
            {self.student_class} obj = new {self.student_class}();
            int[][] tests = new int[][] {{
                new int[] {{2, 1}},
                new int[] {{3, 2, 1}},
                new int[] {{1, 2, 3}},
                new int[] {{5, 1, 4, 2, 8}},
                new int[] {{2, 2, 1, 1}},
                new int[] {{0, -1, 5, -3, 2}}
            }};

            for (int i = 0; i < tests.length; i++) {{
                int[] input = Arrays.copyOf(tests[i], tests[i].length);
                int[] actual = Arrays.copyOf(tests[i], tests[i].length);
                int[] expected = Arrays.copyOf(tests[i], tests[i].length);
                Arrays.sort(expected);

                // pre-sort both halves so merge has valid input
                int mid = actual.length / 2;
                Arrays.sort(actual, 0, mid);
                Arrays.sort(actual, mid, actual.length);

                try {{
                    obj.merge(actual, 0, mid - 1, actual.length - 1);

                    if (!Arrays.equals(actual, expected)) {{
                        System.out.println("{{\\"status\\":\\"fail\\",\\"testIndex\\":" + i
                            + ",\\"input\\":\\"" + Arrays.toString(input) + "\\"" 
                            + ",\\"expected\\":\\"" + Arrays.toString(expected) + "\\"" 
                            + ",\\"actual\\":\\"" + Arrays.toString(actual) + "\\"}}");
                        return;
                    }}

                }} catch (Throwable t) {{
                    System.out.println("{{\\"status\\":\\"error\\",\\"testIndex\\":" + i
                        + ",\\"exception\\":\\"" + t.toString().replace("\\"", "\\\\\\"") + "\\"}}");
                    return;
                }}
            }}
            System.out.println("{{\\"status\\":\\"pass\\",\\"tests\\":" + tests.length + "}}");"""

    def _sort_main(self,method):
        return f"""
        {self.student_class} obj = new {self.student_class}();
    // test loop below...
    // Define a small but useful test set (can expand later)
        int[][] tests = new int[][] {{
            new int[] {{}},
            new int[] {{1}},
            new int[] {{2, 1}},
            new int[] {{3, 2, 1}},
            new int[] {{1, 2, 3}},
            new int[] {{5, 1, 4, 2, 8}},
            new int[] {{2, 2, 1, 1}},
            new int[] {{0, -1, 5, -3, 2}},
            new int[] {{3, 3, 1}},
            new int[] {{3, 1, 2}}
        }};

    for (int i = 0; i < tests.length; i++) {{
        int[] input = Arrays.copyOf(tests[i], tests[i].length);
        int[] expected = Arrays.copyOf(tests[i], tests[i].length);
        Arrays.sort(expected);

        int[] actual = Arrays.copyOf(tests[i], tests[i].length);

        try {{
            // call student method (assumes static void insertionSort(int[]))
            obj.{method["method_name"]}({method["call_args"]});
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
"""