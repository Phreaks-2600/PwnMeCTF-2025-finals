// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import { DevToken } from "../tokens/DevToken.sol";
import { DevLead } from "../tokens/DevLead.sol";
import "../interfaces/IFacet.sol";
import { ERC20 } from "../external_lib/ERC20.sol";
import { LibRefreshLeader } from "../libraries/LibRefreshLeader.sol";
import { ReentrancyGuard } from "../external_lib/ReentrancyGuard.sol";
import { LibDiamond } from "../libraries/LibDiamond.sol";

contract RefreshLeaderFacet is ReentrancyGuard, IFacet {
    function setTokensAddresses(address devtoken, address devlead) external {
        LibDiamond.enforceIsContractOwner(msg.sender);
        LibRefreshLeader.Layout storage s = LibRefreshLeader.layout();
        s.devToken = devtoken;
        s.devLead = devlead;
    }

    function refreshLeader(address newLeader) external nonReentrant {
        LibRefreshLeader.Layout storage s = LibRefreshLeader.layout();
        address devtoken = s.devToken;
        address devlead = s.devLead;
        require(ERC20(address(devtoken)).balanceOf(newLeader) > ERC20(address(devtoken)).totalSupply() / 2, "Not enough tokens to be leader");
        // This contract must be the owner of DevLead contract
        DevLead(devlead).mint(newLeader, "Leadership taken");
    }

    function getSelectors() external pure returns (bytes4[] memory selectors) {
        selectors = new bytes4[](2);
        selectors[0] = this.refreshLeader.selector;
        selectors[1] = this.setTokensAddresses.selector;
    }
}