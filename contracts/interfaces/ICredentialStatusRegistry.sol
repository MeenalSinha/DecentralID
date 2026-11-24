// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface ICredentialStatusRegistry {
    enum CredentialStatus {
        Active,
        Suspended,
        Revoked
    }

    struct StatusRecord {
        CredentialStatus status;
        uint256 updatedAt;
        string reason;
    }

    event CredentialStatusChanged(
        bytes32 indexed credentialId,
        CredentialStatus indexed previousStatus,
        CredentialStatus indexed newStatus,
        address updatedBy,
        string reason
    );

    function getCredentialStatus(bytes32 credentialId) external view returns (CredentialStatus status, uint256 updatedAt);
    function suspendCredential(bytes32 credentialId, string calldata reason) external;
    function reinstateCredential(bytes32 credentialId, string calldata reason) external;
    function revokeCredential(bytes32 credentialId, string calldata reason) external;
}
