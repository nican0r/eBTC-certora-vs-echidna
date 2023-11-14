import "./sanity.spec";
import "./erc20.spec";


using CollateralTokenTester as collateral;
using DummyERC20Impl as tokenToSweep;

methods {
    
    function call_isAuthorized(address user, uint32 functionSig) external  returns (bool) envfree;
    function borrowerOperationsAddress() external  returns (address) envfree;
    function getSurplusCollShares(address _account) external returns (uint256) envfree;
    function getTotalSurplusCollShares() external returns (uint256) envfree;
    function increaseSurplusCollShares(address _account, uint256 _amount) external envfree;
    function claimSurplusCollShares(address _account) external envfree;
    function feeRecipientAddress() external returns (address) envfree;
    // collateral methods
    function collateral.balanceOf(address) external returns (uint256) envfree;
    function collateral.sharesOf(address) external returns (uint256) envfree;

    function tokenToSweep.myAddress() external returns (address) envfree;
}

rule reachability(method f) {
    env e;
    calldataarg args;
    f(e,args);
    satisfy true;
}

rule changeToCollateralBalance(method f) {
    uint256 before = collateral.balanceOf(currentContract);
    env e;
    calldataarg args;
    f(e,args);
    uint256 after = collateral.balanceOf(currentContract);
    assert after < before =>  
        ( call_isAuthorized(e.msg.sender, f.selector) || e.msg.sender == borrowerOperationsAddress()); 
}

// verifies that surplus collateral is always increased ✅
rule increaseSurplusCollSharesIntegrity(address account, uint amount) {
    mathint collateral_balance_before = getSurplusCollShares(account);

    increaseSurplusCollShares(account, amount);

    mathint collateral_balance_after = getSurplusCollShares(account);

    assert collateral_balance_after == collateral_balance_before + amount;
}

// verify that claiming surplus collateral transfers correct amount to user ✅
rule claimSurplusCollSharesIntegrity(env e, address account) {
    mathint balance_coll_shares_before = getSurplusCollShares(account);
    mathint balance_coll_token_before = collateral.balanceOf(account);


    claimSurplusCollShares(account);

    mathint balance_coll_shares_after = getSurplusCollShares(account);
    mathint balance_coll_token_after = collateral.balanceOf(account);

    // checks that all shares are removed from account's balance
    assert balance_coll_shares_after == 0,
        "claiming surplus shares should transfer all shares";
    
    assert balance_coll_token_after == balance_coll_token_before + balance_coll_shares_before,
        "claiming surplus shares should transfer collateral token to account";
}

// verify that increasing total surplus collateral shares increases ✅
rule increaseTotalSurplusCollSharesIntegrity(env e, uint value) {
    mathint total_surplus_shares_before = getTotalSurplusCollShares();

    increaseTotalSurplusCollShares(e, value);

    mathint total_surplus_shares_after = getTotalSurplusCollShares();

    assert total_surplus_shares_after == total_surplus_shares_before + value;
}

// calling sweepToken sends the stuck token to fee recipient address ✅ 
rule sweepTokenIntegrity(env e, uint256 amount) {
    address fee_recipient = feeRecipientAddress();
    address sweep_token_address = tokenToSweep.myAddress();

    mathint pool_balance_before = tokenToSweep.balanceOf(e, currentContract);
    mathint fee_recipient_balance_before = tokenToSweep.balanceOf(e, fee_recipient);

    sweepToken(e, sweep_token_address, amount);

    mathint pool_balance_after = tokenToSweep.balanceOf(e, currentContract);
    mathint fee_recipient_balance_after = tokenToSweep.balanceOf(e, fee_recipient);

    assert pool_balance_after == pool_balance_before - amount,
        "token didn't leave pool balance";
    assert fee_recipient_balance_after == fee_recipient_balance_before + amount,
        "fee recipient didn't receive swept tokens";
}