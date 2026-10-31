import React from 'react';

interface InsetGroupedListProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export const InsetGroupedList: React.FC<InsetGroupedListProps> = ({
  title,
  children,
  className = '',
}) => {
  return (
    <div className={`inset-group-wrapper ${className}`} style={{ marginBottom: 24 }}>
      {title && (
        <div
          style={{
            fontSize: 13,
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: 'var(--text-secondary)',
            marginBottom: 8,
            paddingLeft: 16,
          }}
        >
          {title}
        </div>
      )}
      <div className="inset-group">{children}</div>
    </div>
  );
};

interface InsetRowProps {
  label: React.ReactNode;
  value?: React.ReactNode;
  icon?: React.ReactNode;
  onClick?: () => void;
  className?: string;
}

export const InsetRow: React.FC<InsetRowProps> = ({
  label,
  value,
  icon,
  onClick,
  className = '',
}) => {
  return (
    <div
      className={`inset-row ${className}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        {icon && <span aria-hidden="true" style={{ color: 'var(--accent)' }}>{icon}</span>}
        <div style={{ fontSize: 16, fontWeight: 500 }}>{label}</div>
      </div>
      {value && <div style={{ fontSize: 15, color: 'var(--text-secondary)' }}>{value}</div>}
    </div>
  );
};

