import React from 'react';

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  helperText?: string;
  error?: string;
  options?: Array<{ value: string; label: string }>;
}

export const Select: React.FC<SelectProps> = ({
  label,
  helperText,
  error,
  options,
  children,
  className = '',
  id,
  ...props
}) => {
  const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={selectId}
          className="block text-xs font-semibold text-foreground mb-1.5"
        >
          {label}
        </label>
      )}
      <select
        id={selectId}
        className={`w-full bg-surface text-foreground text-sm rounded-control border ${
          error
            ? 'border-status-danger focus:ring-status-danger/20'
            : 'border-border hover:border-border-strong focus:border-primary focus:ring-primary/20'
        } px-3.5 py-2 transition-colors duration-150 focus:outline-none focus:ring-2 disabled:bg-surface-subtle disabled:cursor-not-allowed shadow-subtle ${className}`}
        {...props}
      >
        {options
          ? options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))
          : children}
      </select>
      {error ? (
        <p className="mt-1 text-xs text-status-danger">{error}</p>
      ) : helperText ? (
        <p className="mt-1 text-xs text-foreground-secondary">{helperText}</p>
      ) : null}
    </div>
  );
};
