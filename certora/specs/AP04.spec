methods {
    function getSystemCollShares() external returns (uint256) envfree;
    function increaseSystemCollShares(uint256 _value) external;
    function transferSystemCollShares(address _account, uint256 _shares) external;
}

// ** these all run but need to double check that these assumptions are okay to make and that they're not a source of vacuity

// we can assume that the sum of the cdps is a constant since the CDPM and BO only call AP after having changed the CDPs, 
// so in the context of the AP contract, the sum of cdps doesn't change
function sumCdps(bool adding, uint256 systemCollateral, uint256 deltaCollateral) returns mathint {
    if(adding) {
        return systemCollateral + deltaCollateral;
    } else {
        return systemCollateral - deltaCollateral;
    }
}

// when any function is called in ActivePool that modifies systemCollShares the collateral in the CDPs have already been updated by BO or CDPM so it should be a constant
// so the operation in the pool needs to increase/decrease the systemCollShares by the difference between the systemCollShares and the total CDP collateral
// this might be able to be used as an axiom for the sumCdps where it can be declared as +/- value passed into the functions that modify systemCollShares

/** Property 1a: 	
    The total collateral in active pool should be equal to the sum of all individual CDP collateral when increasing collateral
**/
rule increaseTotalCollateralIntegrity() {
    env e;
    mathint sum;
    address recipient;
    uint256 deltaCollateral;
    uint256 system_collateral_after;
    uint256 system_collateral_before = getSystemCollShares();

    require deltaCollateral <= system_collateral_before;

    // initially only calling increaseSystemCollShares for testing 
    sum = sumCdps(true, system_collateral_before, deltaCollateral);

    increaseSystemCollShares(e, deltaCollateral);

    system_collateral_after = getSystemCollShares();
    // this is same as system_collateral_after == system_collateral_before + deltaCollateral
    assert to_mathint(system_collateral_after) == sum;
}

/** Property 1b: 	
    The total collateral in active pool should be equal to the sum of all individual CDP collateral when decreasing collateral
**/
rule decreaseTotalCollateralIntegrity() {
    env e;
    mathint sum;

    address recipient;
    uint256 deltaCollateral;
    uint256 liquidatorRewardShares;
    uint256 system_collateral_before = getSystemCollShares();
    storage init = lastStorage;

    require deltaCollateral <= system_collateral_before;
    sum = sumCdps(false, system_collateral_before, deltaCollateral);

    // calling the first function that transfers collateral shares
    transferSystemCollShares(e, recipient, deltaCollateral);
    uint256 system_collateral_after_first_transfer = getSystemCollShares();

    // calling the second function that transfers collateral shares at the initial state
    transferSystemCollSharesAndLiquidatorReward(e, recipient, deltaCollateral, liquidatorRewardShares) at init;
    uint256 system_collateral_after_second_transfer = getSystemCollShares();

    // this is same as system_collateral_after == system_collateral_before - deltaCollateral
    assert to_mathint(system_collateral_after_first_transfer) == sum;
    assert to_mathint(system_collateral_after_second_transfer) == sum;
}