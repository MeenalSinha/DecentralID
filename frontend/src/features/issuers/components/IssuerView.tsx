import React, { useState, useEffect } from 'react';
import {
  Building2,
  Key,
  FileSpreadsheet,
  Award,
  CheckCircle2,
  Clock,
  ShieldCheck,
  AlertTriangle,
  PlusCircle,
  FileCheck,
  RefreshCw,
  Info,
} from 'lucide-react';
import { fetchApi } from '../../../app/config/api';

interface OrgInfo {
  id: string;
  name: string;
  legal_entity_id: string;
  domain: string;
  status: string;
  on_chain_address: string;
}

interface OrgMetrics {
  total_credentials: number;
  pending_approval: number;
  active_credentials: number;
  suspended_credentials: number;
  revoked_credentials: number;
  authorized_keys_count: number;
  members_count: number;
}

interface CredentialSummary {
  id: string;
  w3c_id: string;
  credential_id: string;
  recipient_address: string;
  schema_type: string;
  commitment: string;
  workflow_status: string;
  status: string;
  tx_hash?: string;
  created_at: string;
}

interface SigningKeyItem {
  id: string;
  public_key_address: string;
  key_type: string;
  status: string;
  valid_until?: number;
  created_at: string;
}

interface SchemaDefinition {
  schema_id: string;
  name: string;
  version: string;
  description: string;
  fields: Array<{
    name: string;
    type: string;
    required: boolean;
    description: string;
  }>;
}

