"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Loader2, BookOpen, ExternalLink, AlertTriangle, FlaskConical } from "lucide-react";
import { API_BASE } from "@/lib/config";

interface PaperDetail {
  pmid: string;
  title: string;
  authors: string;
  journal: string;
  year: number;
  url: string;
}

interface TrialEntry {
  trial_id: string;
  title: string;
  status: string;
  phase: string;
  conditions: string[];
}

interface DrugDetailData {
  drug_name: string;
  disease: string;
  literature: {
    total_papers: number;
    papers: PaperDetail[];
    abstracts: Record<string, string>;
  };
  adverse_events: { term: string; count: number }[];
  all_trials: TrialEntry[];
}

interface DrugDetailPanelProps {
  drugName: string;
  diseaseName: string;
  onClose: () => void;
}

const STATUS_COLORS: Record<string, string> = {
  COMPLETED: "bg-green/10 text-green",
  RECRUITING: "bg-blue/10 text-blue",
  ACTIVE_NOT_RECRUITING: "bg-blue/10 text-blue",
  TERMINATED: "bg-red/10 text-red",
  WITHDRAWN: "bg-red/10 text-red",
  SUSPENDED: "bg-amber/10 text-amber",
  NOT_YET_RECRUITING: "bg-muted/10 text-muted",
};

export default function DrugDetailPanel({ drugName, diseaseName, onClose }: DrugDetailPanelProps) {
  const [data, setData] = useState<DrugDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"literature" | "trials" | "safety">("literature");

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/api/drug-detail/${encodeURIComponent(drugName)}?disease=${encodeURIComponent(diseaseName)}`)
      .then((r) => r.json())
      .then((d) => {
        if (cancelled) return;
        // Normalize shape so optional fields never crash the UI
        const normalized: DrugDetailData = {
          drug_name: d.drug_name ?? drugName,
          disease: d.disease ?? diseaseName,
          literature: {
            total_papers: d.literature?.total_papers ?? 0,
            papers: d.literature?.papers ?? [],
            abstracts: d.literature?.abstracts ?? {},
          },
          adverse_events: d.adverse_events ?? [],
          all_trials: d.all_trials ?? [],
        };
        setData(normalized);
        setLoading(false);
      })
      .catch(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [drugName, diseaseName]);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-black/30 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ x: "100%" }}
          animate={{ x: 0 }}
          exit={{ x: "100%" }}
          transition={{ type: "spring", damping: 30, stiffness: 300 }}
          className="absolute right-0 top-0 h-full w-full max-w-2xl overflow-y-auto border-l border-border bg-background shadow-2xl"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-background/80 px-6 py-4 backdrop-blur-xl">
            <div>
              <h2 className="text-lg font-bold text-foreground">{drugName}</h2>
              <p className="text-xs text-muted">Deep dive · {diseaseName}</p>
            </div>
            <button onClick={onClose} className="rounded-lg p-1.5 text-muted hover:bg-subtle hover:text-foreground">
              <X size={18} />
            </button>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-24">
              <Loader2 size={24} className="animate-spin text-purple" />
              <span className="ml-3 text-sm text-muted">Loading expanded data...</span>
            </div>
          ) : data ? (
            <div className="p-6">
              {/* Tabs */}
              <div className="flex gap-1 rounded-xl bg-subtle p-1">
                {([
                  { key: "literature" as const, label: "Literature", icon: BookOpen, count: data.literature.total_papers },
                  { key: "trials" as const, label: "All Trials", icon: FlaskConical, count: data.all_trials.length },
                  { key: "safety" as const, label: "Adverse Events", icon: AlertTriangle, count: data.adverse_events.length },
                ]).map((t) => (
                  <button
                    key={t.key}
                    onClick={() => setTab(t.key)}
                    className={`flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition-all ${
                      tab === t.key ? "bg-white text-foreground shadow-sm" : "text-muted hover:text-foreground"
                    }`}
                  >
                    <t.icon size={12} />
                    {t.label}
                    <span className="rounded-full bg-purple/10 px-1.5 py-0.5 text-[9px] font-bold text-purple">
                      {t.count}
                    </span>
                  </button>
                ))}
              </div>

              {/* Literature Tab */}
              {tab === "literature" && (
                <div className="mt-6 space-y-4">
                  {data.literature.papers.length === 0 && (
                    <p className="py-8 text-center text-sm text-muted">No papers found in PubMed.</p>
                  )}
                  {data.literature.papers.map((p) => (
                    <div key={p.pmid} className="rounded-xl border border-border p-4">
                      <a
                        href={p.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm font-medium leading-snug text-foreground hover:text-purple"
                      >
                        {p.title}
                        <ExternalLink size={10} className="ml-1 inline text-muted" />
                      </a>
                      <p className="mt-1 text-[10px] text-muted">
                        {p.authors} · {p.journal} · {p.year}
                      </p>
                      {data.literature.abstracts[p.pmid] && (
                        <p className="mt-2 text-xs leading-relaxed text-muted">
                          {data.literature.abstracts[p.pmid].slice(0, 500)}
                          {data.literature.abstracts[p.pmid].length > 500 ? "..." : ""}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Trials Tab */}
              {tab === "trials" && (
                <div className="mt-6 space-y-3">
                  {data.all_trials.length === 0 && (
                    <p className="py-8 text-center text-sm text-muted">No clinical trials found.</p>
                  )}
                  {data.all_trials.map((t) => (
                    <div key={t.trial_id} className="rounded-xl border border-border p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1">
                          <a
                            href={`https://clinicaltrials.gov/study/${t.trial_id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm font-medium text-foreground hover:text-purple"
                          >
                            {t.trial_id}
                            <ExternalLink size={10} className="ml-1 inline text-muted" />
                          </a>
                          <p className="mt-1 text-xs leading-relaxed text-muted">{t.title}</p>
                          {t.conditions.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              {t.conditions.slice(0, 3).map((c) => (
                                <span key={c} className="rounded bg-subtle px-1.5 py-0.5 text-[9px] text-muted">{c}</span>
                              ))}
                            </div>
                          )}
                        </div>
                        <div className="flex shrink-0 flex-col items-end gap-1">
                          <span className={`rounded-full px-2 py-0.5 text-[9px] font-bold ${STATUS_COLORS[t.status] || "bg-subtle text-muted"}`}>
                            {t.status.replace(/_/g, " ")}
                          </span>
                          <span className="text-[10px] text-muted">{t.phase}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Safety Tab */}
              {tab === "safety" && (
                <div className="mt-6">
                  {data.adverse_events.length === 0 && (
                    <p className="py-8 text-center text-sm text-muted">No adverse events in FDA FAERS.</p>
                  )}
                  <div className="space-y-2">
                    {data.adverse_events.map((ae) => (
                      <div key={ae.term} className="flex items-center justify-between rounded-lg border border-border px-4 py-2.5">
                        <span className="text-sm text-foreground">{ae.term}</span>
                        <span className="font-mono text-xs text-muted">{ae.count.toLocaleString()} reports</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center py-24">
              <p className="text-sm text-muted">Failed to load data.</p>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
