import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-gray-50 border-t border-gray-200 py-8 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-gray-500">
        <p className="font-medium text-gray-700">DecentralID Trust Infrastructure</p>
        <p className="mt-1 text-xs">
          W3C Verifiable Credentials • EIP-712 Data Integrity • On-Chain Public Key Infrastructure
        </p>
        <p className="mt-2 text-xs text-gray-400">
          Zero Personal Data on Public Blockchain • Salted Commitments
        </p>
      </div>
    </footer>
  );
};
