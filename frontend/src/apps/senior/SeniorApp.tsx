import React, { useState, useRef } from 'react';
import { VoiceMicButton } from '../../components/VoiceMicButton';
import { InsetGroupedList, InsetRow } from '../../components/InsetGroupedList';
import { PillButton } from '../../components/PillButton';
import { translations, SupportedLanguage } from '../../i18n';
import { Volume2, PhoneCall, AlertTriangle, CheckCircle, RefreshCw, XCircle, Camera } from 'lucide-react';

interface SeniorAppProps {
  lang: SupportedLanguage;
  onChangeLang: (lang: SupportedLanguage) => void;
  highContrast: boolean;
  onToggleHighContrast: () => void;
}

export const SeniorApp: React.FC<SeniorAppProps> = ({
  lang,
  onChangeLang,
  highContrast,
  onToggleHighContrast,
}) => {
  const t = translations[lang] || translations.en;
  const [scale, setScale] = useState<number>(1.2); // Default larger for seniors
  const [step, setStep] = useState<'idle' | 'listening' | 'confirm' | 'alerts'>('idle');
  const [candidate, setCandidate] = useState<string>('Telma 40 (Telmisartan 40mg)');
  const [rxImagePreview, setRxImagePreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeMeds, setActiveMeds] = useState<string[]>([
    'Ecosprin 75mg (Aspirin)',
    'Metosartan 50mg (Telmisartan + Metoprolol)',
  ]);
  const [ttsActive, setTtsActive] = useState<boolean>(false);

  // Read aloud helper using Web Speech API
  const handleSpeak = (text: string) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = lang === 'hi' ? 'hi-IN' : lang === 'kn' ? 'kn-IN' : 'en-US';
      utterance.rate = 0.88; // Slower cadence for seniors
      utterance.onstart = () => setTtsActive(true);
      utterance.onend = () => setTtsActive(false);
      utterance.onerror = () => setTtsActive(false);
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleSimulateVoice = () => {
    setStep('listening');
    setRxImagePreview(null);
    setTimeout(() => {
      setCandidate('Combiflam (Ibuprofen 400mg + Paracetamol 325mg)');
      setStep('confirm');
      handleSpeak(
        lang === 'hi'
          ? 'क्या आपने कॉम्बिफ्लेम लिया है? कृपया पुष्टि करें।'
          : 'Did you say Combiflam? Please confirm.'
      );
    }, 2000);
  };

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const reader = new FileReader();
      reader.onload = () => {
        const dataUrl = reader.result as string;
        setRxImagePreview(dataUrl);
        setCandidate('Combiflam 400mg + Paracetamol 325mg (From Prescription Slip)');
        setStep('confirm');
        handleSpeak(
          lang === 'hi'
            ? 'पर्चे से कॉम्बिफ्लेम दवा पहचानी गई है। क्या यह सही है?'
            : 'We identified Combiflam on your prescription slip. Please confirm.'
        );
      };
      reader.readAsDataURL(file);
    }
  };

  const handleConfirmMed = () => {
    setActiveMeds([...activeMeds, candidate]);
    setStep('alerts');
    handleSpeak(
      lang === 'hi'
        ? 'दवा जोड़ दी गई है। एस्पिरिन और कॉम्बिफ्लेम साथ लेने पर पेट में रक्तस्राव का जोखिम हो सकता है। कृपया अपने डॉक्टर से परामर्श करें।'
        : 'Medication added. Taking Aspirin and Combiflam together increases bleeding risk. Please discuss with your doctor.'
    );
  };

  return (
    <div
      style={{
        maxWidth: 720,
        margin: '0 auto',
        padding: '24px 20px 80px',
        fontSize: `calc(var(--senior-base-font-size) * ${scale})`,
        lineHeight: 1.55,
      }}
    >
      {/* Accessibility Toolbar: Text Scaling & Contrast */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 12,
          padding: '12px 16px',
          background: 'var(--bg-alt)',
          borderRadius: 16,
          marginBottom: 24,
          border: '1px solid var(--hairline)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 16, fontWeight: 600 }}>{t.textSize}:</span>
          <button
            onClick={() => setScale((s) => Math.max(1.0, s - 0.2))}
            style={{
              padding: '6px 14px',
              borderRadius: 8,
              background: 'var(--surface)',
              border: '1px solid var(--hairline)',
              fontSize: 16,
              fontWeight: 700,
            }}
            aria-label="Decrease font size"
          >
            A-
          </button>
          <button
            onClick={() => setScale((s) => Math.min(2.0, s + 0.2))}
            style={{
              padding: '6px 14px',
              borderRadius: 8,
              background: 'var(--surface)',
              border: '1px solid var(--hairline)',
              fontSize: 20,
              fontWeight: 700,
            }}
            aria-label="Increase font size"
          >
            A+
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            onClick={onToggleHighContrast}
            style={{
              padding: '8px 16px',
              borderRadius: 8,
              background: highContrast ? 'var(--text)' : 'var(--surface)',
              color: highContrast ? 'var(--bg)' : 'var(--text)',
              border: '1px solid var(--hairline)',
              fontSize: 15,
              fontWeight: 600,
            }}
          >
            {t.highContrast}
          </button>

          <select
            value={lang}
            onChange={(e) => onChangeLang(e.target.value as SupportedLanguage)}
            style={{
              padding: '8px 12px',
              borderRadius: 8,
              border: '1px solid var(--hairline)',
              background: 'var(--surface)',
              color: 'var(--text)',
              fontSize: 15,
              fontWeight: 600,
            }}
          >
            <option value="en">English</option>
            <option value="hi">हिंदी</option>
            <option value="kn">ಕನ್ನಡ</option>
          </select>
        </div>
      </div>

      {/* Emergency & Caregiver Shortcuts Bar */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 12,
          marginBottom: 32,
        }}
      >
        <a
          href="tel:112"
          className="pill-btn"
          style={{
            background: 'var(--sev-critical)',
            color: '#fff',
            minHeight: 56,
            fontSize: 17,
            fontWeight: 700,
            textDecoration: 'none',
          }}
        >
          <PhoneCall size={20} />
          <span>{t.callEmergency}</span>
        </a>

        <a
          href="tel:+919876543210"
          className="pill-btn"
          style={{
            background: 'var(--bg-alt)',
            color: 'var(--text)',
            border: '2px solid var(--hairline)',
            minHeight: 56,
            fontSize: 17,
            fontWeight: 700,
            textDecoration: 'none',
          }}
        >
          <PhoneCall size={20} />
          <span>{t.callCaregiver}</span>
        </a>
      </div>

      {/* Hidden file input for senior prescription camera */}
      <input
        type="file"
        ref={fileInputRef}
        accept="image/*"
        style={{ display: 'none' }}
        onChange={handlePhotoUpload}
      />

      {/* Step 1: Voice or Photo Input Screen */}
      {step === 'idle' && (
        <div style={{ textAlign: 'center', padding: '32px 0' }}>
          <h2 style={{ fontSize: '1.5em', fontWeight: 700, marginBottom: 12 }}>
            {lang === 'hi' ? 'दवा का नाम बोलें या फोटो दिखाएं' : 'Speak medicine name or take photo'}
          </h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 32 }}>
            {lang === 'hi'
              ? 'बड़ा माइक बटन दबाकर बोलें, या अपने पर्चे की फोटो खींचें।'
              : 'Tap the large microphone to speak, or tap below to photograph your prescription.'}
          </p>

          <VoiceMicButton
            isListening={false}
            onClick={handleSimulateVoice}
            label={t.tapToSpeak}
          />

          <div style={{ margin: '32px 0 16px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16 }}>
            <div style={{ height: 1, background: 'var(--hairline)', flex: 1 }} />
            <span style={{ fontSize: 14, color: 'var(--text-secondary)', fontWeight: 600 }}>OR</span>
            <div style={{ height: 1, background: 'var(--hairline)', flex: 1 }} />
          </div>

          <button
            onClick={() => fileInputRef.current?.click()}
            className="pill-btn pill-btn-large pill-btn-secondary"
            style={{
              width: '100%',
              maxWidth: 420,
              margin: '0 auto',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 12,
              minHeight: 64,
              fontSize: 19,
              fontWeight: 700,
              border: '2px dashed var(--accent)',
              borderRadius: 20,
            }}
          >
            <Camera size={26} color="var(--accent)" />
            <span>{lang === 'hi' ? '📷 पर्चे या पैकेट की फोटो खींचें' : '📷 Take Prescription Photo'}</span>
          </button>
        </div>
      )}

      {/* Step 2: Listening Active Screen */}
      {step === 'listening' && (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <VoiceMicButton
            isListening={true}
            onClick={() => {}}
            label={t.listening}
          />
        </div>
      )}

      {/* Step 3: Confirm-before-store (Principle S4) */}
      {step === 'confirm' && (
        <div
          style={{
            background: 'var(--surface)',
            borderRadius: 'var(--radius-card)',
            padding: 32,
            border: '2px solid var(--accent)',
            boxShadow: 'var(--shadow-card)',
            marginBottom: 32,
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '1.2em', fontWeight: 700, marginBottom: 12 }}>
            {lang === 'hi' ? 'क्या यह सही दवा है?' : 'Did we identify correctly?'}
          </div>

          {rxImagePreview && (
            <div style={{ margin: '16px auto', maxWidth: 300, borderRadius: 16, overflow: 'hidden', border: '1px solid var(--hairline)' }}>
              <img src={rxImagePreview} alt="Prescription" style={{ width: '100%', maxHeight: 180, objectFit: 'cover', display: 'block' }} />
            </div>
          )}

          <div
            style={{
              fontSize: '1.4em',
              fontWeight: 800,
              color: 'var(--accent)',
              padding: '16px 20px',
              background: 'var(--bg-alt)',
              borderRadius: 16,
              margin: '20px 0',
            }}
          >
            {candidate}
          </div>

          <div style={{ display: 'flex', gap: 16, justifyContent: 'center' }}>
            <PillButton
              size="large"
              variant="primary"
              onClick={handleConfirmMed}
              icon={<CheckCircle size={24} />}
            >
              {lang === 'hi' ? 'हाँ, यही है' : 'Yes, Confirm'}
            </PillButton>
            <PillButton
              size="large"
              variant="secondary"
              onClick={() => setStep('idle')}
              icon={<XCircle size={24} />}
            >
              {lang === 'hi' ? 'गलत नाम' : 'No, Try Again'}
            </PillButton>
          </div>
        </div>
      )}

      {/* Step 4: Safety Alerts View */}
      {step === 'alerts' && (
        <div>
          {/* Read aloud action */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
            <button
              onClick={() =>
                handleSpeak(
                  'Safety alert: Taking Combiflam with Aspirin significantly increases bleeding risk. Please ask your doctor.'
                )
              }
              className="pill-btn pill-btn-secondary"
              style={{ minHeight: 48, fontSize: 16 }}
            >
              <Volume2 size={20} color={ttsActive ? 'var(--accent)' : 'currentColor'} />
              <span>{t.readToMe}</span>
            </button>
          </div>

          {/* Active Alert Card */}
          <div
            style={{
              background: 'var(--surface)',
              borderRadius: 'var(--radius-card)',
              padding: 28,
              border: '2px solid var(--sev-critical)',
              marginBottom: 32,
              boxShadow: 'var(--shadow-card)',
            }}
          >
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '6px 14px',
                borderRadius: 'var(--radius-pill)',
                background: 'rgba(215, 0, 21, 0.1)',
                color: 'var(--sev-critical)',
                fontWeight: 700,
                fontSize: 15,
                marginBottom: 16,
              }}
            >
              <AlertTriangle size={18} />
              <span>HIGH BLEEDING RISK</span>
            </div>

            <h3 style={{ fontSize: '1.3em', fontWeight: 700, marginBottom: 12 }}>
              Combiflam + Aspirin (Ecosprin)
            </h3>

            <p style={{ color: 'var(--text-secondary)', marginBottom: 20 }}>
              Both medicines thin the stomach lining and prevent normal blood clotting. In adults over 65, taking them together significantly raises the chance of stomach ulcers and bleeding.
            </p>

            <div
              style={{
                padding: '16px 20px',
                background: 'var(--bg-alt)',
                borderRadius: 16,
                borderLeft: '4px solid var(--accent)',
                marginBottom: 16,
              }}
            >
              <div style={{ fontWeight: 700, color: 'var(--accent)', marginBottom: 4 }}>
                {t.askDoctorQuestion}
              </div>
              <div>
                &ldquo;Could we review whether Combiflam is safe with my daily blood thinner, or if there is a safer pain relief alternative?&rdquo;
              </div>
            </div>

            <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              <strong>{t.sourcesLabel}</strong> AGS Beers Criteria 2023, Rule INT-ANTICOAG-NSAID
            </div>
          </div>

          <div style={{ textAlign: 'center', marginTop: 24 }}>
            <PillButton
              variant="secondary"
              size="large"
              onClick={() => setStep('idle')}
              icon={<RefreshCw size={20} />}
            >
              {lang === 'hi' ? 'एक और दवा जोड़ें' : 'Add Another Medicine'}
            </PillButton>
          </div>
        </div>
      )}

      {/* Persistent Active Medications Group */}
      <InsetGroupedList title={t.activeMedications}>
        {activeMeds.map((med, idx) => (
          <InsetRow key={idx} label={med} value="Confirmed" />
        ))}
      </InsetGroupedList>
    </div>
  );
};

