import "./sanity.spec";

methods {
    function balanceOf(address) external returns (uint256) envfree;
    function allowance(address owner, address spender) external returns (uint256) envfree;
    function increaseAllowance(address spender,uint256 addedValue) external returns (bool);
    function decreaseAllowance(address spender, uint256 subtractedValue) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
    function permit(address owner,address spender, uint256 amount, uint256 deadline, uint8 v, bytes32 r, bytes32 s) external; 
    function burn(uint256 _amount) external;
    function totalSupply() external returns (uint256) envfree;
}

// @audit this is used for ensuring there's at last one non-reverting path through contract functions
use rule sanity;

// @audit check to show integrity of minting function
rule mintIntegrity(env e) {
    address account;
    address user;
    uint256 amount;

    uint256 accountBalanceBefore = balanceOf(account);
    uint256 userBalanceBefore = balanceOf(user);

    mint(e, account, amount);

    uint256 accountBalanceAfter = balanceOf(account);
    uint256 userBalanceAfter = balanceOf(user);

    assert to_mathint(accountBalanceAfter) == accountBalanceBefore + amount;        // checking that account's balance was properly updated
    assert user != account => userBalanceBefore == userBalanceAfter;                // checking that other users' balances were not affected
}

// @audit check to show transfer integrity
// @audit need to add a check that ensures only owner or permitted user can transfer tokens
rule transferIntegrity(env e, address recipient, uint amount) {
    mathint balance_sender_before = balanceOf(e.msg.sender);
    mathint balance_recipient_before = balanceOf(recipient);

    transfer(e, recipient, amount);

    mathint balance_sender_after = balanceOf(e.msg.sender);
    mathint balance_recipient_after = balanceOf(recipient);

    address sender = e.msg.sender;

    assert recipient != sender => balance_sender_after == balance_sender_before - amount,
        "transfer must decrease sender's balance by amount";

    assert recipient != sender => balance_recipient_after == balance_recipient_before + amount,
        "transfer must increase recipient's balance by amount";
    
    assert recipient == sender => balance_sender_after == balance_sender_before,
        "transfer must not change sender's balancer when transferring to self";
}

// @audit verifying that only the owner or someone approved by them can call 
// this should be conducive to a parametric test that checks all functions to ensure only approved accounts can increase balance
// requirements:
// 1. should decrease sender's allowance unless they're approved for max
// 2. should decrease owner's balance and increase recipient's balance
rule transferFromIntegrity(env e, address owner, address recipient, uint amount) {
    address sender = e.msg.sender;

    mathint balance_owner_before = balanceOf(owner);
    mathint balance_recipient_before = balanceOf(recipient);
    mathint allowance_sender_before = allowance(owner, sender);

    transferFrom(e, owner, recipient, amount);

    mathint balance_owner_after = balanceOf(owner);
    mathint balance_recipient_after = balanceOf(recipient);
    mathint allowance_sender_after = allowance(owner, sender);

    mathint max = 2^256 - 1;
    
    // need to check that sender allowance is decreased and recipient's balance is increased
    // only decrease sender appproval if they're not owner and not approved for max
    assert owner != sender && allowance_sender_before != max => allowance_sender_after == allowance_sender_before - amount,
        "transferFrom must decrease sender allowance";
    
    assert recipient != owner => balance_owner_after == balance_owner_before - amount,
        "transfer must decrease owner's balance by amount";

    assert recipient != owner => balance_recipient_after == balance_recipient_before + amount,
        "transfer must increase recipient's balance by amount";
    
    assert recipient == owner => balance_owner_after == balance_owner_before,
        "transfer must not change owner's balancer when transferring to self";
}

// @audit ensures that user's approval is properly modified
// need to ensure that the approval only changes for calls to increaseAllowance
rule increaseAllowanceIntegrity(env e, address owner, address spender, uint addedValue) {
    method f;
    calldataarg args;
    
    mathint allowance_before = allowance(owner, spender);

    // f(e, args);
    increaseAllowance(e, spender, addedValue);

    mathint allowance_after = allowance(owner, spender);

    address sender = e.msg.sender;

    assert sender != owner => allowance_before == allowance_after, 
        "nonowner can't increase spender's balance";

    assert sender == owner => allowance_after == allowance_before + addedValue,
        "balance must increase for nonzero addedValue";

    // @audit using parametric method finds that allowance is only ever increased when explicitly called by owner 
    // or when a signed message increases it 
    // assert allowance_after > allowance_before => sender == owner || sender ,
    //     "allowance must be increased by owner";
}

rule decreaseAllowanceIntegrity(env e, address owner, address spender, uint subtractedValue) {
    method f;
    calldataarg args;
    
    mathint allowance_before = allowance(owner, spender);

    // f(e, args);
    decreaseAllowance(e, spender, subtractedValue);

    mathint allowance_after = allowance(owner, spender);

    address sender = e.msg.sender;

    assert sender != owner => allowance_before == allowance_after, 
        "nonowner can't decrease spender's balance";

    assert sender == owner => allowance_after == allowance_before - subtractedValue,
        "balance must decrease for subtractedValue";

    // @audit using parametric method finds that allowance is only ever increased when explicitly called by owner 
    // or when a signed message increases it 
    // assert allowance_after > allowance_before => sender == owner || sender ,
    //     "allowance must be increased by owner";
}

// @audit offers same functionality as increase/decreaseAllowance so verification logic is the same
// modifies approved amount for a spender with msg.sender as the owner
rule approveIntegrity(env e, address spender, uint amount) {
    address owner = e.msg.sender;

    uint allowance_before = allowance(owner, spender);

    approve(e, spender, amount);

    uint allowance_after = allowance(owner, spender);

    assert allowance_after == amount,
        "balance must increase for nonzero addedValue";
}

// @audit add check to ensure that signature approval works corectly
// requirements:
// 1. only valid signatures should be accepted (this is checked by the contract)
// 2. approval should increase 
rule permitIntegrity(env e, address owner, address spender, uint amount, uint deadline, uint8 v, bytes32 r, bytes32 s) {
    uint allowance_spender_before = allowance(owner, spender);

    permit(e, owner, spender, amount, deadline, v, r, s);

    uint allowance_spender_after = allowance(owner, spender);

    assert allowance_spender_after == amount,
        "spender's allowance must be amount after permit is called";
}

// @audit burn integrity test
// requirements: 
// 1. when an amount is burned it should decrease the total supply
rule burnIntegrity(env e, uint amount) {
    mathint total_supply_before = totalSupply();

    burn(e, amount);

    mathint total_supply_after = totalSupply();

    assert total_supply_after == total_supply_before - amount,
        "total supply must be reduced by amount";
}