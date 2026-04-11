"use client";

import { useState, useMemo, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Loader2,
  Dna,
  FlaskConical,
  ShieldCheck,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Shield,
  ShieldAlert,
  ShieldX,
  CheckCircle2,
  Circle,
  Zap,
  BookOpen,
  Download,
  Database,
  Star,
  StickyNote,
  GitCompareArrows,
  FileText,
  Clock,
  Trash2,
  PanelRightOpen,
  X,
  type LucideIcon,
} from "lucide-react";
import dynamic from "next/dynamic";
import { API_BASE } from "@/lib/config";
import { useEventStream } from "@/hooks/useEventStream";
import type {
  DrugCandidate,
  SafetyAssessment,
  EvidenceSummary,
  SSEEvent,
} from "@/lib/diseaseTypes";
import {
  getSessions,
  saveSession,
  deleteSession,
  createSessionFromResults,
  getSearchHistory,
  addToSearchHistory,
  type ResearchSession,
} from "@/lib/sessions";

const MoleculeViewer = dynamic(() => import("./MoleculeViewer"), { ssr: false });
const HeroScene = dynamic(() => import("./HeroScene"), { ssr: false });
const CompareView = dynamic(() => import("./CompareView"), { ssr: false });
const DrugDetailPanel = dynamic(() => import("./DrugDetailPanel"), { ssr: false });
const GrantAbstractModal = dynamic(() => import("./GrantAbstractModal"), { ssr: false });
const RelatedDiseases = dynamic(() => import("./RelatedDiseases"), { ssr: false });
const MoleculeEditor = dynamic(() => import("./MoleculeEditor"), { ssr: false });

const SUGGESTIONS = [
  "Friedreich's Ataxia",
  "Huntington Disease",
  "Amyotrophic Lateral Sclerosis",
  "Cystic Fibrosis",
  "Duchenne Muscular Dystrophy",
];

const VERDICT: Record<string, { label: string; cls: string; icon: LucideIcon }> = {
  PASS: { label: "Safe", cls: "text-green", icon: Shield },
  WARNING: { label: "Caution", cls: "text-amber", icon: ShieldAlert },
  HARD_FAIL: { label: "Unsafe", cls: "text-red", icon: ShieldX },
};

const AGENT_STYLE: Record<string, { icon: LucideIcon; color: string; label: string }> = {
  disease_analyst: { icon: Dna, color: "text-blue", label: "Biology" },
  drug_hunter: { icon: FlaskConical, color: "text-purple", label: "Drug Search" },
  safety_checker: { icon: ShieldCheck, color: "text-green", label: "Safety" },
  evidence_agent: { icon: BookOpen, color: "text-blue", label: "Literature" },
  contradiction: { icon: AlertTriangle, color: "text-amber", label: "Verify" },
  system: { icon: CheckCircle2, color: "text-foreground", label: "Done" },
};

interface Suggestion {
  id: string;
  name: string;
  description: string;
}

