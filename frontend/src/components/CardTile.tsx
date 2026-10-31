import React from 'react';

interface CardTileProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  colSpan?: 4 | 6 | 8 | 12;
  highlight?: boolean;
}

export const CardTile: React.FC<CardTileProps> = ({
  children,
  colSpan = 4,
  highlight = false,
  className = '',
  style = {},
  ...props
}) => {
  const colClass = `col-${colSpan}`;
  const highlightStyle = highlight
    ? { borderColor: 'var(--accent)', background: 'var(--surface-alt)' }
    : {};

  return (
    <div
      className={`tile-card ${colClass} ${className}`}
      style={{ ...highlightStyle, ...style }}
      {...props}
    >
      {children}
    </div>
  );
};

