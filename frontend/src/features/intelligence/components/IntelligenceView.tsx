import React, { useState, useEffect } from 'react';
import {
  Brain,
  Upload,
  CheckCircle2,
  XCircle,
  ArrowRight,
  ShieldAlert,
  Sparkles,
  Lock,
  FileCheck,
} from 'lucide-react';
import { useWallet } from '../../authentication/hooks/useWallet';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Badge } from '../../../components/ui/Badge';
import { Input } from '../../../components/ui/Input';
import { Select } from '../../../components/ui/Select';
import { fetchApi } from '../../../app/config/api';

interface ExtractedField {
  value: any;
  confidence: number;
  evidence_snippet?: string;
  is_valid: boolean;
  human_corrected: boolean;
}

interface AnomalyFinding {
  rule: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  description: string;
  evidence?: string;
}

interface DocumentExtraction {
  id: string;
  document_id: string;
  filename: string;
  mime_type: string;
  status: string;
  schema_type: string;
  raw_text: string;
  extracted_fields: Record<string, ExtractedField>;
  anomaly_findings: AnomalyFinding[];
  overall_confidence: number;
  review_status: 'PENDING_REVIEW' | 'APPROVED' | 'REJECTED';
  reviewed_by?: string;
  reviewed_at?: string;
  credential_id?: string;
  created_at: string;
}

interface OrgInfo {
  id: string;
  name: string;
  on_chain_address?: string;
}