export default function Dashboard() {
  const stream = useEventStream();
  const [query, setQuery] = useState("");
  const [searched, setSearched] = useState(false);

  // Session state
  const [activeSession, setActiveSession] = useState<ResearchSession | null>(null);
  const [sessions, setSessions] = useState<ResearchSession[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Notes & stars
  const [starred, setStarred] = useState<string[]>([]);
  const [notes, setNotes] = useState<Record<string, string>>({});

  // Compare
  const [compareSet, setCompareSet] = useState<Set<string>>(new Set());
  const [showCompare, setShowCompare] = useState(false);

  // Deep dive
  const [deepDiveDrug, setDeepDiveDrug] = useState<string | null>(null);

  // Grant abstract
  const [grantDrug, setGrantDrug] = useState<string | null>(null);
  const [editDrug, setEditDrug] = useState<string | null>(null);

  // Autocomplete
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // PDF loading
  const [pdfLoading, setPdfLoading] = useState(false);

  useEffect(() => {
    setSessions(getSessions());
    setSearchHistory(getSearchHistory());
  }, []);

  const safetyMap = useMemo(() => {
    const m: Record<string, SafetyAssessment> = {};
    for (const sa of stream.safetyAssessments) m[sa.drug_name] = sa;
    return m;
  }, [stream.safetyAssessments]);

  const evidenceMap = useMemo(() => {
    const m: Record<string, EvidenceSummary> = {};
    for (const es of stream.evidenceSummaries) m[es.drug_name] = es;
    return m;
  }, [stream.evidenceSummaries]);

  // Auto-save session when pipeline completes
  useEffect(() => {
    if (!stream.isStreaming && stream.result) {
      const session = activeSession
        ? { ...activeSession, results: stream.result, updated_at: new Date().toISOString() }
        : createSessionFromResults(stream.result);
      session.notes = notes;
      session.starred = starred;
      saveSession(session);
      setActiveSession(session);
      setSessions(getSessions());
      addToSearchHistory(stream.result.disease_name);
      setSearchHistory(getSearchHistory());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stream.isStreaming, stream.result]);

  const handleSearch = (q: string) => {
    setQuery(q);
    setSearched(true);
    setActiveSession(null);
    setStarred([]);
    setNotes({});
    setCompareSet(new Set());
    setShowSuggestions(false);
    stream.evaluate(q);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !stream.isStreaming) handleSearch(query.trim());
  };

  const handleLoadSession = (session: ResearchSession) => {
    setActiveSession(session);
    setQuery(session.disease_name);
    setSearched(true);
    setStarred(session.starred || []);
    setNotes(session.notes || {});
    setCompareSet(new Set());
    setSidebarOpen(false);
  };

  const handleDeleteSession = (id: string) => {
    deleteSession(id);
    setSessions(getSessions());
    if (activeSession?.id === id) setActiveSession(null);
  };

  const handleToggleStar = (drugName: string) => {
    const newStarred = starred.includes(drugName)
      ? starred.filter((s) => s !== drugName)
      : [...starred, drugName];
    setStarred(newStarred);
    if (activeSession) {
      activeSession.starred = newStarred;
      saveSession(activeSession);
    }
  };

  const handleNoteChange = (drugName: string, note: string) => {
    const newNotes = { ...notes, [drugName]: note };
    if (!note.trim()) delete newNotes[drugName];
    setNotes(newNotes);
    if (activeSession) {
      activeSession.notes = newNotes;
      saveSession(activeSession);
    }
  };

  const handleToggleCompare = (drugName: string) => {
    const next = new Set(compareSet);
    if (next.has(drugName)) next.delete(drugName);
    else if (next.size < 2) next.add(drugName);
    setCompareSet(next);
  };

  const handleDownloadPDF = async () => {
    const results = activeSession?.results ?? stream.result;
    if (!results) return;
    setPdfLoading(true);
    try {
      const { generatePDF } = await import("./PDFReport");
      const blob = await generatePDF(results, notes, starred);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `PharmaSynapse_${results.disease_name.replace(/\s+/g, "_")}_${new Date().toISOString().slice(0, 10)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("PDF generation failed:", err);
    } finally {
      setPdfLoading(false);
    }
  };

  // Autocomplete
  const handleQueryChange = (val: string) => {
    setQuery(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (val.length < 2) {
      setSuggestions([]);
      setShowSuggestions(val.length > 0 && searchHistory.length > 0);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const resp = await fetch(`${API_BASE}/api/suggest/${encodeURIComponent(val)}`);
        if (resp.ok) {
          const data = await resp.json();
          setSuggestions(data.suggestions || []);
          setShowSuggestions(true);
        }
      } catch { /* ignore */ }
    }, 300);
  };

  const blocking = stream.contradictions.filter((c) => c.severity === "BLOCKING");

  // Determine which data to render (live stream or loaded session)
  const displayResult = activeSession?.results ?? null;
  const displayCandidates = !stream.isStreaming && displayResult && !stream.result
    ? displayResult.candidates
    : stream.candidates;
  const displaySafetyMap = !stream.isStreaming && displayResult && !stream.result
    ? Object.fromEntries(displayResult.safety_assessments.map((s) => [s.drug_name, s]))
    : safetyMap;
  const displayEvidenceMap = !stream.isStreaming && displayResult && !stream.result
    ? Object.fromEntries(displayResult.evidence_summaries.map((e) => [e.drug_name, e]))
    : evidenceMap;
  const displaySummary = !stream.isStreaming && displayResult && !stream.result
    ? displayResult.disease_summary
    : stream.diseaseSummary;
  const displayTargets = !stream.isStreaming && displayResult && !stream.result
    ? displayResult.targets
    : stream.targets;
  const displayDataSources = !stream.isStreaming && displayResult && !stream.result
    ? displayResult.data_sources
    : stream.dataSources;
  const displayContradictions = !stream.isStreaming && displayResult && !stream.result
    ? displayResult.contradictions
    : stream.contradictions;

  // Sort: starred first, then by score
  const sortedCandidates = useMemo(() => {
    return [...displayCandidates].sort((a, b) => {
      const aStar = starred.includes(a.drug_name) ? 1 : 0;
      const bStar = starred.includes(b.drug_name) ? 1 : 0;
      if (aStar !== bStar) return bStar - aStar;
      return (b.evidence_score?.total ?? 0) - (a.evidence_score?.total ?? 0);
    });
  }, [displayCandidates, starred]);

  const compareDrugs = useMemo(() => {
    const arr = Array.from(compareSet);
    if (arr.length !== 2) return null;
    const a = displayCandidates.find((c) => c.drug_name === arr[0]);
    const b = displayCandidates.find((c) => c.drug_name === arr[1]);
    return a && b ? [a, b] as [DrugCandidate, DrugCandidate] : null;
  }, [compareSet, displayCandidates]);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-background/60 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-2">
            <Zap size={18} className="text-purple" />
            <span className="text-sm font-bold tracking-tight">PharmaSynapse</span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen((o) => !o)}
              className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-[10px] font-medium text-muted transition-all hover:border-purple/30 hover:text-foreground"
            >
              <Clock size={12} />
              My Research
              {sessions.length > 0 && (
                <span className="rounded-full bg-purple/10 px-1.5 text-[9px] font-bold text-purple">
                  {sessions.length}
                </span>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Session Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-black/20"
              onClick={() => setSidebarOpen(false)}
            />
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 30, stiffness: 300 }}
              className="fixed right-0 top-0 z-50 h-full w-80 border-l border-border bg-background shadow-2xl"
            >
              <div className="flex items-center justify-between border-b border-border px-5 py-4">
                <h3 className="text-sm font-bold text-foreground">My Research</h3>
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="rounded-lg p-1 text-muted hover:bg-subtle hover:text-foreground"
                >
                  <X size={16} />
                </button>
              </div>
              <div className="overflow-y-auto p-4" style={{ maxHeight: "calc(100vh - 60px)" }}>
                {sessions.length === 0 ? (
                  <p className="py-12 text-center text-xs text-muted">
                    No saved sessions yet. Run a search to get started.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {sessions.map((s) => (
                      <div
                        key={s.id}
                        className={`group rounded-xl border p-3 transition-all cursor-pointer ${
                          activeSession?.id === s.id
                            ? "border-purple/30 bg-purple/[0.03]"
                            : "border-border hover:border-purple/20"
                        }`}
                        onClick={() => handleLoadSession(s)}
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="text-sm font-semibold text-foreground">{s.disease_name}</p>
                            <p className="mt-0.5 text-[10px] text-muted">
                              {s.results.candidates.length} candidates
                              {s.starred.length > 0 && ` · ${s.starred.length} starred`}
                            </p>
                            <p className="mt-0.5 text-[9px] text-muted/50">
                              {new Date(s.updated_at).toLocaleDateString()}
                            </p>
                          </div>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleDeleteSession(s.id); }}
                            className="rounded p-1 text-muted/30 opacity-0 transition-opacity hover:text-red group-hover:opacity-100"
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <div className="mx-auto max-w-6xl px-6">
        {!searched && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="pt-10 text-center"
          >
            <h1 className="text-5xl font-bold tracking-tight text-foreground">
              Find new life for<br />abandoned drugs
            </h1>
            <p className="mx-auto mt-4 max-w-md text-sm leading-relaxed text-muted">
              Search a rare disease. We check real medical databases for drugs that
              passed human trials but got shelved — and might work for something new.
            </p>
          </motion.div>
        )}

        {!searched && (
          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="-mx-6 mt-4 h-[70vh]"
          >
            <HeroScene className="h-full w-full" />
          </motion.div>
        )}

        <div className={searched ? "pt-6" : "-mt-4"}>
          <form onSubmit={handleSubmit} className="relative mx-auto max-w-xl">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-muted" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => handleQueryChange(e.target.value)}
                  onFocus={() => {
                    if (query.length >= 2 && suggestions.length > 0) setShowSuggestions(true);
                    else if (query.length < 2 && searchHistory.length > 0) setShowSuggestions(true);
                  }}
                  onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                  placeholder="Type a disease name..."
                  disabled={stream.isStreaming}
                  className="w-full rounded-xl border border-border bg-white py-3 pl-11 pr-4 text-sm shadow-sm transition-shadow placeholder:text-muted/40 focus:border-purple/40 focus:shadow-[0_0_0_3px_rgba(124,58,237,0.08)] focus:outline-none disabled:opacity-50"
                />
                {/* Autocomplete dropdown */}
                <AnimatePresence>
                  {showSuggestions && (
                    <motion.div
                      initial={{ opacity: 0, y: -4 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -4 }}
                      className="absolute left-0 right-0 top-full z-50 mt-1 overflow-hidden rounded-xl border border-border bg-white shadow-lg"
                    >
                      {query.length < 2 && searchHistory.length > 0 && (
                        <div className="p-2">
                          <p className="mb-1 px-2 text-[9px] font-semibold uppercase tracking-wider text-muted/50">Recent</p>
                          {searchHistory.slice(0, 5).map((h) => (
                            <button
                              key={h}
                              type="button"
                              onMouseDown={(e) => e.preventDefault()}
                              onClick={() => handleSearch(h)}
                              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-foreground hover:bg-subtle"
                            >
                              <Clock size={12} className="text-muted/50" />
                              {h}
                            </button>
                          ))}
                        </div>
                      )}
                      {suggestions.length > 0 && (
                        <div className="max-h-64 overflow-y-auto p-2">
                          {suggestions.map((s) => (
                            <button
                              key={s.id}
                              type="button"
                              onMouseDown={(e) => e.preventDefault()}
                              onClick={() => handleSearch(s.name)}
                              className="flex w-full flex-col rounded-lg px-3 py-2 text-left hover:bg-subtle"
                            >
                              <span className="text-sm font-medium text-foreground">{s.name}</span>
                              {s.description && (
                                <span className="mt-0.5 text-[10px] leading-snug text-muted line-clamp-2">{s.description}</span>
                              )}
                            </button>
                          ))}
                        </div>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
              <motion.button
                whileTap={{ scale: 0.96 }}
                type="submit"
                disabled={!query.trim() || stream.isStreaming}
                className="flex items-center gap-2 rounded-xl bg-foreground px-6 py-3 text-sm font-medium text-white shadow-sm transition-opacity hover:opacity-85 disabled:opacity-30"
              >
                {stream.isStreaming ? (
                  <><Loader2 size={14} className="animate-spin" /> Analyzing</>
                ) : (
                  "Search"
                )}
              </motion.button>
            </div>
          </form>

          {!searched && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="mx-auto mt-3 flex max-w-xl flex-wrap justify-center gap-2 pb-16"
            >
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => handleSearch(s)}
                  className="rounded-lg border border-border bg-white px-3 py-1 text-xs text-muted shadow-sm transition-all hover:border-purple/30 hover:text-foreground"
                >
                  {s}
                </button>
              ))}
            </motion.div>
          )}
        </div>

        {searched && (
          <div className="mt-8 pb-16">
            {/* Disclaimer */}
            <div className="mb-6 rounded-xl border border-amber/20 bg-amber/[0.02] px-5 py-3">
              <p className="text-[11px] leading-relaxed text-muted">
                <span className="font-semibold text-amber">Research tool.</span>{" "}
                Results come from public databases (Open Targets, ClinicalTrials.gov, FDA FAERS, PubMed, ChEMBL).
                Not medical advice. All claims link to their data source.
              </p>
            </div>

            {/* Only show pipeline when streaming */}
            {(stream.isStreaming || stream.events.length > 0) && (
              <PipelineProgress events={stream.events} isStreaming={stream.isStreaming} />
            )}

            <AnimatePresence>
              {blocking.map((c, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mb-6 rounded-2xl border border-red/20 bg-red/[0.03] px-6 py-4"
                >
                  <div className="flex items-start gap-3">
                    <AlertTriangle size={16} className="mt-0.5 shrink-0 text-red" />
                    <div>
                      <p className="text-sm font-semibold text-red">
                        Contradiction: {c.agent_a} vs {c.agent_b}
                      </p>
                      <p className="mt-1 text-xs leading-relaxed text-foreground">
                        {c.explanation}
                      </p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Disease summary */}
            {displaySummary && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mb-8 rounded-2xl border border-border bg-card px-6 py-5"
              >
                <div className="flex items-center justify-between">
                  <p className="text-[10px] font-semibold uppercase tracking-widest text-purple">
                    Disease biology
                  </p>
                  <SourceBadge label="Open Targets" />
                </div>
                <p className="mt-2 text-sm leading-relaxed text-foreground">
                  {displaySummary}
                </p>
                {displayTargets.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {displayTargets.slice(0, 6).map((t) => (
                      <span
                        key={t.target_id}
                        className="rounded-md bg-subtle px-2 py-0.5 text-[10px] font-medium text-muted"
                      >
                        {t.gene_name}
                        <span className="ml-1 text-muted/50">
                          {(t.association_score * 100).toFixed(0)}%
                        </span>
                      </span>
                    ))}
                  </div>
                )}
              </motion.div>
            )}

            {/* Related diseases */}
            {displaySummary && !stream.isStreaming && (
              <RelatedDiseases
                diseaseName={query}
                onSelectDisease={handleSearch}
              />
            )}

            {displayContradictions.filter((c) => c.severity === "WARNING").length > 0 && (
              <div className="mb-6 space-y-3">
                {displayContradictions.filter((c) => c.severity === "WARNING").map((c, i) => (
                  <div key={i} className="rounded-xl border border-amber/20 bg-amber/[0.03] px-5 py-3">
                    <p className="text-[11px] font-semibold text-amber">
                      Warning: {c.agent_a} vs {c.agent_b}
                    </p>
                    <p className="mt-1 text-xs leading-relaxed text-muted">
                      {c.explanation}
                    </p>
                  </div>
                ))}
              </div>
            )}

            {/* Data sources bar + actions */}
            {displayDataSources.length > 0 && (
              <div className="mb-6 flex flex-wrap items-center gap-2">
                <Database size={12} className="text-muted/40" />
                <span className="text-[10px] text-muted/40">Sources:</span>
                {displayDataSources.map((src) => (
                  <SourceBadge key={src} label={src} />
                ))}
                <div className="ml-auto flex items-center gap-2">
                  {compareSet.size === 2 && (
                    <button
                      onClick={() => setShowCompare(true)}
                      className="flex items-center gap-1 rounded-lg border border-purple/30 bg-purple/5 px-3 py-1 text-[10px] font-medium text-purple transition-all hover:bg-purple/10"
                    >
                      <GitCompareArrows size={10} />
                      Compare ({compareSet.size})
                    </button>
                  )}
                  {!stream.isStreaming && sortedCandidates.length > 0 && (
                    <>
                      <button
                        onClick={handleDownloadPDF}
                        disabled={pdfLoading}
                        className="flex items-center gap-1 rounded-lg border border-border px-3 py-1 text-[10px] font-medium text-muted transition-all hover:border-purple/30 hover:text-foreground disabled:opacity-40"
                      >
                        {pdfLoading ? <Loader2 size={10} className="animate-spin" /> : <FileText size={10} />}
                        Download PDF
                      </button>
                      <button
                        onClick={() => window.open(`${API_BASE}/api/export/${encodeURIComponent(query)}`, "_blank")}
                        className="flex items-center gap-1 rounded-lg border border-border px-3 py-1 text-[10px] font-medium text-muted transition-all hover:border-purple/30 hover:text-foreground"
                      >
                        <Download size={10} />
                        Export JSON
                      </button>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Drug cards */}
            <div className="space-y-5">
              <AnimatePresence>
                {sortedCandidates.map((drug, i) => (
                  <motion.div
                    key={drug.drug_name}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1, duration: 0.4 }}
                  >
                    <DrugCard
                      drug={drug}
                      safety={displaySafetyMap[drug.drug_name]}
                      evidence={displayEvidenceMap[drug.drug_name]}
                      rank={i + 1}
                      delay={i * 600}
                      isStarred={starred.includes(drug.drug_name)}
                      onToggleStar={() => handleToggleStar(drug.drug_name)}
                      note={notes[drug.drug_name] || ""}
                      onNoteChange={(note) => handleNoteChange(drug.drug_name, note)}
                      isCompareSelected={compareSet.has(drug.drug_name)}
                      onToggleCompare={() => handleToggleCompare(drug.drug_name)}
                      compareDisabled={compareSet.size >= 2 && !compareSet.has(drug.drug_name)}
                      onDeepDive={() => setDeepDiveDrug(drug.drug_name)}
                      onGrantAbstract={() => setGrantDrug(drug.drug_name)}
                      onEditMolecule={() => setEditDrug(drug.drug_name)}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>

            {stream.events.length > 0 && <AgentLog events={stream.events} />}
          </div>
        )}
      </div>

      {/* Compare overlay */}
      <AnimatePresence>
        {showCompare && compareDrugs && (
          <CompareView
            drugs={compareDrugs}
            safetyMap={displaySafetyMap}
            evidenceMap={displayEvidenceMap}
            onClose={() => setShowCompare(false)}
          />
        )}
      </AnimatePresence>

      {/* Deep dive panel */}
      <AnimatePresence>
        {deepDiveDrug && (
          <DrugDetailPanel
            drugName={deepDiveDrug}
            diseaseName={query}
            onClose={() => setDeepDiveDrug(null)}
          />
        )}
      </AnimatePresence>

      {/* Grant abstract modal */}
      <AnimatePresence>
        {grantDrug && (
          <GrantAbstractModal
            drugName={grantDrug}
            diseaseName={query}
            onClose={() => setGrantDrug(null)}
          />
        )}
      </AnimatePresence>

      {/* 3D Molecule Editor */}
      <AnimatePresence>
        {editDrug && (
          <MoleculeEditor
            drugName={editDrug}
            onClose={() => setEditDrug(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}


function SourceBadge({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-md border border-border bg-subtle px-1.5 py-0.5 text-[9px] font-medium text-muted">
      <Database size={8} className="text-muted/50" />
      {label}
    </span>
  );
}


/* ---------- Pipeline Progress ---------- */

function PipelineProgress({ events }: { events: SSEEvent[]; isStreaming?: boolean }) {
  const steps = [
    { key: "disease_analyst", label: "Targets", icon: Dna },
    { key: "drug_hunter", label: "Drugs", icon: FlaskConical },
    { key: "safety_checker", label: "Safety", icon: ShieldCheck },
    { key: "evidence_agent", label: "Literature", icon: BookOpen },
    { key: "contradiction", label: "Verify", icon: AlertTriangle },
  ];

  const completedAgents = new Set(
    events.filter((e) => e.status === "complete").map((e) => e.agent)
  );
  const workingAgent = events.filter((e) => e.status === "working").pop()?.agent;

  return (
    <div className="mb-8 flex flex-wrap items-center justify-center gap-1">
      {steps.map((step, i) => {
        const done = completedAgents.has(step.key);
        const active = workingAgent === step.key;
        const Icon = step.icon;

        return (
          <div key={step.key} className="flex items-center gap-1">
            <motion.div
              animate={active ? { scale: [1, 1.08, 1] } : {}}
              transition={active ? { duration: 1, repeat: Infinity } : {}}
              className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[10px] font-medium transition-all ${
                done
                  ? "border-green/20 bg-green/5 text-green"
                  : active
                    ? "border-purple/30 bg-purple/5 text-purple shadow-sm"
                    : "border-border text-muted/40"
              }`}
            >
              {active ? (
                <Loader2 size={10} className="animate-spin" />
              ) : done ? (
                <CheckCircle2 size={10} />
              ) : (
                <Icon size={10} />
              )}
              {step.label}
            </motion.div>
            {i < steps.length - 1 && (
              <div className={`h-px w-4 ${done ? "bg-green/30" : "bg-border"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}


/* ---------- Drug Card ---------- */

function DrugCard({
  drug,
  safety,
  evidence,
  rank,
  delay,
  isStarred,
  onToggleStar,
  note,
  onNoteChange,
  isCompareSelected,
  onToggleCompare,
  compareDisabled,
  onDeepDive,
  onGrantAbstract,
  onEditMolecule,
}: {
  drug: DrugCandidate;
  safety?: SafetyAssessment;
  evidence?: EvidenceSummary;
  rank: number;
  delay: number;
  isStarred: boolean;
  onToggleStar: () => void;
  note: string;
  onNoteChange: (note: string) => void;
  isCompareSelected: boolean;
  onToggleCompare: () => void;
  compareDisabled: boolean;
  onDeepDive: () => void;
  onGrantAbstract: () => void;
  onEditMolecule: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [showNotes, setShowNotes] = useState(!!note);
  const v = safety ? VERDICT[safety.verdict] : null;
  const VIcon = v?.icon ?? Shield;
  const score = drug.evidence_score;
  const pct = score ? score.total : Math.round(drug.confidence * 100);
  const barColor = pct >= 70 ? "bg-green" : pct >= 50 ? "bg-amber" : "bg-red";

  return (
    <div className={`overflow-hidden rounded-2xl border shadow-sm transition-all hover:shadow-md ${
      isStarred ? "border-amber/40 bg-amber/[0.01]" : "border-border bg-card"
    }`}>
      <div className="flex">
        <div className="hidden sm:block shrink-0 border-r border-border">
          <MoleculeViewer drugName={drug.drug_name} size={{ width: 220, height: 220 }} delay={delay} />
        </div>

        <div className="flex-1 p-6">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2.5">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-purple/10 text-[10px] font-bold text-purple">
                  {rank}
                </span>
                <h3 className="text-lg font-bold text-foreground">{drug.drug_name}</h3>
                <button
                  onClick={onToggleStar}
                  className={`rounded-lg p-1 transition-all ${
                    isStarred ? "text-amber" : "text-muted/30 hover:text-amber/60"
                  }`}
                  title={isStarred ? "Unstar" : "Mark as promising"}
                >
                  <Star size={16} fill={isStarred ? "currentColor" : "none"} />
                </button>
              </div>
              <div className="mt-1 flex flex-wrap items-center gap-1.5">
                <p className="text-xs text-muted">
                  {drug.original_indication} · {drug.phase}
                </p>
                {drug.sources?.map((src) => (
                  <SourceBadge key={src} label={src} />
                ))}
              </div>
            </div>

            <div className="flex flex-col items-end gap-2">
              {v && (
                <span className={`inline-flex items-center gap-1 rounded-full border border-current/15 px-2.5 py-1 text-[10px] font-bold ${v.cls}`}>
                  <VIcon size={10} />
                  {v.label}
                </span>
              )}
              <div className="flex items-center gap-2">
                <div className="h-1.5 w-16 overflow-hidden rounded-full bg-subtle">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className={`h-full rounded-full ${barColor}`}
                  />
                </div>
                <span className="font-mono text-xs font-semibold text-foreground">{pct}/100</span>
              </div>
            </div>
          </div>

          {/* Evidence Score Breakdown */}
          {score && (
            <div className="mt-3 flex flex-wrap gap-1">
              <ScorePill label="Target" value={score.target_association} max={30} />
              <ScorePill label="Trial" value={score.trial_evidence} max={25} />
              <ScorePill label="Literature" value={score.literature_support} max={25} />
              <ScorePill label="Safety" value={score.safety_profile} max={20} />
            </div>
          )}

          <p className="mt-3 text-sm leading-relaxed text-foreground">
            {drug.repurposing_rationale}
          </p>

          {/* PubMed citations */}
          {evidence && evidence.paper_count > 0 && (
            <div className="mt-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-blue">
                <BookOpen size={9} className="mr-1 inline" />
                {evidence.paper_count} paper{evidence.paper_count !== 1 ? "s" : ""} in PubMed
              </p>
              <p className="mt-1 text-xs leading-relaxed text-muted">
                {evidence.evidence_summary}
              </p>
              <div className="mt-2 space-y-1">
                {evidence.top_papers.slice(0, 3).map((p) => (
                  <a
                    key={p.pmid}
                    href={p.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block text-[10px] leading-snug text-blue hover:underline"
                  >
                    <ExternalLink size={8} className="mr-0.5 inline" />
                    {p.title} — <span className="text-muted">{p.journal} ({p.year})</span>
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => setExpanded((e) => !e)}
              className="flex items-center gap-1 text-xs font-medium text-muted hover:text-foreground"
            >
              {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
              {expanded ? "Less" : "Details + safety"}
            </button>
            <button
              type="button"
              onClick={onDeepDive}
              className="flex items-center gap-1 text-xs font-medium text-purple/70 hover:text-purple"
            >
              <PanelRightOpen size={12} />
              Deep dive
            </button>
            <button
              type="button"
              onClick={onGrantAbstract}
              className="flex items-center gap-1 text-xs font-medium text-blue/70 hover:text-blue"
            >
              <FileText size={12} />
              Grant draft
            </button>
            <button
              type="button"
              onClick={onEditMolecule}
              className="flex items-center gap-1 text-xs font-medium text-emerald/70 hover:text-emerald"
            >
              <FlaskConical size={12} />
              Edit molecule
            </button>
            <button
              type="button"
              onClick={() => setShowNotes((n) => !n)}
              className={`flex items-center gap-1 text-xs font-medium ${
                note ? "text-amber/70" : "text-muted"
              } hover:text-foreground`}
            >
              <StickyNote size={12} />
              Notes{note ? " ✓" : ""}
            </button>
            <button
              type="button"
              onClick={onToggleCompare}
              disabled={compareDisabled}
              className={`flex items-center gap-1 text-xs font-medium transition-all disabled:opacity-30 ${
                isCompareSelected ? "text-purple" : "text-muted hover:text-foreground"
              }`}
            >
              <GitCompareArrows size={12} />
              {isCompareSelected ? "Selected" : "Compare"}
            </button>
            {drug.trial_id && (
              <a
                href={`https://clinicaltrials.gov/study/${drug.trial_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-xs text-blue hover:underline"
              >
                <ExternalLink size={10} />
                {drug.trial_id}
              </a>
            )}
          </div>

          {/* Notes textarea */}
          <AnimatePresence>
            {showNotes && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="mt-3 rounded-xl border border-amber/20 bg-amber/[0.02] p-3">
                  <p className="mb-1.5 text-[9px] font-semibold uppercase tracking-wider text-amber/60">
                    Research Notes
                  </p>
                  <textarea
                    value={note}
                    onChange={(e) => onNoteChange(e.target.value)}
                    placeholder="Add your observations, hypotheses, or follow-up tasks..."
                    rows={3}
                    className="w-full resize-none rounded-lg border border-amber/10 bg-white px-3 py-2 text-xs leading-relaxed text-foreground placeholder:text-muted/30 focus:border-amber/30 focus:outline-none"
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {expanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="mt-4 grid gap-3 border-t border-border pt-4 sm:grid-cols-2">
                  <DetailBlock label="Mechanism" value={drug.mechanism} />
                  <DetailBlock label="Why it was shelved" value={drug.failure_reason} />
                  {safety && (
                    <>
                      <DetailBlock
                        label={`Safety — ${safety.source || "FDA FAERS"}`}
                        value={safety.reasoning}
                      />
                      {safety.adverse_events.length > 0 && (
                        <div>
                          <p className="text-[10px] font-semibold uppercase tracking-wider text-muted">
                            Adverse Events (FDA Reports)
                          </p>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {safety.adverse_events.slice(0, 8).map((ae) => (
                              <span
                                key={ae}
                                className="rounded bg-subtle px-1.5 py-0.5 text-[9px] text-muted"
                              >
                                {ae}
                                {safety.report_counts?.[ae] && (
                                  <span className="ml-0.5 text-muted/50">
                                    ({safety.report_counts[ae].toLocaleString()})
                                  </span>
                                )}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {safety.organ_conflicts.length > 0 && (
                        <DetailBlock
                          label="Organ conflicts"
                          value={safety.organ_conflicts.join(", ")}
                        />
                      )}
                    </>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

function ScorePill({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = (value / max) * 100;
  const color = pct >= 70 ? "text-green" : pct >= 40 ? "text-amber" : "text-muted";
  return (
    <span className={`inline-flex items-center gap-1 rounded-md border border-border bg-subtle px-1.5 py-0.5 text-[9px] font-medium ${color}`}>
      {label} {value}/{max}
    </span>
  );
}

function DetailBlock({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted">{label}</p>
      <p className="mt-1 text-xs leading-relaxed text-foreground">{value}</p>
    </div>
  );
}


/* ---------- Agent Log ---------- */

function AgentLog({ events }: { events: SSEEvent[] }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="mt-10 rounded-2xl border border-border bg-card">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-6 py-4"
      >
        <div className="flex items-center gap-2">
          <Circle size={6} fill="#16a34a" stroke="none" />
          <span className="text-xs font-semibold text-foreground">Pipeline log</span>
          <span className="text-[10px] text-muted">{events.length} events</span>
        </div>
        {open ? <ChevronUp size={14} className="text-muted" /> : <ChevronDown size={14} className="text-muted" />}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: "auto" }}
            exit={{ height: 0 }}
            className="overflow-hidden"
          >
            <div className="space-y-1 border-t border-border px-6 py-4 font-mono text-[11px]">
              {events.map((evt, i) => {
                const cfg = AGENT_STYLE[evt.agent] ?? AGENT_STYLE.system;
                return (
                  <div key={i} className="flex items-start gap-2 py-0.5">
                    <span className={`mt-0.5 font-semibold ${cfg.color}`}>{cfg.label}</span>
                    <span className="text-muted">—</span>
                    <span className={evt.status === "working" ? "text-muted" : "text-foreground"}>
                      {evt.message}
                    </span>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
