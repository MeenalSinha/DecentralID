import React, { useState, useEffect } from 'react';
import {
  Brain,
  Upload,
  CheckCircle2,
  XCircle,
  ArrowRight,
  ShieldAlert,
  RefreshCw,
  Sparkles,
  Lock,
} from 'lucide-react';
import { useWallet } from '../../authentication/hooks/useWallet';

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
  }, [account]);

  const loadOrganizations = async () => {
    try {
      const res = await fetch('/api/v1/organizations', { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        const items = data.items || (Array.isArray(data) ? data : []);
        setOrganizations(items);
        if (items.length > 0 && !selectedOrgId) {
          setSelectedOrgId(items[0].id);
        }
      }
    } catch (err: any) {
      console.error('Failed to load organizations:', err);
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
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-indigo-900 to-blue-900 text-white rounded-2xl p-8 shadow-xl border border-indigo-800">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-indigo-500/30 text-indigo-200 rounded-full text-xs font-semibold tracking-wide border border-indigo-400/30">
              <Sparkles size={14} />
              <span>DecentralID Intelligence Engine</span>
            </div>
            <h1 className="text-3xl font-bold tracking-tight">AI Document Extraction & Anomaly Detection</h1>
            <p className="text-indigo-200 text-sm max-w-2xl">
              Upload institutional credentials (PDF/Images) to automatically extract claims, cross-reference schemas,
              flag suspicious anomalies, and convert verified records into the standard issuance pipeline.
            </p>
          </div>
          <div className="flex items-center gap-3 bg-white/10 backdrop-blur-sm p-4 rounded-xl border border-white/10 text-xs">
            <Lock className="text-indigo-300" size={24} />
            <div>
              <div className="font-semibold text-white">Non-Bypass Governance</div>
              <div className="text-indigo-200">AI never signs or issues directly. Human review required.</div>
            </div>
          </div>
        </div>
      </div>

      {/* Global Alerts */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3 text-red-800 text-sm">
          <XCircle className="w-5 h-5 flex-shrink-0 text-red-600 mt-0.5" />
          <div>
            <div className="font-semibold">Operation Error</div>
            <div>{error}</div>
          </div>
        </div>
      )}

      {successMsg && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-xl flex items-start gap-3 text-green-800 text-sm">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-green-600 mt-0.5" />
          <div>
            <div className="font-semibold">Success</div>
            <div>{successMsg}</div>
          </div>
        </div>
      )}

      {/* Document Intake Card */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
        <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Upload className="text-indigo-600" size={20} />
          <span>Upload Credential for Ingestion & Analysis</span>
        </h2>

        <form onSubmit={handleFileUpload} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
                Issuing Organization Tenant
              </label>
              <select
                value={selectedOrgId}
                onChange={(e) => setSelectedOrgId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {organizations.map((org) => (
                  <option key={org.id} value={org.id}>
                    {org.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
                Document File (PDF, PNG, JPG)
              </label>
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.txt"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 cursor-pointer"
              />
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={uploading || !file || !selectedOrgId}
              className="inline-flex items-center gap-2 px-6 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-sm"
            >
              {uploading ? (
                <>
                  <RefreshCw className="animate-spin" size={16} />
                  <span>Processing Document...</span>
                </>
              ) : (
                <>
                  <Brain size={16} />
                  <span>Run Document Extraction</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Extraction & Anomaly Report */}
      {extraction && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Extraction Overview & Anomaly Findings */}
          <div className="lg:col-span-1 space-y-6">
            {/* Status Card */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase text-gray-500">Extraction Confidence</span>
                <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                  extraction.overall_confidence >= 0.8
                    ? 'bg-green-100 text-green-800'
                    : extraction.overall_confidence >= 0.6
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {Math.round(extraction.overall_confidence * 100)}%
                </span>
              </div>

              <div>
                <div className="text-xs text-gray-500">Matched Schema</div>
                <div className="font-semibold text-gray-900 text-sm">{extraction.schema_type}</div>
              </div>

              <div>
                <div className="text-xs text-gray-500">Review Status</div>
                <span className={`inline-block mt-1 px-2.5 py-0.5 rounded text-xs font-semibold ${
                  extraction.review_status === 'APPROVED'
                    ? 'bg-green-100 text-green-800'
                    : extraction.review_status === 'REJECTED'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-amber-100 text-amber-800'
                }`}>
                  {extraction.review_status}
                </span>
              </div>
            </div>

            {/* Anomaly Detection Findings */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-4">
              <h3 className="font-bold text-gray-900 text-sm flex items-center gap-2">
                <ShieldAlert size={18} className={extraction.anomaly_findings.length > 0 ? 'text-amber-500' : 'text-green-500'} />
                <span>Anomaly & Integrity Audit</span>
                <span className="ml-auto text-xs px-2 py-0.5 bg-gray-100 rounded-full font-mono text-gray-600">
                  {extraction.anomaly_findings.length}
                </span>
              </h3>

              {extraction.anomaly_findings.length === 0 ? (
                <div className="p-3 bg-green-50 text-green-800 rounded-xl text-xs flex items-center gap-2">
                  <CheckCircle2 size={16} />
                  <span>No suspicious inconsistencies or collisions detected.</span>
                </div>
              ) : (
                <div className="space-y-3">
                  {extraction.anomaly_findings.map((finding, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-xl border text-xs space-y-1 ${
                        finding.severity === 'CRITICAL'
                          ? 'bg-red-50 border-red-200 text-red-900'
                          : finding.severity === 'HIGH'
                          ? 'bg-orange-50 border-orange-200 text-orange-900'
                          : 'bg-yellow-50 border-yellow-200 text-yellow-900'
                      }`}
                    >
                      <div className="flex items-center justify-between font-bold">
                        <span>{finding.rule}</span>
                        <span className="text-[10px] px-1.5 py-0.5 bg-white/70 rounded">
                          {finding.severity}
                        </span>
                      </div>
                      <div>{finding.description}</div>
                      {finding.evidence && (
                        <div className="font-mono text-[11px] opacity-80 pt-1">
                          Evidence: {finding.evidence}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Field-Level Review & Pipeline Submission */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-6">
              <div className="flex items-center justify-between border-b border-gray-100 pb-4">
                <div>
                  <h3 className="font-bold text-gray-900">Extracted Credential Claims</h3>
                  <p className="text-xs text-gray-500">
                    Verify and correct field values before submitting to the approval workflow.
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleReviewAction('APPROVE')}
                    className="px-3 py-1.5 bg-green-600 text-white rounded-lg text-xs font-semibold hover:bg-green-700"
                  >
                    Approve Extraction
                  </button>
                  <button
                    onClick={() => handleReviewAction('REJECT')}
                    className="px-3 py-1.5 bg-red-600 text-white rounded-lg text-xs font-semibold hover:bg-red-700"
                  >
                    Reject
                  </button>
                </div>
              </div>

              {/* Field Form */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(extraction.extracted_fields).map(([fieldName, fieldData]) => (
                  <div key={fieldName} className="space-y-1.5 p-3 bg-gray-50 rounded-xl border border-gray-200">
                    <div className="flex items-center justify-between text-xs font-semibold text-gray-700">
                      <span>{fieldName}</span>
                      <span className="text-[10px] text-gray-500 font-mono">
                        {Math.round(fieldData.confidence * 100)}% conf
                      </span>
                    </div>
                    <input
                      type="text"
                      value={editingFields[fieldName] ?? ''}
                      onChange={(e) =>
                        setEditingFields({ ...editingFields, [fieldName]: e.target.value })
                      }
                      className="w-full px-3 py-1.5 bg-white border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                    {fieldData.evidence_snippet && (
                      <div className="text-[11px] text-gray-500 truncate" title={fieldData.evidence_snippet}>
                        Source: "{fieldData.evidence_snippet}"
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Credential Preparation Gateway */}
              <div className="border-t border-gray-100 pt-6 space-y-4">
                <h4 className="font-bold text-gray-900 text-sm flex items-center gap-2">
                  <ArrowRight size={16} className="text-indigo-600" />
                  <span>Prepare Verifiable Credential from Extraction</span>
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
                  <div className="md:col-span-2">
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      Recipient Holder Wallet Address (0x...)
                    </label>
                    <input
                      type="text"
                      placeholder="0x..."
                      value={recipientAddress}
                      onChange={(e) => setRecipientAddress(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>

                  <div>
                    <button
                      onClick={handlePrepareCredential}
                      disabled={preparing || extraction.review_status !== 'APPROVED' || !recipientAddress}
                      className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-sm"
                    >
                      {preparing ? 'Preparing...' : 'Prepare Credential'}
                    </button>
                  </div>
                </div>

                {extraction.review_status !== 'APPROVED' && (
                  <p className="text-xs text-amber-700 bg-amber-50 p-2.5 rounded-lg border border-amber-200">
                    Extraction must be approved by authorized staff before submitting into the credential pipeline.
                  </p>
                )}

                {preparedSummary && (
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl space-y-2 text-xs text-blue-900">
                    <div className="font-bold text-sm">Credential Draft Prepared!</div>
                    <div>W3C ID: <span className="font-mono">{preparedSummary.w3c_id}</span></div>
                    <div>Commitment: <span className="font-mono">{preparedSummary.commitment}</span></div>
                    <div className="pt-1 text-gray-600">{preparedSummary.notice}</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
