import React from 'react';
import { Shield, Moon, Sun, Eye } from 'lucide-react';
import { SupportedLanguage } from '../i18n';

interface HeaderBarProps {
  currentApp: string;
  onSelectApp: (app: string) => void;
  lang: SupportedLanguage;
  onChangeLang: (lang: SupportedLanguage) => void;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
  highContrast: boolean;
  onToggleHighContrast: () => void;
}

export const HeaderBar: React.FC<HeaderBarProps> = ({
  currentApp,
  onSelectApp,
  lang,
  onChangeLang,
  theme,
  onToggleTheme,
  highContrast,
  onToggleHighContrast,
}) => {
  const apps = [
    { id: 'landing', label: 'Overview' },
    { id: 'senior', label: 'Senior' },
    { id: 'caregiver', label: 'Caregiver' },
    { id: 'clinician', label: 'Clinician' },
    { id: 'admin', label: 'Admin' },
    { id: 'simulator', label: 'Simulator' },
  ];

  return (
    <header className="top-nav" role="banner">
      {/* Brand logo & wordmark */}
      <div
        style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}
        onClick={() => onSelectApp('landing')}
      >
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            background: 'var(--accent)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
          }}
        >
          <Shield size={20} strokeWidth={2.5} />
        </div>
        <span style={{ fontSize: 18, fontWeight: 700, letterSpacing: '-0.02em' }}>
          MedGuard
        </span>
      </div>

      {/* Main Apps Navigation */}
      <nav style={{ display: 'flex', gap: 4 }} aria-label="Application navigation">
        {apps.map((a) => {
          const isActive = currentApp === a.id;
          return (
            <button
              key={a.id}
              onClick={() => onSelectApp(a.id)}
              style={{
                padding: '6px 14px',
                borderRadius: 'var(--radius-pill)',
                fontSize: 14,
                fontWeight: isActive ? 600 : 500,
                color: isActive ? 'var(--text)' : 'var(--text-secondary)',
                background: isActive ? 'var(--bg-alt)' : 'transparent',
                transition: 'all 0.15s var(--ease)',
              }}
            >
              {a.label}
            </button>
          );
        })}
      </nav>

      {/* Utilities: Lang, High Contrast, Dark Mode */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {/* Language selector */}
        <select
          value={lang}
          onChange={(e) => onChangeLang(e.target.value as SupportedLanguage)}
          aria-label="Language Selector"
          style={{
            padding: '4px 8px',
            borderRadius: 8,
            border: '1px solid var(--hairline)',
            background: 'var(--surface)',
            color: 'var(--text)',
            fontSize: 13,
            cursor: 'pointer',
          }}
        >
          <option value="en">English</option>
          <option value="hi">हिंदी</option>
          <option value="kn">ಕನ್ನಡ</option>
        </select>

        {/* High contrast toggle */}
        <button
          onClick={onToggleHighContrast}
          aria-label="Toggle High Contrast"
          title="Toggle High Contrast"
          style={{
            padding: 8,
            borderRadius: 8,
            color: highContrast ? 'var(--accent)' : 'var(--text-secondary)',
            background: highContrast ? 'var(--bg-alt)' : 'transparent',
          }}
        >
          <Eye size={18} />
        </button>

        {/* Theme toggle */}
        <button
          onClick={onToggleTheme}
          aria-label="Toggle Dark Mode"
          title="Toggle Dark Mode"
          style={{
            padding: 8,
            borderRadius: 8,
            color: 'var(--text-secondary)',
          }}
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </header>
  );
};

