# PharmaSynapse Frontend

Next.js 16 + React 19 + Tailwind CSS 4 frontend for the PharmaSynapse drug repurposing research workbench.

## Component Architecture

```
Dashboard.tsx              Main orchestrator — search, sessions, results
├── HeroScene.tsx          Three.js interactive 3D molecule scene
├── MoleculeViewer.tsx     3Dmol.js per-drug 3D structure (PubChem SDF)
├── DrugDetailPanel.tsx    Slide-out deep-dive (literature, trials, safety)
├── CompareView.tsx        Side-by-side drug comparison modal
├── GrantAbstractModal.tsx LLM-drafted NIH R21 grant abstract
├── RelatedDiseases.tsx    Shared protein target disease network
├── MoleculeEditor.tsx     3D molecular editor (React Three Fiber, SDF export)
└── PDFReport.tsx          Client-side PDF generation (@react-pdf/renderer)
```

## Key Libraries

| Library | Purpose |
|---------|---------|
| `@react-three/fiber` + `drei` | Interactive 3D hero scene |
| `3Dmol.js` | Per-drug molecular structure rendering |
| `framer-motion` | UI animations and transitions |
| `@react-pdf/renderer` | Client-side PDF export |
| `lucide-react` | Icon system |

## State Management

- **SSE streaming**: `useEventStream.ts` hook consumes `/api/evaluate/{disease}` events
- **Sessions**: `localStorage`-based persistence via `lib/sessions.ts`
- **Types**: Shared Pydantic-mirrored types in `lib/diseaseTypes.ts`

## Environment Variables

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend URL (default: `http://localhost:8000`) |

## Development

```bash
npm install
npm run dev     # starts on http://localhost:3000
npm run build   # production build
npm run lint    # ESLint check
```
