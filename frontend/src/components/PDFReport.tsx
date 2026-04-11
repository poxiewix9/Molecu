"use client";

import {
  Document,
  Page,
  Text,
  View,
  StyleSheet,
  pdf,
} from "@react-pdf/renderer";
import type { DiseaseEvaluation, DrugCandidate, SafetyAssessment, EvidenceSummary } from "@/lib/diseaseTypes";

const styles = StyleSheet.create({
  page: { padding: 40, fontFamily: "Helvetica", fontSize: 10, color: "#1a1a2e" },
  titlePage: { flex: 1, justifyContent: "center", alignItems: "center" },
  title: { fontSize: 24, fontFamily: "Helvetica-Bold", textAlign: "center", marginBottom: 8 },
  subtitle: { fontSize: 12, color: "#666", textAlign: "center", marginBottom: 4 },
  disclaimer: { fontSize: 8, color: "#888", textAlign: "center", marginTop: 24, maxWidth: 400 },
  sectionTitle: { fontSize: 14, fontFamily: "Helvetica-Bold", marginTop: 20, marginBottom: 8, color: "#1a1a2e", borderBottomWidth: 1, borderBottomColor: "#e5e5e5", paddingBottom: 4 },
  subTitle: { fontSize: 11, fontFamily: "Helvetica-Bold", marginTop: 12, marginBottom: 4 },
  body: { fontSize: 10, lineHeight: 1.5, color: "#333" },
  small: { fontSize: 8, color: "#666", lineHeight: 1.4 },
  badge: { fontSize: 8, backgroundColor: "#f3f0ff", color: "#7c3aed", padding: "2 6", borderRadius: 3, marginRight: 4 },
  row: { flexDirection: "row", marginBottom: 4 },
  label: { fontSize: 9, fontFamily: "Helvetica-Bold", width: 100, color: "#555" },
  value: { fontSize: 9, flex: 1, color: "#1a1a2e" },
  drugCard: { marginBottom: 16, padding: 12, borderWidth: 1, borderColor: "#e5e5e5", borderRadius: 6 },
  drugName: { fontSize: 13, fontFamily: "Helvetica-Bold", color: "#7c3aed" },
  scoreBar: { flexDirection: "row", marginTop: 6, gap: 4 },
  scorePill: { fontSize: 8, padding: "2 5", borderRadius: 3, backgroundColor: "#f5f5f5", color: "#555" },
  citation: { fontSize: 8, color: "#2563eb", marginBottom: 2 },
  noteBox: { marginTop: 8, padding: 8, backgroundColor: "#fffde8", borderRadius: 4 },
  noteLabel: { fontSize: 8, fontFamily: "Helvetica-Bold", color: "#92700c", marginBottom: 2 },
  noteText: { fontSize: 9, color: "#555" },
  refSection: { marginTop: 20 },
  footer: { position: "absolute", bottom: 20, left: 40, right: 40, textAlign: "center", fontSize: 7, color: "#aaa" },
});

interface PDFReportProps {
  results: DiseaseEvaluation;
  notes: Record<string, string>;
  starred: string[];
}

function TitlePage({ diseaseName }: { diseaseName: string }) {
  return (
    <Page size="A4" style={styles.page}>
      <View style={styles.titlePage}>
        <Text style={styles.title}>Drug Repurposing Analysis</Text>
        <Text style={{ ...styles.subtitle, fontSize: 16 }}>{diseaseName}</Text>
        <Text style={styles.subtitle}>Generated {new Date().toLocaleDateString()}</Text>
        <Text style={styles.subtitle}>PharmaSynapse Research Workbench</Text>
        <Text style={styles.disclaimer}>
          This is a computational research tool. Results are generated from public databases
          (Open Targets, ClinicalTrials.gov, FDA FAERS, PubMed, ChEMBL) and should not be
          interpreted as medical advice.
        </Text>
      </View>
      <Text style={styles.footer}>PharmaSynapse · AI-Powered Drug Repurposing</Text>
    </Page>
  );
}

