package M4;

import java.util.*;

public class Sort {
	
	
public static int[] insertionSort (int[] array) {
    if (array == null) return null;

    for (int j = 1; j < array.length; j++) {
        int key = array[j];
        int i = j - 1;

        while (i >= 0 && array[i] > key) {
            array[i + 1] = array[i];
            i--;
        }

        array[i + 1] = key;
    }

    return array;


	}
	
	public int[] merge_sort (int[] array, int p, int r) {
		/*
		 * fill in your program
		 */
		return array;
	}
	
	public int[] merge (int[] array, int p, int q, int r) {
		/*
		 * fill in your program
		 */
		return array;
	}
	
	public int[] quick_sort (int[] array, int p, int r) {
		/*
		 * fill in your program
		 */
		return array;
	}
	
	public int partition (int[] array, int p, int r) {
		/*
		 * fill in your program
		 */
		return 0;
	}
	
	
	/*
	 * n: the size of the output array
	 * k: the maximum value in the array
	 */
	public int[] generate_random_array (int n, int k) {
		List<Integer> list;
		int[] array;
		Random rnd;
		
		rnd = new Random(System.currentTimeMillis());
		
		list = new ArrayList<Integer> ();
		for (int i = 1; i <= n; i++) 
			list.add(Integer.valueOf(rnd.nextInt(k+1)));
		
		Collections.shuffle(list, rnd);
		
		array = new int[n];
		for (int i = 0; i < n; i++) 
			array[i] = list.get(i).intValue();
		
		return array;
	}
	
	/*
	 * n: the size of the output array
	 */
	public int[] generate_random_array (int n) {
		List<Integer> list;
		int[] array;
		
		list = new ArrayList<Integer> ();
		for (int i = 1; i <= n; i++) 
			list.add(Integer.valueOf(i));
		
		Collections.shuffle(list, new Random(System.currentTimeMillis()));
		
		array = new int[n];
		for (int i = 0; i < n; i++) 
			array[i] = list.get(i).intValue();
		
		return array;
	}
	
	/*
	 * Input: an integer array
	 * Output: true if the array is acsendingly sorted, otherwise return false
	 */
	public boolean check_sorted (int[] array) {
		for (int i = 1; i < array.length; i++) {
			if (array[i-1] > array[i])
				return false;
		}
		return true;
	}
	
	public void print_array (int[] array) {
		for (int i = 0; i < array.length; i++)
			System.out.print(array[i] + ", ");
		System.out.println();
	}
	
	public static void main(String[] args) {
		// TODO Auto-generated method stub		
		Sort obj = new Sort();
		System.out.println("Insertion sort starts ------------------");
		for (int n = 100000; n <= 1000000; n=n+100000) {
			int[] array = obj.generate_random_array(n);
			long t1 = System.currentTimeMillis();
			array = obj.insertionSort(array);
			long t2 = System.currentTimeMillis();
			long t = t2 - t1;
			boolean flag = obj.check_sorted(array);
			System.out.println(n + "," + t + "," + flag);
		}
		System.out.println("Insertion sort ends ------------------");
		
		System.out.println("Merge sort starts ------------------");
		for (int n = 100000; n <= 1000000; n=n+100000) {
			int[] array = obj.generate_random_array(n);
			//Sort.print_array(array);
			long t1 = System.currentTimeMillis();
			array = obj.merge_sort(array, 0, n-1);
			long t2 = System.currentTimeMillis();
			long t = t2 - t1;
			//Sort.print_array(array);
			boolean flag = obj.check_sorted(array);
			System.out.println(n + "," + t + "," + flag);
		}
		System.out.println("Merge sort ends ------------------");
		
		System.out.println("Quick sort starts ------------------");
		for (int n = 100000; n <= 1000000; n=n+100000) {
			int[] array = obj.generate_random_array(n);
			long t1 = System.currentTimeMillis();
			array = obj.quick_sort(array, 0, n-1);
			long t2 = System.currentTimeMillis();
			long t = t2 - t1;
			boolean flag = obj.check_sorted(array);
			System.out.println(n + "," + t + "," + flag);
		}
		System.out.println("Quick sort ends ------------------");
		
	}

}
