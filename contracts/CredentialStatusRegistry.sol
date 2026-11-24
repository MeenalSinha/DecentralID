// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "./interfaces/ICredentialStatusRegistry.sol";
import "./interfaces/IIssuerRegistry.sol";
import "./interfaces/ICredentialRegistry.sol";

/**
 * @title CredentialStatusRegistry
 * @dev Cryptographic lifecycle status registry managing suspension and revocation.
 * Non-repudiable state machine: Revoked credentials can NEVER be reinstated.
 */
contract CredentialStatusRegistry is ICredentialStatusRegistry, AccessControl, Pausable {
    bytes32 public constant STATUS_OPERATOR_ROLE = keccak256("STATUS_OPERATOR_ROLE");

    IIssuerRegistry public immutable issuerRegistry;
    ICredentialRegistry public immutable credentialRegistry;

    // Custom errors
    error ZeroAddress();
    error CredentialNotFound(bytes32 credentialId);
    error CredentialAlreadyRevoked(bytes32 credentialId);
    error InvalidStatusTransition(CredentialStatus current, CredentialStatus requested);
    error UnauthorizedCaller(address caller);

    mapping(bytes32 => StatusRecord) private _statuses;

    constructor(
        address initialAdmin,
        address issuerRegistryAddress,
        address credentialRegistryAddress
    ) {
        if (
            initialAdmin == address(0) ||
            issuerRegistryAddress == address(0) ||
            credentialRegistryAddress == address(0)
        ) {
            revert ZeroAddress();
        }

        _grantRole(DEFAULT_ADMIN_ROLE, initialAdmin);
        _grantRole(STATUS_OPERATOR_ROLE, initialAdmin);

        issuerRegistry = IIssuerRegistry(issuerRegistryAddress);
        credentialRegistry = ICredentialRegistry(credentialRegistryAddress);
    }

    modifier onlyAuthorizedUpdater(bytes32 credentialId) {
        (, address issuer, uint256 issuedAt) = credentialRegistry.getCredential(credentialId);
        if (issuedAt == 0) revert CredentialNotFound(credentialId);

        bool isGov = hasRole(STATUS_OPERATOR_ROLE, msg.sender);
        bool isIssuerKey = issuerRegistry.isSigningKeyValid(issuer, msg.sender);

        if (!isGov && !isIssuerKey) {
            revert UnauthorizedCaller(msg.sender);
        }
        _;
    }

    /**
     * @notice Temporarily suspend an active credential.
     */
    function suspendCredential(
        bytes32 credentialId,
        string calldata reason
    ) external override onlyAuthorizedUpdater(credentialId) whenNotPaused {
        StatusRecord storage rec = _statuses[credentialId];
        CredentialStatus current = rec.status;

        if (current == CredentialStatus.Revoked) {
            revert CredentialAlreadyRevoked(credentialId);
        }
        if (current == CredentialStatus.Suspended) {
            revert InvalidStatusTransition(current, CredentialStatus.Suspended);
        }

        rec.status = CredentialStatus.Suspended;
        rec.updatedAt = block.timestamp;
        rec.reason = reason;

        emit CredentialStatusChanged(
            credentialId,
            current,
            CredentialStatus.Suspended,
            msg.sender,
            reason
        );
    }

    /**
     * @notice Reinstate a suspended credential back to Active.
     */
    function reinstateCredential(
        bytes32 credentialId,
        string calldata reason
    ) external override onlyAuthorizedUpdater(credentialId) whenNotPaused {
        StatusRecord storage rec = _statuses[credentialId];
        CredentialStatus current = rec.status;

        if (current == CredentialStatus.Revoked) {
            revert CredentialAlreadyRevoked(credentialId);
        }
        if (current != CredentialStatus.Suspended) {
            revert InvalidStatusTransition(current, CredentialStatus.Active);
        }

        rec.status = CredentialStatus.Active;
        rec.updatedAt = block.timestamp;
        rec.reason = reason;

        emit CredentialStatusChanged(
            credentialId,
            current,
            CredentialStatus.Active,
            msg.sender,
            reason
        );
    }

    /**
     * @notice Permanently revoke a credential. Irreversible terminal transition.
     */
    function revokeCredential(
        bytes32 credentialId,
        string calldata reason
    ) external override onlyAuthorizedUpdater(credentialId) {
        StatusRecord storage rec = _statuses[credentialId];
        CredentialStatus current = rec.status;

        if (current == CredentialStatus.Revoked) {
            revert CredentialAlreadyRevoked(credentialId);
        }

        rec.status = CredentialStatus.Revoked;
        rec.updatedAt = block.timestamp;
        rec.reason = reason;

        emit CredentialStatusChanged(
            credentialId,
            current,
            CredentialStatus.Revoked,
            msg.sender,
            reason
        );
    }

    // --- Query Functions ---

    function getCredentialStatus(
        bytes32 credentialId
    ) external view override returns (CredentialStatus status, uint256 updatedAt) {
        StatusRecord memory rec = _statuses[credentialId];
        return (rec.status, rec.updatedAt);
    }

    // --- Emergency Controls ---

    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }
}
