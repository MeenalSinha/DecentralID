import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  AlertCircle,
  CheckCircle2,
  XCircle,
  FileText,
  Upload,
  Link2,
  Code,
  Download,
  Building,
  Key,
  Calendar,
  Shield,
  ChevronDown,
  ChevronUp,
  FileCheck,
  Hash,
} from 'lucide-react';
import { apiPost } from '../../../app/config/api';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Badge } from '../../../components/ui/Badge';
import { Input } from '../../../components/ui/Input';

interface VerificationChecks {
  structural: boolean;
  signature: boolean;
  issuer_authorized: boolean;
  signing_key_authorized: boolean;
  commitment_verified: boolean | null;
  not_expired: boolean;
}

interface VerificationIssuerInfo {
  name: string;
  address: string;
}

interface VerificationResponse {
  is_valid: boolean;
  checks: VerificationChecks;
  lifecycle_status: string;
  issuer: VerificationIssuerInfo;
  signer_address: string;
  credential_id: string;
  schema_type?: string;
  disclosed_claims?: Record<string, any>;
  is_selective_disclosure?: boolean;
  errors: string[];
  warnings: string[];
  verified_at: string;
}

export const VerificationView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'upload' | 'token' | 'json'>('upload');
  const [inputToken, setInputToken] = useState('');
  const [rawJson, setRawJson] = useState('');
  const [optionalSalt, setOptionalSalt] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [result, setResult] = useState<VerificationResponse | null>(null);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  // Parse token from query parameter if present
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const tokenParam = params.get('token');
    if (tokenParam) {
      setInputToken(tokenParam);
      setActiveTab('token');
      triggerTokenVerification(tokenParam);
    }
  }, []);

  const triggerTokenVerification = async (token: string) => {
    setIsVerifying(true);
    setErrorBanner(null);
    setResult(null);
    try {
      const res = await apiPost<VerificationResponse>('/verification/verify', {
        token: token.trim(),
      });
      setResult(res);
    } catch (err: any) {
      setErrorBanner(err.message || 'Verification of presentation token failed.');
    } finally {
      setIsVerifying(false);
    }
  };

  const processFile = (file: File) => {
    if (!file.name.endsWith('.json') && file.type !== 'application/json') {
      setErrorBanner('Please select a valid JSON credential file.');
      return;
    }
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const text = event.target?.result as string;
        setRawJson(text);
        runVerification(JSON.parse(text));
      } catch {
        setErrorBanner('Selected file is not valid JSON.');
      }
    };
    reader.readAsText(file);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) processFile(file);
  };

  const runVerification = async (doc: any) => {
    setIsVerifying(true);
    setErrorBanner(null);
    setResult(null);

    try {
      const res = await apiPost<VerificationResponse>('/verification/verify', {
        credential: doc,
        salt: optionalSalt.trim() || undefined,
      });
      setResult(res);
    } catch (err: any) {
      setErrorBanner(err.message || 'Verification request failed.');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleJsonSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!rawJson.trim()) return;
    try {
      const parsed = JSON.parse(rawJson);
      runVerification(parsed);
    } catch {
      setErrorBanner('Invalid JSON: Please check the syntax of your credential document.');
    }
  };

  const exportAuditReport = () => {
    if (!result) return;
    const report = {
      title: 'DecentralID Verification Audit Certificate',
      timestamp: result.verified_at,
      verdict: result.is_valid ? 'AUTHENTIC_VERIFIED' : 'FAILED',
      credential_id: result.credential_id,
      schema_type: result.schema_type,
      issuer: result.issuer,
      signer_address: result.signer_address,
      lifecycle_status: result.lifecycle_status,
      checks: result.checks,
      claims: result.disclosed_claims,
      is_selective_disclosure: result.is_selective_disclosure,
      errors: result.errors,
      warnings: result.warnings,
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `decentralid-verification-${result.credential_id.slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Editorial Page Header */}
      <div className="border-b border-border pb-5">
        <div className="flex items-center gap-2 text-primary font-semibold text-xs tracking-wider uppercase mb-1">
          <ShieldCheck size={15} />
          <span>Independent Trust Gate</span>
        </div>
        <h1 className="text-2xl font-bold text-foreground tracking-tight">
          Verify a Credential
        </h1>
        <p className="text-sm text-foreground-secondary mt-1 max-w-2xl leading-relaxed">
          Verify the authenticity and current status of digitally signed credentials issued through trusted institutions.
        </p>
      </div>

      {/* Verification Workspace Card */}
      <Card>
        {/* Workspace Mode Tabs */}
        <div className="flex items-center gap-1 border-b border-border pb-3 mb-5">
          <button
            onClick={() => setActiveTab('upload')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-control text-xs font-medium transition-colors ${
              activeTab === 'upload'
                ? 'bg-primary-soft text-primary font-semibold'
                : 'text-foreground-secondary hover:text-foreground hover:bg-surface-subtle'
            }`}
          >
            <Upload size={14} /> File Upload (.json)
          </button>
          <button
            onClick={() => setActiveTab('token')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-control text-xs font-medium transition-colors ${
              activeTab === 'token'
                ? 'bg-primary-soft text-primary font-semibold'
                : 'text-foreground-secondary hover:text-foreground hover:bg-surface-subtle'
            }`}
          >
            <Link2 size={14} /> QR / Presentation Token
          </button>
          <button
            onClick={() => setActiveTab('json')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-control text-xs font-medium transition-colors ${
              activeTab === 'json'
                ? 'bg-primary-soft text-primary font-semibold'
                : 'text-foreground-secondary hover:text-foreground hover:bg-surface-subtle'
            }`}
          >
            <Code size={14} /> Raw W3C JSON
          </button>
        </div>

        {/* Tab 1: File Upload */}
        {activeTab === 'upload' && (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-card p-8 text-center transition-all ${
              isDragging
                ? 'border-primary bg-primary-soft/40'
                : 'border-border hover:border-border-strong bg-surface-subtle/50'
            }`}
          >
            <div className="w-12 h-12 rounded-full bg-surface border border-border flex items-center justify-center mx-auto text-primary mb-3 shadow-subtle">
              <Upload size={20} />
            </div>
            <h3 className="text-sm font-semibold text-foreground">
              Drop your Verifiable Credential file here
            </h3>
            <p className="text-xs text-foreground-secondary mt-1 max-w-md mx-auto">
              Supports W3C Verifiable Credentials (.json) and Verifiable Presentations.
            </p>

            <div className="mt-4">
              <label className="inline-block cursor-pointer">
                <span className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white text-xs font-medium rounded-control hover:bg-primary-hover shadow-subtle transition-colors">
                  <FileCheck size={14} />
                  Browse JSON Document
                </span>
                <input
                  type="file"
                  accept=".json,application/json"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
            </div>
          </div>
        )}

        {/* Tab 2: Presentation Token */}
        {activeTab === 'token' && (
          <div className="space-y-3">
            <p className="text-xs text-foreground-secondary">
              Enter an opaque presentation token generated from a holder's QR code or shared verification link.
            </p>
            <div className="flex flex-col sm:flex-row gap-2">
              <Input
                placeholder="e.g. pr_x9K7... or paste full verification URL"
                value={inputToken}
                onChange={(e) => {
                  const val = e.target.value;
                  if (val.includes('token=')) {
                    const extracted = new URLSearchParams(val.split('?')[1]).get('token');
                    setInputToken(extracted || val);
                  } else {
                    setInputToken(val);
                  }
                }}
                className="font-mono text-xs"
              />
              <Button
                variant="primary"
                size="md"
                onClick={() => triggerTokenVerification(inputToken)}
                isLoading={isVerifying}
                disabled={!inputToken.trim()}
                className="shrink-0"
              >
                Verify Token
              </Button>
            </div>
          </div>
        )}

        {/* Tab 3: Raw JSON */}
        {activeTab === 'json' && (
          <form onSubmit={handleJsonSubmit} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-foreground mb-1.5">
                W3C JSON Document
              </label>
              <textarea
                rows={7}
                placeholder="Paste complete W3C VC 2.0 or VP 2.0 JSON document here..."
                value={rawJson}
                onChange={(e) => setRawJson(e.target.value)}
                className="w-full bg-surface text-foreground font-mono text-xs rounded-control border border-border p-3 focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 shadow-subtle"
              />
            </div>
            <div className="flex flex-col sm:flex-row items-center gap-2 pt-1">
              <Input
                placeholder="Optional 32-byte salt hex (0x...) for private commitment check"
                value={optionalSalt}
                onChange={(e) => setOptionalSalt(e.target.value)}
                className="font-mono text-xs flex-1"
              />
              <Button
                type="submit"
                variant="primary"
                size="md"
                isLoading={isVerifying}
                disabled={!rawJson.trim()}
                className="w-full sm:w-auto shrink-0"
              >
                Verify Payload
              </Button>
            </div>
          </form>
        )}

        {/* Upload Error Banner */}
        {errorBanner && (
          <div className="mt-4 p-3.5 rounded-control bg-status-danger-soft border border-status-danger/30 text-status-danger flex items-start gap-2.5 text-xs">
            <AlertCircle size={16} className="shrink-0 mt-0.5" />
            <span className="font-medium">{errorBanner}</span>
          </div>
        )}
      </Card>

      {/* Verification Result Card */}
      {result && (
        <Card className="space-y-6 animate-in fade-in duration-200">
          {/* Verdict Banner */}
          <div
            className={`p-5 rounded-control border flex flex-col md:flex-row md:items-center justify-between gap-4 ${
              result.is_valid
                ? 'bg-status-success-soft border-status-success/30 text-status-success'
                : 'bg-status-danger-soft border-status-danger/30 text-status-danger'
            }`}
          >
            <div className="flex items-center gap-3.5">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${
                  result.is_valid
                    ? 'bg-status-success text-white'
                    : 'bg-status-danger text-white'
                }`}
              >
                {result.is_valid ? <ShieldCheck size={22} /> : <XCircle size={22} />}
              </div>
              <div>
                <h2 className="text-base font-bold tracking-tight text-foreground">
                  {result.is_valid
                    ? 'Authentic & Cryptographically Verified'
                    : 'Verification Failed / Not Authentic'}
                </h2>
                <p className="text-xs text-foreground-secondary mt-0.5">
                  {result.is_valid
                    ? 'All signatures, issuer credentials, and status registries confirmed authentic.'
                    : 'One or more required security verification checks failed.'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2.5 shrink-0">
              <Badge
                variant={
                  result.lifecycle_status === 'ACTIVE'
                    ? 'success'
                    : result.lifecycle_status === 'SUSPENDED'
                    ? 'warning'
                    : 'danger'
                }
                size="md"
                dot
              >
                Status: {result.lifecycle_status}
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={exportAuditReport}
                leftIcon={<Download size={13} />}
              >
                Audit Report
              </Button>
            </div>
          </div>

          {/* Credential Metadata Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="p-3 bg-surface-subtle rounded-control border border-border-subtle">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block">
                Credential Type
              </span>
              <span className="text-xs font-semibold text-foreground mt-0.5 block truncate">
                {result.schema_type || 'VerifiableCredential'}
              </span>
            </div>

            <div className="p-3 bg-surface-subtle rounded-control border border-border-subtle">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block">
                Issuing Institution
              </span>
              <span className="text-xs font-semibold text-foreground mt-0.5 block truncate">
                {result.issuer.name || 'Accredited Issuer'}
              </span>
            </div>

            <div className="p-3 bg-surface-subtle rounded-control border border-border-subtle">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block">
                Signer Public Key
              </span>
              <span className="text-xs font-mono font-medium text-foreground mt-0.5 block truncate" title={result.signer_address}>
                {result.signer_address
                  ? `${result.signer_address.slice(0, 6)}...${result.signer_address.slice(-4)}`
                  : 'N/A'}
              </span>
            </div>

            <div className="p-3 bg-surface-subtle rounded-control border border-border-subtle">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block">
                Timestamp
              </span>
              <span className="text-xs font-medium text-foreground mt-0.5 block truncate">
                {new Date(result.verified_at).toLocaleDateString()} {new Date(result.verified_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>

          {/* 5-Point Security Pipeline Checks */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground-secondary">
              Security & Regulatory Verification Checks
            </h3>
            <div className="border border-border rounded-control divide-y divide-border overflow-hidden">
              <div className="flex items-center justify-between p-3 bg-surface hover:bg-surface-subtle/50 transition-colors">
                <span className="text-xs font-medium text-foreground flex items-center gap-2">
                  <FileText size={15} className="text-foreground-muted" />
                  1. W3C Envelope & Structural Schema
                </span>
                {result.checks.structural ? (
                  <Badge variant="success" size="sm">
                    <CheckCircle2 size={12} className="mr-1" /> PASS
                  </Badge>
                ) : (
                  <Badge variant="danger" size="sm">
                    <XCircle size={12} className="mr-1" /> FAIL
                  </Badge>
                )}
              </div>

              <div className="flex items-center justify-between p-3 bg-surface hover:bg-surface-subtle/50 transition-colors">
                <span className="text-xs font-medium text-foreground flex items-center gap-2">
                  <Shield size={15} className="text-foreground-muted" />
                  2. Cryptographic Digital Signature (ECDSA)
                </span>
                {result.checks.signature ? (
                  <Badge variant="success" size="sm">
                    <CheckCircle2 size={12} className="mr-1" /> VALID SIGNATURE
                  </Badge>
                ) : (
                  <Badge variant="danger" size="sm">
                    <XCircle size={12} className="mr-1" /> INVALID SIGNATURE
                  </Badge>
                )}
              </div>

              <div className="flex items-center justify-between p-3 bg-surface hover:bg-surface-subtle/50 transition-colors">
                <span className="text-xs font-medium text-foreground flex items-center gap-2">
                  <Building size={15} className="text-foreground-muted" />
                  3. Issuer Registry Accreditation
                </span>
                {result.checks.issuer_authorized ? (
                  <Badge variant="success" size="sm">
                    <CheckCircle2 size={12} className="mr-1" /> ACCREDITED
                  </Badge>
                ) : (
                  <Badge variant="danger" size="sm">
                    <XCircle size={12} className="mr-1" /> NOT ACCREDITED
                  </Badge>
                )}
              </div>

              <div className="flex items-center justify-between p-3 bg-surface hover:bg-surface-subtle/50 transition-colors">
                <span className="text-xs font-medium text-foreground flex items-center gap-2">
                  <Key size={15} className="text-foreground-muted" />
                  4. Operational Signing Key Authorization
                </span>
                {result.checks.signing_key_authorized ? (
                  <Badge variant="success" size="sm">
                    <CheckCircle2 size={12} className="mr-1" /> AUTHORIZED
                  </Badge>
                ) : (
                  <Badge variant="danger" size="sm">
                    <XCircle size={12} className="mr-1" /> UNAUTHORIZED
                  </Badge>
                )}
              </div>

              <div className="flex items-center justify-between p-3 bg-surface hover:bg-surface-subtle/50 transition-colors">
                <span className="text-xs font-medium text-foreground flex items-center gap-2">
                  <Calendar size={15} className="text-foreground-muted" />
                  5. Validity Period & Expiration Check
                </span>
                {result.checks.not_expired ? (
                  <Badge variant="success" size="sm">
                    <CheckCircle2 size={12} className="mr-1" /> UNEXPIRED
                  </Badge>
                ) : (
                  <Badge variant="danger" size="sm">
                    <XCircle size={12} className="mr-1" /> EXPIRED
                  </Badge>
                )}
              </div>
            </div>
          </div>

          {/* Verified Disclosed Claims Table */}
          {result.disclosed_claims && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground-secondary">
                  Verified Credential Subject Attributes
                </h3>
                {result.is_selective_disclosure && (
                  <Badge variant="info" size="sm">
                    Selective Disclosure Active
                  </Badge>
                )}
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 p-3.5 bg-surface-subtle rounded-control border border-border-subtle">
                {Object.entries(result.disclosed_claims)
                  .filter(([k]) => k !== 'id')
                  .map(([k, v]) => (
                    <div
                      key={k}
                      className="p-3 bg-surface rounded-control border border-border shadow-subtle"
                    >
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block">
                        {k.replace(/([A-Z])/g, ' $1')}
                      </span>
                      <span className="text-xs font-semibold text-foreground mt-0.5 block break-words">
                        {String(v)}
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Failure Reasons */}
          {result.errors.length > 0 && (
            <div className="p-3.5 rounded-control bg-status-danger-soft border border-status-danger/30 text-xs text-status-danger space-y-1">
              <span className="font-semibold block">Validation Failure Reasons:</span>
              <ul className="list-disc pl-5 space-y-0.5">
                {result.errors.map((err, idx) => (
                  <li key={idx}>{err}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Expandable Technical Cryptographic Details */}
          <div className="border-t border-border pt-3">
            <button
              onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
              className="flex items-center justify-between w-full text-xs font-semibold text-foreground-secondary hover:text-foreground transition-colors py-1"
            >
              <span className="flex items-center gap-1.5">
                <Hash size={14} className="text-primary" />
                Technical Cryptographic & Blockchain Details
              </span>
              {showTechnicalDetails ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>

            {showTechnicalDetails && (
              <div className="mt-3 p-3 bg-surface-subtle rounded-control border border-border-subtle font-mono text-[11px] text-foreground space-y-2 overflow-x-auto">
                <div>
                  <span className="text-foreground-muted">Credential ID: </span>
                  <span className="break-all">{result.credential_id}</span>
                </div>
                <div>
                  <span className="text-foreground-muted">Issuer Address: </span>
                  <span className="break-all">{result.issuer.address}</span>
                </div>
                <div>
                  <span className="text-foreground-muted">Signer Address: </span>
                  <span className="break-all">{result.signer_address}</span>
                </div>
                <div>
                  <span className="text-foreground-muted">Signature Scheme: </span>
                  <span>ECDSA secp256k1 (EIP-712 Structured Data)</span>
                </div>
                {result.checks.commitment_verified !== null && (
                  <div>
                    <span className="text-foreground-muted">Commitment Check: </span>
                    <span>{result.checks.commitment_verified ? 'VERIFIED ON-CHAIN' : 'SALT REQUIRED'}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};
