from pathlib import Path
from adapters.base import Adapter

class M5DataStructuresAdapter(Adapter):

    def harness_main_class(self) -> str:
        return "harness.Harness"
    
    def methods(self) -> list:
        return [{"class_name": "Stack", "harness_type": "stack", "pseduo_code": """
STACK-EMPTY(S):
    if S.top == 0:          // check if stack has no elements
        return TRUE
    else return FALSE

PUSH(S, x):
    S.top = S.top + 1       // increment top pointer
    S[S.top] = x            // place new element at top

POP(S):
    if STACK-EMPTY(S):      // check if stack is empty before popping
        error "underflow"
    else:
        S.top = S.top - 1   // decrement top pointer
        return S[S.top + 1] // return the removed element
"""},
                {"class_name": "Queue", "harness_type": "queue", "pseduo_code": """
ENQUEUE(Q, x):
    Q[Q.tail] = x                       // place element at tail
    if Q.tail == Q.length:              // wrap around if at end
        Q.tail = 1
    else:
        Q.tail = Q.tail + 1

DEQUEUE(Q):
    x = Q[Q.head]                       // get element at head
    if Q.head == Q.length:              // wrap around if at end
        Q.head = 1
    else:
        Q.head = Q.head + 1
    return x
"""},
                {"class_name": "linkedList", "harness_type": "linkedList", "pseduo_code": """
LIST-SEARCH(L, k):
    x = L.head                          // start from head
    while x != NIL and x.key != k:     // traverse until found or end
        x = x.next
    return x                            // return node or NIL

LIST-INSERT(L, x):
    x.next = L.head                     // new node points to current head
    if L.head != NIL:                   // if list not empty
        L.head.prev = x                 // old head points back to new node
    L.head = x                          // update head to new node
    x.prev = NIL                        // new node has no predecessor

LIST-DELETE(L, x):
    if x.prev != NIL:                   // if not the first node
        x.prev.next = x.next            // bypass x from the left
    else:
        L.head = x.next                 // update head if deleting first node
    if x.next != NIL:                   // if not the last node
        x.next.prev = x.prev            // bypass x from the right
"""},
                {"class_name": "BinarySearchTree", "harness_type": "bst", "pseduo_code": """
INORDER-TREE-WALK(x):
    if x != NIL:                        // base case: empty subtree
        INORDER-TREE-WALK(x.left)       // visit left subtree first
        print x.key                     // print current node
        INORDER-TREE-WALK(x.right)      // visit right subtree last

TREE-SEARCH(x, k):
    if x == NIL or k == x.key:         // base case: not found or found
        return x
    if k < x.key:                      // search left subtree
        return TREE-SEARCH(x.left, k)
    else:                              // search right subtree
        return TREE-SEARCH(x.right, k)

ITERATIVE-TREE-SEARCH(x, k):
    while x != NIL and k != x.key:    // loop until found or end
        if k < x.key:                 // go left if key is smaller
            x = x.left
        else:                         // go right if key is larger
            x = x.right
    return x

TREE-MINIMUM(x):
    while x.left != NIL:              // keep going left
        x = x.left
    return x                          // leftmost node is minimum

TREE-MAXIMUM(x):
    while x.right != NIL:             // keep going right
        x = x.right
    return x                          // rightmost node is maximum

TREE-SUCCESSOR(x):
    if x.right != NIL:                // if right subtree exists
        return TREE-MINIMUM(x.right)  // successor is leftmost in right subtree
    y = x.p                           // otherwise go up the tree
    while y != NIL and x == y.right:  // until we find a node we came from the left
        x = y
        y = y.p
    return y

TREE-INSERT(T, z):
    y = NIL                           // trailing pointer
    x = T.root                        // start from root
    while x != NIL:                   // find correct position
        y = x
        if z.key < x.key:            // go left if smaller
            x = x.left
        else:                         // go right if larger
            x = x.right
    z.p = y                           // set parent
    if y == NIL:                      // tree was empty
        T.root = z
    else if z.key < y.key:           // insert as left child
        y.left = z
    else:                             // insert as right child
        y.right = z
"""}]
    
