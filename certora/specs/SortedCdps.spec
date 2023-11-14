

/*

verification of SortedCdps
This is an advnaced project and requires probably qunatifiers and more summarization.
see https://github.com/Certora/Examples/tree/master/CVLByExample/QuantifierExamples 


*/
methods {
    function contains(bytes32 _id) external  returns (bool) envfree;

    function isFull() external  returns (bool) envfree; 

    function isEmpty() external  returns (bool) envfree;

    function getSize() external  returns (uint256) envfree;

    function getMaxSize() external  returns (uint256) envfree;

    function getFirst() external  returns (bytes32) envfree;

    function getLast() external  returns (bytes32) envfree;

    function getNext(bytes32 _id) external  returns (bytes32) envfree;

    function getPrev(bytes32 _id) external  returns (bytes32) envfree;

    function borrowerOperationsAddress() external returns (address) envfree;

    function cdpManager() external returns (address) envfree;

    /* summarizing as a deterministic and unique function. need to prove that this.
        see certora/specs/SortedCdps_DpdIds.spec 
    */
    // @audit this tells the tool to use the uniqueId ghost function as a summary for the toCdpId function from the contract
    function toCdpId(
        address owner,
        uint256 blockHeight,
        uint256 nonce
    ) internal returns (bytes32) => uniqueId(owner,blockHeight,nonce);

    function toCdpId(
        address owner,
        uint256 blockHeight,
        uint256 nonce
    ) external returns (bytes32) envfree;


    // CdpManager
    /* placeholder - NONDET is the default (safe) summarization but might be 
    too over apporximation for certrain properties
    */
    // @audit NONDET makes no assumption about return values so each call to the method can return a different result
    // using _ applies to methods in all contracts with the given signature
    function _.getNominalICR(bytes32) external  => NONDET;
    function _.getCdpStatus(bytes32) external => NONDET;

}

ghost uniqueId(address /*owner*/, uint256 /*blockHeight*/, uint256 /*nonce*/ ) returns bytes32 {
    // @audit this axiom constrains the behavior of the ghost function such that owner, blockheight and nonce are never equivalent for a uniqueId
    axiom forall address o1. forall address o2. 
    forall uint256 b1. forall uint256 b2.
    forall uint256 n1. forall uint256 n2.
    ( o1 != o2 || b1 != b2 || n1 != n2 ) => uniqueId(o1, b1, n1) != uniqueId(o2, b2, n2);
}

rule uniqunessOfId(address o1,  address o2,
        uint256 b1,  uint256 b2, 
        uint256 n1,  uint256 n2) 
{
// calls to toCdpId are to the public solidity function which calls the internal one that is summarized
// therefore, this rule actually checks the summarization uniqueId 
// @audit when a contract contains a public method, the Solidity compiler generates an internal method that executes the code, 
// and an external method that calls the internal method so this is essentially overriding the interface of the contract and making the external method call the internal method that's been defined,
// which calls the summarized ghost function instead of the contract itself

assert ( o1 != o2 || b1 != b2 || n1 != n2 ) => toCdpId(o1, b1, n1) != toCdpId(o2, b2, n2);
}
    

rule reachability(method f) {
    env e;
    calldataarg args;
    f(e,args);
    satisfy true;
}


rule changeToFirst(method f) {
    bytes32 before = getFirst();

    env e;
    calldataarg args;
    f(e,args);

    bytes32 after = getFirst();
    assert after != before =>
        (   f.selector == sig:insert(address,uint256,bytes32,bytes32).selector ||  
            f.selector == sig:reInsert(bytes32,uint256,bytes32,bytes32).selector ||
            f.selector == sig:remove(bytes32).selector ||
            f.selector == sig:batchRemove(bytes32[]).selector ); 
}

rule isFullCanNotIncrease(method f) {
    bool isFullBefore = isFull();
    uint256 sizeBefore = getSize();

    env e;
    calldataarg args;
    f(e,args);

    // @audit asserting that if the list is full before adding,
    // after calling a method the size should have stayed the same or decreased
    assert  isFullBefore =>  getSize() <= sizeBefore ;
}

