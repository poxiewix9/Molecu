import type { DiseaseEvaluation } from "./diseaseTypes";

const STORAGE_KEY = "pharmasynapse_sessions";
const HISTORY_KEY = "pharmasynapse_search_history";

export interface ResearchSession {
  id: string;
  disease_name: string;
  created_at: string;
  updated_at: string;
  results: DiseaseEvaluation;
  notes: Record<string, string>;
  starred: string[];
}

export function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

export function getSessions(): ResearchSession[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveSession(session: ResearchSession): void {
  const sessions = getSessions();
  const idx = sessions.findIndex((s) => s.id === session.id);
  session.updated_at = new Date().toISOString();
  if (idx >= 0) {
    sessions[idx] = session;
  } else {
    sessions.unshift(session);
  }
  // Keep max 20 sessions
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions.slice(0, 20)));
}

export function deleteSession(id: string): void {
  const sessions = getSessions().filter((s) => s.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
}

export function getSession(id: string): ResearchSession | null {
  return getSessions().find((s) => s.id === id) ?? null;
}

export function createSessionFromResults(results: DiseaseEvaluation): ResearchSession {
  return {
    id: generateId(),
    disease_name: results.disease_name,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    results,
    notes: {},
    starred: [],
  };
}

export function updateNote(sessionId: string, drugName: string, note: string): void {
  const session = getSession(sessionId);
  if (!session) return;
  if (note.trim()) {
    session.notes[drugName] = note;
  } else {
    delete session.notes[drugName];
  }
  saveSession(session);
}

export function toggleStar(sessionId: string, drugName: string): boolean {
  const session = getSession(sessionId);
  if (!session) return false;
  const idx = session.starred.indexOf(drugName);
  if (idx >= 0) {
    session.starred.splice(idx, 1);
  } else {
    session.starred.push(drugName);
  }
  saveSession(session);
  return idx < 0; // returns new starred state
}

export function getSearchHistory(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function addToSearchHistory(query: string): void {
  const history = getSearchHistory().filter((h) => h.toLowerCase() !== query.toLowerCase());
  history.unshift(query);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, 10)));
}