def write_harness(self, harness_path: Path, method: dict) -> None:
    harness_type = method.get("harness_type")
    
    if harness_type == "stack":
        main_body = self._stack_main(method)
    elif harness_type == "queue":
        main_body = self._queue_main(method)
    elif harness_type == "linkedlist":
        main_body = self._linkedlist_main(method)
    elif harness_type == "bst":
        main_body = self._bst_main(method)

    code = f"""\
package harness;

import M5.Stack;
import M5.Queue;
import M5.LinkedList;
import M5.ListNode;
import M5.TreeNode;
import M5.BinarySearchTree;

public class Harness {{
    public static void main(String[] args) {{
        {main_body}
    }}
}}
"""
    harness_path.parent.mkdir(parents=True, exist_ok=True)
    harness_path.write_text(code, encoding="utf-8")

    def _stack_main(self, method):
        return f"""
Stack s = new Stack(10);

// test empty() on fresh stack
if (!s.empty()) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"Stack\\",\\"reason\\":\\"empty() should return true on new stack\\"}}");
    return;
}}

// test push() and empty()
s.push(1);
s.push(2);
s.push(3);

if (s.empty()) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"Stack\\",\\"reason\\":\\"empty() should return false after pushing\\"}}");
    return;
}}

if (s.top != 2) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"Stack\\",\\"reason\\":\\"top should be 2 after 3 pushes, got \\" + s.top}}");
    return;
}}

// test pop()
int val = s.pop();
if (val != 3) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"Stack\\",\\"reason\\":\\"pop() should return 3, got \\" + val}}");
    return;
}}

if (s.top != 1) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"Stack\\",\\"reason\\":\\"top should be 1 after pop, got \\" + s.top}}");
    return;
}}

// test pop on empty stack returns -1
s.pop(); s.pop();
int emptyPop = s.pop();
if (emptyPop != -1) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"Stack\\",\\"reason\\":\\"pop() on empty stack should return -1, got \\" + emptyPop}}");
    return;
}}

System.out.println("{{\\"status\\":\\"pass\\",\\"class\\":\\"Stack\\"}}");
"""

    def _stack_main(self, method):
        return f"""
Queue q = new Queue(10);

// test enqueue
q.enqueue(1);
q.enqueue(2);
q.enqueue(3);

if (q.tail != 3) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"Queue\\",\\"reason\\":\\"tail should be 3 after 3 enqueues, got \\" + q.tail}}");
    return;
}}

// test dequeue returns correct value
int val = q.dequeue();
if (val != 1) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"Queue\\",\\"reason\\":\\"dequeue() should return 1 (FIFO), got \\" + val}}");
    return;
}}

// test head advanced
if (q.head != 1) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"Queue\\",\\"reason\\":\\"head should be 1 after dequeue, got \\" + q.head}}");
    return;
}}

// test second dequeue
int val2 = q.dequeue();
if (val2 != 2) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"Queue\\",\\"reason\\":\\"dequeue() should return 2, got \\" + val2}}");
    return;
}}

System.out.println("{{\\"status\\":\\"pass\\",\\"class\\":\\"Queue\\"}}");
"""
    
    def _linkedlist_main(self, method):
        return f"""
LinkedList l = new LinkedList();

// test insert - inserts at front so order is reversed
l.insert(1);
l.insert(2);
l.insert(3);

// test toString to verify structure
String listStr = l.toString();
if (!listStr.equals("[3,2,1,]")) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"LinkedList\\",\\"reason\\":\\"insert() failed, expected [3,2,1,] got \\" + listStr}}");
    return;
}}

// test search - should find existing node
ListNode found = l.search(2);
if (found == null || found.key != 2) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"LinkedList\\",\\"reason\\":\\"search(2) failed, expected node with key 2\\"}}");
    return;
}}

// test search - should return null for missing key
ListNode notFound = l.search(99);
if (notFound != null) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"LinkedList\\",\\"reason\\":\\"search(99) should return null\\"}}");
    return;
}}

// test delete - remove middle node
l.delete(found);
String afterDelete = l.toString();
if (!afterDelete.equals("[3,1,]")) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"LinkedList\\",\\"reason\\":\\"delete() failed, expected [3,1,] got \\" + afterDelete}}");
    return;
}}

System.out.println("{{\\"status\\":\\"pass\\",\\"class\\":\\"LinkedList\\"}}");
"""
    
    def _bst_main(self, method):
        return f"""
BinarySearchTree bst = new BinarySearchTree();
int[] keys = {{15, 6, 18, 3, 7, 17, 20, 2, 4, 13, 9}};

// test insert - build the tree
for (int k : keys) {{
    bst.insert(k);
}}

if (bst.root == null || bst.root.key != 15) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"BinarySearchTree\\",\\"reason\\":\\"insert() failed, root should be 15\\"}}");
    return;
}}

// test inorder_tree_walk - should print sorted order
java.io.ByteArrayOutputStream baos = new java.io.ByteArrayOutputStream();
java.io.PrintStream ps = new java.io.PrintStream(baos);
System.setOut(ps);
bst.inorder_tree_walk(bst.root);
System.setOut(new java.io.PrintStream(new java.io.FileOutputStream(java.io.FileDescriptor.out)));
String walkOutput = baos.toString().trim().replaceAll("\\\\s+", " ");
if (!walkOutput.equals("2 3 4 6 7 9 13 15 17 18 20")) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"BinarySearchTree\\",\\"reason\\":\\"inorder_tree_walk() failed, got \\" + walkOutput}}");
    return;
}}

// test search
TreeNode found = bst.search(bst.root, 13);
if (found == null || found.key != 13) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"BinarySearchTree\\",\\"reason\\":\\"search(13) failed\\"}}");
    return;
}}

// test iterative_search
TreeNode iFound = bst.iterative_search(4);
if (iFound == null || iFound.key != 4) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"BinarySearchTree\\",\\"reason\\":\\"iterative_search(4) failed\\"}}");
    return;
}}

// test minimum
TreeNode min = bst.minimum();
if (min == null || min.key != 2) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"BinarySearchTree\\",\\"reason\\":\\"minimum() should return 2, got \\" + (min == null ? \\"null\\" : min.key)}}");
    return;
}}

// test maximum
TreeNode max = bst.maximum();
if (max == null || max.key != 20) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"BinarySearchTree\\",\\"reason\\":\\"maximum() should return 20, got \\" + (max == null ? \\"null\\" : max.key)}}");
    return;
}}

// test successor - successor of 13 should be 15
TreeNode node13 = bst.search(bst.root, 13);
TreeNode succ = bst.successor(node13);
if (succ == null || succ.key != 15) {{
    System.out.println("{{\\"status\\":\\"fail\\",\\"class\\":\\"BinarySearchTree\\",\\"reason\\":\\"successor(13) should be 15, got \\" + (succ == null ? \\"null\\" : succ.key)}}");
    return;
}}

System.out.println("{{\\"status\\":\\"pass\\",\\"class\\":\\"BinarySearchTree\\"}}");
"""