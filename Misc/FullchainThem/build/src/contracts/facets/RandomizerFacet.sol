// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../interfaces/IFacet.sol";
import "../interfaces/IDiamondLoupe.sol";

contract RandomizerFacet is IFacet {

    function generateRandom() external view returns (uint256) {
        uint256 MAX_RANDOM = 133713371337;
        uint256 random = uint256(
            keccak256(
                abi.encodePacked(
                    block.timestamp,
                    block.prevrandao,
                    block.number,
                    msg.sender,
                    tx.origin,
                    gasleft()
                )
            )
        );
        uint256 finalRandom = random % (MAX_RANDOM + 1);
        return finalRandom;
    }

    function getSelectors() external pure returns (bytes4[] memory selectors) {
        selectors = new bytes4[](1);
        selectors[0] = this.generateRandom.selector;
    }

}