// verify that the caller of a method that modifies the CDP list is correctly authorized to call it ✅
rule isAllowedToModifyCDPList(env e, method f, calldataarg args) {
    address cdpManager_address = cdpManager();
    address borrower_operations_address = borrowerOperationsAddress(); 
    address sender = e.msg.sender;
    // upon calling any public method that modifies state the msg.sender should either be the BorrowerOperations or CDPManager contract
    // can use the list length change if a node is being added/removed but how can this be extended to check if an existing node has been modified?
    // if the list length is the same then know that the order of the list must have changed if a node's position is changed, therefore its index should change too
    uint size_before = getSize();

    f(e, args);
    
    uint size_after = getSize();

    // both CDPManager and BorrowerOperations can add/modify nodes
    assert size_after > size_before => 
        sender == cdpManager_address 
    ||  sender == borrower_operations_address,
        "only CDPManager or BorrowerOperations can add nodes";

    // only CDPManager can remove nodes
    assert size_after < size_before => 
        sender == cdpManager_address,
        "only CDPManager can remove nodes";
    
}

// @audit invariant asserting that after every call the size of the linked list doesn't exceed the max size
invariant maxSizeIntegrity() 
    getSize() <= getMaxSize();




// properties of the linked list to verify:
// 1. inserting a CDP places it in the right position
// 2. removing a node preserves the ordering of the list and rearranges pointers
// 3. inserting a new starting CDP (lowest ICR) places it as next of the head
// 4. inserting a new ending CDP (highest ICR) places it as prev of tail


// GHOST COPIES - used to recreate the functionality of the methods of the contract without requiring evaluating each

// ghostNextId and ghostPrevId are copies of the Node struct
ghost mapping(bytes32 => bytes32) ghostNextId {
    init_state axiom forall bytes32 x. ghostNextId[x] == to_bytes32(0);
}
ghost mapping(bytes32 => bytes32) ghostPrevId {
    init_state axiom forall bytes32 x. ghostPrevId[x] == to_bytes32(0);
}

// ghostHead, ghostTail and ghostSize are copies of the Data struct 
ghost bytes32 ghostHead;
ghost bytes32 ghostTail;
// @audit need to figure out how to describe this 
ghost mathint ghostSize;
 // used for comparisons of bytes32 values to 0 because CVL doesn't allow comparison directly with 0

// @audit asserts that the linkedlist starts off empty by ensuring that ids of the nodes are equivalent
// the id of the only node initially should be 0 since it's the default value of bytes32
ghost nextstar(bytes32, bytes32) returns bool {
    init_state axiom forall bytes32 x. forall bytes32 y. nextstar(x, y) == (x == y);
}
ghost prevstar(bytes32, bytes32) returns bool {
    init_state axiom forall bytes32 x. forall bytes32 y. prevstar(x, y) == (x == y);
}


// HOOKS - used to attach the CVL spec to the low-level operations in specific storage slots

// storing hooks

// sets the ghostHead/ghostTail using the values passed in
hook Sstore currentContract.data.head bytes32 newHead STORAGE {
    ghostHead = newHead;
}
hook Sstore currentContract.data.tail bytes32 newTail STORAGE {
    ghostTail = newTail;
}

// whenever a node is added it should increase the size of the list by 1
// should only update the size when a new node is inserted, not during collateral update
// if a node already exists its value in the nodes mapping would be nonzero so can check for this before increasing size
hook Sstore currentContract.data.nodes[KEY bytes32 id].nextId bytes32 newNext STORAGE {
    ghostNextId[id] = newNext;
}
hook Sstore currentContract.data.nodes[KEY bytes32 id].prevId bytes32 newPrev STORAGE {
    ghostPrevId[id] = newPrev;
}
hook Sstore currentContract.data.size uint256 newSize STORAGE {
    ghostSize = newSize;
}

// loading hooks

hook Sload bytes32 head currentContract.data.head STORAGE {
    require ghostHead == head;
}
hook Sload bytes32 tail currentContract.data.tail STORAGE {
    require ghostTail == tail;
}
hook Sload bytes32 next currentContract.data.nodes[KEY bytes32 id].nextId STORAGE {
    require ghostNextId[id] == next;
}
hook Sload bytes32 prev currentContract.data.nodes[KEY bytes32 id].prevId STORAGE {
    require ghostPrevId[id] == prev;
}
hook Sload uint size currentContract.data.size STORAGE {
    require ghostSize == to_mathint(size);
}


// INVARIANTS

