package harness;

import java.util.Arrays;
import M4.Sort;
import java.io.StringWriter;
import java.io.PrintWriter;

public class Harness {

    static boolean arraysEqual(int[] a, int[] b) {
        return Arrays.equals(a, b);
    }

    static String arrToString(int[] a) {
        return Arrays.toString(a);
    }

    public static void main(String[] args) {
                    Sort obj = new Sort();
            int[][] tests = new int[][] {
                new int[] {2, 1},
                new int[] {3, 2, 1},
                new int[] {1, 2, 3},
                new int[] {5, 1, 4, 2, 8},
                new int[] {2, 2, 1, 1},
                new int[] {0, -1, 5, -3, 2}
            };

            for (int i = 0; i < tests.length; i++) {
                int[] input = Arrays.copyOf(tests[i], tests[i].length);
                int[] actual = Arrays.copyOf(tests[i], tests[i].length);

                try {
                    int q = obj.partition(actual, 0, actual.length - 1);

                    // check left side <= pivot
                    for (int k = 0; k < q; k++) {
                        if (actual[k] > actual[q]) {
                            System.out.println("{\"status\":\"fail\",\"testIndex\":" + i
                                + ",\"reason\":\"left element > pivot\""
                                + ",\"input\":\"" + Arrays.toString(input) + "\"}");
                            return;
                        }
                    }
                    // check right side >= pivot
                    for (int k = q + 1; k < actual.length; k++) {
                        if (actual[k] < actual[q]) {
                            System.out.println("{\"status\":\"fail\",\"testIndex\":" + i
                                + ",\"reason\":\"right element < pivot\""
                                + ",\"input\":\"" + Arrays.toString(input) + "\"}");
                            return;
                        }
                    }

                } catch (Throwable t) {
                    System.out.println("{\"status\":\"error\",\"testIndex\":" + i
                        + ",\"exception\":\"" + t.toString().replace("\"", "\\\"") + "\"}");
                    return;
                }
            }
            System.out.println("{\"status\":\"pass\",\"tests\":" + tests.length + "}");
    }
}
