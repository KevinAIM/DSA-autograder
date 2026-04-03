package harness;

import M5.Stack;
import M5.Queue;
import M5.LinkedList;
import M5.ListNode;
import M5.TreeNode;
import M5.BinarySearchTree;

public class Harness {
    public static void main(String[] args) {
        
LinkedList l = new LinkedList();

// test insert - inserts at front so order is reversed
l.insert(1);
l.insert(2);
l.insert(3);

// test toString to verify structure
String listStr = l.toString();
if (!listStr.equals("[3,2,1,]")) {
    System.out.println("{\"status\":\"fail\",\"class\":\"LinkedList\",\"reason\":\"insert() failed, expected [3,2,1,] got \" + listStr}");
    return;
}

// test search - should find existing node
ListNode found = l.search(2);
if (found == null || found.key != 2) {
    System.out.println("{\"status\":\"fail\",\"class\":\"LinkedList\",\"reason\":\"search(2) failed, expected node with key 2\"}");
    return;
}

// test search - should return null for missing key
ListNode notFound = l.search(99);
if (notFound != null) {
    System.out.println("{\"status\":\"fail\",\"class\":\"LinkedList\",\"reason\":\"search(99) should return null\"}");
    return;
}

// test delete - remove middle node
l.delete(found);
String afterDelete = l.toString();
if (!afterDelete.equals("[3,1,]")) {
    System.out.println("{\"status\":\"fail\",\"class\":\"LinkedList\",\"reason\":\"delete() failed, expected [3,1,] got \" + afterDelete}");
    return;
}

System.out.println("{\"status\":\"pass\",\"class\":\"LinkedList\"}");

    }
}