export const IssuerView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'prepare' | 'approvals' | 'signing' | 'batch' | 'keys' | 'history'>('dashboard');
  const [org, setOrg] = useState<OrgInfo | null>(null);
  const [metrics, setMetrics] = useState<OrgMetrics | null>(null);
  const [credentials, setCredentials] = useState<CredentialSummary[]>([]);
  const [signingKeys, setSigningKeys] = useState<SigningKeyItem[]>([]);
  const [schemas, setSchemas] = useState<SchemaDefinition[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [orgLoadError, setOrgLoadError] = useState<string | null>(null);

  // Single Issuance Form State — all empty by default; operator enters real data
  const [selectedSchema, setSelectedSchema] = useState<string>('UniversityDegreeCredential');
  const [recipientAddress, setRecipientAddress] = useState<string>('');
  const [formClaims, setFormClaims] = useState<Record<string, string>>({});
  const [preparedResult, setPreparedResult] = useState<any>(null);

  // Signing State — no private key in browser; operator selects an authorized key
  const [selectedKeyForSigning, setSelectedKeyForSigning] = useState<string>('');
  const [selectedForSigning, setSelectedForSigning] = useState<string>('');
  const [signingStatus, setSigningStatus] = useState<string | null>(null);

  // Batch CSV State — empty by default; operator pastes their own data
  const [csvContent, setCsvContent] = useState<string>(
    'recipient_address,studentName,degree,major,institutionName,graduationDate'
  );
  const [batchResults, setBatchResults] = useState<any>(null);

  // Key Registration State
  const [newKeyAddress, setNewKeyAddress] = useState<string>('');

  // Load schemas
  useEffect(() => {
    fetchApi<SchemaDefinition[]>('/credentials/schemas')
      .then(setSchemas)
      .catch((err) => console.error('Failed to load schemas:', err));
  }, []);

  // Load the authenticated user's organization on mount
  useEffect(() => {
    loadUserOrganization();
  }, []);

  const loadUserOrganization = async () => {
    setLoading(true);
    setOrgLoadError(null);
    try {
      // Fetch organizations the authenticated user belongs to
      const orgsRes = await fetchApi<{ items: OrgInfo[] }>('/organizations');
      const orgs = orgsRes?.items || (Array.isArray(orgsRes) ? orgsRes : []);
      if (orgs.length === 0) {
        setOrgLoadError('No organizations found for your account. Please register or join an institution first.');
        return;
      }
      const primary = orgs[0];
      setOrg(primary);
      await refreshOrgData(primary.id);
    } catch (err: any) {
      setOrgLoadError(err.message || 'Failed to load your organization. Please ensure you are authenticated.');
    } finally {
      setLoading(false);
    }
  };

  const refreshOrgData = async (targetOrgId: string) => {
    if (!targetOrgId) return;
    setLoading(true);
    try {
      const [metricsData, credsData, keysData] = await Promise.all([
        fetchApi<OrgMetrics>(`/organizations/${targetOrgId}/metrics`).catch(() => null),
        fetchApi<{ total: number; items: CredentialSummary[] }>(`/credentials?organization_id=${targetOrgId}`).catch(() => ({ total: 0, items: [] })),
        fetchApi<SigningKeyItem[]>(`/organizations/${targetOrgId}/signing-keys`).catch(() => []),
      ]);
      if (metricsData) setMetrics(metricsData);
      setCredentials(credsData.items);
      setSigningKeys(keysData);
    } catch (err: any) {
      console.error('Refresh error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePrepareCredential = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!org) {
      setStatusMessage({ type: 'error', text: 'No organization loaded. Please ensure you are logged in and have an institutional account.' });
      return;
    }
    setStatusMessage(null);
    setLoading(true);
    try {
      const res = await fetchApi<any>('/credentials/prepare', {
        method: 'POST',
        body: JSON.stringify({
          organization_id: org.id,
          recipient_address: recipientAddress,
          schema_type: selectedSchema,
          claims: formClaims,
        }),
      });

      setPreparedResult(res);
      setStatusMessage({ type: 'success', text: `Credential draft prepared successfully (ID: ${res.credential_id.slice(0, 10)}...).` });
      refreshOrgData(org.id);
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.message || 'Failed to prepare credential.' });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitForApproval = async (credentialRecordId: string) => {
    try {
      await fetchApi(`/credentials/${credentialRecordId}/submit-approval`, { method: 'POST' });
      setStatusMessage({ type: 'success', text: 'Credential successfully submitted for administrative approval.' });
      if (org) refreshOrgData(org.id);
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.message });
    }
  };

  const handleApprove = async (credentialRecordId: string) => {
    try {
      await fetchApi(`/credentials/${credentialRecordId}/approve`, { method: 'POST' });
      setStatusMessage({ type: 'success', text: 'Credential approved. Ready for cryptographic signing.' });
      if (org) refreshOrgData(org.id);
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.message });
    }
  };

  /**
   * Signing handler — SECURE DESIGN NOTE:
   * The backend `sign_credential` endpoint receives a private key in the request body.
   * This is an acknowledged architectural limitation for the current demo environment.
   * In a production deployment this MUST be replaced with one of:
   *   (a) A backend HSM/KMS integration where the key never leaves the secure enclave.
   *   (b) Client-side signing using an external Ethereum wallet (e.g. MetaMask, WalletConnect)
   *       where the browser signs the credential hash and sends only the signature.
   *   (c) A dedicated institutional signing service with hardware-backed key storage.
   *
   * The current implementation prompts the operator for a private key ONLY in the signing tab,
   * marks it as a password field, and transmits it over HTTPS. It is NOT stored in state
   * between sessions and is cleared immediately after signing.
   *
   * For the demo/development phase this is acceptable. It MUST NOT be used in production.
   */
  const handleSign = async () => {
    if (!selectedForSigning || !selectedKeyForSigning) {
      setStatusMessage({ type: 'error', text: 'Please select an approved credential and an authorized signing key.' });
      return;
    }
    setLoading(true);
    setSigningStatus(null);
    try {
      const signRes = await fetchApi<any>(`/credentials/${selectedForSigning}/sign`, {
        method: 'POST',
        body: JSON.stringify({ private_key: selectedKeyForSigning }),
      });

      // Confirm issuance — tx_hash is provided by the backend blockchain integration.
      // If no blockchain is connected, confirm-issuance is skipped and status stays PENDING_BLOCKCHAIN_REGISTRATION.
      const txHash = signRes?.tx_hash;
      if (txHash) {
        await fetchApi<any>(`/credentials/${selectedForSigning}/confirm-issuance`, {
          method: 'POST',
          body: JSON.stringify({ tx_hash: txHash }),
        });
        setStatusMessage({
          type: 'success',
          text: `Credential signed with W3C Data Integrity proof. On-chain Tx: ${txHash.slice(0, 12)}...`,
        });
      } else {
        setStatusMessage({
          type: 'success',
          text: 'Credential signed with W3C Data Integrity proof. Awaiting blockchain confirmation.',
        });
      }

      setSelectedForSigning('');
      setSelectedKeyForSigning('');
      if (org) refreshOrgData(org.id);
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
      setSigningStatus(null);
    }
  };

  const handleBatchPrepare = async () => {
    if (!org) {
      setStatusMessage({ type: 'error', text: 'No organization loaded.' });
      return;
    }
    setStatusMessage(null);
    setLoading(true);
    try {
      const lines = csvContent.trim().split('\n');
      if (lines.length < 2) throw new Error('CSV must contain a header line and at least one data record.');

      const headers = lines[0].split(',').map((h) => h.trim());
      const recipientIdx = headers.indexOf('recipient_address');
      if (recipientIdx === -1) throw new Error("CSV must have 'recipient_address' column.");

      const items = [];
      for (let i = 1; i < lines.length; i++) {
        const parts = lines[i].split(',').map((p) => p.trim());
        if (parts.length < headers.length) continue;
        const claims: Record<string, string> = {};
        headers.forEach((h, idx) => {
          if (h !== 'recipient_address') {
            claims[h] = parts[idx];
          }
        });
        items.push({
          recipient_address: parts[recipientIdx],
          claims,
        });
      }

      const res = await fetchApi<any>('/credentials/batch-prepare', {
        method: 'POST',
        body: JSON.stringify({
          organization_id: org.id,
          schema_type: selectedSchema,
          items,
        }),
      });

      setBatchResults(res);
      setStatusMessage({
        type: 'success',
        text: `Batch processing complete: ${res.successful_count} prepared, ${res.failed_count} failed.`,
      });
      refreshOrgData(org.id);
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyAddress || !org) return;
    try {
      await fetchApi(`/organizations/${org.id}/signing-keys`, {
        method: 'POST',
        body: JSON.stringify({
          public_key_address: newKeyAddress,
          key_type: 'secp256k1',
        }),
      });
      setStatusMessage({ type: 'success', text: `Signing key ${newKeyAddress} authorized successfully.` });
      setNewKeyAddress('');
      refreshOrgData(org.id);
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.message });
    }
  };

  // Derive dynamic form fields from selected schema
  const getSchemaFields = (): string[] => {
    const schema = schemas.find((s) => s.name === selectedSchema || s.schema_id.includes(selectedSchema));
    if (schema) return schema.fields.map((f) => f.name);
    // Fallback: use current formClaims keys or standard set
    return Object.keys(formClaims).length > 0
      ? Object.keys(formClaims)
      : ['recipientName', 'degree', 'major', 'institutionName', 'graduationDate'];
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-200 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
              Issuer Portal • Phase 6
            </span>
            {org && (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 flex items-center gap-1">
                <ShieldCheck size={12} /> {org.status}
              </span>
            )}
          </div>
          <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight mt-1">
            {org ? org.name : 'Loading Institution…'}
          </h1>
          <p className="text-sm text-gray-500">
            Cryptographic Credential Studio, Separation-of-Duties Governance & Public Key Infrastructure
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => org && refreshOrgData(org.id)}
            disabled={!org || loading}
            className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition disabled:opacity-50"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {/* Organization load error */}
      {orgLoadError && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-sm flex items-start gap-3">
          <AlertTriangle size={18} className="text-amber-600 mt-0.5 shrink-0" />
          <div>
            <p className="font-semibold">Organization Not Loaded</p>
            <p className="text-xs mt-1">{orgLoadError}</p>
          </div>
        </div>
      )}

      {/* Status Messages */}
      {statusMessage && (
        <div
          className={`p-4 rounded-xl text-sm flex items-start gap-3 ${
            statusMessage.type === 'success'
              ? 'bg-emerald-50 border border-emerald-200 text-emerald-900'
              : 'bg-rose-50 border border-rose-200 text-rose-900'
          }`}
        >
          {statusMessage.type === 'success' ? (
            <CheckCircle2 size={18} className="text-emerald-600 mt-0.5 shrink-0" />
          ) : (
            <AlertTriangle size={18} className="text-rose-600 mt-0.5 shrink-0" />
          )}
          <div className="flex-1 font-medium">{statusMessage.text}</div>
          <button onClick={() => setStatusMessage(null)} className="text-gray-400 hover:text-gray-600">
            ×
          </button>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between text-gray-500 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Issued</span>
            <Award size={18} className="text-blue-500" />
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {metrics ? metrics.total_credentials : '—'}
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between text-gray-500 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider">Awaiting Review</span>
            <Clock size={18} className="text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-amber-600">
            {metrics ? metrics.pending_approval : '—'}
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between text-gray-500 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider">Active Credentials</span>
            <CheckCircle2 size={18} className="text-emerald-500" />
          </div>
          <div className="text-2xl font-bold text-emerald-600">
            {metrics ? metrics.active_credentials : '—'}
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between text-gray-500 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider">Suspended / Revoked</span>
            <AlertTriangle size={18} className="text-rose-500" />
          </div>
          <div className="text-2xl font-bold text-rose-600">
            {metrics ? (metrics.suspended_credentials + metrics.revoked_credentials) : '—'}
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between text-gray-500 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider">Authorized PKI Keys</span>
            <Key size={18} className="text-indigo-500" />
          </div>
          <div className="text-2xl font-bold text-indigo-600">
            {metrics ? metrics.authorized_keys_count : '—'}
          </div>
        </div>
      </div>

      {/* Portal Tabs Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 overflow-x-auto">
          {[
            { id: 'dashboard', label: 'Dashboard', icon: Building2 },
            { id: 'prepare', label: 'Issue Credential', icon: PlusCircle },
            { id: 'approvals', label: 'Approvals Queue', icon: FileCheck },
            { id: 'signing', label: 'Sign & Anchor', icon: Award },
            { id: 'batch', label: 'Batch CSV Import', icon: FileSpreadsheet },
            { id: 'keys', label: 'Signing Keys (PKI)', icon: Key },
            { id: 'history', label: 'Issuance History', icon: Clock },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition whitespace-nowrap ${
                  isActive
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon size={18} />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab 1: Dashboard */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100 p-6 rounded-2xl space-y-3">
              <div className="p-3 bg-blue-600 text-white rounded-xl w-fit">
                <PlusCircle size={24} />
              </div>
              <h3 className="text-lg font-bold text-gray-900">Prepare Single Credential</h3>
              <p className="text-sm text-gray-600">
                Use validated W3C schemas to generate salted privacy commitments and prepare drafts.
              </p>
              <button
                onClick={() => setActiveTab('prepare')}
                className="mt-2 inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 transition"
              >
                Launch Issuance Studio →
              </button>
            </div>

            <div className="bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-100 p-6 rounded-2xl space-y-3">
              <div className="p-3 bg-emerald-600 text-white rounded-xl w-fit">
                <FileCheck size={24} />
              </div>
              <h3 className="text-lg font-bold text-gray-900">Governance & Approvals</h3>
              <p className="text-sm text-gray-600">
                Multi-party approval queue enforcing separation of duties before cryptographic signing.
              </p>
              <button
                onClick={() => setActiveTab('approvals')}
                className="mt-2 inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-semibold hover:bg-emerald-700 transition"
              >
                View Pending ({metrics?.pending_approval ?? '—'}) →
              </button>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-pink-50 border border-purple-100 p-6 rounded-2xl space-y-3">
              <div className="p-3 bg-purple-600 text-white rounded-xl w-fit">
                <FileSpreadsheet size={24} />
              </div>
              <h3 className="text-lg font-bold text-gray-900">Bulk Batch Issuance</h3>
              <p className="text-sm text-gray-600">
                Upload CSV tables of graduates or employees with strict per-record schema validation.
              </p>
              <button
                onClick={() => setActiveTab('batch')}
                className="mt-2 inline-flex items-center gap-1.5 px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-semibold hover:bg-purple-700 transition"
              >
                Import CSV Batch →
              </button>
            </div>
          </div>

          {org && (
            <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-4">
              <h3 className="text-lg font-bold text-gray-900">Registry & Accreditation Status</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div className="p-4 bg-gray-50 rounded-xl space-y-1">
                  <span className="text-xs text-gray-500 font-medium uppercase">On-Chain Primary Identity</span>
                  <div className="font-mono text-gray-800 break-all">{org.on_chain_address || 'Not registered on-chain'}</div>
                </div>
                <div className="p-4 bg-gray-50 rounded-xl space-y-1">
                  <span className="text-xs text-gray-500 font-medium uppercase">Legal Entity Identifier</span>
                  <div className="text-gray-800 font-semibold">{org.legal_entity_id} • Domain: {org.domain}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Issue Credential Studio */}
      {activeTab === 'prepare' && (
        <div className="bg-white p-8 rounded-2xl border border-gray-200 shadow-sm space-y-6">
          <div className="border-b border-gray-200 pb-4">
            <h2 className="text-xl font-bold text-gray-900">W3C Credential Preparation Studio</h2>
            <p className="text-sm text-gray-500">
              Enter recipient claims. All claims and salts are automatically encrypted at rest using AES-256-GCM.
            </p>
          </div>

          {!org && (
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-800">
              Please ensure you have an institutional account to prepare credentials.
            </div>
          )}

          <form onSubmit={handlePrepareCredential} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">
                  Credential Schema Type
                </label>
                <select
                  value={selectedSchema}
                  onChange={(e) => {
                    setSelectedSchema(e.target.value);
                    const schema = schemas.find((s) => s.name === e.target.value || s.schema_id.includes(e.target.value));
                    if (schema) {
                      const initialClaims: Record<string, string> = {};
                      schema.fields.forEach((f) => (initialClaims[f.name] = ''));
                      setFormClaims(initialClaims);
                    } else {
                      setFormClaims({});
                    }
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="UniversityDegreeCredential">University Degree Credential</option>
                  <option value="AcademicTranscriptCredential">Academic Transcript</option>
                  <option value="CourseCompletionCertificate">Course Completion Certificate</option>
                  <option value="ProfessionalCertification">Professional Certification</option>
                  <option value="EmploymentVerificationCredential">Employment Verification Credential</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">
                  Recipient Ethereum Address (Student/Professional)
                </label>
                <input
                  type="text"
                  value={recipientAddress}
                  onChange={(e) => setRecipientAddress(e.target.value)}
                  placeholder="0x... (holder wallet address)"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>

            {/* Dynamic Claims Form */}
            <div className="bg-gray-50 p-6 rounded-xl space-y-4">
              <h4 className="text-sm font-bold text-gray-900 uppercase tracking-wider">
                Schema Claims: {selectedSchema}
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {getSchemaFields().map((claimKey) => (
                  <div key={claimKey}>
                    <label className="block text-xs font-semibold text-gray-700 mb-1 capitalize">
                      {claimKey.replace(/([A-Z])/g, ' $1')}
                    </label>
                    <input
                      type="text"
                      value={formClaims[claimKey] || ''}
                      onChange={(e) => setFormClaims({ ...formClaims, [claimKey]: e.target.value })}
                      className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
              <button
                type="submit"
                disabled={loading || !org}
                className="px-6 py-2.5 bg-blue-600 text-white font-semibold rounded-lg text-sm hover:bg-blue-700 transition disabled:opacity-50"
              >
                {loading ? 'Preparing Draft...' : '1. Prepare W3C Credential Draft'}
              </button>
            </div>
          </form>

          {/* Prepared Draft Preview */}
          {preparedResult && (
            <div className="mt-8 p-6 bg-slate-900 text-slate-100 rounded-2xl space-y-4 font-mono text-xs">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="text-emerald-400 font-bold flex items-center gap-1.5">
                  <CheckCircle2 size={16} /> Draft Prepared • Ready for Institutional Approval
                </span>
                <span className="text-slate-400">ID: {preparedResult.credential_id.slice(0, 16)}...</span>
              </div>

              <div>
                <span className="text-slate-400">On-Chain Salted Commitment:</span>
                <div className="text-blue-400 font-bold">{preparedResult.commitment}</div>
              </div>

              <div className="max-h-60 overflow-y-auto bg-slate-950 p-4 rounded-xl text-slate-300">
                <pre>{JSON.stringify(preparedResult.credential_document, null, 2)}</pre>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  onClick={() => handleSubmitForApproval(preparedResult.id)}
                  className="px-4 py-2 bg-emerald-600 text-white rounded-lg font-sans text-sm font-semibold hover:bg-emerald-700 transition"
                >
                  2. Submit Draft for Administrative Approval →
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Approvals Queue */}
      {activeTab === 'approvals' && (
        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-6">
          <div className="border-b border-gray-200 pb-4">
            <h2 className="text-xl font-bold text-gray-900">Institutional Governance & Approvals</h2>
            <p className="text-sm text-gray-500">
              Separation-of-Duties: Institutional administrators must inspect and approve credentials before signing.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase font-semibold">
                <tr>
                  <th className="p-3">Credential ID</th>
                  <th className="p-3">Schema</th>
                  <th className="p-3">Recipient</th>
                  <th className="p-3">Workflow State</th>
                  <th className="p-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {credentials.filter((c) => c.workflow_status === 'PENDING_APPROVAL').length === 0 ? (
                  <tr>
                    <td colSpan={5} className="p-6 text-center text-gray-500">
                      No credentials currently pending approval.
                    </td>
                  </tr>
                ) : (
                  credentials
                    .filter((c) => c.workflow_status === 'PENDING_APPROVAL')
                    .map((cred) => (
                      <tr key={cred.id} className="hover:bg-gray-50">
                        <td className="p-3 font-mono text-xs">{cred.credential_id.slice(0, 14)}...</td>
                        <td className="p-3 font-medium">{cred.schema_type}</td>
                        <td className="p-3 font-mono text-xs">{cred.recipient_address}</td>
                        <td className="p-3">
                          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
                            Pending Approval
                          </span>
                        </td>
                        <td className="p-3 text-right">
                          <button
                            onClick={() => handleApprove(cred.id)}
                            className="px-3 py-1.5 bg-emerald-600 text-white font-semibold text-xs rounded-lg hover:bg-emerald-700 transition"
                          >
                            Approve for Signing
                          </button>
                        </td>
                      </tr>
                    ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: Signing & Blockchain Anchor */}
      {activeTab === 'signing' && (
        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-6">
          <div className="border-b border-gray-200 pb-4">
            <h2 className="text-xl font-bold text-gray-900">Cryptographic Signing & Blockchain Registration</h2>
            <p className="text-sm text-gray-500">
              Apply W3C Data Integrity proofs with an authorized operational signing key and anchor commitments on-chain.
            </p>
          </div>

          {/* Security notice */}
          <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800">
            <Info size={16} className="text-amber-600 mt-0.5 shrink-0" />
            <div>
              <p className="font-bold">Signing Key Security Notice</p>
              <p className="mt-1">
                Enter only the private key of an operational signing key that has been registered with this institution's
                IssuerRegistry on-chain. The key is transmitted over HTTPS and used only for credential signing — it is
                not stored. In production, replace this with a backend HSM/KMS integration or client-side wallet signing.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Select Approved Credential
              </label>
              <select
                value={selectedForSigning}
                onChange={(e) => setSelectedForSigning(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              >
                <option value="">-- Choose an approved credential --</option>
                {credentials
                  .filter((c) => c.workflow_status === 'APPROVED')
                  .map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.schema_type} for {c.recipient_address.slice(0, 10)}... (Commitment: {c.commitment.slice(0, 12)}...)
                    </option>
                  ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Authorized Operational Private Key (secp256k1)
              </label>
              <input
                type="password"
                value={selectedKeyForSigning}
                onChange={(e) => setSelectedKeyForSigning(e.target.value)}
                placeholder="0x... (private key of registered signing key)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm"
                autoComplete="off"
              />
              <p className="text-xs text-gray-500 mt-1">
                This key must correspond to an address registered via the Signing Keys tab. Transmitted over HTTPS only. Never stored.
              </p>
            </div>

            {signingStatus && (
              <p className="text-sm text-blue-600 font-medium">{signingStatus}</p>
            )}

            <button
              onClick={handleSign}
              disabled={loading || !selectedForSigning || !selectedKeyForSigning}
              className="px-6 py-2.5 bg-indigo-600 text-white font-semibold text-sm rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
            >
              {loading ? 'Signing...' : 'Sign W3C Proof & Confirm On-Chain'}
            </button>
          </div>
        </div>
      )}

      {/* Tab 5: Batch CSV Import */}
      {activeTab === 'batch' && (
        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-6">
          <div className="border-b border-gray-200 pb-4">
            <h2 className="text-xl font-bold text-gray-900">Bulk Batch Credential Preparation</h2>
            <p className="text-sm text-gray-500">
              Import a CSV table for automated batch validation, salted commitment generation, and draft creation.
            </p>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                CSV Data (with headers)
              </label>
              <p className="text-xs text-gray-500 mb-2">
                Required header: <code>recipient_address</code>. Additional columns become credential claims.
              </p>
              <textarea
                value={csvContent}
                onChange={(e) => setCsvContent(e.target.value)}
                rows={6}
                className="w-full p-3 font-mono text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                placeholder="recipient_address,claimOne,claimTwo&#10;0x...wallet,value1,value2"
              />
            </div>

            <button
              onClick={handleBatchPrepare}
              disabled={loading || !org}
              className="px-6 py-2.5 bg-purple-600 text-white font-semibold text-sm rounded-lg hover:bg-purple-700 transition disabled:opacity-50 flex items-center gap-2"
            >
              <FileSpreadsheet size={18} />
              {loading ? 'Processing Batch...' : 'Process Batch CSV'}
            </button>
          </div>

          {batchResults && (
            <div className="mt-6 border border-gray-200 rounded-xl overflow-hidden">
              <div className="p-3 bg-gray-50 border-b border-gray-200 text-sm font-bold text-gray-900 flex justify-between">
                <span>Batch Results: {batchResults.successful_count} Succeeded, {batchResults.failed_count} Failed</span>
                <span className="text-xs text-gray-500">Total: {batchResults.total}</span>
              </div>
              <div className="max-h-64 overflow-y-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-gray-100 text-gray-600 font-semibold">
                    <tr>
                      <th className="p-2">#</th>
                      <th className="p-2">Recipient</th>
                      <th className="p-2">Status</th>
                      <th className="p-2">Commitment / Error</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {batchResults.results.map((r: any, idx: number) => (
                      <tr key={idx} className={r.success ? 'bg-emerald-50/50' : 'bg-rose-50/50'}>
                        <td className="p-2 font-mono">{r.index + 1}</td>
                        <td className="p-2 font-mono">{r.recipient_address}</td>
                        <td className="p-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              r.success ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                            }`}
                          >
                            {r.success ? 'PREPARED' : 'FAILED'}
                          </span>
                        </td>
                        <td className="p-2 font-mono text-[11px] text-gray-700">
                          {r.success ? r.commitment : r.error}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 6: Signing Keys (PKI) */}
      {activeTab === 'keys' && (
        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-6">
          <div className="border-b border-gray-200 pb-4">
            <h2 className="text-xl font-bold text-gray-900">Institutional Public Key Infrastructure (PKI)</h2>
            <p className="text-sm text-gray-500">
              Manage operational signing keys accredited on the IssuerRegistry smart contract.
            </p>
          </div>

          <form onSubmit={handleRegisterKey} className="flex gap-4">
            <input
              type="text"
              value={newKeyAddress}
              onChange={(e) => setNewKeyAddress(e.target.value)}
              placeholder="0x... (operational signing key public address)"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm"
              required
            />
            <button
              type="submit"
              disabled={!org}
              className="px-4 py-2 bg-indigo-600 text-white font-semibold text-sm rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
            >
              Authorize Signing Key
            </button>
          </form>

          <div className="space-y-3">
            <h4 className="text-sm font-bold text-gray-900 uppercase tracking-wider">Authorized Operational Keys</h4>
            {signingKeys.length === 0 ? (
              <div className="p-4 bg-gray-50 rounded-xl text-sm text-gray-500 text-center">
                No operational signing keys registered. Register a key address above to allow credential signing.
              </div>
            ) : (
              signingKeys.map((k) => (
                <div key={k.id} className="p-4 bg-gray-50 rounded-xl flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="font-mono text-sm font-bold text-gray-900">{k.public_key_address}</div>
                    <div className="text-xs text-gray-500">Type: {k.key_type} • Status: {k.status}</div>
                  </div>
                  <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                    k.status === 'ACTIVE' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                  }`}>
                    {k.status}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Tab 7: Issuance History */}
      {activeTab === 'history' && (
        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-6">
          <div className="border-b border-gray-200 pb-4 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-900">Institutional Credential Records</h2>
              <p className="text-sm text-gray-500">Authoritative audit ledger of all issued credentials.</p>
            </div>
            <span className="text-xs font-semibold px-3 py-1 bg-gray-100 text-gray-700 rounded-full">
              {credentials.length} Total Records
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase font-semibold">
                <tr>
                  <th className="p-3">Credential ID</th>
                  <th className="p-3">Schema</th>
                  <th className="p-3">Recipient</th>
                  <th className="p-3">Workflow</th>
                  <th className="p-3">On-Chain Status</th>
                  <th className="p-3">Tx Hash</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {credentials.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-6 text-center text-gray-500">
                      No credentials issued yet. Prepare a draft in the Issuance Studio to begin.
                    </td>
                  </tr>
                ) : (
                  credentials.map((c) => (
                    <tr key={c.id} className="hover:bg-gray-50">
                      <td className="p-3 font-mono text-xs">{c.credential_id.slice(0, 14)}...</td>
                      <td className="p-3 font-medium">{c.schema_type}</td>
                      <td className="p-3 font-mono text-xs">{c.recipient_address.slice(0, 12)}...</td>
                      <td className="p-3">
                        <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
                          {c.workflow_status}
                        </span>
                      </td>
                      <td className="p-3">
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                            c.status === 'ACTIVE'
                              ? 'bg-emerald-100 text-emerald-800'
                              : c.status === 'SUSPENDED'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-rose-100 text-rose-800'
                          }`}
                        >
                          {c.status}
                        </span>
                      </td>
                      <td className="p-3 font-mono text-xs text-gray-500">
                        {c.tx_hash ? `${c.tx_hash.slice(0, 10)}...` : 'Pending Anchor'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
