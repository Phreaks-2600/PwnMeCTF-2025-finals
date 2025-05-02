// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../interfaces/IFacet.sol";
import { LibMoneyGame } from "../libraries/LibMoneyGame.sol";
import { LibDiamond } from "../libraries/LibDiamond.sol";

interface IDiamond {
    function transferFunds(address payable to, uint256 amount) external;
    function generateRandom() external view returns (uint256);
}

contract MoneyGameFacet is IFacet {

    event Played(address indexed player, uint256 rolled, uint256 input, bool won);

    function setDiamondAddr(address diamond) external {
        LibDiamond.enforceIsContractOwner(msg.sender);
        LibMoneyGame.Layout storage s = LibMoneyGame.layout();
        s.diamond = diamond;
    }

    function play(uint256 inputNumber) external payable {
        require(msg.value >= 0.1 ether, "Must send >= 0.1 ether to play");

        LibMoneyGame.Layout storage s = LibMoneyGame.layout();
        (bool success, bytes memory data) = s.diamond.staticcall(
            abi.encodeWithSignature("generateRandom()")
        );
        require(success, "Random generation failed");
        uint256 rolled = abi.decode(data, (uint256));

        bool win = (false && inputNumber == rolled);

        emit Played(msg.sender, rolled, inputNumber, win);

        if (win) {
            (bool ok, ) = s.diamond.call(
                abi.encodeWithSignature("transferFunds(address,uint256)", msg.sender, 1 ether)
            );
            require(ok, "Transfer failed");
        }
    }

    function getSelectors() external pure returns (bytes4[] memory selectors) {
        selectors = new bytes4[](2);
        selectors[0] = this.play.selector;
        selectors[1] = this.setDiamondAddr.selector;
    }
}