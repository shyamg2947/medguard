import React from 'react';
import { Mic, Square, Loader2 } from 'lucide-react';

interface VoiceMicButtonProps {
  isListening: boolean;
  isProcessing?: boolean;
  onClick: () => void;
  label?: string;
}

export const VoiceMicButton: React.FC<VoiceMicButtonProps> = ({
  isListening,
  isProcessing = false,
  onClick,
  label = "Tap to speak medicine name"
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
      <button
        onClick={onClick}
        aria-label={isListening ? "Stop listening" : label}
        aria-pressed={isListening}
        style={{
          width: 80,
          height: 80,
          borderRadius: '50%',
          background: isListening ? 'var(--sev-critical)' : 'var(--accent)',
          color: '#ffffff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: isListening
            ? '0 0 0 10px rgba(215, 0, 21, 0.2), 0 8px 24px rgba(215, 0, 21, 0.4)'
            : '0 8px 24px rgba(0, 113, 227, 0.35)',
          transition: 'all 0.3s var(--ease)',
          transform: isListening ? 'scale(1.08)' : 'scale(1.0)',
          outline: 'none',
        }}
      >
        {isProcessing ? (
          <Loader2 className="animate-spin" size={36} />
        ) : isListening ? (
          <Square size={32} />
        ) : (
          <Mic size={36} />
        )}
      </button>
      <div
        style={{
          fontSize: 16,
          fontWeight: 600,
          color: isListening ? 'var(--sev-critical)' : 'var(--text-secondary)',
        }}
      >
        {isProcessing ? "Analyzing..." : isListening ? "Listening... (Tap to finish)" : label}
      </div>
    </div>
  );
};

