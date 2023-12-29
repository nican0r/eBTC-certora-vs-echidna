This repo contains tests for comparing the Certora Prover with Trail of Bits' Echidna fuzzer.

## Setup
1. Sign-up for Certora Free Tier
* Note: It's important to also set the CERTORAKEY environment variable.
2. Install the Certora prover

## Running the Tests 
The Certora tests are contained in the [specs](https://github.com/nican0r/eBTC-certora-vs-echidna/tree/main/certora/specs) folder. 

The tests were created to verify the following properties from the [README](https://github.com/nican0r/eBTC-certora-vs-echidna/blob/main/packages/contracts/specs/PROPERTIES.md): 
1. [AP-04](https://github.com/nican0r/eBTC-certora-vs-echidna/blob/main/certora/specs/AP04.spec) - the total collateral in active pool should be equal to the sum of all individual CDP collateral (run with `certoraRun eBTC-certora-vs-echidna/certora/confs/AP04.conf`)
2. [BO-07](https://github.com/nican0r/eBTC-certora-vs-echidna/blob/main/certora/specs/BO07.spec) - eBTC tokens are burned upon repayment of a CDP's debt (run with `certoraRun eBTC-certora-vs-echidna/certora/confs/BO07.conf`)
3. [CDPM-06](https://github.com/nican0r/eBTC-certora-vs-echidna/blob/main/certora/specs/CDPM06.spec) - redemptions do not increase a CDPs debt (run with `certoraRun eBTC-certora-vs-echidna/certora/confs/CDPM06.conf`)

