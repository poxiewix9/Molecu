# User Experience Design

## Design Philosophy

PharmaSynapse follows these UX principles:

1. **Research Workbench, Not Search Engine**: Sessions persist, notes save, work accumulates over days/weeks
2. **Progressive Disclosure**: Summary first, deep-dive on demand
3. **Real-Time Feedback**: Watch each agent work via SSE streaming
4. **Source Transparency**: Every claim links to its database
5. **Beautiful Minimalism**: Clean white theme, purposeful animations, zero clutter
6. **Actionable Exports**: PDF reports formatted for grant proposals

---

## User Journey: College Researcher

```
1. DISCOVER
   └─ Landing page: "Find new life for abandoned drugs"
   └─ Interactive Three.js molecular scene (draggable, auto-rotating)
   └─ Disease search with autocomplete from Open Targets
   └─ Quick suggestions: Huntington, ALS, Cystic Fibrosis...
        │
        ▼
2. SEARCH
   └─ Type "Huntington Disease" → autocomplete dropdown shows matches
   └─ Or click a suggestion chip
        │
        ▼
3. WATCH AGENTS WORK
   └─ Pipeline progress bar: Biology → Drugs → Safety → Literature → Verify
   └─ Each step animates as the agent works
   └─ Results appear incrementally as agents complete
        │
        ▼
4. EXPLORE RESULTS
   └─ Disease biology card (targets, association scores)
   └─ Drug candidate cards with:
      ├── 3D molecule structure (3Dmol.js from PubChem)
      ├── Evidence score breakdown (Target/Trial/Literature/Safety)
      ├── Safety verdict badge (Safe / Caution / Unsafe)
      ├── PubMed citations with links
      ├── ★ Star toggle — mark as promising
      ├── 📝 Notes — add research observations
      ├── ⇔ Compare — select for side-by-side comparison
      ├── → Deep dive — open full data panel
      └── 🧪 Edit molecule — open 3D molecular editor
        │
        ▼
5. EDIT MOLECULE (optional)
   └─ Click "Edit molecule" → centered popup modal
   └─ Drug's 3D structure loads from PubChem SDF
   └─ Tools: Select, Add Atom, Bond, Delete
   └─ Element palette: C, N, O, S, H, F, Cl, P, Br
   └─ Undo/Redo history, keyboard shortcuts (⌘Z / ⌘⇧Z)
   └─ Rotate/zoom the molecule with mouse
   └─ Export modified structure as .SDF file
   └─ Close via X, Escape, or backdrop click
        │
        ▼
6. DEEP DIVE
   └─ Slide-out panel with 3 tabs:
      ├── Literature: Up to 20 PubMed papers with abstracts
      ├── All Trials: Every ClinicalTrials.gov entry for this drug
      └── Adverse Events: Full FDA FAERS data with report counts
        │
        ▼
7. COMPARE
   └─ Select 2 drugs → "Compare" button appears
   └─ Two-column modal: scores, safety, papers, mechanism, rationale
        │
        ▼
8. EXPORT
   └─ "Download PDF" — multi-page report for grant proposals
   └─ "Export JSON" — structured data for computational pipelines
        │
        ▼
9. RETURN LATER
   └─ "My Research" sidebar shows all past sessions
   └─ Click to reload any session with all notes and stars preserved
   └─ Search history for quick re-runs
```

---

## Interface Design

### Visual System

| Element | Treatment |
|---------|-----------|
| **Background** | Clean white (#ffffff) |
| **Cards** | White with subtle border, shadow on hover |
| **Primary accent** | Purple (#7c3aed) — buttons, active states, scores |
| **Success** | Green — PASS verdicts, completed agents |
| **Warning** | Amber — WARNING verdicts, cautions |
| **Error** | Red — HARD_FAIL, contradictions |
| **Typography** | System font stack, tight tracking for headings |
| **Spacing** | Generous padding, max-w-6xl container |

### Animation System (Framer Motion)

- **Page transitions**: Fade + slide on search
- **Card entry**: Staggered fade-up (100ms delay per card)
- **Pipeline progress**: Pulse animation on active agent
- **Expandable sections**: Height + opacity spring animation
- **Score bars**: Animated fill from 0 to value
- **Panel slide**: Spring-damped slide from right

### 3D Visualization

1. **Hero Scene** (Three.js + @react-three/fiber)
   - Floating molecular lattice (atoms + bonds)
   - Ambient particles
   - Auto-rotation with orbital controls
   - Appears on landing page, fills 70vh

2. **Molecule Viewers** (3Dmol.js)
   - Per-drug PubChem SDF structure rendering
   - Stick + sphere visualization with Jmol coloring
   - Slow spin animation
   - Graceful fallback (stylized initial) when structure unavailable
   - Name variation matching for complex drug names

---

## Research Workbench Features

### Sessions (localStorage)
```typescript
interface ResearchSession {
  id: string;
  disease_name: string;
  created_at: string;
  updated_at: string;
  results: DiseaseEvaluation;
  notes: Record<string, string>;     // drug_name → researcher note
  starred: string[];                  // promising drug names
}
```
- Auto-save when pipeline completes
- Max 20 sessions stored
- Delete sessions you don't need
- Sessions survive browser refresh

### Starring
- Click star on any drug card
- Starred drugs highlighted with amber border
- Starred drugs sort to top of results
- Stars included in PDF report (★ prefix)

### Notes
- Expandable textarea per drug card
- "Add your observations, hypotheses, or follow-up tasks..."
- Auto-persisted to session
- Included in PDF report as "Researcher Notes" section

### Comparison
- Checkbox on each card (max 2)
- "Compare (2)" button appears in actions bar
- Two-column modal comparing all dimensions:
  - Evidence scores (total + breakdown)
  - Safety verdicts + adverse events
  - Phase, indication, mechanism
  - Paper counts
  - Rationale text

### PDF Report
Multi-page document generated client-side:
1. **Title page**: Disease name, date, MolecuThread branding, disclaimer
2. **Executive summary**: Disease biology, target count, top 3 candidates
3. **Per-drug pages**: Evidence scores, mechanism, safety, PubMed citations, researcher notes
4. **Methodology**: Pipeline steps, scoring formula, databases queried
5. **Formatted for grant proposals** — printable, professional, citable
