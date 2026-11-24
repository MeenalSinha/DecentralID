// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IIssuerRegistry {
    enum IssuerRole {
        Individual,
        Organization,
        DAO,
        VerifiedInstitution
    }

    enum IssuerStatus {
        Inactive,
        Active,
        Suspended,
        Revoked
    }

    struct IssuerInfo {
        string metadataURI;
        IssuerRole role;
        IssuerStatus status;
        uint256 authorizedAt;
    }

    struct SigningKeyInfo {
        bool isActive;
        uint256 validUntil;
    }

    event IssuerRegistered(address indexed issuer, IssuerRole role, string metadataURI);
    event IssuerAuthorized(address indexed issuer, IssuerRole role);
    event IssuerSuspended(address indexed issuer);
    event IssuerReinstated(address indexed issuer);
    event IssuerRevoked(address indexed issuer);
    event SigningKeyRegistered(address indexed issuer, address indexed signingKey, uint256 validUntil);
    event SigningKeyRevoked(address indexed issuer, address indexed signingKey);

    function isIssuerAuthorized(address issuer) external view returns (bool);
    function isSigningKeyValid(address issuer, address signingKey) external view returns (bool);
    function getIssuer(address issuer) external view returns (IssuerInfo memory);
}
