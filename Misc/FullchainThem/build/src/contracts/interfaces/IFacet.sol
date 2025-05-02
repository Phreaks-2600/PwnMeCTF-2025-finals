// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IFacet {
    function getSelectors() external pure returns (bytes4[] memory);
}
