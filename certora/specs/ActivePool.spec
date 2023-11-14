import "./sanity.spec";
import "./erc20.spec";

using CollateralTokenTester as collateralToken;
using  MockFlashBorrower as mockFlashBorrower;

methods {
    function _.increaseTotalSurplusCollShares(uint256) external => DISPATCHER(true);
    function _.onFlashLoan(address, address, uint256, uint256, bytes) external => DISPATCHER(true);
    
    function transferSystemCollShares(address, uint256) external;
    function transferSystemCollSharesAndLiquidatorReward(address, uint256, uint256) external envfree;
    function getSystemCollShares() external returns (uint256) envfree;
    function getFeeRecipientClaimableCollShares() external returns (uint256) envfree;
    function getSystemDebt() external returns (uint256) envfree;
    function increaseSystemDebt(uint256) external envfree;
    function decreaseSystemDebt(uint256) external envfree;
    function increaseSystemCollShares(uint256 ) external envfree;
    function allocateSystemCollSharesToFeeRecipient(uint256 _shares) external envfree;
    function flashLoan(address receiver, address token, uint256 amount, bytes data) external returns (bool) envfree;
    function claimFeeRecipientCollShares(uint256) external envfree;
    function flashFee(address token, uint256 amount) external returns (uint256) envfree;
    function feeRecipientAddress() external returns (address) envfree;
    function maxFlashLoan(address token) external returns (uint256);
    function sweepToken(address token, uint256 amount) external envfree;
    function collateral() external returns (address) envfree;

    function collateralToken.balanceOf(address) external returns (uint256) envfree; 
    // function _.balanceOf(address) external => DISPATCHER(true); //is this the correct way of defining an interface for an unknown contract? 
}

use rule sanity;


// @audit invariant: total stETH balance of the system always exceeds the deposits

// transferring systemCollShares properly accounts shares to account they were transferred to ✅ 
rule transferSystemCollSharesIntegrity(env e, address account, uint shares) {
    mathint system_shares_before = getSystemCollShares();

    // this test can be used for testing transfer with liquidator reward as well because the fundamental logic is the same 
    transferSystemCollShares(e, account, shares);

    mathint system_shares_after = getSystemCollShares();

    assert system_shares_after == system_shares_before - shares,
        "shares after should decrease after transfer";
}

// transferring systemCollShares and liquidatorRewardShares to an account is properly accounted for account ✅ 
rule transferSystemCollSharesAndLiquidatorRewardIntegrity(env e, address account, uint shares, uint liquidatorRewardShares) {
    mathint system_shares_before = getSystemCollShares();

    // liquidator reward gets transferred with systemCollShares
    transferSystemCollSharesAndLiquidatorReward(e, account, shares, liquidatorRewardShares);

    mathint system_shares_after = getSystemCollShares();

    assert system_shares_after == system_shares_before - shares,
        "shares after should decrease after transfer";
}

// fee recipient shares are properly allocated and removed from systemCollShares ✅
rule allocateSystemCollSharesToFeeRecipientIntegrity(uint shares) {
    // check that cached shares are decreased and fee recipient shares increased
    mathint system_shares_before = getSystemCollShares();
    mathint fee_recipient_shares_before = getFeeRecipientClaimableCollShares();

    allocateSystemCollSharesToFeeRecipient(shares);

    mathint system_shares_after = getSystemCollShares();
    mathint fee_recipient_shares_after = getFeeRecipientClaimableCollShares();

    assert system_shares_after == system_shares_before - shares,
        "system shares must be decreased by share amount";
    assert fee_recipient_shares_after == fee_recipient_shares_before + shares,
        "fee recipient shares must be increased by share amount";
}

// verify that increasing debt works ✅
rule increaseSystemDebtIntegrity(uint amount) {
    mathint system_debt_before = getSystemDebt();

    increaseSystemDebt(amount);

    mathint system_debt_after = getSystemDebt();

    assert system_debt_after == system_debt_before + amount, 
        "system debt not increased";
}

