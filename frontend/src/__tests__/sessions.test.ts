import { describe, it, expect, beforeEach } from "vitest";
import {
  getSessions,
  saveSession,
  deleteSession,
  getSession,
  createSessionFromResults,
  generateId,
  toggleStar,
  updateNote,
  getSearchHistory,
  addToSearchHistory,
} from "@/lib/sessions";
import type { DiseaseEvaluation } from "@/lib/diseaseTypes";

function mockEvaluation(name: string): DiseaseEvaluation {
  return {
    disease_name: name,
    disease_summary: `Summary for ${name}`,
    targets: [],
    candidates: [],
    safety_assessments: [],
    contradictions: [],
    evidence_summaries: [],
    data_sources: ["Open Targets"],
  };
}

describe("sessions.ts — localStorage session management", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("getSessions returns empty array when no sessions exist", () => {
    expect(getSessions()).toEqual([]);
  });

  it("generateId produces unique IDs", () => {
    const ids = new Set(Array.from({ length: 100 }, () => generateId()));
    expect(ids.size).toBe(100);
  });

  it("createSessionFromResults creates a valid session object", () => {
    const results = mockEvaluation("Huntington Disease");
    const session = createSessionFromResults(results);
    expect(session.disease_name).toBe("Huntington Disease");
    expect(session.id).toBeTruthy();
    expect(session.notes).toEqual({});
    expect(session.starred).toEqual([]);
    expect(session.created_at).toBeTruthy();
    expect(session.results).toBe(results);
  });

  it("saveSession persists and retrieves sessions", () => {
    const session = createSessionFromResults(mockEvaluation("ALS"));
    saveSession(session);
    const sessions = getSessions();
    expect(sessions).toHaveLength(1);
    expect(sessions[0].disease_name).toBe("ALS");
  });

  it("saveSession updates existing session by ID", () => {
    const session = createSessionFromResults(mockEvaluation("ALS"));
    saveSession(session);
    session.notes["DrugA"] = "Promising";
    saveSession(session);
    const sessions = getSessions();
    expect(sessions).toHaveLength(1);
    expect(sessions[0].notes["DrugA"]).toBe("Promising");
  });

  it("getSession returns session by ID", () => {
    const session = createSessionFromResults(mockEvaluation("Cystic Fibrosis"));
    saveSession(session);
    const found = getSession(session.id);
    expect(found).not.toBeNull();
    expect(found!.disease_name).toBe("Cystic Fibrosis");
  });

  it("getSession returns null for unknown ID", () => {
    expect(getSession("nonexistent")).toBeNull();
  });

  it("deleteSession removes a session", () => {
    const session = createSessionFromResults(mockEvaluation("ALS"));
    saveSession(session);
    expect(getSessions()).toHaveLength(1);
    deleteSession(session.id);
    expect(getSessions()).toHaveLength(0);
  });

  it("enforces max 20 sessions", () => {
    for (let i = 0; i < 25; i++) {
      const s = createSessionFromResults(mockEvaluation(`Disease ${i}`));
      saveSession(s);
    }
    expect(getSessions().length).toBeLessThanOrEqual(20);
  });

  it("toggleStar adds and removes starred drugs", () => {
    const session = createSessionFromResults(mockEvaluation("ALS"));
    saveSession(session);
    const starred = toggleStar(session.id, "Idebenone");
    expect(starred).toBe(true);
    const s1 = getSession(session.id);
    expect(s1!.starred).toContain("Idebenone");

    const unstarred = toggleStar(session.id, "Idebenone");
    expect(unstarred).toBe(false);
    const s2 = getSession(session.id);
    expect(s2!.starred).not.toContain("Idebenone");
  });

  it("updateNote sets and clears notes", () => {
    const session = createSessionFromResults(mockEvaluation("ALS"));
    saveSession(session);
    updateNote(session.id, "DrugA", "Interesting mechanism");
    expect(getSession(session.id)!.notes["DrugA"]).toBe("Interesting mechanism");

    updateNote(session.id, "DrugA", "  ");
    expect(getSession(session.id)!.notes["DrugA"]).toBeUndefined();
  });

  it("getSearchHistory returns empty array initially", () => {
    expect(getSearchHistory()).toEqual([]);
  });

  it("addToSearchHistory stores and deduplicates queries", () => {
    addToSearchHistory("Huntington Disease");
    addToSearchHistory("ALS");
    addToSearchHistory("huntington disease");
    const history = getSearchHistory();
    expect(history[0]).toBe("huntington disease");
    expect(history).toHaveLength(2);
  });

  it("addToSearchHistory limits to 10 entries", () => {
    for (let i = 0; i < 15; i++) addToSearchHistory(`Disease ${i}`);
    expect(getSearchHistory().length).toBeLessThanOrEqual(10);
  });
});
