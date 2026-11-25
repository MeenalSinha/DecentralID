import React from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  error?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({
  label,
  helperText,
  error,
  leftIcon,
  rightIcon,
  className = '',
  id,
  disabled,
  ...props
}) => {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-xs font-semibold text-foreground mb-1.5"
        >
          {label}
        </label>
      )}
      <div className="relative flex items-center">
        {leftIcon && (
          <div className="absolute left-3 text-foreground-muted pointer-events-none flex items-center">
            {leftIcon}
          </div>
        )}
        <input
          id={inputId}
          disabled={disabled}
          className={`w-full bg-surface text-foreground text-sm rounded-control border ${
            error
              ? 'border-status-danger focus:ring-status-danger/20 focus:border-status-danger'
              : 'border-border hover:border-border-strong focus:border-primary focus:ring-primary/20'
          } ${leftIcon ? 'pl-9' : 'pl-3.5'} ${
            rightIcon ? 'pr-9' : 'pr-3.5'
          } py-2 transition-colors duration-150 focus:outline-none focus:ring-2 disabled:bg-surface-subtle disabled:cursor-not-allowed placeholder:text-foreground-muted shadow-subtle ${className}`}
          {...props}
        />
        {rightIcon && (
          <div className="absolute right-3 text-foreground-muted flex items-center">
            {rightIcon}
          </div>
        )}
      </div>
      {error ? (
        <p className="mt-1 text-xs text-status-danger">{error}</p>
      ) : helperText ? (
        <p className="mt-1 text-xs text-foreground-secondary">{helperText}</p>
      ) : null}
    </div>
  );
};
