// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;


library LibMoneyGame {
    bytes32 constant STORAGE_POSITION = keccak256("diamond.storage.moneygame");

    struct Layout {
        address diamond;
    }

    function layout() internal pure returns (Layout storage s) {
        bytes32 position = STORAGE_POSITION;
        assembly {
            s.slot := position
        }
    }
}