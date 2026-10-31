import React, { useState } from 'react';
import { PillButton } from '../../components/PillButton';
import { Check, X, HelpCircle, RotateCcw, Eye, ShieldAlert, FileText, CheckCircle2 } from 'lucide-react';

interface MockCase {
  id: string;
  patientToken: string;
  age: number;
  gender: string;
  severity: 'critical' | 'high' | 'moderate';
  medications: Array<{ name: string; dose: string }>;
  alerts: Array<{
    ruleId: string;
    title: string;
    rationale: string;
    doctorQuestion: string;
    sources: string;
  }>;
  specialistPanelSummary: string;
  draftPatientMessage: string;
}

const mockCases: MockCase[] = [
  {
    id: 'case-scen-a',
    patientToken: 'PT-DEMO-A74',
    age: 74,
    gender: 'Female',
    severity: 'critical',
    medications: [
      { name: 'Warfarin', dose: '2mg daily' },
      { name: 'Aspirin (Ecosprin)', dose: '75mg daily' },
      { name: 'Combiflam (Ibuprofen + Paracetamol)', dose: 'PRN knee pain' },
      { name: 'Pantoprazole (Pantocid)', dose: '40mg daily (14 wks)' },
      { name: 'Ashwagandha Churna', dose: '5g nightly' },
    ],
    alerts: [
      {
        ruleId: 'INT-ANTICOAG-NSAID',
        title: 'Anticoagulant + NSAID Bleeding Hazard',
        rationale: 'Warfarin combined with Ibuprofen multiplies upper gastrointestinal bleeding risk by 4-6x in older adults.',
        doctorQuestion: 'Ask your doctor whether Combiflam can be substituted with a topical NSAID or paracetamol alone.',
        sources: 'AGS Beers Criteria 2023; STOPP v3 Section A',
      },
      {
        ruleId: 'DUR-PPI-8WEEKS',
        title: 'Proton Pump Inhibitor Duration > 8 Weeks',
        rationale: 'Extended PPI therapy beyond 8 weeks without documented ulceration is associated with bone fractures and C. difficile.',
        doctorQuestion: 'Ask your doctor whether the pantoprazole dose can be reviewed or tapered.',
        sources: 'Beers Criteria 2023 Table 2',
      },
    ],
    specialistPanelSummary:
      'Cardiology: High thromboembolic risk requires Warfarin continuation; NSAID must be avoided. GI: Severe bleeding hazard with dual antithrombotic + systemic NSAID. Panel consensus: Neutral recommendation to discuss pain alternatives with prescribing physician.',
    draftPatientMessage:
      'We noticed you are taking Combiflam alongside Warfarin and Aspirin. Taking these together can increase the chance of stomach bleeding. Please ask your doctor if a safer pain medicine is available for your knees.',
  },
  {
    id: 'case-scen-b',
    patientToken: 'PT-DEMO-B69',
    age: 69,
    gender: 'Male',
    severity: 'critical',
    medications: [
      { name: 'Telmisartan (Telma)', dose: '40mg daily' },
      { name: 'Furosemide (Lasix)', dose: '20mg daily' },
      { name: 'Diclofenac (Voveran)', dose: '50mg PRN back pain' },
      { name: 'Metformin (Glycomet)', dose: '500mg BD' },
    ],
    alerts: [
      {
        ruleId: 'COMBO-TRIPLE-WHAMMY',
        title: 'Triple Whammy Acute Kidney Injury Risk',
        rationale: 'Concomitant ARB (Telmisartan) + Loop Diuretic (Furosemide) + NSAID (Diclofenac) produces synergistic hemodynamic renal hypoperfusion.',
        doctorQuestion: 'Ask your doctor whether Diclofenac should be avoided while taking blood pressure and water pills.',
        sources: 'STOPP v3 Criteria Section C; BNF Drug Interactions',
      },
    ],
    specialistPanelSummary:
      'Nephrology: High acute renal failure risk. CrCl estimated at 42 mL/min. ARB + Diuretic already constrict glomerular flow. Discontinuation of oral NSAID strongly advised in discussion with doctor.',
    draftPatientMessage:
      'Taking pain medicine like Voveran while on blood pressure medicines and water tablets can stress your kidneys. Ask your doctor about safer options for back pain relief.',
  },
];