// verify that decreasing debt works ✅
rule decreaseSystemDebtIntegrity(uint amount) {
    mathint system_debt_before = getSystemDebt();

    decreaseSystemDebt(amount);

    mathint system_debt_after = getSystemDebt();

    assert system_debt_after == system_debt_before - amount, 
        "system debt not decreased";
}

// verify increasing collateral shares of system works ✅
rule increaseSystemCollSharesIntegrity(uint value) {
    mathint system_shares_before = getSystemCollShares();

    increaseSystemCollShares(value);

    mathint system_shares_after = getSystemCollShares();

    assert system_shares_after == system_shares_before + value;
}

// @audit verify that flashloan meets the following requirements ❌
// 1. is fully repaid within the transaction in which it's created (balance of eBTC/stETH in the pool shouldn't change)
// 2. fee is paid 
// rule flashLoanIntegrity(address receiver, address token, uint amount, bytes data)  {
//     address fee_recipient = feeRecipientAddress();
//     mathint fee = flashFee(token, amount);
    
//     mathint balance_pool_before = collateralToken.balanceOf(currentContract);
//     mathint balance_fee_recipient_before = collateralToken.balanceOf(fee_recipient);
    
//     flashLoan(receiver, token, amount, data);

//     // balance after should include the fee paid by the user
//     mathint balance_pool_after = collateralToken.balanceOf(currentContract);
//     mathint balance_fee_recipient_after = collateralToken.balanceOf(fee_recipient);

//     // taking balance of the collateralToken because it makes the address visible 
//     // @audit it looks like the addresses are correct and the collateralToken accessed is the same in spec as in contract
//     uint256 collateral_address_from_spec = collateralToken.balanceOf(collateralToken);
//     address collateral_address_from_contract = collateral();

//     // pool receives the previous balance plus the fee, then fee is transferred to recipient
//     assert balance_pool_after >= balance_pool_before,
//         "pool balance should only increase after flashloan";
//     // fee gets sent to the feeRecipient address
//     assert balance_fee_recipient_after == balance_fee_recipient_before + fee,
//         "recipient must receive fees";
// }

// verify that the flashloan fee is always > 0 ❌
// rule flashFeeIntegrity(address token, uint amount) {
//     uint flash_fee = flashFee(token, amount);

//     assert amount > 0 => flash_fee > 0, 
//         "flash fee must be greater than 0";
// }

// verify that flashloan is never greater than the balance of the pool ✅
rule maxFlashLoanIntegrity(env e, address token) {
    uint max_loan_amount = maxFlashLoan(e, token);

    assert max_loan_amount <= collateralToken.balanceOf(currentContract);
}

// verify that shares are updated in accounting and transferred to the fee recipient ❌
// rule claimFeeRecipientCollSharesIntegrity(uint shares) {
//     address feeRecipient = feeRecipientAddress();

//     mathint fee_recipient_shares_before = getFeeRecipientClaimableCollShares();
//     mathint fee_recipient_balance_before = collateralToken.balanceOf(feeRecipient);

//     claimFeeRecipientCollShares(shares);

//     mathint fee_recipient_shares_after = getFeeRecipientClaimableCollShares();
//     mathint fee_recipient_balance_after = collateralToken.balanceOf(feeRecipient);

//     assert fee_recipient_shares_after == fee_recipient_shares_before - shares,
//         "fee recipient's share balance should be reduced";
//     assert fee_recipient_balance_after == fee_recipient_balance_before + shares,
//         "fee recipient's collateral balance should be increased";
// }

// need a way to pass in an interface to ERC20 so it can be queried ❌
// rule sweepTokenIntegrity(address token, uint amount) {
//     address feeRecipient = feeRecipientAddress();
//     mathint fee_recipient_balance_before = token.balanceOf(currentContract);

//     sweepToken(token, amount);

//     mathint fee_recipient_balance_after = token.balanceOf(currentContract);
    
//     assert fee_recipient_balance_after == fee_recipient_balance_before + amount;
// }



