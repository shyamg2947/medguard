import React, { useState } from 'react';
import { CardTile } from '../../components/CardTile';
import { BentoGrid } from '../../components/BentoGrid';
import { InsetGroupedList, InsetRow } from '../../components/InsetGroupedList';
import { PillButton } from '../../components/PillButton';
import { Cpu, GitPullRequest, Database, Check, X, ShieldCheck, Activity } from 'lucide-react';

interface RuleProposal {
  id: string;
  ruleId: string;
  rejectionCount: number;
  totalReviews: number;
  primaryReason: string;
  proposedChange: string;
  status: 'open' | 'accepted' | 'rejected';
}

const mockProposals: RuleProposal[] = [
  {
    id: 'prop-1',
    ruleId: 'DUR-PPI-8WEEKS',
    rejectionCount: 5,
    totalReviews: 6,
    primaryReason: 'clinically_acceptable',
    proposedChange: 'Exempt patients with documented Barrett esophagus or active Zollinger-Ellison syndrome from duration cap.',
    status: 'open',
  },
  {
    id: 'prop-2',
    ruleId: 'HERB-ASHWAGANDHA-INTERACTION',
    rejectionCount: 4,
    totalReviews: 5,
    primaryReason: 'unclear_wording',
    proposedChange: 'Clarify that Ashwagandha has theoretical, not proven bleeding potentiation, and tone down patient alert text.',
    status: 'open',
  },
];

export const AdminApp: React.FC = () => {
  const [proposals, setProposals] = useState<RuleProposal[]>(mockProposals);

  const usageStats = {
    dailyCalls: 18,
    dailyBudget: 1500,
    sessionCalls: 4,
    sessionBudget: 20,
    cachedQueries: 52,
    circuitBreaker: 'CLOSED (Normal operation)',
    freeTierMode: 'ACTIVE (Deterministic rules-first)',
  };

  const handleDecide = (id: string, action: 'accepted' | 'rejected') => {
    setProposals((prev) =>
      prev.map((p) => (p.id === id ? { ...p, status: action } : p))
    );
  };

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '32px 24px 80px' }}>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>
          Governance & Administration
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Review clinician feedback proposals and monitor system resource health.
        </p>
      </div>

      {/* LLM Usage & Circuit Breaker Telemetry */}
      <div style={{ marginBottom: 40 }}>
        <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Cpu size={20} color="var(--accent)" />
          <span>LLM Gateway Telemetry & Free-Tier Budget</span>
        </h2>

        <BentoGrid>
          <CardTile colSpan={4}>
            <div style={{ fontSize: 13, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: 8 }}>
              Daily Call Budget
            </div>
            <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--text)' }}>
              {usageStats.dailyCalls} / {usageStats.dailyBudget}
            </div>
            <div style={{ fontSize: 13, color: 'var(--sev-low)', marginTop: 4 }}>
              1.2% consumed • 1,482 calls remaining
            </div>
          </CardTile>

          <CardTile colSpan={4}>
            <div style={{ fontSize: 13, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: 8 }}>
              Session Token Bucket
            </div>
            <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--text)' }}>
              {usageStats.sessionCalls} / {usageStats.sessionBudget}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
              Rate limiter: 15 RPM • Max 20 calls/session
            </div>
          </CardTile>

          <CardTile colSpan={4}>
            <div style={{ fontSize: 13, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: 8 }}>
              Cache & Circuit Breaker
            </div>
            <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--accent)' }}>
              {usageStats.cachedQueries} hits
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
              {usageStats.circuitBreaker}
            </div>
          </CardTile>
        </BentoGrid>
      </div>

      {/* Governed Rule-Change Proposals Queue */}
      <div style={{ marginBottom: 40 }}>
        <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <GitPullRequest size={20} color="var(--accent)" />
          <span>Governed Rule-Change Queue (Feedback Loop)</span>
        </h2>
        <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 20 }}>
          Triggered automatically when a clinical rule receives &gt;= 60% rejections across 5+ reviews.
          Changes require human clinician sign-off; nothing updates autonomously.
        </p>

        {proposals.map((p) => (
          <div
            key={p.id}
            style={{
              background: 'var(--surface)',
              borderRadius: 16,
              padding: 24,
              border: '1px solid var(--hairline)',
              boxShadow: 'var(--shadow-card)',
              marginBottom: 20,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
              <div>
                <span
                  style={{
                    fontSize: 12,
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    padding: '4px 8px',
                    borderRadius: 6,
                    background: 'var(--bg-alt)',
                    color: 'var(--accent)',
                    marginRight: 8,
                  }}
                >
                  {p.ruleId}
                </span>
                <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
                  Rejections: {p.rejectionCount} / {p.totalReviews} ({Math.round((p.rejectionCount / p.totalReviews) * 100)}%)
                </span>
              </div>

              <span
                style={{
                  fontSize: 12,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-pill)',
                  background:
                    p.status === 'accepted'
                      ? 'rgba(29, 125, 63, 0.12)'
                      : p.status === 'rejected'
                      ? 'rgba(215, 0, 21, 0.12)'
                      : 'rgba(0, 113, 227, 0.12)',
                  color:
                    p.status === 'accepted'
                      ? 'var(--sev-low)'
                      : p.status === 'rejected'
                      ? 'var(--sev-critical)'
                      : 'var(--accent)',
                }}
              >
                {p.status}
              </span>
            </div>

            <div style={{ fontSize: 14, marginBottom: 8 }}>
              <strong>Primary Clinician Reason:</strong> {p.primaryReason}
            </div>

            <div
              style={{
                fontSize: 15,
                background: 'var(--bg-alt)',
                padding: '12px 16px',
                borderRadius: 12,
                marginBottom: 16,
              }}
            >
              <strong>Proposed Rule Adjustment:</strong> {p.proposedChange}
            </div>

            {p.status === 'open' && (
              <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
                <PillButton
                  variant="secondary"
                  onClick={() => handleDecide(p.id, 'rejected')}
                  icon={<X size={16} />}
                >
                  Reject Proposal
                </PillButton>
                <PillButton
                  variant="primary"
                  onClick={() => handleDecide(p.id, 'accepted')}
                  icon={<Check size={16} />}
                >
                  Accept & Create Rule Version
                </PillButton>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Rules Engine Status */}
      <InsetGroupedList title="Verified Rule Sets">
        <InsetRow
          icon={<ShieldCheck size={18} />}
          label="AGS Beers Criteria® (2023 Update)"
          value="14 Active Rules • Hash: 9f8a...c32"
        />
        <InsetRow
          icon={<ShieldCheck size={18} />}
          label="STOPP/START Criteria Version 3"
          value="12 Active Rules • Hash: 4e1b...d90"
        />
        <InsetRow
          icon={<Activity size={18} />}
          label="Anticholinergic Cognitive Burden (ACB) Engine"
          value="Scoring Active • Cutoff >= 3"
        />
        <InsetRow
          icon={<Database size={18} />}
          label="AYUSH & Herbal Interaction Matrix"
          value="7 Formulations • Hash: a83d...11f"
        />
      </InsetGroupedList>
    </div>
  );
};

