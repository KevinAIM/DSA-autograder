package M6;

public class RodCut {
	int n;
	int[] p;
	public int[] r;
	public int[] s;
	
	public RodCut () {
		n = 10;
		p = new int[11];
		p[0] = 0;
		p[1] = 1;
		p[2] = 5;
		p[3] = 8;
		p[4] = 9;
		p[5] = 10;
		p[6] = 17;
		p[7] = 17;
		p[8] = 20;
		p[9] = 24;
		p[10] = 30;
	}
	
    public int memoized_cut_rod() {
        return 0;
    }

    public int memoized_cut_rod_aux(int p[], int n, int r[]) {
        return 0;
    }

    public int bottom_up_cut_rod() {
        return 0;
    }

    public void extended_bottom_up_cut_rod() {
        return 0;
    }
	
	public void print_cut_rod_solution () {
		for (int i = 0; i <= n; i++) {
			System.out.print(i + "\t");
		}
		System.out.print("\n");
		for (int i = 0; i <= n; i++) {
			System.out.print(r[i] + "\t");
		}
		System.out.print("\n");
		for (int i = 0; i <= n; i++) {
			System.out.print(s[i] + "\t");
		}
		System.out.print("\n");
	}

	public static void main(String[] args) {
		RodCut rc = new RodCut();
		System.out.println(rc.memoized_cut_rod());
		System.out.println(rc.bottom_up_cut_rod());
		rc.extended_bottom_up_cut_rod();
		rc.print_cut_rod_solution();
	}
}