function SummaryPage({ results, starred }: { results: DiseaseEvaluation; starred: string[] }) {
  const top3 = results.candidates.slice(0, 3);
  return (
    <Page size="A4" style={styles.page}>
      <Text style={styles.sectionTitle}>Executive Summary</Text>

      <Text style={styles.subTitle}>Disease Biology</Text>
      <Text style={styles.body}>{results.disease_summary}</Text>

      {results.targets.length > 0 && (
        <>
          <Text style={styles.subTitle}>Protein Targets ({results.targets.length})</Text>
          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 4, marginBottom: 8 }}>
            {results.targets.slice(0, 8).map((t) => (
              <Text key={t.target_id} style={styles.badge}>
                {t.gene_name} ({(t.association_score * 100).toFixed(0)}%)
              </Text>
            ))}
          </View>
        </>
      )}

      <Text style={styles.subTitle}>
        Candidates Found: {results.candidates.length} · Starred: {starred.length}
      </Text>

      {top3.length > 0 && (
        <>
          <Text style={{ ...styles.subTitle, marginTop: 8 }}>Top Ranked</Text>
          {top3.map((c, i) => (
            <View key={c.drug_name} style={{ ...styles.row, marginBottom: 8 }}>
              <Text style={styles.label}>#{i + 1} {c.drug_name}</Text>
              <Text style={styles.value}>
                Score: {c.evidence_score?.total ?? "—"}/100 · {c.phase} · {c.original_indication}
              </Text>
            </View>
          ))}
        </>
      )}

      {results.data_sources.length > 0 && (
        <>
          <Text style={styles.subTitle}>Data Sources</Text>
          {results.data_sources.map((src) => (
            <Text key={src} style={styles.small}>• {src}</Text>
          ))}
        </>
      )}
      <Text style={styles.footer}>PharmaSynapse · AI-Powered Drug Repurposing</Text>
    </Page>
  );
}

function DrugPage({
  drug,
  safety,
  evidence,
  note,
  isStarred,
}: {
  drug: DrugCandidate;
  safety?: SafetyAssessment;
  evidence?: EvidenceSummary;
  note?: string;
  isStarred: boolean;
}) {
  const score = drug.evidence_score;
  return (
    <Page size="A4" style={styles.page}>
      <View style={styles.drugCard}>
        <Text style={styles.drugName}>
          {isStarred ? "★ " : ""}{drug.drug_name}
        </Text>
        <Text style={styles.small}>{drug.original_indication} · {drug.phase}</Text>

        {score && (
          <View style={styles.scoreBar}>
            <Text style={styles.scorePill}>Total: {score.total}/100</Text>
            <Text style={styles.scorePill}>Target: {score.target_association}/30</Text>
            <Text style={styles.scorePill}>Trial: {score.trial_evidence}/25</Text>
            <Text style={styles.scorePill}>Lit: {score.literature_support}/25</Text>
            <Text style={styles.scorePill}>Safety: {score.safety_profile}/20</Text>
          </View>
        )}

        <View style={{ ...styles.row, marginTop: 8 }}>
          <Text style={styles.label}>Mechanism</Text>
          <Text style={styles.value}>{drug.mechanism}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Rationale</Text>
          <Text style={styles.value}>{drug.repurposing_rationale}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Failure Reason</Text>
          <Text style={styles.value}>{drug.failure_reason}</Text>
        </View>

        {safety && (
          <>
            <Text style={styles.subTitle}>Safety: {safety.verdict}</Text>
            <Text style={styles.small}>{safety.reasoning}</Text>
            {safety.adverse_events.length > 0 && (
              <Text style={{ ...styles.small, marginTop: 4 }}>
                Events: {safety.adverse_events.join(", ")}
              </Text>
            )}
          </>
        )}

        {evidence && evidence.paper_count > 0 && (
          <>
            <Text style={styles.subTitle}>Literature ({evidence.paper_count} papers)</Text>
            <Text style={styles.small}>{evidence.evidence_summary}</Text>
            {evidence.top_papers.slice(0, 5).map((p) => (
              <Text key={p.pmid} style={styles.citation}>
                {p.authors}. &quot;{p.title}&quot; {p.journal} ({p.year}). PMID: {p.pmid}
              </Text>
            ))}
          </>
        )}

        {note && (
          <View style={styles.noteBox}>
            <Text style={styles.noteLabel}>Researcher Notes</Text>
            <Text style={styles.noteText}>{note}</Text>
          </View>
        )}
      </View>
      <Text style={styles.footer}>PharmaSynapse · AI-Powered Drug Repurposing</Text>
    </Page>
  );
}

