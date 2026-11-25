import React, { useState, useEffect } from 'react';
import {
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  PauseCircle,
  PlayCircle,
  ShieldAlert,
  Lock,
} from 'lucide-react';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Badge } from '../../../components/ui/Badge';
import { Modal } from '../../../components/ui/Modal';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../../../components/ui/Table';
import { fetchApi } from '../../../app/config/api';

interface CredentialItem {
  id: string;
  w3c_id: string;
  credential_id: string;
  organization_id: string;
  recipient_address: string;
  schema_type: string;
  commitment: string;
  workflow_status: string;
  status: 'ACTIVE' | 'SUSPENDED' | 'REVOKED' | string;
  tx_hash?: string;
  revocation_reason?: string;
  created_at: string;
}

export const LifecycleView: React.FC = () => {
  const [credentials, setCredentials] = useState<CredentialItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Modal State
  const [selectedCred, setSelectedCred] = useState<CredentialItem | null>(null);
  const [actionType, setActionType] = useState<'suspend' | 'reinstate' | 'revoke' | null>(null);
  const [actionReason, setActionReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadCredentials();
  }, []);

  const loadCredentials = async () => {
    setLoading(true);
    try {
      const orgsRes = await fetchApi<{ items: Array<{ id: string }> }>('/organizations');
      const orgId = orgsRes?.items?.[0]?.id;
      if (orgId) {
        const res = await fetchApi<{ total: number; items: CredentialItem[] }>(
          `/credentials?organization_id=${orgId}`
        );
        setCredentials(res.items || []);
      }
    } catch (err: any) {
      console.error('Failed to load credentials:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (cred: CredentialItem, type: 'suspend' | 'reinstate' | 'revoke') => {
    setSelectedCred(cred);
    setActionType(type);
    setActionReason(
      type === 'suspend'
        ? 'Periodic compliance audit in progress; temporary administrative hold.'
        : type === 'reinstate'
        ? 'Institutional compliance verification completed; student reinstated in good standing.'
        : 'Academic integrity disciplinary board determination; degree permanently forfeited.'
    );
  };

  const executeLifecycleAction = async () => {
    if (!selectedCred || !actionType) return;
    setActionLoading(true);
    setStatusMessage(null);
    try {
      await fetchApi(`/credentials/${selectedCred.id}/${actionType}`, {
        method: 'POST',
        body: JSON.stringify({ reason: actionReason }),
      });

      setStatusMessage({
        type: 'success',
        text: `Credential ${selectedCred.credential_id.slice(0, 10)}... successfully transitioned to ${
          actionType === 'suspend' ? 'SUSPENDED' : actionType === 'reinstate' ? 'ACTIVE' : 'REVOKED'
        }. On-chain bitstring updated.`,
      });

      setSelectedCred(null);
      setActionType(null);
      await loadCredentials();
    } catch (err: any) {
      setStatusMessage({
        type: 'error',
        text: err.message || `Failed to ${actionType} credential.`,
      });
    } finally {
      setActionLoading(false);
    }
  };

  const activeCount = credentials.filter((c) => c.status === 'ACTIVE').length;
  const suspendedCount = credentials.filter((c) => c.status === 'SUSPENDED').length;
  const revokedCount = credentials.filter((c) => c.status === 'REVOKED').length;

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-16">
      {/* Editorial Header */}
      <div className="border-b border-border pb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-primary font-semibold text-xs tracking-wider uppercase mb-1">
            <RefreshCw size={15} />
            <span>State Machine & Status Management</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">
            Credential Lifecycle & Status Lists
          </h1>
          <p className="text-sm text-foreground-secondary mt-1 max-w-2xl leading-relaxed">
            Manage W3C Bitstring Status List v1.0 entries and execute on-chain state machine transitions: reversible administrative suspension and permanent, irreversible revocation.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={loadCredentials}
          isLoading={loading}
          leftIcon={<RefreshCw size={13} />}
        >
          Refresh Ledger
        </Button>
      </div>

      {statusMessage && (
        <div
          className={`p-3.5 rounded-control text-xs flex items-center justify-between ${
            statusMessage.type === 'success'
              ? 'bg-status-success-soft border border-status-success/30 text-status-success'
              : 'bg-status-danger-soft border border-status-danger/30 text-status-danger'
          }`}
        >
          <span className="font-medium">{statusMessage.text}</span>
          <button
            onClick={() => setStatusMessage(null)}
            className="text-foreground-muted hover:text-foreground text-xs font-bold ml-2"
          >
            ✕
          </button>
        </div>
      )}

      {/* State Machine Architecture Card */}
      <Card className="p-6">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-primary mb-3">
          Non-Repudiable Cryptographic State Machine
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-control bg-status-success-soft/30 border border-status-success/30 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-status-success flex items-center gap-1.5">
                <CheckCircle2 size={16} /> 1. ACTIVE (0x00)
              </span>
              <Badge variant="success" size="sm">
                Normal Operational
              </Badge>
            </div>
            <p className="text-[11px] text-foreground-secondary leading-relaxed">
              Credential passes all cryptographic and on-chain bitstring checks. Verifiers receive authoritative verification confirmation.
            </p>
            <span className="text-[10px] font-mono text-foreground-muted block pt-1">
              Transitions to: SUSPENDED or REVOKED
            </span>
          </div>

          <div className="p-4 rounded-control bg-status-warning-soft/30 border border-status-warning/30 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-status-warning flex items-center gap-1.5">
                <PauseCircle size={16} /> 2. SUSPENDED (0x01)
              </span>
              <Badge variant="warning" size="sm">
                Reversible Hold
              </Badge>
            </div>
            <p className="text-[11px] text-foreground-secondary leading-relaxed">
              Temporary administrative hold (e.g., student fee audit or disciplinary inquiry). Verifier is alerted of the hold.
            </p>
            <span className="text-[10px] font-mono text-foreground-muted block pt-1">
              Transitions to: ACTIVE or REVOKED
            </span>
          </div>

          <div className="p-4 rounded-control bg-status-danger-soft/30 border border-status-danger/30 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-status-danger flex items-center gap-1.5">
                <XCircle size={16} /> 3. REVOKED (0x02)
              </span>
              <Badge variant="danger" size="sm">
                Terminal State
              </Badge>
            </div>
            <p className="text-[11px] text-foreground-secondary leading-relaxed">
              Permanent degree or certificate forfeiture. Invariant: terminal state can NEVER be reinstated.
            </p>
            <span className="text-[10px] font-mono text-status-danger font-semibold block pt-1">
              Terminal: Irreversible on-chain invariant
            </span>
          </div>
        </div>

        {/* Dynamic Registry Stats Bar */}
        <div className="mt-5 pt-4 border-t border-border grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div>
            <span className="text-[10px] uppercase font-semibold text-foreground-muted block">
              Active Credentials
            </span>
            <span className="text-lg font-bold text-status-success">{activeCount}</span>
          </div>
          <div>
            <span className="text-[10px] uppercase font-semibold text-foreground-muted block">
              Under Suspension
            </span>
            <span className="text-lg font-bold text-status-warning">{suspendedCount}</span>
          </div>
          <div>
            <span className="text-[10px] uppercase font-semibold text-foreground-muted block">
              Permanently Revoked
            </span>
            <span className="text-lg font-bold text-status-danger">{revokedCount}</span>
          </div>
          <div>
            <span className="text-[10px] uppercase font-semibold text-foreground-muted block">
              Bitstring Status Registry
            </span>
            <span className="font-mono text-xs font-semibold text-primary block mt-1">
              0x9fE467366...
            </span>
          </div>
        </div>
      </Card>

      {/* Interactive Credential Ledger Table */}
      <Card className="space-y-4">
        <div className="border-b border-border pb-3 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-foreground">
              Institutional Credential Lifecycle Ledger
            </h2>
            <p className="text-xs text-foreground-secondary mt-0.5">
              Execute real-time status transitions anchored directly to the EVM CredentialStatusRegistry smart contract.
            </p>
          </div>
          <Badge variant="neutral" size="sm">
            {credentials.length} Managed Credentials
          </Badge>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Credential ID</TableHead>
              <TableHead>Recipient</TableHead>
              <TableHead>Schema Type</TableHead>
              <TableHead>Current Status</TableHead>
              <TableHead>Reason / Audit Note</TableHead>
              <TableHead className="text-right">Lifecycle Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {credentials.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="py-8 text-center text-foreground-secondary">
                  No credentials available in the registry.
                </TableCell>
              </TableRow>
            ) : (
              credentials.map((cred) => (
                <TableRow key={cred.id}>
                  <TableCell className="font-mono font-semibold text-foreground">
                    {cred.credential_id.slice(0, 14)}...
                  </TableCell>
                  <TableCell className="font-mono text-xs text-foreground-secondary">
                    {cred.recipient_address.slice(0, 10)}...{cred.recipient_address.slice(-4)}
                  </TableCell>
                  <TableCell className="font-medium text-xs">
                    {cred.schema_type}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        cred.status === 'ACTIVE'
                          ? 'success'
                          : cred.status === 'SUSPENDED'
                          ? 'warning'
                          : 'danger'
                      }
                      size="sm"
                      dot
                    >
                      {cred.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs text-foreground-muted max-w-[200px] truncate">
                    {cred.revocation_reason || 'In active institutional standing'}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      {cred.status === 'ACTIVE' && (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleOpenModal(cred, 'suspend')}
                            leftIcon={<PauseCircle size={13} />}
                          >
                            Suspend
                          </Button>
                          <Button
                            variant="danger"
                            size="sm"
                            onClick={() => handleOpenModal(cred, 'revoke')}
                            leftIcon={<XCircle size={13} />}
                          >
                            Revoke
                          </Button>
                        </>
                      )}

                      {cred.status === 'SUSPENDED' && (
                        <>
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => handleOpenModal(cred, 'reinstate')}
                            leftIcon={<PlayCircle size={13} />}
                          >
                            Reinstate
                          </Button>
                          <Button
                            variant="danger"
                            size="sm"
                            onClick={() => handleOpenModal(cred, 'revoke')}
                            leftIcon={<XCircle size={13} />}
                          >
                            Revoke
                          </Button>
                        </>
                      )}

                      {cred.status === 'REVOKED' && (
                        <span className="text-[11px] font-mono text-status-danger font-semibold flex items-center gap-1 justify-end">
                          <Lock size={12} /> Terminal Invariant
                        </span>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      {/* Confirmation & Reason Modal */}
      {selectedCred && actionType && (
        <Modal
          isOpen={!!selectedCred}
          onClose={() => {
            setSelectedCred(null);
            setActionType(null);
          }}
          title={
            actionType === 'suspend'
              ? 'Suspend Credential (Administrative Hold)'
              : actionType === 'reinstate'
              ? 'Reinstate Credential to Active Status'
              : 'Permanently Revoke Credential'
          }
          description={`Target Credential: ${selectedCred.credential_id}`}
          maxWidth="md"
          footer={
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSelectedCred(null);
                  setActionType(null);
                }}
              >
                Cancel
              </Button>
              <Button
                variant={actionType === 'revoke' ? 'danger' : 'primary'}
                size="sm"
                onClick={executeLifecycleAction}
                isLoading={actionLoading}
                leftIcon={actionType === 'revoke' ? <ShieldAlert size={14} /> : <RefreshCw size={14} />}
              >
                Confirm {actionType.toUpperCase()}
              </Button>
            </>
          }
        >
          <div className="space-y-4 text-xs">
            {actionType === 'revoke' && (
              <div className="p-3 bg-status-danger-soft border border-status-danger/30 rounded-control text-status-danger flex items-start gap-2">
                <AlertTriangle size={18} className="shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold block">Warning: Irreversible Action</span>
                  <p className="text-[11px] text-foreground-secondary mt-0.5">
                    Terminal revocation cannot be reversed. The on-chain bitstring will permanently flag this credential index as revoked.
                  </p>
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-foreground mb-1.5">
                Official Administrative Reason
              </label>
              <textarea
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                rows={3}
                className="w-full bg-surface text-foreground font-mono text-xs rounded-control border border-border p-2.5 focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 shadow-subtle"
                placeholder="Enter regulatory or administrative audit justification..."
                required
              />
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