export const IntelligenceView: React.FC = () => {
  const { account } = useWallet();
  const [organizations, setOrganizations] = useState<OrgInfo[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [extraction, setExtraction] = useState<DocumentExtraction | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Correction and preparation form state
  const [editingFields, setEditingFields] = useState<Record<string, string>>({});
  const [recipientAddress, setRecipientAddress] = useState<string>('');
  const [preparing, setPreparing] = useState<boolean>(false);
  const [preparedSummary, setPreparedSummary] = useState<any | null>(null);

  useEffect(() => {
    loadOrganizations();
    loadExistingDemoExtraction();
  }, [account]);

  const loadOrganizations = async () => {
    try {
      const data = await fetchApi<any>('/organizations');
      const items = data.items || (Array.isArray(data) ? data : []);
      setOrganizations(items);
      if (items.length > 0 && !selectedOrgId) {
        setSelectedOrgId(items[0].id);
      }
    } catch (err: any) {
      console.error('Failed to load organizations:', err);
    }
  };

  const loadExistingDemoExtraction = async () => {
    try {
      const data = await fetchApi<DocumentExtraction>('/intelligence/documents/00000000-0000-0000-0000-000000000301');
      if (data) {
        setExtraction(data);
        const initialEdits: Record<string, string> = {};
        if (data.extracted_fields) {
          Object.entries(data.extracted_fields).forEach(([k, v]: [string, any]) => {
            initialEdits[k] = String(v.value);
          });
        }
        setEditingFields(initialEdits);
        setRecipientAddress('0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC');
      }
    } catch (err: any) {
      console.error('No existing demo extraction:', err);
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !selectedOrgId) {
      setError('Please select an organization and a document to upload.');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccessMsg(null);
    setExtraction(null);
    setPreparedSummary(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('organization_id', selectedOrgId);

    try {
      const res = await fetch('/api/v1/intelligence/upload', {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error?.message || data.detail || 'Upload failed');
      }

      setExtraction(data);
      // Initialize edit fields
      const initialEdits: Record<string, string> = {};
      Object.entries(data.extracted_fields).forEach(([k, v]: [string, any]) => {
        initialEdits[k] = String(v.value);
      });
      setEditingFields(initialEdits);
      setSuccessMsg('Document successfully ingested, scanned, and analyzed.');
    } catch (err: any) {
      setError(err.message || 'Failed to process document');
    } finally {
      setUploading(false);
    }
  };

  const handleReviewAction = async (action: 'APPROVE' | 'REJECT' | 'UPDATE') => {
    if (!extraction) return;
    setError(null);
    setSuccessMsg(null);

    try {
      const res = await fetch(`/api/v1/intelligence/documents/${extraction.document_id}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          review_action: action,
          corrected_fields: editingFields,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error?.message || data.detail || 'Review update failed');
      }

      setExtraction(data);
      setSuccessMsg(`Document extraction state updated to: ${action}.`);
    } catch (err: any) {
      setError(err.message || 'Failed to submit review');
    }
  };

  const handlePrepareCredential = async () => {
    if (!extraction || !recipientAddress) {
      setError('Please provide the recipient holder Ethereum wallet address.');
      return;
    }

    setPreparing(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const res = await fetch(`/api/v1/intelligence/documents/${extraction.document_id}/prepare-credential`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          recipient_address: recipientAddress,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error?.message || data.detail || 'Credential preparation failed');
      }

      setPreparedSummary(data);
      setSuccessMsg('Credential prepared into the institutional approval pipeline!');
    } catch (err: any) {
      setError(err.message || 'Failed to prepare credential');
    } finally {
      setPreparing(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      {/* Editorial Page Header */}
      <div className="border-b border-border pb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-primary font-semibold text-xs tracking-wider uppercase mb-1">
            <Sparkles size={15} />
            <span>Document Intelligence Workspace</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">
            OCR Extraction & Anomaly Detection
          </h1>
          <p className="text-sm text-foreground-secondary mt-1 max-w-xl leading-relaxed">
            Ingest certificates, transcripts, and official documentation with automated field extraction, schema alignment, and cross-record integrity checks.
          </p>
        </div>

        {/* Governance Rule Badge */}
        <div className="p-3 bg-surface-subtle rounded-control border border-border-subtle flex items-center gap-3 text-xs shrink-0 max-w-xs">
          <Lock className="text-primary shrink-0" size={18} />
          <div>
            <span className="font-semibold text-foreground block">Separation of Duties</span>
            <span className="text-[11px] text-foreground-secondary">
              AI assists extraction. Human review & cryptographic signing required.
            </span>
          </div>
        </div>
      </div>

      {/* Global Alerts */}
      {error && (
        <div className="p-3.5 rounded-control bg-status-danger-soft border border-status-danger/30 flex items-start gap-2.5 text-xs text-status-danger">
          <XCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block">Operation Error</span>
            <span>{error}</span>
          </div>
        </div>
      )}

      {successMsg && (
        <div className="p-3.5 rounded-control bg-status-success-soft border border-status-success/30 flex items-start gap-2.5 text-xs text-status-success">
          <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block">Operation Completed</span>
            <span>{successMsg}</span>
          </div>
        </div>
      )}

      {/* Document Intake Card */}
      <Card className="space-y-4">
        <div className="border-b border-border pb-3">
          <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
            <Upload size={16} className="text-primary" />
            Document Intake & Ingestion
          </h2>
          <p className="text-xs text-foreground-secondary mt-0.5">
            Select the issuing organization tenant and upload a digital credential document for automated processing.
          </p>
        </div>

        <form onSubmit={handleFileUpload} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Issuing Organization Tenant"
              value={selectedOrgId}
              onChange={(e) => setSelectedOrgId(e.target.value)}
            >
              {organizations.map((org) => (
                <option key={org.id} value={org.id}>
                  {org.name}
                </option>
              ))}
            </Select>

            <div>
              <label className="block text-xs font-semibold text-foreground mb-1.5">
                Document File (PDF, PNG, JPG)
              </label>
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.txt"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="w-full text-xs text-foreground-secondary file:mr-3 file:py-1.5 file:px-3 file:rounded-control file:border-0 file:text-xs file:font-semibold file:bg-primary-soft file:text-primary hover:file:bg-primary-soft/80 cursor-pointer border border-border rounded-control p-1 bg-surface shadow-subtle"
              />
            </div>
          </div>

          <div className="flex justify-end pt-2 border-t border-border">
            <Button
              type="submit"
              variant="primary"
              size="md"
              isLoading={uploading}
              disabled={!file || !selectedOrgId}
              leftIcon={<Brain size={15} />}
            >
              Run Document Extraction
            </Button>
          </div>
        </form>
      </Card>

      {/* Extraction & Anomaly Report */}
      {extraction && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in duration-200">
          {/* Left Column: Extraction Overview & Anomaly Findings */}
          <div className="lg:col-span-1 space-y-4">
            {/* Confidence & Schema Card */}
            <Card className="space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-border">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted">
                  Extraction Confidence
                </span>
                <Badge
                  variant={
                    extraction.overall_confidence >= 0.8
                      ? 'success'
                      : extraction.overall_confidence >= 0.6
                      ? 'warning'
                      : 'danger'
                  }
                  size="sm"
                >
                  {Math.round(extraction.overall_confidence * 100)}% Confidence
                </Badge>
              </div>

              <div>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block">
                  Matched Credential Schema
                </span>
                <span className="text-xs font-semibold text-foreground mt-0.5 block truncate">
                  {extraction.schema_type}
                </span>
              </div>

              <div>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block">
                  Human Review Status
                </span>
                <div className="mt-1">
                  <Badge
                    variant={
                      extraction.review_status === 'APPROVED'
                        ? 'success'
                        : extraction.review_status === 'REJECTED'
                        ? 'danger'
                        : 'warning'
                    }
                    size="md"
                    dot
                  >
                    {extraction.review_status}
                  </Badge>
                </div>
              </div>
            </Card>

            {/* Anomaly Detection Findings Card */}
            <Card className="space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-border">
                <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                  <ShieldAlert
                    size={15}
                    className={
                      extraction.anomaly_findings.length > 0
                        ? 'text-status-warning'
                        : 'text-status-success'
                    }
                  />
                  Anomaly & Integrity Audit
                </span>
                <Badge variant="neutral" size="sm">
                  {extraction.anomaly_findings.length} Findings
                </Badge>
              </div>

              {extraction.anomaly_findings.length === 0 ? (
                <div className="p-3 bg-status-success-soft text-status-success rounded-control text-xs flex items-center gap-2 border border-status-success/20">
                  <CheckCircle2 size={15} className="shrink-0" />
                  <span>No suspicious inconsistencies or collisions detected.</span>
                </div>
              ) : (
                <div className="space-y-2">
                  {extraction.anomaly_findings.map((finding, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-control border text-xs space-y-1 ${
                        finding.severity === 'CRITICAL'
                          ? 'bg-status-danger-soft border-status-danger/30 text-status-danger'
                          : finding.severity === 'HIGH'
                          ? 'bg-status-warning-soft border-status-warning/30 text-status-warning'
                          : 'bg-surface-subtle border-border text-foreground'
                      }`}
                    >
                      <div className="flex items-center justify-between font-semibold">
                        <span>{finding.rule}</span>
                        <Badge
                          variant={
                            finding.severity === 'CRITICAL'
                              ? 'danger'
                              : finding.severity === 'HIGH'
                              ? 'warning'
                              : 'neutral'
                          }
                          size="sm"
                        >
                          {finding.severity}
                        </Badge>
                      </div>
                      <p className="text-[11px] opacity-90">{finding.description}</p>
                      {finding.evidence && (
                        <div className="font-mono text-[10px] text-foreground-muted pt-0.5 truncate">
                          Evidence: {finding.evidence}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>

          {/* Right Column: Field-Level Review & Pipeline Submission */}
          <div className="lg:col-span-2 space-y-4">
            <Card className="space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border">
                <div>
                  <h3 className="text-sm font-semibold text-foreground">
                    Extracted Credential Claims
                  </h3>
                  <p className="text-xs text-foreground-secondary mt-0.5">
                    Inspect and correct field values before submitting to the approval pipeline.
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleReviewAction('APPROVE')}
                    leftIcon={<FileCheck size={13} />}
                  >
                    Approve Extraction
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => handleReviewAction('REJECT')}
                    leftIcon={<XCircle size={13} />}
                  >
                    Reject
                  </Button>
                </div>
              </div>

              {/* Editable Fields Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {Object.entries(extraction.extracted_fields).map(([fieldName, fieldData]) => (
                  <div
                    key={fieldName}
                    className="p-3 bg-surface-subtle rounded-control border border-border-subtle space-y-1.5"
                  >
                    <div className="flex items-center justify-between text-xs font-semibold text-foreground">
                      <span className="capitalize">{fieldName.replace(/([A-Z])/g, ' $1')}</span>
                      <span className="text-[10px] font-mono text-foreground-muted">
                        {Math.round(fieldData.confidence * 100)}% conf
                      </span>
                    </div>
                    <Input
                      type="text"
                      value={editingFields[fieldName] ?? ''}
                      onChange={(e) =>
                        setEditingFields({ ...editingFields, [fieldName]: e.target.value })
                      }
                      className="bg-surface"
                    />
                    {fieldData.evidence_snippet && (
                      <p
                        className="text-[10px] text-foreground-muted truncate"
                        title={fieldData.evidence_snippet}
                      >
                        Evidence: "{fieldData.evidence_snippet}"
                      </p>
                    )}
                  </div>
                ))}
              </div>

              {/* Credential Preparation Gateway */}
              <div className="border-t border-border pt-4 space-y-3">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-foreground-secondary flex items-center gap-1.5">
                  <ArrowRight size={14} className="text-primary" />
                  <span>Prepare Verifiable Credential from Extraction</span>
                </h4>

                <div className="flex flex-col sm:flex-row gap-3 items-end">
                  <Input
                    label="Recipient Holder Wallet Address"
                    type="text"
                    placeholder="0x... (holder wallet address)"
                    value={recipientAddress}
                    onChange={(e) => setRecipientAddress(e.target.value)}
                    className="font-mono text-xs flex-1"
                  />

                  <Button
                    variant="primary"
                    size="md"
                    onClick={handlePrepareCredential}
                    isLoading={preparing}
                    disabled={extraction.review_status !== 'APPROVED' || !recipientAddress}
                    className="shrink-0"
                  >
                    Prepare Draft
                  </Button>
                </div>

                {extraction.review_status !== 'APPROVED' && (
                  <div className="p-3 rounded-control bg-status-warning-soft border border-status-warning/20 text-xs text-status-warning">
                    Extraction must be approved by authorized staff before submitting into the credential pipeline.
                  </div>
                )}

                {preparedSummary && (
                  <div className="p-4 bg-status-success-soft border border-status-success/30 rounded-control space-y-1.5 text-xs text-status-success">
                    <span className="font-semibold text-foreground block">
                      Credential Draft Prepared Successfully
                    </span>
                    <div>
                      <span className="text-foreground-muted">W3C ID: </span>
                      <span className="font-mono">{preparedSummary.w3c_id}</span>
                    </div>
                    <div>
                      <span className="text-foreground-muted">Commitment: </span>
                      <span className="font-mono">{preparedSummary.commitment}</span>
                    </div>
                    {preparedSummary.notice && (
                      <p className="text-[11px] text-foreground-secondary pt-1">
                        {preparedSummary.notice}
                      </p>
                    )}
                  </div>
                )}
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};
