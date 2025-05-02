// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../external_lib/ERC20.sol";
import "../external_lib/ECDSA.sol";
import "../external_lib/MessageHashUtils.sol";

contract DevToken is ERC20 {
    using ECDSA for bytes32;
    mapping(bytes => bool) public usedDevKeys;
    address mafiaMember;
    bool initializationDone = false;
    address initSupplyReceiver;

    constructor(address _initSupplyReceiver, uint256 initialSupply, address _mafiaMember) ERC20("DevToken", "DVT", 1){
        initSupplyReceiver = _initSupplyReceiver;
        _mint(initSupplyReceiver, initialSupply);
        mafiaMember = _mafiaMember;
    }

    function initPoolAuthorization(address diamond) external {
        require(!initializationDone, "pool already setup");
        initializationDone = true;
        allowance[initSupplyReceiver][diamond] = totalSupply;
    }

    function mint(address to, uint256 amount, uint8 nextKey, bytes[] memory devkeys) public {
        require(amount <= devkeys.length, "Amount must match number of devkeys");
        require(nextKey < amount, "Next key must be less than amount");
        
        for (uint256 i = nextKey; i < amount; i++) {
            require(!usedDevKeys[devkeys[i]], "Devkey already used");
            bytes32 messageHash = keccak256(abi.encodePacked("Developer key for mafia gang", i));
            address signer = ECDSA.recover(MessageHashUtils.toEthSignedMessageHash(messageHash), devkeys[i]);
            require(signer == mafiaMember, "Invalid signature");
            usedDevKeys[devkeys[i]] = true;
        }

        _mint(to, amount);
    }
}