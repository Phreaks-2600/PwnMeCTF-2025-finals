// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

library LibRefreshLeader {
    bytes32 constant STORAGE_POSITION = keccak256("diamond.storage.refreshleader");

    struct Layout {
        address devToken;
        address devLead;
    }

    function layout() internal pure returns (Layout storage s) {
        bytes32 position = STORAGE_POSITION;
        assembly {
            s.slot := position
        }
    }

    function getDevToken() external view returns (address) {
        return LibRefreshLeader.layout().devToken;
    }

    function getDevLead() external view returns (address) {
        return LibRefreshLeader.layout().devLead;
    }
}