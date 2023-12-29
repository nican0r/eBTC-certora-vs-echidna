using EBTCToken as token;
using SortedCdps as sortedCdps;
using CollSurplusPool as collSurplusPool;

methods {
    function token.balanceOf(address) external returns (uint256) envfree;
    function token.totalSupply() external returns (uint256) envfree;
    function sortedCdps._ external => NONDET;
    function collSurplusPool._ external => NONDET;
    function _.locked() external => CONSTANT;
    function _.getOwnerAddress(address) external => PER_CALLEE_CONSTANT;
    function _.increaseTotalSurplusCollShares(uint256) external => NONDET;

    function repayDebt(bytes32, uint256, bytes32, bytes32) external;
}

// @audit successfully passes! No reason to assume it's vacuous 

/** Property 2: 
    eBTC tokens are burned upon repayment of a CDP's debt
**/
// @audit repayDebt can also be called by someone other than the CDP owner so need to check this as well
// @audit for failing counterexample: might need to define a ghost variable that tracks balance to make sure that it's properly updated 
rule burnAfterRepayIntegrity(bytes32 _cdpId, uint256 _debt, bytes32 _upperHint, bytes32 _lowerHint) {
    env e;
    address caller = e.msg.sender;
    // get caller's eBTC balance before
    uint256 token_balance_before = token.balanceOf(caller);
    uint256 total_supply = token.totalSupply();

    // preconditions: ensure that the debt of a cdp is <= user's eBTC balance and balance is less than totalSupply
    // filters cases where the caller is the 0 address or the current contract
    require token_balance_before >= _debt && token_balance_before <= total_supply;
    require caller != 0 && caller != currentContract;

    // repay the debt
    repayDebt(e, _cdpId, _debt, _upperHint, _lowerHint);

    uint256 token_balance_after = token.balanceOf(caller);
    // assert that user's eBTC balance after should be changed by the amount of debt paid
    assert to_mathint(token_balance_after) == token_balance_before - _debt,
        "user's eBTC balance should decrease after burning";
}