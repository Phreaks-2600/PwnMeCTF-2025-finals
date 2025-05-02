// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

library LibPoolStorage {
    bytes32 constant STORAGE_POSITION = keccak256("diamond.pool.storage");

    struct DevKeyManager {
        bytes[20] devkeys;
        uint8 nextDevKey;
    }

    struct PoolStorage {
        mapping(address => uint256) balances;
        DevKeyManager devKeyManager;
        uint256 totalLiquidity;
        address devtoken;
        address devlead;
    }

    function poolStorage() internal pure returns (PoolStorage storage ps) {
        bytes32 position = STORAGE_POSITION;
        assembly {
            ps.slot := position
        }
    }

    function setDevKeys(bytes[20] memory keys) internal {
        PoolStorage storage ps = poolStorage();
        for (uint8 i = 0; i < 20; i++) {
            ps.devKeyManager.devkeys[i] = keys[i];
        }
        ps.devKeyManager.nextDevKey = 0;
    }

    function useKey() internal returns (bytes memory key) {
        PoolStorage storage ps = poolStorage();
        uint8 index = ps.devKeyManager.nextDevKey;

        require(index < 20, "All devKeys used");

        key = ps.devKeyManager.devkeys[index];

        ps.devKeyManager.nextDevKey = index + 1;
    }
}
