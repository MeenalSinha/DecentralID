import React from 'react';
import { ShieldCheck, Lock } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="mt-auto border-t border-border bg-surface-subtle py-5 px-4 sm:px-6 lg:px-8 text-foreground-secondary">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded bg-primary/10 text-primary flex items-center justify-center">
            <ShieldCheck size={13} />
          </div>
          <span className="font-semibold text-foreground">DecentralID</span>
          <span className="text-foreground-muted">•</span>
          <span>Digital Infrastructure for Verifiable Credentials</span>
        </div>

        <div className="flex items-center gap-4 text-[11px] text-foreground-muted">
          <span className="flex items-center gap-1">
            <Lock size={12} className="text-primary" />
            Zero PII on Chain
          </span>
          <span>•</span>
          <span>W3C VC Data Model v2.0</span>
          <span>•</span>
          <span>EIP-712 Integrity</span>
        </div>
      </div>
    </footer>
  );
};
