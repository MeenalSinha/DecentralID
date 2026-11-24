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
  Shield
} from 'lucide-react';
import { apiPost } from '../../../app/config/api';

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

  // Check URL query parameters for ?token=...
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

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

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
    <div className="max-w-5xl mx-auto space-y-8 pb-16">
      {/* Title & Introduction */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-50 text-blue-700 text-xs font-bold rounded-full border border-blue-200">
          <ShieldCheck size={14} />
          Public Trust Verification Network
        </div>
        <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">
          DecentralID Independent Verification Portal
        </h1>
        <p className="text-gray-600 text-sm max-w-2xl mx-auto">
          Verify academic, professional, and institutional credentials with zero trust. Checks cryptographic signatures, decentralized issuer authorization, on-chain commitment registration, and real-time lifecycle status.
        </p>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-6">
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('upload')}
            className={`pb-3 px-4 text-xs font-bold flex items-center gap-2 border-b-2 transition ${
              activeTab === 'upload'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Upload size={16} /> File Upload (.json)
          </button>
          <button
            onClick={() => setActiveTab('token')}
            className={`pb-3 px-4 text-xs font-bold flex items-center gap-2 border-b-2 transition ${
              activeTab === 'token'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Link2 size={16} /> QR / Presentation Token
          </button>
          <button
            onClick={() => setActiveTab('json')}
            className={`pb-3 px-4 text-xs font-bold flex items-center gap-2 border-b-2 transition ${
              activeTab === 'json'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Code size={16} /> Raw W3C JSON Paste
          </button>
        </div>

        {/* Tab 1: File Upload */}
        {activeTab === 'upload' && (
          <div className="border-2 border-dashed border-gray-300 rounded-2xl p-8 text-center space-y-4 hover:border-blue-400 transition bg-gray-50/50">
            <div className="p-3 bg-blue-100 text-blue-700 rounded-2xl w-fit mx-auto">
              <Upload size={28} />
            </div>
            <div>
              <p className="text-sm font-bold text-gray-800">
                Select or Drag & Drop a Verifiable Credential file
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Supports W3C Verifiable Credentials (.json) and Verifiable Presentations (.json)
              </p>
            </div>
            <label className="inline-block px-5 py-2.5 bg-blue-600 text-white text-xs font-bold rounded-xl cursor-pointer hover:bg-blue-700 transition">
              Browse File
              <input
                type="file"
                accept=".json,application/json"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>
          </div>
        )}

        {/* Tab 2: Token / Link */}
        {activeTab === 'token' && (
          <div className="space-y-4">
            <p className="text-xs text-gray-600">
              Enter an opaque presentation token generated from a holder's QR code or shared verification link.
            </p>
            <div className="flex gap-2">
              <input
                type="text"
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
                className="flex-1 border border-gray-300 rounded-xl px-4 py-2.5 text-xs font-mono focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={() => triggerTokenVerification(inputToken)}
                disabled={isVerifying || !inputToken.trim()}
                className="px-6 py-2.5 bg-blue-600 text-white font-bold text-xs rounded-xl hover:bg-blue-700 disabled:opacity-50 transition"
              >
                {isVerifying ? 'Verifying...' : 'Verify Token'}
              </button>
            </div>
          </div>
        )}

        {/* Tab 3: Raw JSON */}
        {activeTab === 'json' && (
          <form onSubmit={handleJsonSubmit} className="space-y-4">
            <textarea
              rows={8}
              placeholder="Paste complete W3C VC 2.0 or VP 2.0 JSON document here..."
              value={rawJson}
              onChange={(e) => setRawJson(e.target.value)}
              className="w-full border border-gray-300 rounded-xl p-3 text-xs font-mono bg-gray-900 text-gray-100 focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex items-center justify-between gap-4">
              <input
                type="text"
                placeholder="Optional 32-byte salt hex (0x...) for private commitment check"
                value={optionalSalt}
                onChange={(e) => setOptionalSalt(e.target.value)}
                className="flex-1 border border-gray-300 rounded-xl px-3 py-2 text-xs font-mono"
              />
              <button
                type="submit"
                disabled={isVerifying || !rawJson.trim()}
                className="px-6 py-2.5 bg-blue-600 text-white font-bold text-xs rounded-xl hover:bg-blue-700 disabled:opacity-50 transition"
              >
                {isVerifying ? 'Running Cryptographic Verification...' : 'Verify Payload'}
              </button>
            </div>
          </form>
        )}

        {errorBanner && (
          <div className="bg-red-50 border border-red-200 text-red-800 rounded-xl p-4 flex items-center gap-3 text-xs">
            <AlertCircle size={20} className="text-red-600 flex-shrink-0" />
            <p className="font-medium">{errorBanner}</p>
          </div>
        )}
      </div>

      {/* Verification Result Card */}
      {result && (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-md p-6 md:p-8 space-y-6">
          {/* Top Verdict Banner */}
          <div
            className={`p-6 rounded-2xl border flex flex-col md:flex-row md:items-center justify-between gap-4 ${
              result.is_valid
                ? 'bg-emerald-50/80 border-emerald-300 text-emerald-950'
                : 'bg-red-50/80 border-red-300 text-red-950'
            }`}
          >
            <div className="flex items-center gap-4">
              <div
                className={`p-3 rounded-2xl ${
                  result.is_valid ? 'bg-emerald-600 text-white' : 'bg-red-600 text-white'
                }`}
              >
                {result.is_valid ? <ShieldCheck size={32} /> : <XCircle size={32} />}
              </div>
              <div>
                <h2 className="text-xl font-extrabold tracking-tight">
                  {result.is_valid
                    ? 'Authentic & Cryptographically Verified'
                    : 'Verification Failed / Not Authentic'}
                </h2>
                <p className="text-xs opacity-90 mt-0.5">
                  {result.is_valid
                    ? 'All cryptographic signatures, issuer credentials, and status registries confirmed.'
                    : 'One or more verification quality gates failed. Review diagnostic findings below.'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span
                className={`px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                  result.lifecycle_status === 'ACTIVE'
                    ? 'bg-emerald-200 text-emerald-900'
                    : result.lifecycle_status === 'SUSPENDED'
                    ? 'bg-amber-200 text-amber-900'
                    : 'bg-red-200 text-red-900'
                }`}
              >
                Status: {result.lifecycle_status}
              </span>
              <button
                onClick={exportAuditReport}
                className="px-3 py-1.5 bg-white border border-gray-300 rounded-xl text-xs font-bold text-gray-700 hover:bg-gray-50 transition flex items-center gap-1.5"
              >
                <Download size={14} /> Audit Report
              </button>
            </div>
          </div>

          {/* Diagnostic Checks Breakdown Table */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">
              Cryptographic & Regulatory Verification Pipeline
            </h3>
            <div className="border border-gray-200 rounded-xl divide-y divide-gray-100 text-xs overflow-hidden">
              <div className="flex items-center justify-between p-3.5 bg-gray-50/50">
                <span className="font-semibold text-gray-700 flex items-center gap-2">
                  <FileText size={16} className="text-gray-500" />
                  1. W3C Envelope & Schema Structure
                </span>
                {result.checks.structural ? (
                  <span className="text-emerald-700 font-bold flex items-center gap-1">
                    <CheckCircle2 size={16} /> PASS
                  </span>
                ) : (
                  <span className="text-red-700 font-bold flex items-center gap-1">
                    <XCircle size={16} /> FAIL
                  </span>
                )}
              </div>

              <div className="flex items-center justify-between p-3.5 bg-gray-50/50">
                <span className="font-semibold text-gray-700 flex items-center gap-2">
                  <Shield size={16} className="text-gray-500" />
                  2. ECDSA JCS-2019 Digital Signature
                </span>
                {result.checks.signature ? (
                  <span className="text-emerald-700 font-bold flex items-center gap-1">
                    <CheckCircle2 size={16} /> VALID SIGNATURE
                  </span>
                ) : (
                  <span className="text-red-700 font-bold flex items-center gap-1">
                    <XCircle size={16} /> INVALID SIGNATURE
                  </span>
                )}
              </div>

              <div className="flex items-center justify-between p-3.5 bg-gray-50/50">
                <span className="font-semibold text-gray-700 flex items-center gap-2">
                  <Building size={16} className="text-gray-500" />
                  3. Issuer Accreditation (IssuerRegistry)
                </span>
                {result.checks.issuer_authorized ? (
                  <span className="text-emerald-700 font-bold flex items-center gap-1">
                    <CheckCircle2 size={16} /> ACCREDITED
                  </span>
                ) : (
                  <span className="text-red-700 font-bold flex items-center gap-1">
                    <XCircle size={16} /> NOT ACCREDITED
                  </span>
                )}
              </div>

              <div className="flex items-center justify-between p-3.5 bg-gray-50/50">
                <span className="font-semibold text-gray-700 flex items-center gap-2">
                  <Key size={16} className="text-gray-500" />
                  4. Operational Signing Key Authorization
                </span>
                {result.checks.signing_key_authorized ? (
                  <span className="text-emerald-700 font-bold flex items-center gap-1">
                    <CheckCircle2 size={16} /> AUTHORIZED KEY
                  </span>
                ) : (
                  <span className="text-red-700 font-bold flex items-center gap-1">
                    <XCircle size={16} /> UNAUTHORIZED KEY
                  </span>
                )}
              </div>

              <div className="flex items-center justify-between p-3.5 bg-gray-50/50">
                <span className="font-semibold text-gray-700 flex items-center gap-2">
                  <Calendar size={16} className="text-gray-500" />
                  5. Validity Period & Expiration
                </span>
                {result.checks.not_expired ? (
                  <span className="text-emerald-700 font-bold flex items-center gap-1">
                    <CheckCircle2 size={16} /> ACTIVE
                  </span>
                ) : (
                  <span className="text-red-700 font-bold flex items-center gap-1">
                    <XCircle size={16} /> EXPIRED
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Disclosed Claims & Subject Data */}
          {result.disclosed_claims && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">
                  Verified Credential Subject Attributes
                </h3>
                {result.is_selective_disclosure && (
                  <span className="px-2.5 py-0.5 bg-blue-100 text-blue-800 text-[11px] font-bold rounded-full">
                    Selective Disclosure Active
                  </span>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 bg-gray-50 p-4 rounded-xl border border-gray-200 text-xs">
                {Object.entries(result.disclosed_claims)
                  .filter(([k]) => k !== 'id')
                  .map(([k, v]) => (
                    <div key={k} className="p-2.5 bg-white rounded-lg border border-gray-200">
                      <p className="text-gray-500 font-medium capitalize">
                        {k.replace(/([A-Z])/g, ' $1')}
                      </p>
                      <p className="text-gray-900 font-bold text-sm mt-0.5">{String(v)}</p>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Errors / Warnings */}
          {result.errors.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-xs text-red-900 space-y-1.5">
              <p className="font-bold">Failure Reasons:</p>
              <ul className="list-disc pl-5 space-y-1">
                {result.errors.map((err, idx) => (
                  <li key={idx}>{err}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
