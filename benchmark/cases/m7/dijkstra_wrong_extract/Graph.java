package M7;

public class Graph {
	public int n;	//number of vertice
	public int[][] A;	//the adjacency matrix
	public int[] d;	//shortest distance
	private final int WHITE = 2;
	private final int GRAY = 3;
	private final int BLACK = 4;
	
	public Graph () {
		n = 0;
		A = null;
		d = null;
	}
	
	public Graph (int _n, int[][] _A) {
		this.n = _n;
		this.A = _A;
		this.d = new int[_n];
	}
	
	/*
	 * Input: s denotes the index of the source node
	 * Output: the array dist, where dist[i] is the distance between the i-th node to s
	 */
	public int[] bfs(int s) {
		int[] color = new int[n];
		int[] dist = new int[n];
		for (int i = 0; i < n; i++) {
			color[i] = WHITE;
			dist[i] = Integer.MAX_VALUE;
		}
		color[s] = GRAY;
		dist[s] = 0;
		java.util.Queue<Integer> queue = new java.util.LinkedList<>();
		queue.add(s);
		while (!queue.isEmpty()) {
			int u = queue.poll();
			for (int v = 0; v < n; v++) {
				if (A[u][v] != 0 && color[v] == WHITE) {
					color[v] = GRAY;
					dist[v] = dist[u] + 1;
					queue.add(v);
				}
			}
			color[u] = BLACK;
		}
		return dist;
	}
	
	public void initialize_single_source(int s) {
		for (int i = 0; i < n; i++)
			d[i] = Integer.MAX_VALUE;
		d[s] = 0;
	}
	
	public void relax (int u, int v) {
		if (d[v] > (d[u] + A[u][v])) 
			d[v] = d[u] + A[u][v];
	}
	
	public boolean bellman_ford(int s) {
		initialize_single_source(s);
		for (int i = 1; i < n; i++) {
			for (int u = 0; u < n; u++) {
				for (int v = 0; v < n; v++) {
					if (A[u][v] != 0) relax(u, v);
				}
			}
		}
		for (int u = 0; u < n; u++) {
			for (int v = 0; v < n; v++) {
				if (A[u][v] != 0 && d[v] > d[u] + A[u][v])
					return false;
			}
		}
		return true;
	}
	
	public void dijkstra(int s) {
		initialize_single_source(s);
		boolean[] visited = new boolean[n];
		for (int i = 0; i < n; i++) {
			int u = -1;
			for (int v = 0; v < n; v++) {
				if (!visited[v] && (u == -1 || d[v] < d[u])) u = v;
			}
			if (d[u] == Integer.MAX_VALUE) break;
			// visited[u] = true;  -- never marks as visited
			for (int v = 0; v < n; v++) {
				if (A[u][v] != 0) relax(u, v);
			}
		}
	}
	
	public void display_distance () {
		for (int i = 0; i < n; i++)
			System.out.println(i + ": " + d[i]);
	}
	
	public void print_array (int[] array) {
		for (int i = 0; i < array.length; i++)
			System.out.println(i + ": " + array[i]);
	}
	
	/**
	 * @param args
	 */
	public static void main(String[] args) {
		// TODO Auto-generated method stub
		// Test BFS
		int n = 8;
		int[][] A = 
			{{0, 1, 0, 0, 1, 0, 0, 0},
			{1, 0, 0, 0, 0, 1, 0, 0},
			{0, 0, 0, 1, 0, 1, 1, 0},
			{0, 0, 1, 0, 0, 0, 1, 1},
			{1, 0, 0, 0, 0, 0, 0, 0},
			{0, 1, 1, 0, 0, 0, 1, 0},
			{0, 0, 1, 1, 0, 1, 0, 1},
			{0, 0, 0, 1, 0, 0, 1, 0}};
		Graph g1 = new Graph(n, A);
		g1.print_array(g1.bfs(1));
		
		// Test Bellman_Ford 
		n = 5;
		int[][] B = {
		{0, 6, 0, 7, 0},
		{0, 0, 5, 8, -4},
		{0, -2, 0, 0, 0},
		{0, 0, -3, 0, 9},
		{2, 0, 7, 0, 0}
		};
		Graph g2 = new Graph(n, B);
		g2.bellman_ford(0);
		g2.display_distance();
		
		System.out.println("-----------------------");
		
		// Test Dijkstra
		int[][] C = {
		{0, 10, 0, 5, 0},
		{0, 0, 1, 2, 0},
		{0, 0, 0, 0, 4},
		{0, 3, 9, 0, 2},
		{7, 0, 6, 0, 0}
		};
		Graph g3 = new Graph(n, C);
		g3.dijkstra(0);
		g3.display_distance();
	}

}
