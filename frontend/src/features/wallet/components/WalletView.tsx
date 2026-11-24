import React from 'react';
import { Wallet, Shield, Award } from 'lucide-react';
import { useWallet } from '../../authentication/hooks/useWallet';

export const WalletView: React.FC = () => {
  const { account, chainId } = useWallet();

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">
          DecentralID Holder Credential Wallet
        </h1>
        <p className="text-gray-600">
          Manage your self-sovereign verifiable credentials. Hold tamper-proof qualifications,
          control selective disclosures, and share cryptographically verifiable presentations.
        </p>
      </div>

      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 md:p-8 space-y-6">
        <div className="flex items-center justify-between pb-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-100 text-blue-700 rounded-xl">
              <Wallet size={24} />
            </div>
            <div>
              <h3 className="font-bold text-gray-900">Wallet DID Identity</h3>
              <p className="font-mono text-xs text-gray-500">
                {account ? `did:ethr:${chainId || 31337}:${account}` : 'No wallet connected'}
              </p>
            </div>
          </div>
          {account && (
            <span className="px-3 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded-full">
              Connected
            </span>
          )}
        </div>

        <div>
          <h4 className="text-sm font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Award size={18} className="text-blue-600" />
            My Stored Credentials
          </h4>

          {account ? (
            <div className="border border-dashed border-gray-300 rounded-xl p-8 text-center text-gray-500 space-y-2">
              <Shield size={32} className="mx-auto text-gray-400" />
              <p className="text-sm font-medium">No credentials received yet</p>
              <p className="text-xs text-gray-400">
                Credentials issued to your DID by verified institutions will appear here automatically.
              </p>
            </div>
          ) : (
            <div className="bg-gray-50 rounded-xl p-6 text-center text-sm text-gray-600">
              Connect your Ethereum wallet to access your private credential vault.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
