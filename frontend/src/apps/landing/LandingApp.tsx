import React from 'react';
import { PillButton } from '../../components/PillButton';
import { CardTile } from '../../components/CardTile';
import { BentoGrid } from '../../components/BentoGrid';
import { DeviceFrame } from '../../components/DeviceFrame';
import { SimulatorApp } from '../simulator/SimulatorApp';
import { translations, SupportedLanguage } from '../../i18n';
import { ShieldCheck, Brain, FileText, ArrowRight, HeartPulse, Stethoscope, Lock } from 'lucide-react';

interface LandingAppProps {
  lang: SupportedLanguage;
  onNavigate: (app: string) => void;
}

export const LandingApp: React.FC<LandingAppProps> = ({ lang, onNavigate }) => {
  const t = translations[lang] || translations.en;

  return (
    <div style={{ width: '100%', overflowX: 'hidden' }}>
      {/* Hero Section */}
      <section
        style={{
          padding: '100px 24px 80px',
          textAlign: 'center',
          maxWidth: 1000,
          margin: '0 auto',
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 8,
            padding: '6px 16px',
            borderRadius: 'var(--radius-pill)',
            background: 'var(--bg-alt)',
            border: '1px solid var(--hairline)',
            fontSize: 14,
            fontWeight: 500,
            marginBottom: 24,
            color: 'var(--accent)',
          }}
        >
          <HeartPulse size={16} />
          <span>Clinical Geriatric Decision Support</span>
        </div>

        <h1
          style={{
            fontSize: 'clamp(40px, 6.5vw, 76px)',
            fontWeight: 600,
            letterSpacing: '-0.025em',
            lineHeight: 1.05,
            marginBottom: 24,
          }}
        >
          {t.heroHeadline}
        </h1>

        <p
          style={{
            fontSize: 'clamp(18px, 2.5vw, 22px)',
            lineHeight: 1.45,
            color: 'var(--text-secondary)',
            maxWidth: 720,
            margin: '0 auto 40px',
          }}
        >
          {t.heroSubheadline}
        </p>

        <div style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
          <PillButton
            size="large"
            variant="primary"
            onClick={() => onNavigate('senior')}
            icon={<ArrowRight size={20} />}
          >
            {t.tryDemo}
          </PillButton>
          <PillButton
            size="large"
            variant="secondary"
            onClick={() => {
              const el = document.getElementById('how-it-works');
              el?.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            {t.howItWorks}
          </PillButton>
        </div>
      </section>

      {/* Bento Grid Headline Capabilities */}
      <section style={{ padding: '40px 24px 80px', background: 'var(--bg-alt)' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <h2 style={{ fontSize: 'clamp(28px, 4vw, 44px)', fontWeight: 600, letterSpacing: '-0.02em' }}>
              Designed for Care. Grounded in Evidence.
            </h2>
          </div>

          <BentoGrid>
            <CardTile colSpan={8} highlight>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, marginBottom: 16 }}>
                <div style={{ padding: 12, borderRadius: 16, background: 'var(--accent)', color: '#fff' }}>
                  <ShieldCheck size={28} />
                </div>
                <div>
                  <h3 style={{ fontSize: 24, fontWeight: 600, marginBottom: 8 }}>
                    Deterministic Clinical Rules Engine
                  </h3>
                  <p style={{ fontSize: 17, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    Zero LLM hallucinations. All safety evaluations are performed by hard deterministic rules encoded from the 2023 AGS Beers Criteria®, STOPP/START v3, and the Anticholinergic Burden (ACB) scale.
                  </p>
                </div>
              </div>
            </CardTile>

            <CardTile colSpan={4}>
              <div style={{ padding: 12, borderRadius: 16, background: 'var(--bg-alt)', width: 'fit-content', marginBottom: 16 }}>
                <Brain size={28} color="var(--accent)" />
              </div>
              <h3 style={{ fontSize: 22, fontWeight: 600, marginBottom: 8 }}>
                Specialty Agent Panel
              </h3>
              <p style={{ fontSize: 16, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                Multi-specialist deliberation across Cardiology, Nephrology, Geriatrics, and GI with a neutral moderator that never forces artificial consensus.
              </p>
            </CardTile>

            <CardTile colSpan={4}>
              <div style={{ padding: 12, borderRadius: 16, background: 'var(--bg-alt)', width: 'fit-content', marginBottom: 16 }}>
                <FileText size={28} color="var(--accent)" />
              </div>
              <h3 style={{ fontSize: 22, fontWeight: 600, marginBottom: 8 }}>
                Doctor Discussion Guide
              </h3>
              <p style={{ fontSize: 16, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                Generates a structured 1-page A4 PDF with questions to empower seniors and caregivers during clinical visits.
              </p>
            </CardTile>

            <CardTile colSpan={4}>
              <div style={{ padding: 12, borderRadius: 16, background: 'var(--bg-alt)', width: 'fit-content', marginBottom: 16 }}>
                <Lock size={28} color="var(--accent)" />
              </div>
              <h3 style={{ fontSize: 22, fontWeight: 600, marginBottom: 8 }}>
                Masked PII Vault
              </h3>
              <p style={{ fontSize: 16, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                Patient identifiers are encrypted in a Fernet vault. LLM calls only ever see synthetic surrogate tokens like PT-DEMO.
              </p>
            </CardTile>

            <CardTile colSpan={4}>
              <div style={{ padding: 12, borderRadius: 16, background: 'var(--bg-alt)', width: 'fit-content', marginBottom: 16 }}>
                <Stethoscope size={28} color="var(--accent)" />
              </div>
              <h3 style={{ fontSize: 22, fontWeight: 600, marginBottom: 8 }}>
                Clinician Swipe Queue
              </h3>
              <p style={{ fontSize: 16, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                Card-based review queue with mandatory reason tags, 10-second undo, and a governed feedback loop for continuous rule refinement.
              </p>
            </CardTile>
          </BentoGrid>
        </div>
      </section>

      {/* 3-Step Scroll Story */}
      <section id="how-it-works" style={{ padding: '96px 24px', maxWidth: 1000, margin: '0 auto' }}>
        <h2 style={{ fontSize: 'clamp(32px, 5vw, 52px)', fontWeight: 600, textAlign: 'center', marginBottom: 64, letterSpacing: '-0.02em' }}>
          Three simple steps to medication safety.
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 40 }}>
          <div style={{ padding: 24, borderLeft: '3px solid var(--accent)' }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase', marginBottom: 8 }}>
              {t.sayItTitle}
            </div>
            <p style={{ fontSize: 18, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              {t.sayItDesc}
            </p>
          </div>

          <div style={{ padding: 24, borderLeft: '3px solid var(--accent)' }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase', marginBottom: 8 }}>
              {t.checkItTitle}
            </div>
            <p style={{ fontSize: 18, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              {t.checkItDesc}
            </p>
          </div>

          <div style={{ padding: 24, borderLeft: '3px solid var(--accent)' }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase', marginBottom: 8 }}>
              {t.shareItTitle}
            </div>
            <p style={{ fontSize: 18, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              {t.shareItDesc}
            </p>
          </div>
        </div>
      </section>

      {/* Embedded Live WhatsApp Simulator Preview */}
      <section style={{ padding: '80px 24px', background: 'var(--bg-alt)' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', textAlign: 'center' }}>
          <h2 style={{ fontSize: 'clamp(28px, 4vw, 44px)', fontWeight: 600, marginBottom: 16 }}>
            Live Interactive Simulator
          </h2>
          <p style={{ fontSize: 18, color: 'var(--text-secondary)', marginBottom: 48, maxWidth: 600, margin: '0 auto 48px' }}>
            Experience how a senior interacts via WhatsApp. You can type, choose test scenarios, or test emergency red-flags.
          </p>

          <DeviceFrame>
            <div style={{ height: 600, overflow: 'hidden' }}>
              <SimulatorApp isEmbedded />
            </div>
          </DeviceFrame>
        </div>
      </section>

      {/* Clinical Footnotes & Disclaimers */}
      <footer style={{ padding: '64px 24px 80px', borderTop: '1px solid var(--hairline)', background: 'var(--bg)' }}>
        <div style={{ maxWidth: 1000, margin: '0 auto', fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
          <p style={{ marginBottom: 12 }}>
            <strong>1. Clinical Grounding:</strong> MedGuard references the 2023 American Geriatrics Society (AGS) Beers Criteria®, the Screening Tool of Older Persons&apos; Prescriptions (STOPP) v3, and the Medication Appropriateness Index (MAI). MedGuard is decision support and not a medical device.
          </p>
          <p style={{ marginBottom: 12 }}>
            <strong>2. Non-Directive Advice:</strong> All recommendations are phrased neutrally (&ldquo;Ask your doctor whether...&rdquo;) and never instruct patients to stop or change prescribed therapy without medical supervision.
          </p>
          <p>
            <strong>3. Emergency Red Flags:</strong> Critical acute symptoms immediately trigger emergency escalation to national emergency services (112 in India).
          </p>
        </div>
      </footer>
    </div>
  );
};