invariant nextPrevMatch()
    // list is empty, head, tail and size are 0,
    ((ghostHead == to_bytes32(0) && ghostTail == to_bytes32(0) && ghostSize == 0)
    // or both head and tail are set and their prev (head) or next (tail) points to 0 and the size of the list > 0
    || (ghostHead != to_bytes32(0) && ghostTail != to_bytes32(0) && ghostNextId[ghostTail] == to_bytes32(0) && ghostPrevId[ghostHead] == to_bytes32(0) && ghostSize > 0))
    // for all ids:
    && (forall bytes32 a.
           // either the id is not part of the list and every field is 0.
           (ghostNextId[a] == to_bytes32(0) && ghostPrevId[a] == to_bytes32(0))
           // or the id is part of the list, id is non-to_bytes32(0),
           // and prev and next pointer are linked correctly.
        || (a != to_bytes32(0)
            && ((a == ghostHead && ghostPrevId[a] == to_bytes32(0)) || ghostNextId[ghostPrevId[a]] == a)
            && ((a == ghostTail && ghostNextId[a] == to_bytes32(0)) || ghostPrevId[ghostNextId[a]] == a)));

// @audit need to find a way to adapt this using the different structure of this linked list
// invariant inList()
//     // @audit if ghostHead isn't 0, then its value in the mapping isn't 0
//     (ghostHead != 0 => ghostSize != 0)
//     // @audit if ghostTail isn't 0, then its value in the mapping isn't 0
//     && (ghostTail != 0 => ghostSize != 0)
//     // @audit for all values of a if the next node isn't 0, then the value of the next node also isn't 0
//     && (forall bytes32 a.  ghostNextId[a] != 0 => ghostValue[ghostNextId[a]] != 0)
//     // @audit for all values of a if the previous node isn't 0, then the value of the next node also isn't 0
//     && (forall bytes32 a.  ghostPrevId[a] != 0 => ghostValue[ghostPrevId[a]] != 0)
//     {
//         preserved {
//             requireInvariant nextPrevMatch();
//         }
//     }

// @audit rule that checks that inserting preserves the value stored at the previous index ❌
rule insert_preserves_old(env e, address owner, bytes32 oldElem, bytes32 nextId,bytes32 prevId, uint nicr) {
    // if a value is in the list either its prev or next value != 0 or both

    require ghostSize > 0;

    bool oldInList = 
    (ghostSize == 1 && ghostNextId[oldElem] == to_bytes32(0) && ghostPrevId[oldElem] == to_bytes32(0)) // node is head and tail
    || (ghostNextId[oldElem] != to_bytes32(0) && ghostPrevId[oldElem] == to_bytes32(0)) // node is the head
    || (ghostPrevId[oldElem] != to_bytes32(0) && ghostNextId[oldElem] == to_bytes32(0)) // node is the tail
    || (ghostNextId[oldElem] != to_bytes32(0) &&  ghostPrevId[oldElem] != to_bytes32(0)); // node is not head or tail but in the list

    insert(e, owner, nicr, prevId, nextId);

    assert oldInList == ((ghostNextId[oldElem] != to_bytes32(0) && ghostPrevId[oldElem] == to_bytes32(0)) 
    || (ghostPrevId[oldElem] != to_bytes32(0) && ghostNextId[oldElem] == to_bytes32(0)) 
    || (ghostNextId[oldElem] != to_bytes32(0) &&  ghostPrevId[oldElem] != to_bytes32(0))),
    "previous nodes should be maintained in the list";
}

// if a node is inserted then after the size of the list should increase and the node should have neighbors that are nonzero
// only if the list is size 1 should the neighbors be 0 (it's the head and tail) ❌
rule insert_adds_new(env e, address owner, bytes32 oldElem, bytes32 nextId,bytes32 prevId, uint nicr) {
    bytes32 new_node_id = insert(e, owner, nicr, prevId, nextId);

    bool node_is_head_and_tail = (ghostNextId[new_node_id] == to_bytes32(0) && ghostPrevId[oldElem] == to_bytes32(0));


    assert ghostSize == 1 => node_is_head_and_tail == true,
        "node should be the head and tail when it's the only one in the list";

    assert ghostSize > 1 => (ghostNextId[new_node_id] != to_bytes32(0) || ghostPrevId[new_node_id] != to_bytes32(0)),
        "node should have one neighbor that isn't zero if it isn't the only node";
}