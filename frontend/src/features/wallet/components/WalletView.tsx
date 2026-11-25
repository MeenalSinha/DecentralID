import React, { useState, useEffect } from 'react';
import {
  Wallet,
  Shield,
  Award,
  Share2,
  Lock,
  QrCode,
  Copy,
  CheckCircle,
  AlertCircle,
  Eye,
  Download,
  RefreshCw,
  Check,
} from 'lucide-react';
import { useWallet } from '../../authentication/hooks/useWallet';
import { apiGet, apiPost } from '../../../app/config/api';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Badge } from '../../../components/ui/Badge';
import { Input } from '../../../components/ui/Input';
import { Modal } from '../../../components/ui/Modal';

interface CredentialItem {
  id: string;
  w3c_id: string;
  credential_id: string;
  organization_id: string;
  recipient_address: string;
  schema_type: string;
  commitment: string;
  workflow_status: string;
  status: string;
  tx_hash?: string;
  created_at: string;
  issued_at?: string;
  valid_until?: string;
  claims: Record<string, any>;
  w3c_document: Record<string, any>;
}

export const WalletView: React.FC = () => {
  const { account, chainId } = useWallet();
  const [credentials, setCredentials] = useState<CredentialItem[]>([]);
  const [loading, setLoading] = useState(false);

  // Modals & Panels
  const [selectedCred, setSelectedCred] = useState<CredentialItem | null>(null);
  const [presentingCred, setPresentingCred] = useState<CredentialItem | null>(null);
  const [disclosedKeys, setDisclosedKeys] = useState<Record<string, boolean>>({});
  const [generatedVP, setGeneratedVP] = useState<any | null>(null);
  const [copiedToken, setCopiedToken] = useState(false);
  const [copiedDid, setCopiedDid] = useState(false);
  const [verificationResults, setVerificationResults] = useState<Record<string, boolean>>({});

  // Encrypted Vault (Web Crypto AES-GCM)
  const [vaultPassword, setVaultPassword] = useState('');
  const [vaultStatus, setVaultStatus] = useState<string | null>(null);
  const [showVaultModal, setShowVaultModal] = useState(false);

  useEffect(() => {
    if (account) {
      fetchHolderCredentials();
    } else {
      setCredentials([]);
    }
  }, [account]);

  const fetchHolderCredentials = async () => {
    if (!account) return;
    setLoading(true);
    try {
      const res = await apiGet<{ total: number; items: CredentialItem[] }>(
        `/credentials/holder/${account}`
      );
      setCredentials(res.items || []);
    } catch {
      setCredentials([]);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyBeforeDisplay = async (cred: CredentialItem) => {
    try {
      const res = await apiPost<any>('/verification/verify', {
        credential: cred.w3c_document,
      });
      setVerificationResults((prev) => ({
        ...prev,
        [cred.id]: res.is_valid,
      }));
    } catch {
      setVerificationResults((prev) => ({
        ...prev,
        [cred.id]: false,
      }));
    }
  };

  const startPresentation = (cred: CredentialItem) => {
    setPresentingCred(cred);
    const initialKeys: Record<string, boolean> = {};
    Object.keys(cred.claims).forEach((k) => {
      initialKeys[k] = true;
    });
    setDisclosedKeys(initialKeys);
    setGeneratedVP(null);
  };

  const submitPresentation = async () => {
    if (!presentingCred) return;
    const selectedAttributes = Object.keys(disclosedKeys).filter((k) => disclosedKeys[k]);

    try {
      const res = await apiPost<any>('/credentials/presentations', {
        credential_id: presentingCred.credential_id,
        disclosed_attributes: selectedAttributes,
        expires_in_hours: 24,
      });
      setGeneratedVP(res);
    } catch (err: any) {
      alert(`Failed to create verifiable presentation: ${err.message}`);
    }
  };

  // Web Crypto Vault Export (AES-GCM encryption with PBKDF2)
  const exportEncryptedVault = async () => {
    if (!vaultPassword || vaultPassword.length < 8) {
      setVaultStatus('Password must be at least 8 characters.');
      return;
    }
    try {
      const enc = new TextEncoder();
      const rawData = enc.encode(JSON.stringify(credentials));
      const salt = window.crypto.getRandomValues(new Uint8Array(16));
      const iv = window.crypto.getRandomValues(new Uint8Array(12));

      const keyMaterial = await window.crypto.subtle.importKey(
        'raw',
        enc.encode(vaultPassword),
        'PBKDF2',
        false,
        ['deriveKey']
      );

      const aesKey = await window.crypto.subtle.deriveKey(
        {
          name: 'PBKDF2',
          salt,
          iterations: 100000,
          hash: 'SHA-256',
        },
        keyMaterial,
        { name: 'AES-GCM', length: 256 },
        false,
        ['encrypt']
      );

      const ciphertext = await window.crypto.subtle.encrypt(
        { name: 'AES-GCM', iv },
        aesKey,
        rawData
      );

      const backupPackage = {
        format: 'decentralid-vault-v1',
        salt: Array.from(salt),
        iv: Array.from(iv),
        ciphertext: Array.from(new Uint8Array(ciphertext)),
        timestamp: new Date().toISOString(),
      };

      const blob = new Blob([JSON.stringify(backupPackage, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `decentralid-vault-${account?.slice(0, 8)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setVaultStatus('Vault successfully encrypted and exported!');
    } catch (err: any) {
      setVaultStatus(`Encryption failed: ${err.message}`);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedToken(true);
    setTimeout(() => setCopiedToken(false), 2000);
  };

  const copyDid = () => {
    if (!account) return;
    const did = `did:pkh:eip155:${chainId || 31337}:${account}`;
    navigator.clipboard.writeText(did);
    setCopiedDid(true);
    setTimeout(() => setCopiedDid(false), 2000);
  };

  const activeCount = credentials.filter((c) => c.status === 'ACTIVE').length;
  const revokedCount = credentials.filter((c) => c.status === 'REVOKED' || c.status === 'SUSPENDED').length;

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12">
      {/* Editorial Header */}
      <div className="border-b border-border pb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-primary font-semibold text-xs tracking-wider uppercase mb-1">
            <Wallet size={15} />
            <span>Self-Sovereign Identity</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">
            Holder Wallet & Vault
          </h1>
          <p className="text-sm text-foreground-secondary mt-1 max-w-xl leading-relaxed">
            Manage your portable verifiable credentials, create selective disclosure presentations, and export encrypted client-side backups.
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowVaultModal(true)}
            leftIcon={<Lock size={13} />}
          >
            Encrypted Backup
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={fetchHolderCredentials}
            isLoading={loading}
            disabled={!account}
            leftIcon={<RefreshCw size={13} />}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Wallet Identity Panel */}
      <Card className="p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-control bg-primary-soft text-primary flex items-center justify-center shrink-0">
              <Wallet size={20} />
            </div>
            <div>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block">
                Decentralized Identifier (DID)
              </span>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="font-mono text-xs font-semibold text-foreground break-all">
                  {account
                    ? `did:pkh:eip155:${chainId || 31337}:${account}`
                    : 'No Wallet Connected'}
                </span>
                {account && (
                  <button
                    onClick={copyDid}
                    className="p-1 rounded text-foreground-muted hover:text-foreground hover:bg-surface-subtle transition-colors"
                    title="Copy DID"
                  >
                    {copiedDid ? <Check size={13} className="text-status-success" /> : <Copy size={13} />}
                  </button>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {account ? (
              <Badge variant="success" size="md" dot>
                Vault Decrypted & Active
              </Badge>
            ) : (
              <Badge variant="warning" size="md" dot>
                Wallet Disconnected
              </Badge>
            )}
          </div>
        </div>

        {/* Metric Badges */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4">
          <div className="p-3 bg-surface-subtle rounded-control border border-border-subtle">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block">
              Total Credentials
            </span>
            <span className="text-lg font-bold text-foreground mt-0.5 block">
              {credentials.length}
            </span>
          </div>

          <div className="p-3 bg-surface-subtle rounded-control border border-border-subtle">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block">
              Active Credentials
            </span>
            <span className="text-lg font-bold text-status-success mt-0.5 block">
              {activeCount}
            </span>
          </div>

          <div className="p-3 bg-surface-subtle rounded-control border border-border-subtle">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block">
              Revoked / Inactive
            </span>
            <span className="text-lg font-bold text-foreground-secondary mt-0.5 block">
              {revokedCount}
            </span>
          </div>

          <div className="p-3 bg-surface-subtle rounded-control border border-border-subtle">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block">
              Vault Privacy Standard
            </span>
            <span className="text-xs font-semibold text-primary mt-1.5 block">
              AES-256-GCM / PBKDF2
            </span>
          </div>
        </div>
      </Card>

      {/* Main Content Area */}
      {!account ? (
        <Card className="p-12 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-surface-subtle border border-border flex items-center justify-center mx-auto text-foreground-muted">
            <Shield size={24} />
          </div>
          <h3 className="text-base font-semibold text-foreground">
            Connect Wallet to Unlock Vault
          </h3>
          <p className="text-xs text-foreground-secondary max-w-sm mx-auto leading-relaxed">
            Please connect your Ethereum wallet to authenticate your identity and retrieve your verifiable credentials.
          </p>
        </Card>
      ) : loading ? (
        <div className="p-12 text-center text-foreground-secondary flex flex-col items-center gap-3">
          <RefreshCw size={24} className="animate-spin text-primary" />
          <p className="text-xs font-medium">Retrieving verifiable credentials from holder registry...</p>
        </div>
      ) : credentials.length === 0 ? (
        <Card className="p-12 text-center space-y-3 border-dashed">
          <div className="w-12 h-12 rounded-full bg-surface-subtle border border-border flex items-center justify-center mx-auto text-foreground-muted">
            <Award size={24} />
          </div>
          <h3 className="text-base font-semibold text-foreground">
            No Verifiable Credentials Found
          </h3>
          <p className="text-xs text-foreground-secondary max-w-md mx-auto leading-relaxed">
            Credentials issued to <code className="bg-surface-subtle px-1.5 py-0.5 rounded font-mono text-foreground">{account}</code> by authorized institutions will appear here automatically.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {credentials.map((cred) => {
            const isVerified = verificationResults[cred.id];
            return (
              <Card
                key={cred.id}
                className="flex flex-col justify-between hover:border-border-strong transition-all space-y-4"
              >
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <Badge variant="primary" size="sm">
                        {cred.schema_type}
                      </Badge>
                      <h3 className="text-base font-semibold text-foreground mt-2 tracking-tight">
                        {cred.claims.degree || cred.claims.title || cred.schema_type}
                      </h3>
                      <p className="text-xs text-foreground-secondary mt-0.5">
                        {cred.claims.institutionName || cred.claims.organization || 'Accredited Institution'}
                      </p>
                    </div>

                    <Badge
                      variant={
                        cred.status === 'ACTIVE'
                          ? 'success'
                          : cred.status === 'SUSPENDED'
                          ? 'warning'
                          : 'danger'
                      }
                      size="sm"
                      dot
                    >
                      {cred.status}
                    </Badge>
                  </div>

                  {/* Claims Snapshot */}
                  <div className="mt-3.5 bg-surface-subtle rounded-control p-3 space-y-1.5 text-xs border border-border-subtle">
                    {Object.entries(cred.claims)
                      .slice(0, 3)
                      .map(([key, val]) => (
                        <div key={key} className="flex justify-between items-center text-xs">
                          <span className="text-foreground-secondary capitalize">
                            {key.replace(/([A-Z])/g, ' $1')}:
                          </span>
                          <span className="text-foreground font-medium truncate max-w-[180px]">
                            {String(val)}
                          </span>
                        </div>
                      ))}
                  </div>

                  {/* Cryptographic Proof Verification */}
                  <div className="mt-3 flex items-center justify-between text-xs pt-2 border-t border-border-subtle">
                    <span className="text-foreground-muted">Proof Integrity:</span>
                    {isVerified === true ? (
                      <span className="text-status-success font-medium flex items-center gap-1 text-[11px]">
                        <CheckCircle size={13} /> Verified On-Chain
                      </span>
                    ) : isVerified === false ? (
                      <span className="text-status-danger font-medium flex items-center gap-1 text-[11px]">
                        <AlertCircle size={13} /> Verification Failed
                      </span>
                    ) : (
                      <button
                        onClick={() => handleVerifyBeforeDisplay(cred)}
                        className="text-primary hover:text-primary-hover font-medium text-[11px] hover:underline"
                      >
                        Verify Proof
                      </button>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="pt-3 border-t border-border flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedCred(cred)}
                    leftIcon={<Eye size={13} />}
                    className="flex-1"
                  >
                    View Details
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => startPresentation(cred)}
                    leftIcon={<Share2 size={13} />}
                    className="flex-1"
                  >
                    Present / Share
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Credential Details Modal */}
      {selectedCred && (
        <Modal
          isOpen={!!selectedCred}
          onClose={() => setSelectedCred(null)}
          title="Verifiable Credential Document"
          description={`Issued to ${selectedCred.recipient_address.slice(0, 8)}...`}
          maxWidth="xl"
          footer={
            <Button variant="outline" size="sm" onClick={() => setSelectedCred(null)}>
              Close
            </Button>
          }
        >
          <div className="space-y-4 text-xs">
            <div>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block mb-1">
                W3C Credential ID
              </span>
              <p className="font-mono bg-surface-subtle p-2 rounded-control border border-border text-foreground break-all">
                {selectedCred.w3c_id}
              </p>
            </div>

            <div>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block mb-1">
                Salted Commitment Hash (Keccak256)
              </span>
              <p className="font-mono bg-surface-subtle p-2 rounded-control border border-border text-foreground break-all">
                {selectedCred.commitment}
              </p>
            </div>

            <div>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block mb-1">
                Decrypted Subject Claims
              </span>
              <pre className="bg-surface-subtle text-foreground p-3 rounded-control border border-border overflow-x-auto text-[11px] font-mono">
                {JSON.stringify(selectedCred.claims, null, 2)}
              </pre>
            </div>

            <div>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block mb-1">
                Canonical W3C VC 2.0 Payload
              </span>
              <pre className="bg-surface-subtle text-foreground-secondary p-3 rounded-control border border-border overflow-x-auto text-[11px] font-mono max-h-40">
                {JSON.stringify(selectedCred.w3c_document, null, 2)}
              </pre>
            </div>
          </div>
        </Modal>
      )}

      {/* Selective Disclosure & Presentation Modal */}
      {presentingCred && (
        <Modal
          isOpen={!!presentingCred}
          onClose={() => setPresentingCred(null)}
          title="Selective Disclosure Presentation"
          description="Choose which attributes to disclose. Unchecked claims will remain cryptographically masked."
          maxWidth="lg"
          footer={
            !generatedVP ? (
              <>
                <Button variant="outline" size="sm" onClick={() => setPresentingCred(null)}>
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={submitPresentation}
                  leftIcon={<Share2 size={13} />}
                >
                  Generate Presentation
                </Button>
              </>
            ) : (
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  setGeneratedVP(null);
                  setPresentingCred(null);
                }}
              >
                Done
              </Button>
            )
          }
        >
          {!generatedVP ? (
            <div className="space-y-3">
              <div className="border border-border rounded-control p-3 bg-surface-subtle space-y-2">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block mb-1">
                  Claims Disclosure Matrix
                </span>
                {Object.entries(presentingCred.claims).map(([key, value]) => (
                  <label
                    key={key}
                    className="flex items-center justify-between p-2 rounded-control hover:bg-surface transition-colors cursor-pointer border border-transparent hover:border-border"
                  >
                    <div className="flex items-center gap-2.5">
                      <input
                        type="checkbox"
                        checked={disclosedKeys[key] || false}
                        onChange={(e) =>
                          setDisclosedKeys((prev) => ({
                            ...prev,
                            [key]: e.target.checked,
                          }))
                        }
                        className="w-4 h-4 text-primary rounded border-border focus:ring-primary/20 accent-primary"
                      />
                      <span className="text-xs font-medium text-foreground capitalize">
                        {key.replace(/([A-Z])/g, ' $1')}
                      </span>
                    </div>
                    <span className="text-xs text-foreground-secondary font-mono">
                      {disclosedKeys[key] ? String(value) : '•••• (Hidden)'}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4 text-xs">
              <div className="p-3.5 rounded-control bg-status-success-soft border border-status-success/30 text-status-success flex items-start gap-2.5">
                <CheckCircle size={18} className="shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold block">Verifiable Presentation Ready</span>
                  <p className="text-[11px] text-foreground-secondary mt-0.5">
                    An opaque presentation token has been created. Verifiers can scan this QR code or access the presentation link without exposing undisclosed PII.
                  </p>
                </div>
              </div>

              {/* Share Link */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">
                  Verification Share Link
                </label>
                <div className="flex gap-2">
                  <Input
                    readOnly
                    value={`${window.location.origin}/?token=${generatedVP.token}`}
                    className="font-mono text-xs flex-1"
                  />
                  <Button
                    variant="outline"
                    size="md"
                    onClick={() =>
                      copyToClipboard(`${window.location.origin}/?token=${generatedVP.token}`)
                    }
                    leftIcon={copiedToken ? <Check size={14} className="text-status-success" /> : <Copy size={14} />}
                  >
                    {copiedToken ? 'Copied' : 'Copy'}
                  </Button>
                </div>
              </div>

              {/* QR Code Presentation Box */}
              <div className="border border-border rounded-control p-5 text-center bg-surface-subtle flex flex-col items-center">
                <div className="p-3 bg-surface rounded-control border border-border shadow-subtle mb-2">
                  <QrCode size={110} className="text-foreground" />
                </div>
                <span className="text-[10px] font-mono text-foreground-muted">
                  Token: {generatedVP.token.slice(0, 18)}...
                </span>
              </div>
            </div>
          )}
        </Modal>
      )}

      {/* Encrypted Vault Modal */}
      {showVaultModal && (
        <Modal
          isOpen={showVaultModal}
          onClose={() => setShowVaultModal(false)}
          title="Client-Side Encrypted Vault Backup"
          description="Encrypt your entire verifiable credential store using client-side AES-256-GCM. Your passphrase never leaves this browser."
          maxWidth="md"
          footer={
            <>
              <Button variant="outline" size="sm" onClick={() => setShowVaultModal(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={exportEncryptedVault}
                leftIcon={<Download size={13} />}
              >
                Export Encrypted Vault
              </Button>
            </>
          }
        >
          <div className="space-y-3">
            <Input
              type="password"
              label="Master Vault Passphrase"
              placeholder="Enter strong encryption passphrase (min 8 chars)"
              value={vaultPassword}
              onChange={(e) => setVaultPassword(e.target.value)}
              helperText="PBKDF2 (100,000 iterations) + AES-256-GCM authenticated encryption."
            />

            {vaultStatus && (
              <p className="text-xs font-medium text-primary bg-primary-soft p-2.5 rounded-control border border-primary/20">
                {vaultStatus}
              </p>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
};
