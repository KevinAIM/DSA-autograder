package harness;

import M5.Stack;
import M5.Queue;
import M5.LinkedList;
import M5.ListNode;
import M5.TreeNode;
import M5.BinarySearchTree;

public class Harness {
    public static void main(String[] args) {
        
BinarySearchTree bst = new BinarySearchTree();
int[] keys = {15, 6, 18, 3, 7, 17, 20, 2, 4, 13, 9};

// test insert - build the tree
for (int k : keys) {
    bst.insert(k);
}

if (bst.root == null || bst.root.key != 15) {
    System.out.println("{\"status\":\"fail\",\"class\":\"BinarySearchTree\",\"reason\":\"insert() failed, root should be 15\"}");
    return;
}

// test inorder_tree_walk - should print sorted order
java.io.ByteArrayOutputStream baos = new java.io.ByteArrayOutputStream();
java.io.PrintStream ps = new java.io.PrintStream(baos);
System.setOut(ps);
bst.inorder_tree_walk(bst.root);
System.setOut(new java.io.PrintStream(new java.io.FileOutputStream(java.io.FileDescriptor.out)));
String walkOutput = baos.toString().trim().replaceAll("\\s+", " ");
if (!walkOutput.equals("2 3 4 6 7 9 13 15 17 18 20")) {
    System.out.println("{\"status\":\"fail\",\"class\":\"BinarySearchTree\",\"reason\":\"inorder_tree_walk() failed, got \" + walkOutput}");
    return;
}

// test search
TreeNode found = bst.search(bst.root, 13);
if (found == null || found.key != 13) {
    System.out.println("{\"status\":\"fail\",\"class\":\"BinarySearchTree\",\"reason\":\"search(13) failed\"}");
    return;
}

// test iterative_search
TreeNode iFound = bst.iterative_search(4);
if (iFound == null || iFound.key != 4) {
    System.out.println("{\"status\":\"fail\",\"class\":\"BinarySearchTree\",\"reason\":\"iterative_search(4) failed\"}");
    return;
}

// test minimum
TreeNode min = bst.minimum();
if (min == null || min.key != 2) {
    System.out.println("{\"status\":\"fail\",\"class\":\"BinarySearchTree\",\"reason\":\"minimum() should return 2, got \" + (min == null ? \"null\" : min.key)}");
    return;
}

// test maximum
TreeNode max = bst.maximum();
if (max == null || max.key != 20) {
    System.out.println("{\"status\":\"fail\",\"class\":\"BinarySearchTree\",\"reason\":\"maximum() should return 20, got \" + (max == null ? \"null\" : max.key)}");
    return;
}

// test successor - successor of 13 should be 15
TreeNode node13 = bst.search(bst.root, 13);
TreeNode succ = bst.successor(node13);
if (succ == null || succ.key != 15) {
    System.out.println("{\"status\":\"fail\",\"class\":\"BinarySearchTree\",\"reason\":\"successor(13) should be 15, got \" + (succ == null ? \"null\" : succ.key)}");
    return;
}

System.out.println("{\"status\":\"pass\",\"class\":\"BinarySearchTree\"}");

    }
}
