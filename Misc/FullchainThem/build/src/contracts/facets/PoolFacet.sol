// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import { Address } from "../external_lib/Address.sol";
import { ReentrancyGuard } from "../external_lib/ReentrancyGuard.sol";
import { DevToken } from "../tokens/DevToken.sol";
import { LibPoolStorage } from "../libraries/LibPoolStorage.sol";
import { LibDiamond } from "../libraries/LibDiamond.sol";
import { ERC20 } from "../external_lib/ERC20.sol";
import "../interfaces/IFacet.sol";
import "../interfaces/IDiamondLoupe.sol";

contract PoolFacet is ReentrancyGuard, IFacet {
    using Address for address;

    event FlashloanExecuted(address borrower, uint256 amount);
    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);

    address private diamond;

    modifier onlyPlayFacet() {
        // Selector of `play(uint256)`
        bytes4 selector = bytes4(keccak256("play(uint256)"));
        address playFacet = IDiamondLoupe(diamond).facetAddress(selector);
        require(msg.sender == playFacet, "Only play() facet can call this");
        _;
    }

    constructor(bytes[20] memory keys, address _diamond) {
        LibPoolStorage.setDevKeys(keys);
        diamond = _diamond;
    }

    function initPool(address devtoken, address devlead) external {
        LibDiamond.enforceIsContractOwner(msg.sender);
        LibPoolStorage.PoolStorage storage ps = LibPoolStorage.poolStorage();
        ps.devtoken = devtoken;
        ps.devlead = devlead;
    }

    function deposit(uint256 amount) external {
        LibPoolStorage.PoolStorage storage ps = LibPoolStorage.poolStorage();
        address devtoken = ps.devtoken;
        ERC20(devtoken).transferFrom(msg.sender, address(this), amount);
        ps.balances[msg.sender] += amount;
        ps.totalLiquidity += amount;
        emit Deposit(msg.sender, amount);
    }

    function withdraw(uint256 amount) external {
        LibPoolStorage.PoolStorage storage ps = LibPoolStorage.poolStorage();
        require(ps.balances[msg.sender] >= amount, "Not enough funds");
        ps.balances[msg.sender] -= amount;
        ps.totalLiquidity -= amount;
        address devtoken = ps.devtoken;
        ERC20(devtoken).transfer(msg.sender, amount);
        emit Withdrawal(msg.sender, amount);
    }

    function flashLoan(
        uint256 amount,
        address borrower,
        address target,
        bytes calldata data
    ) external nonReentrant returns (bool) {
        LibPoolStorage.PoolStorage storage ps = LibPoolStorage.poolStorage();
        address devtoken = ps.devtoken;
        require(
            ps.balances[msg.sender] >= 3,
            "Not enough DevToken deposited to flashloan"
        );

        ERC20 devToken = ERC20(devtoken);
        uint256 balanceBefore = devToken.balanceOf(address(this));

        devToken.transfer(borrower, amount);
        target.functionCall(data);

        require(
            devToken.balanceOf(address(this)) >= balanceBefore,
            "Flashloan not repaid"
        );

        emit FlashloanExecuted(borrower, amount);
        return true;
    }

    function transferFunds(address payable to, uint256 amount) external onlyPlayFacet {
        (bool success, ) = to.call{value: amount}("");
        require(success, "ETH transfer failed");
    }

    receive() external payable {}

    function getSelectors() external pure returns (bytes4[] memory selectors) {
        selectors = new bytes4[](5) ;
        selectors[0] = this.deposit.selector;
        selectors[1] = this.withdraw.selector;
        selectors[2] = this.flashLoan.selector;
        selectors[3] = this.transferFunds.selector;
        selectors[4] = this.initPool.selector;
    }

}
