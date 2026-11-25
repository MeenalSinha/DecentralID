import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  ShieldCheck,
  Wallet,
  Building2,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Shield,
  ExternalLink,
  Cpu,
} from 'lucide-react';

interface SidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  isOpenMobile: boolean;
  onCloseMobile: () => void;
  chainId: number | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isCollapsed,
  onToggleCollapse,
  isOpenMobile,
  onCloseMobile,
  chainId,
}) => {
  const navItems = [
    {
      to: '/',
      label: 'Verify Credential',
      shortLabel: 'Verify',
      description: 'Independent validation',
      icon: ShieldCheck,
    },
    {
      to: '/wallet',
      label: 'My Wallet',
      shortLabel: 'Wallet',
      description: 'Credentials & encrypted vault',
      icon: Wallet,
    },
    {
      to: '/issuer',
      label: 'Institutional Issuer',
      shortLabel: 'Issuer',
      description: 'Issuance & governance',
      icon: Building2,
    },
    {
      to: '/intelligence',
      label: 'Document Intelligence',
      shortLabel: 'Intelligence',
      description: 'AI extraction & verification',
      icon: Sparkles,
    },
  ];

  const content = (
    <div className="flex flex-col h-full bg-surface border-r border-border select-none">
      {/* Brand Header */}
      <div className="h-16 px-4 flex items-center justify-between border-b border-border">
        <NavLink
          to="/"
          onClick={onCloseMobile}
          className="flex items-center gap-3 group focus:outline-none"
        >
          {/* Custom DecentralID Brand Mark */}
          <div className="w-9 h-9 rounded-control bg-primary text-white flex items-center justify-center shadow-subtle group-hover:bg-primary-hover transition-colors shrink-0">
            <Shield className="w-5 h-5 fill-white/10 stroke-[2.2]" />
          </div>
          {!isCollapsed && (
            <div className="flex flex-col">
              <span className="text-base font-bold text-foreground tracking-tight flex items-center gap-1.5">
                DecentralID
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-primary-soft text-primary">
                  v2.0
                </span>
              </span>
              <span className="text-[11px] text-foreground-secondary -mt-0.5">
                Trust Infrastructure
              </span>
            </div>
          )}
        </NavLink>
        <button
          onClick={onToggleCollapse}
          className="hidden md:flex p-1.5 rounded-md text-foreground-muted hover:text-foreground hover:bg-surface-subtle transition-colors"
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 py-5 px-3 space-y-1.5 overflow-y-auto">
        {!isCollapsed && (
          <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-foreground-muted">
            Core Modules
          </div>
        )}
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onCloseMobile}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-control transition-all duration-150 group ${
                  isActive
                    ? 'bg-primary-soft text-primary font-semibold shadow-subtle'
                    : 'text-foreground-secondary hover:text-foreground hover:bg-surface-subtle'
                }`
              }
              title={isCollapsed ? item.label : undefined}
            >
              <Icon
                className={`w-5 h-5 shrink-0 transition-colors ${
                  isCollapsed ? 'mx-auto' : ''
                }`}
              />
              {!isCollapsed && (
                <div className="flex flex-col min-w-0">
                  <span className="text-xs tracking-tight truncate leading-tight">
                    {item.label}
                  </span>
                  <span className="text-[10px] text-foreground-muted truncate leading-tight mt-0.5">
                    {item.description}
                  </span>
                </div>
              )}
            </NavLink>
          );
        })}
      </div>

      {/* Network / Infrastructure Status Card */}
      {!isCollapsed ? (
        <div className="p-3 border-t border-border">
          <div className="p-3 bg-surface-subtle rounded-control border border-border-subtle flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-foreground flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-status-success inline-block animate-pulse" />
                Network Active
              </span>
              <span className="text-[10px] font-mono font-medium text-foreground-secondary bg-surface px-1.5 py-0.5 rounded border border-border">
                #{chainId || 31337}
              </span>
            </div>
            <div className="text-[10px] text-foreground-secondary flex items-center justify-between">
              <span>Registries:</span>
              <span className="font-semibold text-primary">On-Chain</span>
            </div>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="text-[10px] text-foreground-muted hover:text-primary flex items-center gap-1 mt-1 transition-colors"
            >
              <Cpu size={12} />
              API Specification
              <ExternalLink size={10} className="ml-auto" />
            </a>
          </div>
        </div>
      ) : (
        <div className="p-3 border-t border-border flex justify-center">
          <span
            className="w-2.5 h-2.5 rounded-full bg-status-success"
            title="Localhost Blockchain Active"
          />
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <aside
        className={`hidden md:block shrink-0 transition-all duration-200 z-30 ${
          isCollapsed ? 'w-16' : 'w-64'
        }`}
      >
        <div className={`fixed top-0 left-0 bottom-0 ${isCollapsed ? 'w-16' : 'w-64'}`}>
          {content}
        </div>
      </aside>

      {/* Mobile Drawer Backdrop */}
      {isOpenMobile && (
        <div
          className="fixed inset-0 bg-foreground/30 backdrop-blur-sm z-40 md:hidden transition-opacity"
          onClick={onCloseMobile}
        />
      )}

      {/* Mobile Drawer */}
      <div
        className={`fixed top-0 bottom-0 left-0 w-72 max-w-[85vw] z-50 md:hidden transform transition-transform duration-200 ease-in-out ${
          isOpenMobile ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {content}
      </div>
    </>
  );
};
