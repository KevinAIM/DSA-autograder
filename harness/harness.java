package harness;

import M7.Graph;
import java.util.Arrays;

public class Harness {
    public static void main(String[] args) {
        
// Test BFS
int n1 = 8;
int[][] A = {
    {0, 1, 0, 0, 1, 0, 0, 0},
    {1, 0, 0, 0, 0, 1, 0, 0},
    {0, 0, 0, 1, 0, 1, 1, 0},
    {0, 0, 1, 0, 0, 0, 1, 1},
    {1, 0, 0, 0, 0, 0, 0, 0},
    {0, 1, 1, 0, 0, 0, 1, 0},
    {0, 0, 1, 1, 0, 1, 0, 1},
    {0, 0, 0, 1, 0, 0, 1, 0}
};
Graph g1 = new Graph(n1, A);
int[] bfsResult = g1.bfs(1);
int[] bfsExpected = {1, 0, 2, 3, 2, 1, 2, 3};
if (!Arrays.equals(bfsResult, bfsExpected)) {
    System.out.println("{\"status\":\"fail\",\"class\":\"Graph\",\"reason\":\"bfs() wrong answer\"}");
    return;
}

// Test Bellman-Ford
int n2 = 5;
int[][] B = {
    {0, 6, 0, 7, 0},
    {0, 0, 5, 8, -4},
    {0, -2, 0, 0, 0},
    {0, 0, -3, 0, 9},
    {2, 0, 7, 0, 0}
};
Graph g2 = new Graph(n2, B);
boolean bfResult = g2.bellman_ford(0);
if (!bfResult) {
    System.out.println("{\"status\":\"fail\",\"class\":\"Graph\",\"reason\":\"bellman_ford() should return true (no negative cycle)\"}");
    return;
}
int[] bfExpected = {0, 2, 4, 7, -2};
if (!Arrays.equals(g2.d, bfExpected)) {
    System.out.println("{\"status\":\"fail\",\"class\":\"Graph\",\"reason\":\"bellman_ford() wrong distances\"}");
    return;
}

// Test Dijkstra
int[][] C = {
    {0, 10, 0, 5, 0},
    {0, 0, 1, 2, 0},
    {0, 0, 0, 0, 4},
    {0, 3, 9, 0, 2},
    {7, 0, 6, 0, 0}
};
Graph g3 = new Graph(n2, C);
g3.dijkstra(0);
int[] dijkExpected = {0, 8, 9, 5, 7};
if (!Arrays.equals(g3.d, dijkExpected)) {
    System.out.println("{\"status\":\"fail\",\"class\":\"Graph\",\"reason\":\"dijkstra() wrong distances\"}");
    return;
}

System.out.println("{\"status\":\"pass\",\"class\":\"Graph\"}");

    }
}
