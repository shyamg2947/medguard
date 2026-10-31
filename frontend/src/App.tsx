import React, { useState, useEffect } from 'react';
import { HeaderBar } from './components/HeaderBar';
import { LandingApp } from './apps/landing/LandingApp';
import { SeniorApp } from './apps/senior/SeniorApp';
import { CaregiverApp } from './apps/caregiver/CaregiverApp';
import { ClinicianApp } from './apps/clinician/ClinicianApp';
import { AdminApp } from './apps/admin/AdminApp';
import { SimulatorApp } from './apps/simulator/SimulatorApp';
import { SupportedLanguage } from './i18n';
import './styles/tokens.css';

export const App: React.FC = () => {
  const [currentApp, setCurrentApp] = useState<string>('landing');
  const [lang, setLang] = useState<SupportedLanguage>('en');
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [highContrast, setHighContrast] = useState<boolean>(false);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-high-contrast', String(highContrast));
    document.documentElement.setAttribute('lang', lang);
  }, [theme, highContrast, lang]);

  const toggleTheme = () => {
    setTheme((t) => (t === 'light' ? 'dark' : 'light'));
  };

  const toggleHighContrast = () => {
    setHighContrast((hc) => !hc);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <HeaderBar
        currentApp={currentApp}
        onSelectApp={setCurrentApp}
        lang={lang}
        onChangeLang={setLang}
        theme={theme}
        onToggleTheme={toggleTheme}
        highContrast={highContrast}
        onToggleHighContrast={toggleHighContrast}
      />

      <main style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {currentApp === 'landing' && (
          <LandingApp lang={lang} onNavigate={setCurrentApp} />
        )}
        {currentApp === 'senior' && (
          <SeniorApp
            lang={lang}
            onChangeLang={setLang}
            highContrast={highContrast}
            onToggleHighContrast={toggleHighContrast}
          />
        )}
        {currentApp === 'caregiver' && <CaregiverApp />}
        {currentApp === 'clinician' && <ClinicianApp />}
        {currentApp === 'admin' && <AdminApp />}
        {currentApp === 'simulator' && <SimulatorApp />}
      </main>
    </div>
  );
};

