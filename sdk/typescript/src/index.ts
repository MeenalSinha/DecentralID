import * as crypto from "crypto";

export interface DecentralIDConfig {
  baseUrl: string;
  apiKey?: string;
  timeoutMs?: number;
}

export interface VerificationChecks {
  structural: boolean;
  signature: boolean;
  issuer_authorized: boolean;
  signing_key_authorized: boolean;
  commitment_verified: boolean | null;
  not_expired: boolean;
}

export interface VerificationOutcome {
  outcome: "VALID" | "INVALID" | "INDETERMINATE";
  checks: VerificationChecks;
  issuer_address?: string;
  credential_id?: string;
  details: Record<string, any>;
}

export interface IssuerStatus {
  address: string;
  is_authorized: boolean;
  status: string;
  name?: string;
  domain?: string;
  active_keys_count: number;
  keys: Array<{
    key_id: string;
    public_key: string;
    valid_until?: number;
  }>;
}

export interface CredentialStatus {
  credential_id: string;
  status: string;
  on_chain_commitment: string;
  schema_type: string;
  issuer_id: string;
  issuance_date?: string;
  expiration_date?: string;
  revoked_at?: string;
  revocation_reason?: string;
}

export class DecentralIDClient {
  private readonly baseUrl: string;
  private readonly apiKey?: string;
  private readonly timeoutMs: number;

  constructor(config: DecentralIDConfig) {
    this.baseUrl = config.baseUrl.replace(/\/+$/, "");
    this.apiKey = config.apiKey;
    this.timeoutMs = config.timeoutMs ?? 10000;
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      "User-Agent": "DecentralID-TypeScript-SDK/1.0.0",
    };
    if (this.apiKey) {
      headers["X-API-Key"] = this.apiKey;
    }
    return headers;
  }

  /**
   * Verify a W3C Verifiable Presentation via Developer Network API.
   */
  async verifyPresentation(presentation: Record<string, any>): Promise<VerificationOutcome> {
    const res = await fetch(`${this.baseUrl}/api/v1/network/verify`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({ presentation }),
      signal: AbortSignal.timeout(this.timeoutMs),
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Verification request failed (${res.status}): ${errText}`);
    }
    return res.json() as Promise<VerificationOutcome>;
  }

  /**
   * Verify a W3C Verifiable Credential directly.
   */
  async verifyCredential(credential: Record<string, any>): Promise<VerificationOutcome> {
    const res = await fetch(`${this.baseUrl}/api/v1/network/verify`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({ credential }),
      signal: AbortSignal.timeout(this.timeoutMs),
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Credential verification failed (${res.status}): ${errText}`);
    }
    return res.json() as Promise<VerificationOutcome>;
  }

  /**
   * Query institutional authorization status and registered signing keys.
   */
  async getIssuerStatus(address: string): Promise<IssuerStatus> {
    const res = await fetch(`${this.baseUrl}/api/v1/network/issuers/${encodeURIComponent(address)}`, {
      method: "GET",
      headers: this.getHeaders(),
      signal: AbortSignal.timeout(this.timeoutMs),
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Failed to fetch issuer status (${res.status}): ${errText}`);
    }
    return res.json() as Promise<IssuerStatus>;
  }

  /**
   * Query on-chain credential lifecycle status by ID or commitment hash.
   */
  async getCredentialStatus(idOrCommitment: string): Promise<CredentialStatus> {
    const res = await fetch(`${this.baseUrl}/api/v1/network/credentials/${encodeURIComponent(idOrCommitment)}/status`, {
      method: "GET",
      headers: this.getHeaders(),
      signal: AbortSignal.timeout(this.timeoutMs),
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Failed to fetch credential status (${res.status}): ${errText}`);
    }
    return res.json() as Promise<CredentialStatus>;
  }

  /**
   * Cryptographically validates incoming Webhook HMAC-SHA256 signature with replay defense.
   */
  static verifyWebhookSignature(
    payloadBytesOrString: string | Buffer,
    signatureHeader: string,
    secretKey: string,
    toleranceSeconds = 300
  ): boolean {
    try {
      const parts: Record<string, string> = {};
      for (const item of signatureHeader.split(",")) {
        const [k, v] = item.split("=", 2);
        if (k && v) parts[k.trim()] = v.trim();
      }

      const timestampStr = parts["t"];
      const v1Sig = parts["v1"];
      if (!timestampStr || !v1Sig) return false;

      const timestamp = parseInt(timestampStr, 10);
      if (isNaN(timestamp)) return false;

      const now = Math.floor(Date.now() / 1000);
      if (Math.abs(now - timestamp) > toleranceSeconds) return false;

      const payload = typeof payloadBytesOrString === "string" 
        ? Buffer.from(payloadBytesOrString, "utf-8") 
        : payloadBytesOrString;

      const signedData = Buffer.concat([
        Buffer.from(`${timestamp}.`, "utf-8"),
        payload,
      ]);

      const expectedMac = crypto
        .createHmac("sha256", secretKey)
        .update(signedData)
        .digest("hex");

      const expectedBuf = Buffer.from(expectedMac, "hex");
      const actualBuf = Buffer.from(v1Sig, "hex");
      if (expectedBuf.length !== actualBuf.length) return false;

      return crypto.timingSafeEqual(expectedBuf, actualBuf);
    } catch {
      return false;
    }
  }
}
