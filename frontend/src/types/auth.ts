export interface UserProfile {
  id: string;
  email?: string;
  fullName?: string;
  isActive: boolean;
  role: string;
  walletAddress: string;
}

export interface AuthChallengeResponse {
  nonce: string;
  message: string;
  domain: string;
  uri: string;
  chainId: number;
}

export interface SessionInfo {
  isAuthenticated: boolean;
  user?: UserProfile;
  walletAddress?: string;
}
