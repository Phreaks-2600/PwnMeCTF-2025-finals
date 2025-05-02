// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../external_lib/Ownable.sol";

contract DevLead is Ownable {
    string public name = "DevLeadNFT";
    string public symbol = "DLNFT";
    uint256 public nextTokenId;

    mapping(uint256 => address) private _owners;
    mapping(address => uint256) private _balances;

    mapping(uint256 => string) private _tokenURIs;

    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);

    constructor() Ownable(msg.sender) {}

    function mint(address to, string memory _tokenURI) external onlyOwner {
        require(to != address(0), "Invalid address");
        _owners[nextTokenId] = to;
        _balances[to]++;
        _tokenURIs[nextTokenId] = _tokenURI;
        emit Transfer(address(0), to, nextTokenId);
        nextTokenId++;
    }

    function isLeader(address leader) external view returns (bool) {
        if (leader == owner()) {
            return true;
        }
        if (nextTokenId == 0) {
            return false;
        }
        return this.ownerOf(nextTokenId-1) == leader;
    }

    function ownerOf(uint256 tokenId) external view returns (address) {
        require(_owners[tokenId] != address(0), "Token does not exist");
        return _owners[tokenId];
    }

    function balanceOf(address account) external view returns (uint256) {
        require(account != address(0), "Invalid address");
        return _balances[account];
    }

    function tokenURI(uint256 tokenId) external view returns (string memory) {
        require(_owners[tokenId] != address(0), "Token does not exist");
        return _tokenURIs[tokenId];
    }
}