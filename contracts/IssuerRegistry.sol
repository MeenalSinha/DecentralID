// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "./interfaces/IIssuerRegistry.sol";

/**
 * @title IssuerRegistry
 * @dev Authoritative on-chain registry of accredited credential issuers and public signing keys.
 * Part of DecentralID Trust Infrastructure.
 */
contract IssuerRegistry is IIssuerRegistry, AccessControl, Pausable {
    bytes32 public constant GOVERNANCE_ROLE = keccak256("GOVERNANCE_ROLE");

    // Custom errors for gas efficiency
    error ZeroAddress();
    error IssuerAlreadyRegistered(address issuer);
    error IssuerNotRegistered(address issuer);
    error IssuerIsRevoked(address issuer);
    error IssuerNotActive(address issuer);
    error KeyNotActive(address signingKey);
    error KeyAlreadyActive(address signingKey);
    error InvalidKeyExpiration();
    error UnauthorizedCaller();

    mapping(address => IssuerInfo) private _issuers;
    mapping(address => mapping(address => SigningKeyInfo)) private _issuerSigningKeys;

    constructor(address initialAdmin) {
        if (initialAdmin == address(0)) revert ZeroAddress();
        _grantRole(DEFAULT_ADMIN_ROLE, initialAdmin);
        _grantRole(GOVERNANCE_ROLE, initialAdmin);
    }

    /**
     * @notice Register a new institutional issuer.
     */
    function registerIssuer(
        address issuer,
        IssuerRole role,
        string calldata metadataURI
    ) external onlyRole(GOVERNANCE_ROLE) whenNotPaused {
        if (issuer == address(0)) revert ZeroAddress();
        if (_issuers[issuer].status != IssuerStatus.Inactive) {
            revert IssuerAlreadyRegistered(issuer);
        }

        _issuers[issuer] = IssuerInfo({
            metadataURI: metadataURI,
            role: role,
            status: IssuerStatus.Active,
            authorizedAt: block.timestamp
        });

        // The issuer address is implicitly an authorized signing key by default
        _issuerSigningKeys[issuer][issuer] = SigningKeyInfo({
            isActive: true,
            validUntil: 0 // indefinite
        });

        emit IssuerRegistered(issuer, role, metadataURI);
        emit IssuerAuthorized(issuer, role);
        emit SigningKeyRegistered(issuer, issuer, 0);
    }

    /**
     * @notice Authorize or update an existing issuer's role.
     */
    function authorizeIssuer(
        address issuer,
        IssuerRole role
    ) external onlyRole(GOVERNANCE_ROLE) whenNotPaused {
        IssuerInfo storage info = _issuers[issuer];
        if (info.status == IssuerStatus.Inactive) revert IssuerNotRegistered(issuer);
        if (info.status == IssuerStatus.Revoked) revert IssuerIsRevoked(issuer);

        info.role = role;
        info.status = IssuerStatus.Active;
        emit IssuerAuthorized(issuer, role);
    }

    /**
     * @notice Temporarily suspend an issuer.
     */
    function suspendIssuer(address issuer) external onlyRole(GOVERNANCE_ROLE) whenNotPaused {
        IssuerInfo storage info = _issuers[issuer];
        if (info.status == IssuerStatus.Inactive) revert IssuerNotRegistered(issuer);
        if (info.status == IssuerStatus.Revoked) revert IssuerIsRevoked(issuer);

        info.status = IssuerStatus.Suspended;
        emit IssuerSuspended(issuer);
    }

    /**
     * @notice Reinstate a suspended issuer.
     */
    function reinstateIssuer(address issuer) external onlyRole(GOVERNANCE_ROLE) whenNotPaused {
        IssuerInfo storage info = _issuers[issuer];
        if (info.status == IssuerStatus.Inactive) revert IssuerNotRegistered(issuer);
        if (info.status == IssuerStatus.Revoked) revert IssuerIsRevoked(issuer);
        if (info.status != IssuerStatus.Suspended) revert IssuerNotActive(issuer);

        info.status = IssuerStatus.Active;
        emit IssuerReinstated(issuer);
    }

    /**
     * @notice Permanently revoke an issuer. Irreversible terminal state.
     */
    function revokeIssuer(address issuer) external onlyRole(GOVERNANCE_ROLE) {
        IssuerInfo storage info = _issuers[issuer];
        if (info.status == IssuerStatus.Inactive) revert IssuerNotRegistered(issuer);

        info.status = IssuerStatus.Revoked;
        emit IssuerRevoked(issuer);
    }

    /**
     * @notice Register an authorized operational signing key for an institution.
     */
    function registerSigningKey(
        address signingKey,
        uint256 validUntil
    ) external whenNotPaused {
        address issuer = msg.sender;
        IssuerInfo storage info = _issuers[issuer];

        if (info.status != IssuerStatus.Active) revert IssuerNotActive(issuer);
        if (signingKey == address(0)) revert ZeroAddress();
        if (validUntil != 0 && validUntil <= block.timestamp) revert InvalidKeyExpiration();
        if (_issuerSigningKeys[issuer][signingKey].isActive) revert KeyAlreadyActive(signingKey);

        _issuerSigningKeys[issuer][signingKey] = SigningKeyInfo({
            isActive: true,
            validUntil: validUntil
        });

        emit SigningKeyRegistered(issuer, signingKey, validUntil);
    }

    /**
     * @notice Revoke a signing key (e.g., in case of key compromise or operator departure).
     */
    function revokeSigningKey(address signingKey) external {
        address issuer = msg.sender;
        if (!_issuerSigningKeys[issuer][signingKey].isActive) {
            // Also allow GOVERNANCE_ROLE to revoke keys on behalf of an issuer if emergency
            revert KeyNotActive(signingKey);
        }

        _issuerSigningKeys[issuer][signingKey].isActive = false;
        emit SigningKeyRevoked(issuer, signingKey);
    }

    /**
     * @notice Emergency administrative revocation of a compromised signing key.
     */
    function emergencyRevokeSigningKey(
        address issuer,
        address signingKey
    ) external onlyRole(GOVERNANCE_ROLE) {
        if (!_issuerSigningKeys[issuer][signingKey].isActive) revert KeyNotActive(signingKey);

        _issuerSigningKeys[issuer][signingKey].isActive = false;
        emit SigningKeyRevoked(issuer, signingKey);
    }

    // --- Query Functions ---

    function isIssuerAuthorized(address issuer) external view override returns (bool) {
        return _issuers[issuer].status == IssuerStatus.Active;
    }

    function isSigningKeyValid(
        address issuer,
        address signingKey
    ) external view override returns (bool) {
        if (_issuers[issuer].status != IssuerStatus.Active) {
            return false;
        }

        SigningKeyInfo memory keyInfo = _issuerSigningKeys[issuer][signingKey];
        if (!keyInfo.isActive) {
            return false;
        }

        if (keyInfo.validUntil != 0 && block.timestamp > keyInfo.validUntil) {
            return false;
        }

        return true;
    }

    function getIssuer(address issuer) external view override returns (IssuerInfo memory) {
        return _issuers[issuer];
    }

    // --- Emergency Controls ---

    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }
}
