// SPDX-License-Identifier: Unlicense
pragma solidity ^0.8.13;

contract Setup {
    address public immutable devToken;
    address public immutable devLead;
    address public immutable diamond;

    address private immutable poolFacet;

    constructor(address _devToken, address _devLead, address _diamond, address _poolFacet) payable {
        devToken = _devToken;
        devLead = _devLead;
        diamond = _diamond;
        poolFacet = _poolFacet;
    }

    function isSolved() public view returns (bool) {
        return address(poolFacet).balance == 0;
    }
}