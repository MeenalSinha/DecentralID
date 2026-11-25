import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Menu,
  Wallet,
  Check,
  Copy,
  LogOut,
  ChevronDown,
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

interface HeaderProps {
  account: string | null;
  chainId: number | null;
  isConnecting: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
  onToggleMobileMenu: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  account,
  chainId,
  isConnecting,
  onConnect,
  onDisconnect,
  onToggleMobileMenu,
}) => {
  const location = useLocation();
  const [copied, setCopied] = useState(false);
  const [showAccountDropdown, setShowAccountDropdown] = useState(false);

  const routeTitles: Record<string, { title: string; subtitle: string }> = {
    '/': {
      title: 'Credential Verification',
      subtitle: 'Cryptographic & On-Chain Integrity Validation',
    },
    '/wallet': {
      title: 'Holder Wallet',
      subtitle: 'Verifiable Credentials & Encrypted Vault',
    },
    '/issuer': {
      title: 'Institutional Issuer Portal',
      subtitle: 'Multi-Tenant Lifecycle & Key Governance',
    },
    '/intelligence': {
      title: 'Document Intelligence',
      subtitle: 'OCR Extraction, Verification & Anomaly Detection',
    },
  };

  const currentRoute = routeTitles[location.pathname] || {
    title: 'DecentralID Infrastructure',
    subtitle: 'Portable, Privacy-Preserving Verifiable Credentials',
  };

  const copyAddress = () => {
    if (!account) return;
    navigator.clipboard.writeText(account);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatAddress = (addr: string) => {
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
  };

  return (
    <header className="sticky top-0 z-20 bg-surface/90 backdrop-blur-md border-b border-border h-16 px-4 sm:px-6 lg:px-8 flex items-center justify-between transition-colors">
      {/* Left: Mobile Toggle & Page Breadcrumb */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleMobileMenu}
          className="md:hidden p-2 rounded-control text-foreground-secondary hover:text-foreground hover:bg-surface-subtle transition-colors focus:outline-none"
          aria-label="Open navigation menu"
        >
          <Menu size={20} />
        </button>

        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-semibold text-foreground tracking-tight">
              {currentRoute.title}
            </h1>
          </div>
          <p className="text-[11px] text-foreground-secondary hidden sm:block">
            {currentRoute.subtitle}
          </p>
        </div>
      </div>

      {/* Right: Network Status & Wallet Actions */}
      <div className="flex items-center gap-3">
        {/* Network Badge */}
        <Badge variant="neutral" size="sm" className="hidden sm:inline-flex" dot>
          {chainId === 31337
            ? 'Localhost #31337'
            : chainId === 11155111
            ? 'Sepolia Testnet'
            : chainId
            ? `Chain #${chainId}`
            : 'Local Network'}
        </Badge>

        {/* Wallet Connection */}
        {account ? (
          <div className="relative">
            <button
              onClick={() => setShowAccountDropdown(!showAccountDropdown)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-control bg-surface border border-border hover:border-border-strong hover:bg-surface-subtle transition-all shadow-subtle focus:outline-none"
            >
              <div className="w-2 h-2 rounded-full bg-status-success" />
              <span className="text-xs font-mono font-medium text-foreground">
                {formatAddress(account)}
              </span>
              <ChevronDown size={14} className="text-foreground-muted" />
            </button>

            {/* Dropdown Menu */}
            {showAccountDropdown && (
              <>
                <div
                  className="fixed inset-0 z-30"
                  onClick={() => setShowAccountDropdown(false)}
                />
                <div className="absolute right-0 mt-2 w-64 bg-surface rounded-card border border-border shadow-elevated p-3 z-40 animate-in fade-in zoom-in-95 duration-100">
                  <div className="pb-2 mb-2 border-b border-border">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground-muted block">
                      Connected Account
                    </span>
                    <p className="text-xs font-mono text-foreground break-all mt-1">
                      {account}
                    </p>
                  </div>

                  <div className="space-y-1">
                    <button
                      onClick={copyAddress}
                      className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-control text-xs text-foreground hover:bg-surface-subtle transition-colors text-left"
                    >
                      <span className="flex items-center gap-2">
                        {copied ? (
                          <Check size={14} className="text-status-success" />
                        ) : (
                          <Copy size={14} className="text-foreground-muted" />
                        )}
                        {copied ? 'Copied to Clipboard' : 'Copy Address'}
                      </span>
                    </button>

                    <button
                      onClick={() => {
                        setShowAccountDropdown(false);
                        onDisconnect();
                      }}
                      className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-control text-xs text-status-danger hover:bg-status-danger-soft transition-colors text-left"
                    >
                      <LogOut size={14} />
                      Disconnect Wallet
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        ) : (
          <Button
            variant="primary"
            size="sm"
            onClick={onConnect}
            isLoading={isConnecting}
            leftIcon={<Wallet size={14} />}
          >
            Connect Wallet
          </Button>
        )}
      </div>
    </header>
  );
};
