import React, { useState, useEffect } from 'react';
import {
  Building2,
  Key,
  FileSpreadsheet,
  Award,
  CheckCircle2,
  Clock,
  AlertTriangle,
  PlusCircle,
  FileCheck,
  RefreshCw,
  Info,
  ArrowRight,
} from 'lucide-react';
import { fetchApi } from '../../../app/config/api';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Badge } from '../../../components/ui/Badge';
import { Input } from '../../../components/ui/Input';
import { Select } from '../../../components/ui/Select';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../../../components/ui/Table';

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

  // Single Issuance Form State
  const [selectedSchema, setSelectedSchema] = useState<string>('UniversityDegreeCredential');
  const [recipientAddress, setRecipientAddress] = useState<string>('');
  const [formClaims, setFormClaims] = useState<Record<string, string>>({});
  const [preparedResult, setPreparedResult] = useState<any>(null);

  // Signing State
  const [selectedKeyForSigning, setSelectedKeyForSigning] = useState<string>('');
  const [selectedForSigning, setSelectedForSigning] = useState<string>('');
  const [signingStatus, setSigningStatus] = useState<string | null>(null);

  // Batch CSV State
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

  const getSchemaFields = (): string[] => {
    const schema = schemas.find((s) => s.name === selectedSchema || s.schema_id.includes(selectedSchema));
    if (schema) return schema.fields.map((f) => f.name);
    return Object.keys(formClaims).length > 0
      ? Object.keys(formClaims)
      : ['recipientName', 'degree', 'major', 'institutionName', 'graduationDate'];
  };

  const tabs = [
    { id: 'dashboard', label: 'Overview', icon: <Building2 size={15} /> },
    { id: 'prepare', label: 'Issue Credential', icon: <PlusCircle size={15} /> },
    { id: 'approvals', label: 'Approvals Queue', icon: <FileCheck size={15} />, badge: metrics?.pending_approval },
    { id: 'signing', label: 'Sign & Anchor', icon: <Award size={15} /> },
    { id: 'batch', label: 'Batch CSV', icon: <FileSpreadsheet size={15} /> },
    { id: 'keys', label: 'Signing Keys (PKI)', icon: <Key size={15} />, badge: metrics?.authorized_keys_count },
    { id: 'history', label: 'History & Ledger', icon: <Clock size={15} /> },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      {/* Editorial Header */}
      <div className="border-b border-border pb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-primary font-semibold text-xs tracking-wider uppercase mb-1">
            <Building2 size={15} />
            <span>Institutional Governance</span>
            {org && (
              <Badge variant="success" size="sm" dot>
                {org.status}
              </Badge>
            )}
          </div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">
            {org ? org.name : 'Institutional Issuer Portal'}
          </h1>
          <p className="text-sm text-foreground-secondary mt-1 max-w-xl leading-relaxed">
            Multi-tenant credential studio, separation-of-duties governance, and on-chain public key infrastructure.
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={() => org && refreshOrgData(org.id)}
            disabled={!org || loading}
            isLoading={loading}
            leftIcon={<RefreshCw size={13} />}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Organization Load Error */}
      {orgLoadError && (
        <div className="p-3.5 rounded-control bg-status-warning-soft border border-status-warning/30 text-status-warning flex items-start gap-2.5 text-xs">
          <AlertTriangle size={16} className="shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block">Organization Not Loaded</span>
            <p className="mt-0.5">{orgLoadError}</p>
          </div>
        </div>
      )}

      {/* Status Messages */}
      {statusMessage && (
        <div
          className={`p-3.5 rounded-control flex items-start gap-2.5 text-xs ${
            statusMessage.type === 'success'
              ? 'bg-status-success-soft border border-status-success/30 text-status-success'
              : 'bg-status-danger-soft border border-status-danger/30 text-status-danger'
          }`}
        >
          {statusMessage.type === 'success' ? (
            <CheckCircle2 size={16} className="shrink-0 mt-0.5" />
          ) : (
            <AlertTriangle size={16} className="shrink-0 mt-0.5" />
          )}
          <span className="flex-1 font-medium">{statusMessage.text}</span>
          <button
            onClick={() => setStatusMessage(null)}
            className="text-foreground-muted hover:text-foreground text-sm font-semibold ml-2"
          >
            ×
          </button>
        </div>
      )}

      {/* Institutional Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div className="p-4 bg-surface rounded-control border border-border shadow-subtle">
          <div className="flex items-center justify-between text-foreground-muted mb-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider">Total Issued</span>
            <Award size={15} className="text-primary" />
          </div>
          <span className="text-xl font-bold text-foreground">
            {metrics ? metrics.total_credentials : '—'}
          </span>
        </div>

        <div className="p-4 bg-surface rounded-control border border-border shadow-subtle">
          <div className="flex items-center justify-between text-foreground-muted mb-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider">Pending Review</span>
            <Clock size={15} className="text-status-warning" />
          </div>
          <span className="text-xl font-bold text-status-warning">
            {metrics ? metrics.pending_approval : '—'}
          </span>
        </div>

        <div className="p-4 bg-surface rounded-control border border-border shadow-subtle">
          <div className="flex items-center justify-between text-foreground-muted mb-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider">Active Status</span>
            <CheckCircle2 size={15} className="text-status-success" />
          </div>
          <span className="text-xl font-bold text-status-success">
            {metrics ? metrics.active_credentials : '—'}
          </span>
        </div>

        <div className="p-4 bg-surface rounded-control border border-border shadow-subtle">
          <div className="flex items-center justify-between text-foreground-muted mb-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider">Suspended / Revoked</span>
            <AlertTriangle size={15} className="text-status-danger" />
          </div>
          <span className="text-xl font-bold text-status-danger">
            {metrics ? metrics.suspended_credentials + metrics.revoked_credentials : '—'}
          </span>
        </div>

        <div className="p-4 bg-surface rounded-control border border-border shadow-subtle">
          <div className="flex items-center justify-between text-foreground-muted mb-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider">Authorized PKI Keys</span>
            <Key size={15} className="text-primary" />
          </div>
          <span className="text-xl font-bold text-primary">
            {metrics ? metrics.authorized_keys_count : '—'}
          </span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-1 border-b border-border overflow-x-auto scrollbar-none pb-0.5">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-3.5 py-2.5 text-xs font-medium border-b-2 transition-colors whitespace-nowrap -mb-px ${
                isActive
                  ? 'border-primary text-primary font-semibold'
                  : 'border-transparent text-foreground-secondary hover:text-foreground hover:border-border-strong'
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {tab.badge !== undefined && Number(tab.badge) > 0 && (
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                    isActive
                      ? 'bg-primary text-white'
                      : 'bg-surface-subtle text-foreground-secondary border border-border'
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab 1: Overview */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="flex flex-col justify-between space-y-3">
              <div>
                <div className="w-9 h-9 rounded-control bg-primary-soft text-primary flex items-center justify-center mb-2.5">
                  <PlusCircle size={18} />
                </div>
                <h3 className="text-sm font-semibold text-foreground">Prepare Credential</h3>
                <p className="text-xs text-foreground-secondary mt-1 leading-relaxed">
                  Use validated schemas to generate salted privacy commitments and prepare drafts.
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setActiveTab('prepare')}
                rightIcon={<ArrowRight size={13} />}
                className="w-full mt-2"
              >
                Launch Studio
              </Button>
            </Card>

            <Card className="flex flex-col justify-between space-y-3">
              <div>
                <div className="w-9 h-9 rounded-control bg-status-warning-soft text-status-warning flex items-center justify-center mb-2.5">
                  <FileCheck size={18} />
                </div>
                <h3 className="text-sm font-semibold text-foreground">Governance Approvals</h3>
                <p className="text-xs text-foreground-secondary mt-1 leading-relaxed">
                  Multi-party approval queue enforcing separation of duties before cryptographic signing.
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setActiveTab('approvals')}
                rightIcon={<ArrowRight size={13} />}
                className="w-full mt-2"
              >
                View Pending ({metrics?.pending_approval ?? 0})
              </Button>
            </Card>

            <Card className="flex flex-col justify-between space-y-3">
              <div>
                <div className="w-9 h-9 rounded-control bg-primary-soft text-primary flex items-center justify-center mb-2.5">
                  <FileSpreadsheet size={18} />
                </div>
                <h3 className="text-sm font-semibold text-foreground">Bulk Batch Issuance</h3>
                <p className="text-xs text-foreground-secondary mt-1 leading-relaxed">
                  Upload CSV tables of recipients with strict schema validation and commitment anchoring.
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setActiveTab('batch')}
                rightIcon={<ArrowRight size={13} />}
                className="w-full mt-2"
              >
                Import Batch CSV
              </Button>
            </Card>
          </div>

          {org && (
            <Card className="space-y-3">
              <h3 className="text-sm font-semibold text-foreground">
                Institutional Accreditation & Registry Status
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div className="p-3 bg-surface-subtle rounded-control border border-border-subtle">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block mb-0.5">
                    On-Chain Primary Identity
                  </span>
                  <div className="font-mono text-foreground break-all">
                    {org.on_chain_address || 'Not registered on-chain'}
                  </div>
                </div>
                <div className="p-3 bg-surface-subtle rounded-control border border-border-subtle">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block mb-0.5">
                    Legal Entity Identifier & Domain
                  </span>
                  <div className="text-foreground font-medium">
                    {org.legal_entity_id} • Domain: {org.domain}
                  </div>
                </div>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Tab 2: Issue Credential Studio */}
      {activeTab === 'prepare' && (
        <Card className="space-y-6">
          <div className="border-b border-border pb-3">
            <h2 className="text-base font-semibold text-foreground">
              Credential Preparation Studio
            </h2>
            <p className="text-xs text-foreground-secondary mt-0.5">
              Enter recipient claims. Claims and salts are automatically encrypted at rest using AES-256-GCM.
            </p>
          </div>

          <form onSubmit={handlePrepareCredential} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Select
                label="Credential Schema Type"
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
              >
                <option value="UniversityDegreeCredential">University Degree Credential</option>
                <option value="AcademicTranscriptCredential">Academic Transcript</option>
                <option value="CourseCompletionCertificate">Course Completion Certificate</option>
                <option value="ProfessionalCertification">Professional Certification</option>
                <option value="EmploymentVerificationCredential">Employment Verification Credential</option>
              </Select>

              <Input
                label="Recipient Wallet Address"
                type="text"
                value={recipientAddress}
                onChange={(e) => setRecipientAddress(e.target.value)}
                placeholder="0x... (student/professional holder address)"
                className="font-mono text-xs"
                required
              />
            </div>

            {/* Dynamic Claims Form */}
            <div className="bg-surface-subtle p-4 rounded-control border border-border-subtle space-y-3">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block">
                Schema Claims: {selectedSchema}
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {getSchemaFields().map((claimKey) => (
                  <Input
                    key={claimKey}
                    label={claimKey.replace(/([A-Z])/g, ' $1')}
                    type="text"
                    value={formClaims[claimKey] || ''}
                    onChange={(e) => setFormClaims({ ...formClaims, [claimKey]: e.target.value })}
                    required
                  />
                ))}
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-border">
              <Button
                type="submit"
                variant="primary"
                size="md"
                isLoading={loading}
                disabled={!org}
              >
                1. Prepare Credential Draft
              </Button>
            </div>
          </form>

          {/* Prepared Draft Preview */}
          {preparedResult && (
            <div className="mt-6 p-4 bg-surface-subtle rounded-control border border-border font-mono text-xs space-y-3">
              <div className="flex items-center justify-between border-b border-border pb-2.5">
                <span className="text-status-success font-semibold flex items-center gap-1.5 font-sans text-xs">
                  <CheckCircle2 size={15} /> Draft Prepared • Ready for Institutional Approval
                </span>
                <span className="text-foreground-muted text-[11px]">ID: {preparedResult.credential_id.slice(0, 16)}...</span>
              </div>

              <div>
                <span className="text-foreground-muted text-[11px] block">On-Chain Salted Commitment:</span>
                <div className="text-primary font-bold break-all mt-0.5">{preparedResult.commitment}</div>
              </div>

              <div className="max-h-48 overflow-y-auto bg-surface p-3 rounded-control border border-border text-foreground-secondary">
                <pre>{JSON.stringify(preparedResult.credential_document, null, 2)}</pre>
              </div>

              <div className="flex items-center justify-end pt-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleSubmitForApproval(preparedResult.id)}
                  rightIcon={<ArrowRight size={13} />}
                >
                  2. Submit Draft for Administrative Approval
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Tab 3: Approvals Queue */}
      {activeTab === 'approvals' && (
        <Card className="space-y-4">
          <div className="border-b border-border pb-3">
            <h2 className="text-base font-semibold text-foreground">
              Institutional Governance & Approvals
            </h2>
            <p className="text-xs text-foreground-secondary mt-0.5">
              Separation of Duties: Institutional administrators inspect and approve drafts before cryptographic signing.
            </p>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Credential ID</TableHead>
                <TableHead>Schema</TableHead>
                <TableHead>Recipient</TableHead>
                <TableHead>Workflow State</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {credentials.filter((c) => c.workflow_status === 'PENDING_APPROVAL').length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="py-8 text-center text-foreground-secondary">
                    No credentials currently pending approval.
                  </TableCell>
                </TableRow>
              ) : (
                credentials
                  .filter((c) => c.workflow_status === 'PENDING_APPROVAL')
                  .map((cred) => (
                    <TableRow key={cred.id}>
                      <TableCell className="font-mono">{cred.credential_id.slice(0, 14)}...</TableCell>
                      <TableCell className="font-medium">{cred.schema_type}</TableCell>
                      <TableCell className="font-mono">{cred.recipient_address.slice(0, 12)}...</TableCell>
                      <TableCell>
                        <Badge variant="warning" size="sm">
                          Pending Approval
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => handleApprove(cred.id)}
                        >
                          Approve
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
              )}
            </TableBody>
          </Table>
        </Card>
      )}

      {/* Tab 4: Signing & Blockchain Anchor */}
      {activeTab === 'signing' && (
        <Card className="space-y-5">
          <div className="border-b border-border pb-3">
            <h2 className="text-base font-semibold text-foreground">
              Cryptographic Signing & Blockchain Anchor
            </h2>
            <p className="text-xs text-foreground-secondary mt-0.5">
              Apply W3C Data Integrity proofs with an authorized operational signing key and anchor commitments on-chain.
            </p>
          </div>

          <div className="p-3.5 rounded-control bg-status-info-soft border border-status-info/30 text-status-info flex items-start gap-2.5 text-xs">
            <Info size={16} className="shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold block">Authorized Key Security Protocol</span>
              <p className="mt-0.5 text-foreground-secondary">
                Select an authorized operational signing key registered on the IssuerRegistry. Keys are transmitted over HTTPS and never stored.
              </p>
            </div>
          </div>

          <div className="space-y-4 max-w-xl">
            <Select
              label="Select Approved Credential"
              value={selectedForSigning}
              onChange={(e) => setSelectedForSigning(e.target.value)}
            >
              <option value="">-- Choose an approved credential --</option>
              {credentials
                .filter((c) => c.workflow_status === 'APPROVED')
                .map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.schema_type} for {c.recipient_address.slice(0, 10)}... (Commitment: {c.commitment.slice(0, 12)}...)
                  </option>
                ))}
            </Select>

            <Input
              label="Authorized Operational Private Key (secp256k1)"
              type="password"
              value={selectedKeyForSigning}
              onChange={(e) => setSelectedKeyForSigning(e.target.value)}
              placeholder="0x... (private key of registered signing key)"
              className="font-mono text-xs"
              autoComplete="off"
              helperText="Must correspond to an authorized address registered in the Signing Keys tab."
            />

            {signingStatus && (
              <p className="text-xs font-semibold text-primary">{signingStatus}</p>
            )}

            <Button
              variant="primary"
              size="md"
              onClick={handleSign}
              isLoading={loading}
              disabled={!selectedForSigning || !selectedKeyForSigning}
            >
              Sign W3C Proof & Confirm On-Chain
            </Button>
          </div>
        </Card>
      )}

      {/* Tab 5: Batch CSV Import */}
      {activeTab === 'batch' && (
        <Card className="space-y-5">
          <div className="border-b border-border pb-3">
            <h2 className="text-base font-semibold text-foreground">
              Bulk Batch Credential Preparation
            </h2>
            <p className="text-xs text-foreground-secondary mt-0.5">
              Import a CSV table for automated batch validation, salted commitment generation, and draft creation.
            </p>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-foreground mb-1.5">
                CSV Data (with headers)
              </label>
              <textarea
                value={csvContent}
                onChange={(e) => setCsvContent(e.target.value)}
                rows={6}
                className="w-full bg-surface text-foreground font-mono text-xs rounded-control border border-border p-3 focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 shadow-subtle"
                placeholder="recipient_address,claimOne,claimTwo&#10;0x...wallet,value1,value2"
              />
              <p className="text-[11px] text-foreground-secondary mt-1">
                Required header: <code className="bg-surface-subtle px-1 rounded font-mono">recipient_address</code>. Additional columns become credential claims.
              </p>
            </div>

            <Button
              variant="primary"
              size="md"
              onClick={handleBatchPrepare}
              isLoading={loading}
              disabled={!org}
              leftIcon={<FileSpreadsheet size={15} />}
            >
              Process Batch CSV
            </Button>
          </div>

          {batchResults && (
            <div className="mt-4 border border-border rounded-control overflow-hidden">
              <div className="p-3 bg-surface-subtle border-b border-border text-xs font-semibold text-foreground flex justify-between">
                <span>Batch Results: {batchResults.successful_count} Succeeded, {batchResults.failed_count} Failed</span>
                <span className="text-foreground-muted">Total: {batchResults.total}</span>
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>#</TableHead>
                    <TableHead>Recipient</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Commitment / Error</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {batchResults.results.map((r: any, idx: number) => (
                    <TableRow key={idx}>
                      <TableCell className="font-mono">{r.index + 1}</TableCell>
                      <TableCell className="font-mono">{r.recipient_address}</TableCell>
                      <TableCell>
                        <Badge variant={r.success ? 'success' : 'danger'} size="sm">
                          {r.success ? 'PREPARED' : 'FAILED'}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-[11px] text-foreground-secondary">
                        {r.success ? r.commitment : r.error}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </Card>
      )}

      {/* Tab 6: Signing Keys (PKI) */}
      {activeTab === 'keys' && (
        <Card className="space-y-5">
          <div className="border-b border-border pb-3">
            <h2 className="text-base font-semibold text-foreground">
              Institutional Public Key Infrastructure (PKI)
            </h2>
            <p className="text-xs text-foreground-secondary mt-0.5">
              Manage operational signing keys accredited on the IssuerRegistry smart contract.
            </p>
          </div>

          <form onSubmit={handleRegisterKey} className="flex flex-col sm:flex-row gap-3 max-w-xl">
            <Input
              type="text"
              value={newKeyAddress}
              onChange={(e) => setNewKeyAddress(e.target.value)}
              placeholder="0x... (operational signing key public address)"
              className="font-mono text-xs flex-1"
              required
            />
            <Button
              type="submit"
              variant="primary"
              size="md"
              disabled={!org}
              className="shrink-0"
            >
              Authorize Signing Key
            </Button>
          </form>

          <div className="space-y-2 pt-2">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block">
              Authorized Operational Keys
            </span>
            {signingKeys.length === 0 ? (
              <div className="p-6 bg-surface-subtle rounded-control border border-border-subtle text-xs text-foreground-secondary text-center">
                No operational signing keys registered. Register a key address above to allow credential signing.
              </div>
            ) : (
              <div className="divide-y divide-border border border-border rounded-control overflow-hidden">
                {signingKeys.map((k) => (
                  <div key={k.id} className="p-3 bg-surface flex items-center justify-between text-xs">
                    <div>
                      <span className="font-mono font-semibold text-foreground block">{k.public_key_address}</span>
                      <span className="text-[11px] text-foreground-muted">Type: {k.key_type}</span>
                    </div>
                    <Badge variant={k.status === 'ACTIVE' ? 'success' : 'danger'} size="sm" dot>
                      {k.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Tab 7: Issuance History */}
      {activeTab === 'history' && (
        <Card className="space-y-4">
          <div className="border-b border-border pb-3 flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-foreground">
                Institutional Credential Records
              </h2>
              <p className="text-xs text-foreground-secondary mt-0.5">Authoritative audit ledger of all issued credentials.</p>
            </div>
            <Badge variant="neutral" size="sm">
              {credentials.length} Total Records
            </Badge>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Credential ID</TableHead>
                <TableHead>Schema</TableHead>
                <TableHead>Recipient</TableHead>
                <TableHead>Workflow</TableHead>
                <TableHead>On-Chain Status</TableHead>
                <TableHead>Tx Hash</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {credentials.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="py-8 text-center text-foreground-secondary">
                    No credentials issued yet. Prepare a draft in the Issuance Studio to begin.
                  </TableCell>
                </TableRow>
              ) : (
                credentials.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell className="font-mono">{c.credential_id.slice(0, 14)}...</TableCell>
                    <TableCell className="font-medium">{c.schema_type}</TableCell>
                    <TableCell className="font-mono">{c.recipient_address.slice(0, 12)}...</TableCell>
                    <TableCell>
                      <Badge variant="info" size="sm">
                        {c.workflow_status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          c.status === 'ACTIVE'
                            ? 'success'
                            : c.status === 'SUSPENDED'
                            ? 'warning'
                            : 'danger'
                        }
                        size="sm"
                        dot
                      >
                        {c.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-[11px] text-foreground-muted">
                      {c.tx_hash ? `${c.tx_hash.slice(0, 10)}...` : 'Pending Anchor'}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
};
