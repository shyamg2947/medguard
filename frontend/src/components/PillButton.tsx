import React from 'react';

interface PillButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary';
  size?: 'normal' | 'large';
  icon?: React.ReactNode;
  children: React.ReactNode;
}

export const PillButton: React.FC<PillButtonProps> = ({
  variant = 'primary',
  size = 'normal',
  icon,
  children,
  className = '',
  ...props
}) => {
  const baseClass = `pill-btn pill-btn-${variant} ${size === 'large' ? 'pill-btn-large' : ''} ${className}`;
  return (
    <button className={baseClass} {...props}>
      {icon && <span aria-hidden="true">{icon}</span>}
      <span>{children}</span>
    </button>
  );
};

