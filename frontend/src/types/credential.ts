export interface BlockchainConfig {
  chain_id: number;
  network_name: string;
  rpc_url: string;
  contracts: {
    IssuerRegistry?: string | null;
    CredentialRegistry?: string | null;
    CredentialStatusRegistry?: string | null;
  };
}

export interface VerificationResult {
  isValid: boolean;
  credentialId?: string;
  issuerAddress?: string;
  isIssuerAuthorized?: boolean;
  isKeyValid?: boolean;
  status?: "Active" | "Suspended" | "Revoked";
  issuedAt?: string;
  error?: string;
}
