// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface ICredentialRegistry {
    struct CredentialRecord {
        bytes32 commitment;
        address issuer;
        uint256 issuedAt;
    }

    event CredentialRegistered(
        bytes32 indexed credentialId,
        bytes32 indexed commitment,
        address indexed issuer,
        uint256 timestamp
    );

    function registerCredential(bytes32 credentialId, bytes32 commitment, address issuer) external;
    function getCredential(bytes32 credentialId) external view returns (bytes32 commitment, address issuer, uint256 issuedAt);
    function credentialExists(bytes32 credentialId) external view returns (bool);
}
