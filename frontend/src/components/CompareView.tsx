"use client";

import { motion } from "framer-motion";
import { X, Shield, ShieldAlert, ShieldX, BookOpen, type LucideIcon } from "lucide-react";
import type { DrugCandidate, SafetyAssessment, EvidenceSummary } from "@/lib/diseaseTypes";

const VERDICT_CFG: Record<string, { label: string; cls: string; icon: LucideIcon }> = {
  PASS: { label: "Safe", cls: "text-green", icon: Shield },
  WARNING: { label: "Caution", cls: "text-amber", icon: ShieldAlert },
  HARD_FAIL: { label: "Unsafe", cls: "text-red", icon: ShieldX },
};

interface CompareViewProps {
  drugs: [DrugCandidate, DrugCandidate];
  safetyMap: Record<string, SafetyAssessment>;
  evidenceMap: Record<string, EvidenceSummary>;
  onClose: () => void;
}

function Row({ label, left, right }: { label: string; left: React.ReactNode; right: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[140px_1fr_1fr] gap-4 border-b border-border py-3 last:border-0">
      <span className="text-[10px] font-semibold uppercase tracking-wider text-muted">{label}</span>
      <div className="text-sm text-foreground">{left}</div>
      <div className="text-sm text-foreground">{right}</div>
    </div>
  );
}

export default function CompareView({ drugs, safetyMap, evidenceMap, onClose }: CompareViewProps) {
  const [a, b] = drugs;
  const saA = safetyMap[a.drug_name];
  const saB = safetyMap[b.drug_name];
  const evA = evidenceMap[a.drug_name];
  const evB = evidenceMap[b.drug_name];
  const scoreA = a.evidence_score;
  const scoreB = b.evidence_score;

  const vA = saA ? VERDICT_CFG[saA.verdict] : null;
  const vB = saB ? VERDICT_CFG[saB.verdict] : null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 p-6 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ y: 30, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 30, opacity: 0 }}
        className="relative my-8 w-full max-w-3xl rounded-2xl border border-border bg-card p-8 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1 text-muted hover:bg-subtle hover:text-foreground"
        >
          <X size={18} />
        </button>

        <h2 className="text-lg font-bold text-foreground">Side-by-Side Comparison</h2>
        <p className="mt-1 text-xs text-muted">Compare two drug candidates across all dimensions.</p>

        <div className="mt-6">
          <div className="grid grid-cols-[140px_1fr_1fr] gap-4 pb-3">
            <span />
            <h3 className="text-base font-bold text-purple">{a.drug_name}</h3>
            <h3 className="text-base font-bold text-purple">{b.drug_name}</h3>
          </div>

          <Row
            label="Evidence Score"
            left={<span className="font-mono font-bold">{scoreA?.total ?? "—"}/100</span>}
            right={<span className="font-mono font-bold">{scoreB?.total ?? "—"}/100</span>}
          />
          <Row
            label="Target"
            left={<span className="font-mono text-xs">{scoreA?.target_association ?? "—"}/30</span>}
            right={<span className="font-mono text-xs">{scoreB?.target_association ?? "—"}/30</span>}
          />
          <Row
            label="Trial"
            left={<span className="font-mono text-xs">{scoreA?.trial_evidence ?? "—"}/25</span>}
            right={<span className="font-mono text-xs">{scoreB?.trial_evidence ?? "—"}/25</span>}
          />
          <Row
            label="Literature"
            left={<span className="font-mono text-xs">{scoreA?.literature_support ?? "—"}/25</span>}
            right={<span className="font-mono text-xs">{scoreB?.literature_support ?? "—"}/25</span>}
          />
          <Row
            label="Safety Score"
            left={<span className="font-mono text-xs">{scoreA?.safety_profile ?? "—"}/20</span>}
            right={<span className="font-mono text-xs">{scoreB?.safety_profile ?? "—"}/20</span>}
          />
          <Row
            label="Safety Verdict"
            left={vA ? <span className={`font-semibold ${vA.cls}`}>{vA.label}</span> : <span className="text-muted">—</span>}
            right={vB ? <span className={`font-semibold ${vB.cls}`}>{vB.label}</span> : <span className="text-muted">—</span>}
          />
          <Row
            label="Phase"
            left={a.phase}
            right={b.phase}
          />
          <Row
            label="Indication"
            left={<span className="text-xs">{a.original_indication}</span>}
            right={<span className="text-xs">{b.original_indication}</span>}
          />
          <Row
            label="Papers"
            left={
              <span className="flex items-center gap-1 text-xs">
                <BookOpen size={10} /> {evA?.paper_count ?? 0}
              </span>
            }
            right={
              <span className="flex items-center gap-1 text-xs">
                <BookOpen size={10} /> {evB?.paper_count ?? 0}
              </span>
            }
          />
          <Row
            label="Mechanism"
            left={<span className="text-xs leading-relaxed">{a.mechanism}</span>}
            right={<span className="text-xs leading-relaxed">{b.mechanism}</span>}
          />
          <Row
            label="Rationale"
            left={<span className="text-xs leading-relaxed">{a.repurposing_rationale}</span>}
            right={<span className="text-xs leading-relaxed">{b.repurposing_rationale}</span>}
          />
          <Row
            label="Adverse Events"
            left={
              <div className="flex flex-wrap gap-1">
                {saA?.adverse_events.slice(0, 5).map((ae) => (
                  <span key={ae} className="rounded bg-subtle px-1 py-0.5 text-[9px] text-muted">{ae}</span>
                )) ?? <span className="text-muted">—</span>}
              </div>
            }
            right={
              <div className="flex flex-wrap gap-1">
                {saB?.adverse_events.slice(0, 5).map((ae) => (
                  <span key={ae} className="rounded bg-subtle px-1 py-0.5 text-[9px] text-muted">{ae}</span>
                )) ?? <span className="text-muted">—</span>}
              </div>
            }
          />
        </div>
      </motion.div>
    </motion.div>
  );
}
