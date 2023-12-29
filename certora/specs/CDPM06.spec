using SortedCdps as sortedCdps;
using PriceFeed as priceFeed;
using ActivePool as pool;

methods {
    function _.locked() external => CONSTANT;
    function _.getOwnerAddress(address) external => PER_CALLEE_CONSTANT;
    function _.increaseTotalSurplusCollShares(uint256) external => NONDET;
    
    function sortedCdps._ external => NONDET;
    function priceFeed._ external => NONDET;
    function pool.getSystemDebt() external returns (uint256) envfree;
}

// ghost variable tracks total debt in the system 
// if the debt increases after a call to redeemCollateral, this means that debt of an individual CDP has increased
ghost mathint totalDebt {
    init_state axiom totalDebt == 0;
}

// // @audit total debt needs to intially match the actual total debt in the system

// // hook into changes of CDPs to change the totalDebt of the system
hook Sstore Cdps[KEY bytes32 id].(offset 0) uint256 newDebt (uint256 oldDebt) STORAGE {
    totalDebt = totalDebt - oldDebt + newDebt;
}

/** Property 3: 
    Redemptions do not increase a CDPs debt
**/
// @audit redemption redeems collateral from multiple cdps, 
// need to make sure that debt for any one of them isn't increased 
rule redemptionsDontIncreaseDept() {
    env e;
    uint256 debt_to_redeem;
    bytes32 first_redemption_hint;
    bytes32 upper_partial_redemption_hint;
    bytes32 lower_partial_redemption_hint;
    uint256 partial_redemption_hint_NICR;
    uint256 max_Iterations;
    uint256 max_fee_percentage;
    mathint total_debt_before = totalDebt;
    uint256 system_debt_before = pool.getSystemDebt();

    // redeem collateral
    // @audit how to ensure that the right position is being redeemed
    // may need to get a hint based on the redemption 
    redeemCollateral(
        e,
        debt_to_redeem,
        first_redemption_hint,
        upper_partial_redemption_hint,
        lower_partial_redemption_hint,
        partial_redemption_hint_NICR,
        max_Iterations,
        max_fee_percentage
    );

    uint256 system_debt_after = pool.getSystemDebt();
    mathint total_debt_after = totalDebt;

    
    // total debt of CDPs after should be <= total debt before or else this would imply one of the CDPs has had its debt increased
    assert total_debt_after <= total_debt_before, "total debt after should decrease";
    assert system_debt_after <= system_debt_before, "system debt after should decrease";
}