function MethodologyPage() {
  return (
    <Page size="A4" style={styles.page}>
      <Text style={styles.sectionTitle}>Methodology</Text>
      <Text style={styles.body}>
        This report was generated by PharmaSynapse, an AI-powered drug repurposing research tool.
        The pipeline queries multiple public biomedical databases and applies evidence-based scoring.
      </Text>

      <Text style={styles.subTitle}>Pipeline Steps</Text>
      <Text style={styles.small}>1. Disease target identification via Open Targets Platform GraphQL API</Text>
      <Text style={styles.small}>2. Drug candidate search via ClinicalTrials.gov API v2 (terminated/withdrawn trials) and ChEMBL REST API (drug-target binding)</Text>
      <Text style={styles.small}>3. Safety evaluation via FDA FAERS adverse event data (openFDA API), rule-based classification</Text>
      <Text style={styles.small}>4. Literature evidence via PubMed E-utilities (NCBI)</Text>
      <Text style={styles.small}>5. Contradiction detection via DeBERTa NLI model + rule-based logic</Text>

      <Text style={styles.subTitle}>Scoring</Text>
      <Text style={styles.body}>
        Evidence Score = Target Association (0-30) + Trial Phase (0-25) + Literature Support (0-25) + Safety Profile (0-20).
        All scores are computed deterministically from data — no LLM is used for scoring.
      </Text>

      <Text style={styles.subTitle}>Databases Queried</Text>
      <Text style={styles.small}>• Open Targets Platform — disease-gene associations</Text>
      <Text style={styles.small}>• ClinicalTrials.gov — clinical trial data</Text>
      <Text style={styles.small}>• ChEMBL — drug-target binding data</Text>
      <Text style={styles.small}>• FDA FAERS (openFDA) — adverse event reports</Text>
      <Text style={styles.small}>• PubMed / NCBI — biomedical literature</Text>
      <Text style={styles.small}>• PubChem — molecular structure data</Text>
      <Text style={styles.footer}>PharmaSynapse · AI-Powered Drug Repurposing</Text>
    </Page>
  );
}

function PDFReportDocument({ results, notes, starred }: PDFReportProps) {
  const saMap: Record<string, SafetyAssessment> = {};
  for (const sa of results.safety_assessments) saMap[sa.drug_name] = sa;
  const evMap: Record<string, EvidenceSummary> = {};
  for (const es of results.evidence_summaries) evMap[es.drug_name] = es;

  const sortedCandidates = [...results.candidates].sort((a, b) => {
    const aStarred = starred.includes(a.drug_name) ? 1 : 0;
    const bStarred = starred.includes(b.drug_name) ? 1 : 0;
    if (aStarred !== bStarred) return bStarred - aStarred;
    return (b.evidence_score?.total ?? 0) - (a.evidence_score?.total ?? 0);
  });

  return (
    <Document>
      <TitlePage diseaseName={results.disease_name} />
      <SummaryPage results={results} starred={starred} />
      {sortedCandidates.map((drug) => (
        <DrugPage
          key={drug.drug_name}
          drug={drug}
          safety={saMap[drug.drug_name]}
          evidence={evMap[drug.drug_name]}
          note={notes[drug.drug_name]}
          isStarred={starred.includes(drug.drug_name)}
        />
      ))}
      <MethodologyPage />
    </Document>
  );
}

export async function generatePDF(results: DiseaseEvaluation, notes: Record<string, string>, starred: string[]): Promise<Blob> {
  const blob = await pdf(
    <PDFReportDocument results={results} notes={notes} starred={starred} />
  ).toBlob();
  return blob;
}
