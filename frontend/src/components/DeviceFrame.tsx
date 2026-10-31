import React from 'react';

interface DeviceFrameProps {
  children: React.ReactNode;
  className?: string;
}

export const DeviceFrame: React.FC<DeviceFrameProps> = ({ children, className = '' }) => {
  return (
    <div className={`device-frame ${className}`}>
      {/* Top Device Notch / Speaker Bar */}
      <div
        style={{
          height: 24,
          background: 'var(--text)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '0 20px',
        }}
      >
        <div
          style={{
            width: 48,
            height: 4,
            borderRadius: 2,
            background: 'var(--bg)',
            opacity: 0.3,
          }}
        />
      </div>
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {children}
      </div>
    </div>
  );
};

