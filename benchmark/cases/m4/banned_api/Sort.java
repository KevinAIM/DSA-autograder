package M4;

import java.io.File;
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
		if (p < r) {
			int q = (p + r) / 2;
			merge_sort(array, p, q);
			merge_sort(array, q + 1, r);
			merge(array, p, q, r);
		}
		return array;
	}
	
	public int[] merge (int[] array, int p, int q, int r) {
	    int n1 = q - p + 1;
		int n2 = r - q;
		int[] L = new int[n1];
		int[] R = new int[n2];
		for (int i = 0; i < n1; i++) L[i] = array[p + i];
		for (int j = 0; j < n2; j++) R[j] = array[q + 1 + j];
		int i = 0, j = 0, k = p;
		while (i < n1 && j < n2) {
			if (L[i] <= R[j]) array[k++] = L[i++];
			else array[k++] = R[j++];
		}
		while (i < n1) array[k++] = L[i++];
		while (j < n2) array[k++] = R[j++];
		return array;
	}
	
	public int[] quick_sort (int[] array, int p, int r) {
		if (p < r) {
			int q = partition(array, p, r);
			quick_sort(array, p, q - 1);
			quick_sort(array, q + 1, r);
		}
		return array;
	}
	
	public int partition (int[] array, int p, int r) {
		int x = array[r];
		int i = p - 1;
		for (int j = p; j < r; j++) {
			if (array[j] <= x) {
				i++;
				int temp = array[i];
				array[i] = array[j];
				array[j] = temp;
			}
		}
		int temp = array[i + 1];
		array[i + 1] = array[r];
		array[r] = temp;
		return i + 1;
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
