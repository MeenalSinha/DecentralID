import React from 'react';
import { Building2, Key, FileSpreadsheet, ShieldAlert } from 'lucide-react';

export const IssuerView: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">
          DecentralID Institutional Issuer Portal
        </h1>
        <p className="text-gray-600">
          Accredited institutions configure cryptographic signing keys, manage operator roles,
          and issue tamper-evident credentials to graduates and professionals.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-2">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-xl w-fit">
            <Building2 size={24} />
          </div>
          <h3 className="font-bold text-gray-900">Institutional Identity</h3>
          <p className="text-sm text-gray-500">
            Register university accreditation and manage legal entity records.
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-2">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl w-fit">
            <Key size={24} />
          </div>
          <h3 className="font-bold text-gray-900">Signing Keys (PKI)</h3>
          <p className="text-sm text-gray-500">
            Rotate operational keys on-chain and authorize departmental signing authorities.
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-2">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-xl w-fit">
            <FileSpreadsheet size={24} />
          </div>
          <h3 className="font-bold text-gray-900">Batch Credential Issuance</h3>
          <p className="text-sm text-gray-500">
            Generate salted privacy commitments and register batches with sub-second finality.
          </p>
        </div>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 text-sm text-amber-900 flex items-start gap-3">
        <ShieldAlert size={20} className="text-amber-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold">Phase Roadmap Note:</span> Full institutional portal workflows,
          dynamic credential template schemas, and batch CSV issuance will be delivered in Phase 6.
          Phases 2–4 establish the secure backend APIs, tenant isolation, and smart contract registry foundations.
        </div>
      </div>
    </div>
  );
};
