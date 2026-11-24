import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield, CheckCircle, Building, Wallet } from 'lucide-react';

interface HeaderProps {
  account: string | null;
  chainId: number | null;
  isConnecting: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  account,
  chainId,
  isConnecting,
  onConnect,
  onDisconnect,
}) => {
  const location = useLocation();

  const navLinks = [
    { to: '/', label: 'Verify', icon: CheckCircle },
    { to: '/wallet', label: 'My Wallet', icon: Wallet },
    { to: '/issuer', label: 'Institutions', icon: Building },
  ];

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2">
              <div className="p-2 bg-blue-600 text-white rounded-lg">
                <Shield size={24} />
              </div>
              <div>
                <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  DecentralID
                </span>
                <span className="ml-2 text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full font-medium">
                  v2.0 Infrastructure
                </span>
              </div>
            </Link>

            <nav className="hidden md:flex gap-1">
              {navLinks.map(({ to, label, icon: Icon }) => {
                const isActive = location.pathname === to;
                return (
                  <Link
                    key={to}
                    to={to}
                    className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                  >
                    <Icon size={16} />
                    {label}
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="flex items-center gap-3">
            {chainId && (
              <span className="hidden sm:inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                Chain ID: {chainId}
              </span>
            )}

            {account ? (
              <div className="flex items-center gap-2">
                <span className="px-3 py-1.5 bg-gray-100 text-gray-800 text-xs font-mono rounded-lg border border-gray-200">
                  {account.slice(0, 6)}...{account.slice(-4)}
                </span>
                <button
                  onClick={onDisconnect}
                  className="px-3 py-1.5 text-xs text-red-600 hover:bg-red-50 rounded-lg border border-red-200 transition-colors"
                >
                  Disconnect
                </button>
              </div>
            ) : (
              <button
                onClick={onConnect}
                disabled={isConnecting}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                <Wallet size={16} />
                {isConnecting ? 'Connecting...' : 'Connect Wallet'}
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
