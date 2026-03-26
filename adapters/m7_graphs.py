from pathlib import Path
from adapters.base import Adapter


class M7GraphsAdapter(Adapter):

    def harness_main_class(self) -> str:
        return "harness.Harness"

    def methods(self) -> list:
        return [
            {"class_name": "Graph", "harness_type": "graph", "pseudo_code": """
BFS(G, s):
    for each vertex u in G.V - {s}:   // initialize all nodes
        u.color = WHITE
        u.d = infinity
        u.pi = NIL
    s.color = GRAY                     // mark source as discovered
    s.d = 0
    s.pi = NIL
    Q = empty queue
    ENQUEUE(Q, s)
    while Q not empty:                 // process queue
        u = DEQUEUE(Q)
        for each v in G.Adj[u]:       // check all neighbors
            if v.color == WHITE:      // undiscovered neighbor
                v.color = GRAY
                v.d = u.d + 1         // distance is one more than parent
                v.pi = u
                ENQUEUE(Q, v)
        u.color = BLACK               // fully processed

BELLMAN-FORD(G, w, s):
    INITIALIZE-SINGLE-SOURCE(G, s)    // set all d = infinity, d[s] = 0
    for i = 1 to |G.V| - 1:          // relax all edges n-1 times
        for each edge (u, v) in G.E:
            RELAX(u, v, w)
    for each edge (u, v) in G.E:     // check for negative cycles
        if v.d > u.d + w(u,v):
            return FALSE              // negative cycle detected
    return TRUE

DIJKSTRA(G, w, s):
    INITIALIZE-SINGLE-SOURCE(G, s)    // set all d = infinity, d[s] = 0
    S = empty set
    Q = G.V                           // all vertices in priority queue
    while Q not empty:
        u = EXTRACT-MIN(Q)            // get vertex with minimum distance
        S = S union {u}
        for each vertex v in G.Adj[u]:
            RELAX(u, v, w)            // update distances to neighbors
"""}
        ]

    def write_harness(self, harness_path: Path, method: dict) -> None:
        main_body = self._graph_main(method)

        code = f"""\
package harness;

import M7.Graph;
import java.util.Arrays;

public class Harness {{
    public static void main(String[] args) {{
        {main_body}
    }}
}}
"""
        harness_path.parent.mkdir(parents=True, exist_ok=True)
        harness_path.write_text(code, encoding="utf-8")

    def _graph_main(self, method):
        return f"""
// Test BFS
int n1 = 8;
int[][] A = {{
    {{0, 1, 0, 0, 1, 0, 0, 0}},
    {{1, 0, 0, 0, 0, 1, 0, 0}},
    {{0, 0, 0, 1, 0, 1, 1, 0}},
    {{0, 0, 1, 0, 0, 0, 1, 1}},
    {{1, 0, 0, 0, 0, 0, 0, 0}},
    {{0, 1, 1, 0, 0, 0, 1, 0}},
    {{0, 0, 1, 1, 0, 1, 0, 1}},
    {{0, 0, 0, 1, 0, 0, 1, 0}}
}};
Graph g1 = new Graph(n1, A);
int[] bfsResult = g1.bfs(1);
int[] bfsExpected = {{1, 0, 2, 3, 2, 1, 2, 3}};
if (!Arrays.equals(bfsResult, bfsExpected)) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"Graph\\",\\"reason\\":\\"bfs() wrong answer\\"}}");
    return;
}}

// Test Bellman-Ford
int n2 = 5;
int[][] B = {{
    {{0, 6, 0, 7, 0}},
    {{0, 0, 5, 8, -4}},
    {{0, -2, 0, 0, 0}},
    {{0, 0, -3, 0, 9}},
    {{2, 0, 7, 0, 0}}
}};
Graph g2 = new Graph(n2, B);
boolean bfResult = g2.bellman_ford(0);
if (!bfResult) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"Graph\\",\\"reason\\":\\"bellman_ford() should return true (no negative cycle)\\"}}");
    return;
}}
int[] bfExpected = {{0, 2, 4, 7, -2}};
if (!Arrays.equals(g2.d, bfExpected)) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"Graph\\",\\"reason\\":\\"bellman_ford() wrong distances\\"}}");
    return;
}}

// Test Dijkstra
int[][] C = {{
    {{0, 10, 0, 5, 0}},
    {{0, 0, 1, 2, 0}},
    {{0, 0, 0, 0, 4}},
    {{0, 3, 9, 0, 2}},
    {{7, 0, 6, 0, 0}}
}};
Graph g3 = new Graph(n2, C);
g3.dijkstra(0);
int[] dijkExpected = {{0, 8, 9, 5, 7}};
if (!Arrays.equals(g3.d, dijkExpected)) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"Graph\\",\\"reason\\":\\"dijkstra() wrong distances\\"}}");
    return;
}}

System.out.println("{{\\"status\\":\\"pass\\",\\"class\\":\\"Graph\\"}}");
"""