export const ClinicianApp: React.FC = () => {
  const [cases, setCases] = useState<MockCase[]>(mockCases);
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const [patientMessageEdit, setPatientMessageEdit] = useState<string>('');
  void patientMessageEdit;
  const [isRejectModalOpen, setIsRejectModalOpen] = useState<boolean>(false);
  const [rejectReason, setRejectReason] = useState<string>('false_positive');
  const [rejectNote, setRejectNote] = useState<string>('');
  const [undoToast, setUndoToast] = useState<{ visible: boolean; caseId: string; secondsLeft: number } | null>(null);
  const [revealedNames, setRevealedNames] = useState<Record<string, string>>({});
  const [isRevealModalOpen, setIsRevealModalOpen] = useState<boolean>(false);
  const [revealReason, setRevealReason] = useState<string>('');

  const activeCase = cases[selectedIndex];

  const handleAgree = () => {
    if (!activeCase) return;
    triggerUndo(activeCase.id);
    advanceCase();
  };

  const handleOpenRejectModal = () => {
    setIsRejectModalOpen(true);
  };

  const handleConfirmReject = () => {
    if (!activeCase) return;
    setIsRejectModalOpen(false);
    triggerUndo(activeCase.id);
    advanceCase();
  };

  const advanceCase = () => {
    if (selectedIndex < cases.length - 1) {
      setSelectedIndex(selectedIndex + 1);
    } else {
      setCases([]);
    }
  };

  const triggerUndo = (caseId: string) => {
    setUndoToast({ visible: true, caseId, secondsLeft: 10 });
    let sec = 10;
    const interval = setInterval(() => {
      sec -= 1;
      if (sec <= 0) {
        clearInterval(interval);
        setUndoToast(null);
      } else {
        setUndoToast((prev) => (prev ? { ...prev, secondsLeft: sec } : null));
      }
    }, 1000);
  };

  const handleUndo = () => {
    setUndoToast(null);
    alert('Decision undone within 10-second safety window. Case returned to active queue.');
  };

  const handleAuditedReveal = () => {
    if (!revealReason.trim()) {
      alert('Clinical reason for identity reveal is mandatory for the audit log.');
      return;
    }
    setRevealedNames({
      ...revealedNames,
      [activeCase.id]: 'Mrs. Savitri Sharma (Ph: +91 98765 43210)',
    });
    setIsRevealModalOpen(false);
    setRevealReason('');
  };

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 52px)', overflow: 'hidden' }}>
      {/* Left Sidebar: Queue List */}
      <div
        style={{
          width: 360,
          borderRight: '1px solid var(--hairline)',
          background: 'var(--bg-alt)',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--hairline)' }}>
          <h2 style={{ fontSize: 18, fontWeight: 700 }}>Review Queue ({cases.length})</h2>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            Sorted by severity & clinical priority
          </div>
        </div>

        <div style={{ flex: 1 }}>
          {cases.length === 0 ? (
            <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-secondary)' }}>
              <CheckCircle2 size={36} color="var(--sev-low)" style={{ margin: '0 auto 12px' }} />
              <div>All cases reviewed!</div>
            </div>
          ) : (
            cases.map((c, idx) => (
              <div
                key={c.id}
                onClick={() => setSelectedIndex(idx)}
                style={{
                  padding: '16px 20px',
                  borderBottom: '1px solid var(--hairline)',
                  cursor: 'pointer',
                  background: selectedIndex === idx ? 'var(--surface)' : 'transparent',
                  borderLeft: selectedIndex === idx ? '4px solid var(--accent)' : '4px solid transparent',
                  transition: 'background 0.2s var(--ease)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span style={{ fontWeight: 600, fontSize: 15 }}>{c.patientToken}</span>
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      color: c.severity === 'critical' ? 'var(--sev-critical)' : 'var(--sev-high)',
                    }}
                  >
                    {c.severity}
                  </span>
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 4 }}>
                  Age {c.age} • {c.gender} • {c.medications.length} meds
                </div>
                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text)' }}>
                  {c.alerts[0]?.title}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Right Main Detail Pane */}
      {activeCase ? (
        <div style={{ flex: 1, overflowY: 'auto', padding: '32px 40px', background: 'var(--bg)' }}>
          {/* Header Bar with Masking & Reveal */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <h1 style={{ fontSize: 24, fontWeight: 700 }}>
                  {revealedNames[activeCase.id] || activeCase.patientToken}
                </h1>
                {!revealedNames[activeCase.id] && (
                  <button
                    onClick={() => setIsRevealModalOpen(true)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                      fontSize: 13,
                      color: 'var(--accent)',
                      background: 'var(--bg-alt)',
                      padding: '4px 10px',
                      borderRadius: 6,
                      border: '1px solid var(--hairline)',
                    }}
                  >
                    <Eye size={14} />
                    <span>Audited Reveal</span>
                  </button>
                )}
              </div>
              <div style={{ fontSize: 14, color: 'var(--text-secondary)', marginTop: 4 }}>
                Age {activeCase.age} • {activeCase.gender} • Clinical Case ID: {activeCase.id}
              </div>
            </div>

            {/* Swipe Action Buttons */}
            <div style={{ display: 'flex', gap: 12 }}>
              <PillButton
                variant="secondary"
                onClick={handleOpenRejectModal}
                style={{ borderColor: 'var(--sev-critical)', color: 'var(--sev-critical)' }}
                icon={<X size={18} />}
              >
                Reject (Left Arrow)
              </PillButton>

              <PillButton
                variant="secondary"
                onClick={() => alert('Marked Needs More Info (Up Arrow).')}
                icon={<HelpCircle size={18} />}
              >
                Needs Info (Up)
              </PillButton>

              <PillButton
                variant="primary"
                onClick={handleAgree}
                style={{ background: 'var(--sev-low)' }}
                icon={<Check size={18} />}
              >
                Approve (Right Arrow)
              </PillButton>
            </div>
          </div>

          {/* Active Alerts */}
          <div style={{ marginBottom: 32 }}>
            <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <ShieldAlert size={20} color="var(--sev-critical)" />
              <span>Grounded Clinical Alerts ({activeCase.alerts.length})</span>
            </h3>

            {activeCase.alerts.map((a, i) => (
              <div
                key={i}
                style={{
                  background: 'var(--surface)',
                  borderRadius: 16,
                  padding: 24,
                  border: '1px solid var(--hairline)',
                  boxShadow: 'var(--shadow-card)',
                  marginBottom: 16,
                }}
              >
                <div style={{ fontSize: 17, fontWeight: 700, marginBottom: 8 }}>{a.title}</div>
                <p style={{ fontSize: 15, color: 'var(--text-secondary)', marginBottom: 12 }}>
                  {a.rationale}
                </p>
                <div style={{ fontSize: 15, padding: '12px 16px', background: 'var(--bg-alt)', borderRadius: 12, marginBottom: 12 }}>
                  <strong>Doctor Discussion Guide Suggestion:</strong> {a.doctorQuestion}
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                  <strong>Rule ID:</strong> {a.ruleId} • <strong>Sources:</strong> {a.sources}
                </div>
              </div>
            ))}
          </div>

          {/* Specialist Deliberation Panel Summary */}
          <div style={{ marginBottom: 32 }}>
            <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <FileText size={20} color="var(--accent)" />
              <span>Specialty Deliberation Panel</span>
            </h3>
            <div
              style={{
                background: 'var(--surface)',
                borderRadius: 16,
                padding: 20,
                border: '1px solid var(--hairline)',
                fontSize: 15,
                lineHeight: 1.6,
                color: 'var(--text-secondary)',
              }}
            >
              {activeCase.specialistPanelSummary}
            </div>
          </div>

          {/* Patient Message Editor */}
          <div style={{ marginBottom: 32 }}>
            <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12 }}>
              Draft Patient Message (Clinician Edits Permitted)
            </h3>
            <textarea
              defaultValue={activeCase.draftPatientMessage}
              onChange={(e) => setPatientMessageEdit(e.target.value)}
              style={{
                width: '100%',
                minHeight: 100,
                padding: 16,
                borderRadius: 12,
                border: '1px solid var(--hairline)',
                background: 'var(--surface)',
                color: 'var(--text)',
                fontSize: 15,
                fontFamily: 'inherit',
                lineHeight: 1.5,
              }}
            />
          </div>
        </div>
      ) : (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <p style={{ color: 'var(--text-secondary)' }}>Select a case from the queue</p>
        </div>
      )}

      {/* Undo Toast (10s window) */}
      {undoToast && undoToast.visible && (
        <div
          style={{
            position: 'fixed',
            bottom: 32,
            right: 32,
            background: 'var(--text)',
            color: 'var(--bg)',
            padding: '14px 24px',
            borderRadius: 'var(--radius-pill)',
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            boxShadow: 'var(--shadow-float)',
            zIndex: 1000,
          }}
        >
          <span>Decision recorded ({undoToast.secondsLeft}s to undo)</span>
          <button
            onClick={handleUndo}
            style={{
              color: 'var(--accent)',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}
          >
            <RotateCcw size={16} />
            <span>Undo</span>
          </button>
        </div>
      )}

      {/* Rejection Reason Modal */}
      {isRejectModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1100,
          }}
        >
          <div
            style={{
              background: 'var(--surface)',
              borderRadius: 'var(--radius-card)',
              padding: 32,
              width: 480,
              maxWidth: '90%',
            }}
          >
            <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>
              Select Reason for Rejection
            </h3>
            <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 20 }}>
              Feedback feeds directly into the governed rule-improvement queue.
            </p>

            <select
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              style={{
                width: '100%',
                padding: '12px 14px',
                borderRadius: 8,
                border: '1px solid var(--hairline)',
                background: 'var(--surface)',
                color: 'var(--text)',
                fontSize: 15,
                marginBottom: 16,
              }}
            >
              <option value="false_positive">False positive (Alert not clinically applicable)</option>
              <option value="clinically_acceptable">Clinically acceptable risk in this scenario</option>
              <option value="missing_context">Missing clinical context / indication</option>
              <option value="wrong_severity">Wrong severity level</option>
              <option value="unclear_wording">Unclear patient-facing wording</option>
              <option value="other">Other reason</option>
            </select>

            <textarea
              placeholder="Optional clinical note for rule auditor..."
              value={rejectNote}
              onChange={(e) => setRejectNote(e.target.value)}
              style={{
                width: '100%',
                minHeight: 80,
                padding: 12,
                borderRadius: 8,
                border: '1px solid var(--hairline)',
                background: 'var(--surface)',
                color: 'var(--text)',
                fontSize: 14,
                marginBottom: 24,
              }}
            />

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
              <PillButton variant="secondary" onClick={() => setIsRejectModalOpen(false)}>
                Cancel
              </PillButton>
              <PillButton variant="primary" onClick={handleConfirmReject}>
                Submit Rejection
              </PillButton>
            </div>
          </div>
        </div>
      )}

      {/* Audited Reveal Modal */}
      {isRevealModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1100,
          }}
        >
          <div
            style={{
              background: 'var(--surface)',
              borderRadius: 'var(--radius-card)',
              padding: 32,
              width: 480,
              maxWidth: '90%',
            }}
          >
            <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>
              Audited Identity Reveal
            </h3>
            <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 20 }}>
              Under DPDP/HIPAA principles, unmasking patient identity requires an explicit clinical reason that is permanently recorded in the immutable audit log.
            </p>

            <input
              type="text"
              placeholder="e.g. Acute Emergency Consultation with Attending Physician"
              value={revealReason}
              onChange={(e) => setRevealReason(e.target.value)}
              style={{
                width: '100%',
                padding: '12px 14px',
                borderRadius: 8,
                border: '1px solid var(--hairline)',
                background: 'var(--surface)',
                color: 'var(--text)',
                fontSize: 15,
                marginBottom: 24,
              }}
            />

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
              <PillButton variant="secondary" onClick={() => setIsRevealModalOpen(false)}>
                Cancel
              </PillButton>
              <PillButton variant="primary" onClick={handleAuditedReveal}>
                Log & Reveal Identity
              </PillButton>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
