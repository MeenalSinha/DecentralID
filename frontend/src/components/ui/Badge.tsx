import React from 'react';

export type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'primary';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  dot?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  dot = false,
  className = '',
  ...props
}) => {
  const sizeStyles = {
    sm: 'text-[11px] px-2 py-0.5 gap-1 font-medium',
    md: 'text-xs px-2.5 py-1 gap-1.5 font-medium',
  };

  const variantStyles = {
    success: 'bg-status-success-soft text-status-success border border-status-success/20',
    warning: 'bg-status-warning-soft text-status-warning border border-status-warning/20',
    danger: 'bg-status-danger-soft text-status-danger border border-status-danger/20',
    info: 'bg-status-info-soft text-status-info border border-status-info/20',
    neutral: 'bg-surface-subtle text-foreground-secondary border border-border',
    primary: 'bg-primary-soft text-primary border border-primary/20',
  };

  const dotColors = {
    success: 'bg-status-success',
    warning: 'bg-status-warning',
    danger: 'bg-status-danger',
    info: 'bg-status-info',
    neutral: 'bg-foreground-muted',
    primary: 'bg-primary',
  };

  return (
    <span
      className={`inline-flex items-center rounded-md ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]}`} />}
      {children}
    </span>
  );
};
