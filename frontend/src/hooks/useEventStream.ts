"use client";

import { useState, useCallback, useRef } from "react";
import type {
  SSEEvent,
  DiseaseTarget,
  DrugCandidate,
  SafetyAssessment,
  Contradiction,
  EvidenceSummary,
  DiseaseEvaluation,
} from "@/lib/diseaseTypes";

import { API_BASE } from "@/lib/config";

export interface StreamState {
  events: SSEEvent[];
  targets: DiseaseTarget[];
  candidates: DrugCandidate[];
  safetyAssessments: SafetyAssessment[];
  contradictions: Contradiction[];
  evidenceSummaries: EvidenceSummary[];
  diseaseSummary: string;
  dataSources: string[];
  result: DiseaseEvaluation | null;
  isStreaming: boolean;
  error: string | null;
}

const INITIAL: StreamState = {
  events: [],
  targets: [],
  candidates: [],
  safetyAssessments: [],
  contradictions: [],
  evidenceSummaries: [],
  diseaseSummary: "",
  dataSources: [],
  result: null,
  isStreaming: false,
  error: null,
};

export function useEventStream() {
  const [state, setState] = useState<StreamState>(INITIAL);
  const abortRef = useRef<AbortController | null>(null);

  const evaluate = useCallback(async (diseaseName: string) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setState({ ...INITIAL, isStreaming: true });

    try {
      const url = `${API_BASE}/api/evaluate/${encodeURIComponent(diseaseName)}`;
      const resp = await fetch(url, { signal: controller.signal });

      if (!resp.ok || !resp.body) {
        setState((s) => ({ ...s, isStreaming: false, error: "Failed to connect" }));
        return;
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;

          try {
            const event: SSEEvent = JSON.parse(raw);

            setState((prev) => {
              const next = { ...prev, events: [...prev.events, event] };

              if (event.status === "complete" && event.data) {
                if (event.agent === "disease_analyst") {
                  next.targets = (event.data.targets as DiseaseTarget[]) || [];
                  next.diseaseSummary = (event.data.disease_summary as string) || "";
                }
                if (event.agent === "drug_hunter") {
                  next.candidates = (event.data.candidates as DrugCandidate[]) || [];
                }
                if (event.agent === "safety_checker") {
                  next.safetyAssessments = (event.data.safety_assessments as SafetyAssessment[]) || [];
                }
                if (event.agent === "evidence_agent") {
                  next.evidenceSummaries = (event.data.evidence_summaries as EvidenceSummary[]) || [];
                }
                if (event.agent === "contradiction") {
                  next.contradictions = (event.data.contradictions as Contradiction[]) || [];
                }
                if (event.agent === "system") {
                  const fullResult = event.data as unknown as DiseaseEvaluation;
                  next.result = fullResult;
                  next.dataSources = fullResult.data_sources || [];
                  next.candidates = fullResult.candidates || next.candidates;
                  next.evidenceSummaries = fullResult.evidence_summaries || next.evidenceSummaries;
                  next.isStreaming = false;
                }
              }

              return next;
            });
          } catch {
            // skip malformed events
          }
        }
      }

      setState((s) => ({ ...s, isStreaming: false }));
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setState((s) => ({ ...s, isStreaming: false, error: String(err) }));
      }
    }
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setState(INITIAL);
  }, []);

  return { ...state, evaluate, reset };
}
