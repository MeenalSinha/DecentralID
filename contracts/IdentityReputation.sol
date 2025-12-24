// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title IdentityReputation
 * @dev Decentralized Identity & Reputation System with Verifiable Credentials
 * @notice W3C-inspired credentials with role-based issuers and sybil resistance
 */
contract IdentityReputation {
    
    // ⭐ TIER-1: Role-based issuers
    enum IssuerRole {
        Individual,
        Organization,
        DAO,
        VerifiedInstitution
    }
    
    struct Identity {
        string ipfsHash;           // IPFS hash containing full profile data
        uint256 reputation;        // Reputation score (0-100)
        uint256 createdAt;         // Timestamp of identity creation
        uint256 lastActivity;      // ⭐ TIER-2: Last activity timestamp
        uint256 endorsementCount;  // ⭐ TIER-2: Total endorsements received
        bool exists;               // Whether identity has been created
    }
    
    // ⭐ TIER-3: ERC-721 style endorsement tracking
    struct Endorsement {
        address endorser;
        address endorsed;
        uint256 rating;            // 1-5 stars
        uint256 points;            // Reputation points awarded
        uint256 timestamp;
        string message;            // Stored off-chain (IPFS hash)
        bool exists;
    }
    
    // Core mappings
    mapping(address => Identity) public identities;
    mapping(address => IssuerRole) public issuerRoles;
    mapping(address => bool) public verifiedIssuers; // ⭐ TIER-1: Verified issuer registry
    
    // ⭐ TIER-3: Endorsement tracking (NFT-like)
    mapping(uint256 => Endorsement) public endorsements;
    mapping(address => uint256[]) public userEndorsements; // Endorsements received
    uint256 public endorsementCounter;
    
    // ⭐ TIER-2: Sybil resistance
    uint256 public constant MIN_WALLET_AGE = 30 days;
    
    // Contract metadata
    uint256 public totalIdentities;
    address public owner;
    
    // Events
    event IdentityCreated(
        address indexed user, 
        string ipfsHash, 
        uint256 timestamp
    );
    
    event ReputationUpdated(
        address indexed user, 
        address indexed endorser,
        uint256 points,
        uint256 newReputation
    );
    
    event IdentityUpdated(
        address indexed user,
        string newIpfsHash
    );
    
    event IssuerVerified(
        address indexed issuer,
        IssuerRole role
    );
    
    event EndorsementMinted(
        uint256 indexed endorsementId,
        address indexed endorser,
        address indexed endorsed,
        uint256 rating
    );
    
    constructor() {
        owner = msg.sender;
        verifiedIssuers[msg.sender] = true; // Owner is verified by default
        issuerRoles[msg.sender] = IssuerRole.VerifiedInstitution;
    }
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized");
        _;
    }
    
    /**
     * @dev Create a new identity with sybil resistance checks
     * @param ipfsHash IPFS hash containing profile data
     */
    function createIdentity(string memory ipfsHash) public {
        require(!identities[msg.sender].exists, "Identity already exists");
        require(bytes(ipfsHash).length > 0, "IPFS hash cannot be empty");
        
        // ⭐ TIER-2: Sybil resistance - check wallet age (optional check)
        // Note: This is a simplified check. Real implementation would need oracle or historical data
        
        identities[msg.sender] = Identity({
            ipfsHash: ipfsHash,
            reputation: 0,
            createdAt: block.timestamp,
            lastActivity: block.timestamp,
            endorsementCount: 0,
            exists: true
        });
        
        // Set default issuer role
        if (issuerRoles[msg.sender] == IssuerRole(0)) {
            issuerRoles[msg.sender] = IssuerRole.Individual;
        }
        
        totalIdentities++;
        
        emit IdentityCreated(msg.sender, ipfsHash, block.timestamp);
    }
    
    /**
     * @dev Update existing identity IPFS hash
     * @param newIpfsHash New IPFS hash
     */
    function updateIdentity(string memory newIpfsHash) public {
        require(identities[msg.sender].exists, "Identity does not exist");
        require(bytes(newIpfsHash).length > 0, "IPFS hash cannot be empty");
        
        identities[msg.sender].ipfsHash = newIpfsHash;
        identities[msg.sender].lastActivity = block.timestamp;
        
        emit IdentityUpdated(msg.sender, newIpfsHash);
    }
    
    /**
     * @dev Get identity details with reputation breakdown
     * @param user Address of the user
     */
    function getIdentity(address user) public view returns (
        string memory ipfsHash,
        uint256 reputation,
        uint256 createdAt,
        uint256 lastActivity,
        uint256 endorsementCount,
        bool exists
    ) {
        Identity memory identity = identities[user];
        return (
            identity.ipfsHash, 
            identity.reputation, 
            identity.createdAt,
            identity.lastActivity,
            identity.endorsementCount,
            identity.exists
        );
    }
    
    /**
     * ⭐ TIER-3: Mint endorsement as NFT-like token
     * @param user Address of user to endorse
     * @param points Reputation points to add (1-10)
     * @param rating Star rating (1-5)
     * @param messageHash IPFS hash of endorsement message
     */
    function mintEndorsement(
        address user, 
        uint256 points,
        uint256 rating,
        string memory messageHash
    ) public returns (uint256) {
        require(identities[user].exists, "Identity does not exist");
        require(identities[msg.sender].exists, "Endorser must have identity");
        require(user != msg.sender, "Cannot endorse yourself");
        require(points > 0 && points <= 10, "Points must be between 1-10");
        require(rating >= 1 && rating <= 5, "Rating must be between 1-5");
        
        // Update reputation with issuer weight
        uint256 weightedPoints = points;
        if (verifiedIssuers[msg.sender]) {
            weightedPoints = points * 2; // ⭐ TIER-1: Verified issuers give 2x weight
        }
        
        uint256 newReputation = identities[user].reputation + weightedPoints;
        if (newReputation > 100) {
            newReputation = 100;
        }
        
        identities[user].reputation = newReputation;
        identities[user].lastActivity = block.timestamp;
        identities[user].endorsementCount++;
        
        // Mint endorsement NFT
        uint256 endorsementId = endorsementCounter++;
        endorsements[endorsementId] = Endorsement({
            endorser: msg.sender,
            endorsed: user,
            rating: rating,
            points: weightedPoints,
            timestamp: block.timestamp,
            message: messageHash,
            exists: true
        });
        
        userEndorsements[user].push(endorsementId);
        
        emit EndorsementMinted(endorsementId, msg.sender, user, rating);
        emit ReputationUpdated(user, msg.sender, weightedPoints, newReputation);
        
        return endorsementId;
    }
    
    /**
     * @dev Legacy function for backward compatibility
     */
    function updateReputation(address user, uint256 points) public {
        mintEndorsement(user, points, 5, "");
    }
    
    /**
     * ⭐ TIER-1: Verify an issuer with specific role
     * @param issuer Address to verify
     * @param role Role to assign
     */
    function verifyIssuer(address issuer, IssuerRole role) public onlyOwner {
        require(identities[issuer].exists, "Issuer must have identity");
        verifiedIssuers[issuer] = true;
        issuerRoles[issuer] = role;
        emit IssuerVerified(issuer, role);
    }
    
    /**
     * @dev Remove verified status
     */
    function revokeIssuer(address issuer) public onlyOwner {
        verifiedIssuers[issuer] = false;
        emit IssuerVerified(issuer, IssuerRole.Individual);
    }
    
    /**
     * @dev Check if address has an identity
     */
    function hasIdentity(address user) public view returns (bool) {
        return identities[user].exists;
    }
    
    /**
     * ⭐ TIER-2: Get reputation breakdown for transparency
     */
    function getReputationBreakdown(address user) public view returns (
        uint256 totalReputation,
        uint256 endorsementCount,
        uint256 averageRating,
        uint256 daysSinceCreation,
        uint256 daysSinceActivity
    ) {
        require(identities[user].exists, "Identity does not exist");
        
        Identity memory identity = identities[user];
        
        // Calculate average rating from endorsements
        uint256 totalRating = 0;
        uint256[] memory userEndorsementIds = userEndorsements[user];
        
        for (uint256 i = 0; i < userEndorsementIds.length; i++) {
            totalRating += endorsements[userEndorsementIds[i]].rating;
        }
        
        uint256 avgRating = identity.endorsementCount > 0 
            ? totalRating / identity.endorsementCount 
            : 0;
        
        uint256 daysSince = (block.timestamp - identity.createdAt) / 1 days;
        uint256 daysSinceAct = (block.timestamp - identity.lastActivity) / 1 days;
        
        return (
            identity.reputation,
            identity.endorsementCount,
            avgRating,
            daysSince,
            daysSinceAct
        );
    }
    
    /**
     * ⭐ TIER-2: Check sybil resistance signals
     */
    function getSybilResistanceScore(address user) public view returns (
        bool hasIdentity,
        bool meetsWalletAge,
        bool hasEndorsements,
        uint256 score
    ) {
        bool identityExists = identities[user].exists;
        bool walletAge = (block.timestamp - identities[user].createdAt) >= MIN_WALLET_AGE;
        bool endorsed = identities[user].endorsementCount > 0;
        
        uint256 sybilScore = 0;
        if (identityExists) sybilScore += 33;
        if (walletAge) sybilScore += 33;
        if (endorsed) sybilScore += 34;
        
        return (identityExists, walletAge, endorsed, sybilScore);
    }
    
    /**
     * @dev Get all endorsement IDs for a user
     */
    function getUserEndorsements(address user) public view returns (uint256[] memory) {
        return userEndorsements[user];
    }
    
    /**
     * @dev Get endorsement details
     */
    function getEndorsement(uint256 endorsementId) public view returns (
        address endorser,
        address endorsed,
        uint256 rating,
        uint256 points,
        uint256 timestamp,
        string memory message
    ) {
        Endorsement memory e = endorsements[endorsementId];
        require(e.exists, "Endorsement does not exist");
        return (e.endorser, e.endorsed, e.rating, e.points, e.timestamp, e.message);
    }
    
    /**
     * @dev Get contract statistics
     */
    function getStats() public view returns (
        uint256 total,
        uint256 totalEndorsements,
        uint256 verifiedIssuerCount
    ) {
        // Note: verifiedIssuerCount would need separate tracking for exact count
        return (totalIdentities, endorsementCounter, 0);
    }
    
    /**
     * ⭐ TIER-1: Check if address is verified issuer
     */
    function isVerifiedIssuer(address issuer) public view returns (bool, IssuerRole) {
        return (verifiedIssuers[issuer], issuerRoles[issuer]);
    }
}