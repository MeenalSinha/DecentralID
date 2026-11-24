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
  Sliders,
  Check,
  X
} from 'lucide-react';
import { useWallet } from '../../authentication/hooks/useWallet';
import { apiGet, apiPost } from '../../../app/config/api';

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

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">
            DecentralID Personal Credential Vault
          </h1>
          <p className="text-gray-600 text-sm mt-1">
            Privacy-preserving self-sovereign wallet. Hold cryptographically verified credentials, create selective disclosure presentations, and export encrypted vaults.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowVaultModal(true)}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-xl text-sm font-semibold text-gray-700 hover:bg-gray-50 transition"
          >
            <Lock size={16} />
            Encrypted Backup
          </button>
          <button
            onClick={fetchHolderCredentials}
            disabled={loading || !account}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 transition"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {/* Account / DID Card */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-2xl p-6 text-white shadow-lg space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-500/20 rounded-xl border border-blue-400/30">
              <Wallet size={24} className="text-blue-400" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider text-blue-200 font-semibold">
                Self-Sovereign Identity DID
              </p>
              <h2 className="font-mono text-sm md:text-base font-bold text-gray-100">
                {account ? `did:pkh:eip155:${chainId || 1337}:${account}` : 'No Wallet Connected'}
              </h2>
            </div>
          </div>
          {account ? (
            <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs font-semibold rounded-full flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Vault Active
            </span>
          ) : (
            <span className="px-3 py-1 bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs font-semibold rounded-full">
              Disconnected
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2 border-t border-white/10 text-xs">
          <div>
            <p className="text-gray-400">Total Credentials</p>
            <p className="text-lg font-bold text-white">{credentials.length}</p>
          </div>
          <div>
            <p className="text-gray-400">Network Standard</p>
            <p className="text-lg font-bold text-white">W3C VC 2.0</p>
          </div>
          <div>
            <p className="text-gray-400">Signature Suite</p>
            <p className="text-lg font-bold text-white">ecdsa-jcs-2019</p>
          </div>
          <div>
            <p className="text-gray-400">Vault Privacy</p>
            <p className="text-lg font-bold text-emerald-400">AES-256-GCM</p>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {!account ? (
        <div className="bg-white rounded-2xl border border-gray-200 p-12 text-center space-y-4">
          <Shield size={48} className="mx-auto text-gray-400" />
          <h3 className="text-lg font-bold text-gray-900">Connect Wallet to Unlock Vault</h3>
          <p className="text-sm text-gray-500 max-w-md mx-auto">
            Please connect your Ethereum wallet to authenticate and decrypt your verifiable credentials stored on DecentralID.
          </p>
        </div>
      ) : loading ? (
        <div className="p-12 text-center text-gray-500 flex flex-col items-center gap-3">
          <RefreshCw size={32} className="animate-spin text-blue-600" />
          <p className="text-sm font-medium">Decrypting verifiable credentials from personal vault...</p>
        </div>
      ) : credentials.length === 0 ? (
        <div className="bg-white rounded-2xl border border-dashed border-gray-300 p-12 text-center space-y-3">
          <Award size={48} className="mx-auto text-gray-400" />
          <h3 className="text-base font-bold text-gray-800">No Verifiable Credentials Found</h3>
          <p className="text-xs text-gray-500 max-w-md mx-auto">
            Credentials issued to <code className="bg-gray-100 px-1 py-0.5 rounded">{account}</code> by authorized institutions will appear here automatically.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {credentials.map((cred) => {
            const isVerified = verificationResults[cred.id];
            return (
              <div
                key={cred.id}
                className="bg-white rounded-2xl border border-gray-200 shadow-sm hover:shadow-md transition p-6 flex flex-col justify-between space-y-4"
              >
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <span className="px-2.5 py-1 bg-blue-50 text-blue-700 text-xs font-bold rounded-lg border border-blue-200/60">
                        {cred.schema_type}
                      </span>
                      <h3 className="text-lg font-bold text-gray-900 mt-2">
                        {cred.claims.degree || cred.claims.title || cred.schema_type}
                      </h3>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {cred.claims.institutionName || cred.claims.organization || 'Accredited Institution'}
                      </p>
                    </div>

                    <span
                      className={`px-2.5 py-1 text-xs font-semibold rounded-full ${
                        cred.status === 'ACTIVE'
                          ? 'bg-green-100 text-green-800'
                          : cred.status === 'SUSPENDED'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {cred.status}
                    </span>
                  </div>

                  {/* Claims Snapshot */}
                  <div className="mt-4 bg-gray-50 rounded-xl p-3 space-y-1.5 text-xs">
                    {Object.entries(cred.claims)
                      .slice(0, 3)
                      .map(([key, val]) => (
                        <div key={key} className="flex justify-between">
                          <span className="text-gray-500 font-medium capitalize">
                            {key.replace(/([A-Z])/g, ' $1')}:
                          </span>
                          <span className="text-gray-900 font-semibold">{String(val)}</span>
                        </div>
                      ))}
                  </div>

                  {/* Verification Check Pill */}
                  <div className="mt-3 flex items-center justify-between text-xs">
                    <span className="text-gray-400">Cryptographic Integrity:</span>
                    {isVerified === true ? (
                      <span className="text-emerald-600 font-semibold flex items-center gap-1">
                        <CheckCircle size={14} /> Proof Verified
                      </span>
                    ) : isVerified === false ? (
                      <span className="text-red-600 font-semibold flex items-center gap-1">
                        <AlertCircle size={14} /> Verification Failed
                      </span>
                    ) : (
                      <button
                        onClick={() => handleVerifyBeforeDisplay(cred)}
                        className="text-blue-600 hover:underline font-semibold"
                      >
                        Verify Proof
                      </button>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="pt-4 border-t border-gray-100 flex items-center justify-between gap-2">
                  <button
                    onClick={() => setSelectedCred(cred)}
                    className="flex-1 px-3 py-2 border border-gray-200 rounded-xl text-xs font-bold text-gray-700 hover:bg-gray-50 transition flex items-center justify-center gap-1.5"
                  >
                    <Eye size={14} /> View Details
                  </button>
                  <button
                    onClick={() => startPresentation(cred)}
                    className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-xl text-xs font-bold hover:bg-blue-700 transition flex items-center justify-center gap-1.5"
                  >
                    <Share2 size={14} /> Present / Share
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Details Modal */}
      {selectedCred && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 space-y-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-gray-200">
              <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <Shield size={20} className="text-blue-600" />
                Verifiable Credential Document
              </h3>
              <button
                onClick={() => setSelectedCred(null)}
                className="p-1 text-gray-400 hover:text-gray-600 rounded-lg"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div>
                <p className="font-semibold text-gray-500">W3C Credential ID</p>
                <p className="font-mono bg-gray-50 p-2 rounded border border-gray-200 text-gray-800 break-all">
                  {selectedCred.w3c_id}
                </p>
              </div>

              <div>
                <p className="font-semibold text-gray-500">Salted Commitment Hash (Keccak256)</p>
                <p className="font-mono bg-gray-50 p-2 rounded border border-gray-200 text-gray-800 break-all">
                  {selectedCred.commitment}
                </p>
              </div>

              <div>
                <p className="font-semibold text-gray-500">Decrypted Subject Claims</p>
                <pre className="bg-gray-900 text-emerald-400 p-3 rounded-xl overflow-x-auto text-[11px] font-mono">
                  {JSON.stringify(selectedCred.claims, null, 2)}
                </pre>
              </div>

              <div>
                <p className="font-semibold text-gray-500">Complete Canonical W3C VC 2.0 Payload</p>
                <pre className="bg-gray-900 text-blue-300 p-3 rounded-xl overflow-x-auto text-[11px] font-mono max-h-48">
                  {JSON.stringify(selectedCred.w3c_document, null, 2)}
                </pre>
              </div>
            </div>

            <div className="flex justify-end pt-4 border-t border-gray-200">
              <button
                onClick={() => setSelectedCred(null)}
                className="px-4 py-2 bg-gray-100 text-gray-700 font-bold rounded-xl text-xs hover:bg-gray-200 transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Selective Disclosure & Presentation Modal */}
      {presentingCred && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full max-h-[90vh] overflow-y-auto p-6 space-y-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-gray-200">
              <div className="flex items-center gap-2">
                <Sliders size={20} className="text-blue-600" />
                <h3 className="text-lg font-bold text-gray-900">
                  Selective Disclosure Presentation
                </h3>
              </div>
              <button
                onClick={() => setPresentingCred(null)}
                className="p-1 text-gray-400 hover:text-gray-600 rounded-lg"
              >
                <X size={20} />
              </button>
            </div>

            {!generatedVP ? (
              <div className="space-y-4">
                <p className="text-xs text-gray-600">
                  Select which attributes to disclose to the verifier. Unchecked attributes will remain masked and protected from disclosure.
                </p>

                <div className="space-y-2 border border-gray-200 rounded-xl p-4 bg-gray-50">
                  <p className="text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">
                    Claims Disclosure Matrix
                  </p>
                  {Object.entries(presentingCred.claims).map(([key, value]) => (
                    <label
                      key={key}
                      className="flex items-center justify-between p-2 rounded-lg hover:bg-white transition cursor-pointer border border-transparent hover:border-gray-200"
                    >
                      <div className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={disclosedKeys[key] || false}
                          onChange={(e) =>
                            setDisclosedKeys((prev) => ({
                              ...prev,
                              [key]: e.target.checked,
                            }))
                          }
                          className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                        />
                        <span className="text-xs font-medium text-gray-800 capitalize">
                          {key.replace(/([A-Z])/g, ' $1')}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500 font-mono">
                        {disclosedKeys[key] ? String(value) : '•••• (Hidden)'}
                      </span>
                    </label>
                  ))}
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
                  <button
                    onClick={() => setPresentingCred(null)}
                    className="px-4 py-2 border border-gray-300 text-gray-700 font-bold rounded-xl text-xs hover:bg-gray-50 transition"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={submitPresentation}
                    className="px-4 py-2 bg-blue-600 text-white font-bold rounded-xl text-xs hover:bg-blue-700 transition flex items-center gap-1.5"
                  >
                    <Share2 size={14} /> Generate Verifiable Presentation
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4 text-xs">
                <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-center gap-3 text-emerald-800">
                  <CheckCircle size={24} className="text-emerald-600 flex-shrink-0" />
                  <div>
                    <p className="font-bold">Verifiable Presentation Ready!</p>
                    <p className="text-[11px] text-emerald-700 mt-0.5">
                      An opaque presentation token has been created. Verifiers can scan this QR code or access the presentation link without exposing undisclosed PII.
                    </p>
                  </div>
                </div>

                {/* Presentation Token & Share Link */}
                <div className="space-y-2">
                  <label className="font-bold text-gray-700">Presentation Share Link</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      readOnly
                      value={`${window.location.origin}/verify?token=${generatedVP.token}`}
                      className="w-full bg-gray-50 border border-gray-300 rounded-xl px-3 py-2 text-xs font-mono text-gray-800"
                    />
                    <button
                      onClick={() =>
                        copyToClipboard(`${window.location.origin}/verify?token=${generatedVP.token}`)
                      }
                      className="px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-bold flex items-center gap-1 transition"
                    >
                      {copiedToken ? <Check size={14} className="text-green-600" /> : <Copy size={14} />}
                      {copiedToken ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                </div>

                {/* Simulated Opaque QR Code Container */}
                <div className="border border-gray-200 rounded-xl p-6 text-center space-y-3 bg-gray-50 flex flex-col items-center">
                  <div className="p-4 bg-white rounded-2xl shadow-sm border border-gray-200">
                    <QrCode size={120} className="text-gray-900" />
                  </div>
                  <p className="text-[11px] text-gray-500 font-mono">
                    Token: {generatedVP.token.slice(0, 16)}...
                  </p>
                </div>

                <div className="flex justify-end pt-4 border-t border-gray-200">
                  <button
                    onClick={() => {
                      setGeneratedVP(null);
                      setPresentingCred(null);
                    }}
                    className="px-4 py-2 bg-blue-600 text-white font-bold rounded-xl text-xs hover:bg-blue-700 transition"
                  >
                    Done
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Encrypted Vault Modal */}
      {showVaultModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-gray-200">
              <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
                <Lock size={18} className="text-blue-600" />
                Client-Side Encrypted Vault Backup
              </h3>
              <button
                onClick={() => setShowVaultModal(false)}
                className="p-1 text-gray-400 hover:text-gray-600 rounded-lg"
              >
                <X size={18} />
              </button>
            </div>

            <p className="text-xs text-gray-600">
              Encrypt your entire verifiable credential store using client-side AES-256-GCM.
              Your password never leaves this browser.
            </p>

            <div className="space-y-2">
              <label className="text-xs font-bold text-gray-700">Master Vault Password</label>
              <input
                type="password"
                placeholder="Enter strong encryption password"
                value={vaultPassword}
                onChange={(e) => setVaultPassword(e.target.value)}
                className="w-full border border-gray-300 rounded-xl px-3 py-2 text-xs focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {vaultStatus && (
              <p className="text-xs font-semibold text-blue-600 bg-blue-50 p-2.5 rounded-lg border border-blue-200">
                {vaultStatus}
              </p>
            )}

            <div className="flex justify-end gap-3 pt-3 border-t border-gray-200">
              <button
                onClick={() => setShowVaultModal(false)}
                className="px-4 py-2 border border-gray-300 text-gray-700 font-bold rounded-xl text-xs hover:bg-gray-50 transition"
              >
                Cancel
              </button>
              <button
                onClick={exportEncryptedVault}
                className="px-4 py-2 bg-blue-600 text-white font-bold rounded-xl text-xs hover:bg-blue-700 transition flex items-center gap-1.5"
              >
                <Download size={14} /> Export Encrypted Vault
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
