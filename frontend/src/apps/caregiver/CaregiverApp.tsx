import React, { useState } from 'react';
import { InsetGroupedList, InsetRow } from '../../components/InsetGroupedList';
import { PillButton } from '../../components/PillButton';
import { FileDown, PlusCircle, AlertCircle, Clock, CheckCircle2, UserCheck } from 'lucide-react';

export const CaregiverApp: React.FC = () => {
  const [selectedPatient] = useState({
    name: 'Savitri Sharma (Mother)',
    token: 'PT-DEMO-A74',
    age: 74,
    gender: 'Female',
  });

  const medications = [
    { name: 'Warfarin 2mg', class: 'Anticoagulant', schedule: 'Once daily (Evening)' },
    { name: 'Ecosprin 75mg', class: 'Antiplatelet (Aspirin)', schedule: 'Once daily (Post lunch)' },
    { name: 'Combiflam', class: 'NSAID (Ibuprofen + Paracetamol)', schedule: 'As needed for knee pain' },
    { name: 'Pantocid 40mg', class: 'PPI (Pantoprazole)', schedule: '14 weeks ongoing' },
    { name: 'Ashwagandha Churna', class: 'Ayurvedic Supplement', schedule: '5g at bedtime' },
  ];

  const recentChanges = [
    { text: 'Combiflam added via voice note', time: 'Yesterday, 4:15 PM' },
    { text: 'Weekly check-in completed (Reported mild dizziness)', time: '3 days ago' },
  ];

  const alerts = [
    {
      severity: 'critical',
      title: 'Triple Bleeding Hazard: Warfarin + Aspirin + Combiflam',
      question: 'Ask your doctor whether Combiflam should be replaced with topical gel or acetaminophen to prevent major GI bleed.',
      source: 'AGS Beers Criteria 2023, Rule INT-ANTICOAG-NSAID',
    },
    {
      severity: 'high',
      title: 'PPI Duration Exceeded (> 8 Weeks)',
      question: 'Pantoprazole taken continuously for 14 weeks. Inquire if tapering to as-needed is clinically appropriate.',
      source: 'Beers 2023 / STOPP v3, Rule DUR-PPI-8WEEKS',
    },
  ];

  const handleDownloadGuide = () => {
    // Triggers download of generated guide PDF from backend
    window.open('/patients/demo-patient-scen-a/guide.pdf', '_blank');
  };

  return (
    <div style={{ maxWidth: 840, margin: '0 auto', padding: '32px 20px 80px' }}>
      {/* Patient Header Card */}
      <div
        style={{
          background: 'var(--surface)',
          borderRadius: 'var(--radius-card)',
          padding: 24,
          border: '1px solid var(--hairline)',
          boxShadow: 'var(--shadow-card)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 16,
          marginBottom: 32,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: '50%',
              background: 'var(--accent)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
            }}
          >
            <UserCheck size={28} />
          </div>
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 700 }}>{selectedPatient.name}</h2>
            <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              Age {selectedPatient.age} • {selectedPatient.gender} • Token: {selectedPatient.token}
            </div>
          </div>
        </div>

        <PillButton
          variant="primary"
          onClick={handleDownloadGuide}
          icon={<FileDown size={18} />}
        >
          Download Doctor Guide (PDF)
        </PillButton>
      </div>

      {/* What Changed Section */}
      <div style={{ marginBottom: 32 }}>
        <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Clock size={18} color="var(--accent)" />
          <span>What Changed Recently</span>
        </h3>
        <div style={{ background: 'var(--bg-alt)', borderRadius: 16, padding: '16px 20px', border: '1px solid var(--hairline)' }}>
          {recentChanges.map((c, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: i === 0 ? '1px solid var(--hairline)' : 'none' }}>
              <span style={{ fontWeight: 500 }}>{c.text}</span>
              <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{c.time}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Safety Alerts */}
      <div style={{ marginBottom: 32 }}>
        <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
          <AlertCircle size={18} color="var(--sev-critical)" />
          <span>Active Safety Alerts ({alerts.length})</span>
        </h3>

        {alerts.map((a, i) => (
          <div
            key={i}
            style={{
              background: 'var(--surface)',
              borderRadius: 16,
              padding: 20,
              border: `1px solid ${a.severity === 'critical' ? 'var(--sev-critical)' : 'var(--sev-high)'}`,
              marginBottom: 16,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <span
                style={{
                  fontSize: 12,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-pill)',
                  background: a.severity === 'critical' ? 'rgba(215, 0, 21, 0.12)' : 'rgba(201, 52, 0, 0.12)',
                  color: a.severity === 'critical' ? 'var(--sev-critical)' : 'var(--sev-high)',
                }}
              >
                {a.severity}
              </span>
              <span style={{ fontWeight: 600, fontSize: 16 }}>{a.title}</span>
            </div>
            <p style={{ fontSize: 15, color: 'var(--text)', marginBottom: 12 }}>
              <strong>Question for doctor:</strong> {a.question}
            </p>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              Source: {a.source}
            </div>
          </div>
        ))}
      </div>

      {/* Full Medication List */}
      <InsetGroupedList title="Full Medication Picture (Prescriptions + OTC + Herbal)">
        {medications.map((m, i) => (
          <InsetRow
            key={i}
            icon={<CheckCircle2 size={18} />}
            label={m.name}
            value={`${m.class} • ${m.schedule}`}
          />
        ))}
      </InsetGroupedList>

      <div style={{ display: 'flex', justifyContent: 'center', marginTop: 24 }}>
        <PillButton
          variant="secondary"
          onClick={() => alert('Caregiver Add Medication flow: Voice note or manual entry triggers S4 confirm-before-store.')}
          icon={<PlusCircle size={18} />}
        >
          Add Medicine on Patient&apos;s Behalf
        </PillButton>
      </div>
    </div>
  );
};

