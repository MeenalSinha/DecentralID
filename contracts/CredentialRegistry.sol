// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "./interfaces/ICredentialRegistry.sol";
import "./interfaces/IIssuerRegistry.sol";

/**
 * @title CredentialRegistry
 * @dev On-chain reference and integrity anchor for privacy-preserving salted credential commitments.
 * Zero personal identifiable information is written or emitted.
 */
contract CredentialRegistry is ICredentialRegistry, AccessControl, Pausable {
    IIssuerRegistry public immutable issuerRegistry;

    // Custom errors
    error ZeroAddress();
    error EmptyCommitment();
    error EmptyCredentialId();
    error CredentialAlreadyRegistered(bytes32 credentialId);
    error UnauthorizedCaller(address caller, address claimedIssuer);
    error IssuerNotActive(address issuer);

    mapping(bytes32 => CredentialRecord) private _credentials;

    constructor(address initialAdmin, address issuerRegistryAddress) {
        if (initialAdmin == address(0) || issuerRegistryAddress == address(0)) {
            revert ZeroAddress();
        }
        _grantRole(DEFAULT_ADMIN_ROLE, initialAdmin);
        issuerRegistry = IIssuerRegistry(issuerRegistryAddress);
    }

    /**
     * @notice Register a privacy-preserving credential commitment.
     * @param credentialId Unique 32-byte identifier for the credential.
     * @param commitment 32-byte salted hash: keccak256(canonicalSubject || salt).
     * @param issuer Address of the issuing institution.
     */
    function registerCredential(
        bytes32 credentialId,
        bytes32 commitment,
        address issuer
    ) external whenNotPaused {
        if (credentialId == bytes32(0)) revert EmptyCredentialId();
        if (commitment == bytes32(0)) revert EmptyCommitment();
        if (issuer == address(0)) revert ZeroAddress();

        if (_credentials[credentialId].issuedAt != 0) {
            revert CredentialAlreadyRegistered(credentialId);
        }

        // 1. Verify that the claimed institution is active on IssuerRegistry
        if (!issuerRegistry.isIssuerAuthorized(issuer)) {
            revert IssuerNotActive(issuer);
        }

        // 2. Verify that caller (msg.sender) is an authorized operational signing key of the issuer
        if (!issuerRegistry.isSigningKeyValid(issuer, msg.sender)) {
            revert UnauthorizedCaller(msg.sender, issuer);
        }

        _credentials[credentialId] = CredentialRecord({
            commitment: commitment,
            issuer: issuer,
            issuedAt: block.timestamp
        });

        emit CredentialRegistered(credentialId, commitment, issuer, block.timestamp);
    }

    // --- Query Functions ---

    function getCredential(
        bytes32 credentialId
    ) external view override returns (bytes32 commitment, address issuer, uint256 issuedAt) {
        CredentialRecord memory rec = _credentials[credentialId];
        return (rec.commitment, rec.issuer, rec.issuedAt);
    }

    function credentialExists(bytes32 credentialId) external view override returns (bool) {
        return _credentials[credentialId].issuedAt != 0;
    }

    // --- Emergency Controls ---

    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }
}
