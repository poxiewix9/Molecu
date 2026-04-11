"use client";

import { useEffect, useRef, useState } from "react";

interface MoleculeViewerProps {
  drugName: string;
  size?: { width: number; height: number };
  delay?: number;
}

declare global {
  interface Window {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    $3Dmol: any;
  }
}

let scriptPromise: Promise<void> | null = null;

function load3DmolScript(): Promise<void> {
  if (scriptPromise) return scriptPromise;
  scriptPromise = new Promise((resolve) => {
    if (typeof window !== "undefined" && window.$3Dmol) return resolve();

    const script = document.createElement("script");
    script.src = "https://3Dmol.org/build/3Dmol-min.js";
    script.onload = () => {
      const poll = setInterval(() => {
        if (window.$3Dmol) { clearInterval(poll); resolve(); }
      }, 50);
      setTimeout(() => { clearInterval(poll); resolve(); }, 5000);
    };
    script.onerror = () => { scriptPromise = null; resolve(); };
    document.head.appendChild(script);
  });
  return scriptPromise;
}

// Well-known drug names that PubChem indexes under a different spelling
const KNOWN_ALIASES: Record<string, string> = {
  "nicotinamide": "niacinamide",
  "vitamin b3": "niacinamide",
  "epa": "eicosapentaenoic acid",
  "dha": "docosahexaenoic acid",
  "l-dopa": "levodopa",
  "5-ht": "serotonin",
  "asa": "aspirin",
  "acetylsalicylic acid": "aspirin",
  "coq10": "ubiquinone",
  "coenzyme q10": "ubiquinone",
  "nad+": "nad",
  "vitamin c": "ascorbic acid",
  "vitamin d": "cholecalciferol",
  "vitamin e": "alpha-tocopherol",
  "vitamin b1": "thiamine",
  "vitamin b6": "pyridoxine",
  "vitamin b12": "cyanocobalamin",
  "folic acid": "folate",
};

// Words that indicate the name is NOT a small molecule (skip lookup)
const BIOLOGIC_KEYWORDS = [
  "antibody", "mab", "umab", "zumab", "ximab", "tinib",
  "vaccine", "gene therapy", "stem cell", "car-t",
  "sirna", "antisense", "oligonucleotide",
];

function isBiologic(name: string): boolean {
  const lower = name.toLowerCase();
  return BIOLOGIC_KEYWORDS.some((kw) => lower.includes(kw));
}

function generateNameVariations(drugName: string): string[] {
  const variations: string[] = [];
  const base = drugName.trim();

  // Check known aliases first
  const lowerBase = base.toLowerCase();
  if (KNOWN_ALIASES[lowerBase]) {
    variations.push(KNOWN_ALIASES[lowerBase]);
  }
  for (const [key, val] of Object.entries(KNOWN_ALIASES)) {
    if (lowerBase.includes(key)) variations.push(val);
  }

  variations.push(base);

  // Remove parenthetical info: "Nicotinamide (Vitamin B3)" → "Nicotinamide"
  const noParens = base.replace(/\s*\(.*?\)\s*/g, "").trim();
  if (noParens !== base && noParens.length > 2) variations.push(noParens);

  // Lowercase
  if (lowerBase !== base) variations.push(lowerBase);

  // Remove hyphens: "alpha-tocopherol" → "alpha tocopherol"
  const noHyphens = base.replace(/-/g, " ").trim();
  if (noHyphens !== base) variations.push(noHyphens);

  // First word only: "Interferon beta-1a" → "Interferon"
  const firstWord = base.split(/[\s-]/)[0];
  if (firstWord.length > 3 && firstWord !== base) variations.push(firstWord);

  // Remove trailing numbers/codes: "SLS-005" → "SLS", "Drug-123A" → "Drug"
  const noDashes = base.replace(/-\d+[A-Z]?$/i, "").trim();
  if (noDashes !== base && noDashes.length > 2) variations.push(noDashes);

  // Remove "hydrochloride", "sodium", "acetate" etc. (salt forms)
  const noSalt = base.replace(/\s+(hydrochloride|hcl|sodium|potassium|acetate|sulfate|maleate|fumarate|tartrate|mesylate|besylate|citrate|succinate|phosphate|calcium|dihydrate|monohydrate)$/i, "").trim();
  if (noSalt !== base && noSalt.length > 2) variations.push(noSalt);

  // Remove "di-", "tri-" prefix for some compounds
  const noPrefix = base.replace(/^(di|tri|mono|poly)-?/i, "").trim();
  if (noPrefix !== base && noPrefix.length > 3) variations.push(noPrefix);

  // Take everything before " - " or " / "
  const beforeDash = base.split(/\s*[-\/]\s*/)[0].trim();
  if (beforeDash !== base && beforeDash.length > 3) variations.push(beforeDash);

  // Take everything before a comma
  const beforeComma = base.split(",")[0].trim();
  if (beforeComma !== base && beforeComma.length > 3) variations.push(beforeComma);

  return [...new Set(variations)].filter((v) => v.length > 1);
}

async function fetchCIDByName(name: string): Promise<number | null> {
  try {
    const resp = await fetch(
      `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/${encodeURIComponent(name)}/cids/JSON`
    );
    if (!resp.ok) return null;
    const data = await resp.json();
    return data?.IdentifierList?.CID?.[0] ?? null;
  } catch {
    return null;
  }
}

// PubChem autocomplete is much more forgiving with names
async function fetchCIDBySearch(name: string): Promise<number | null> {
  try {
    const resp = await fetch(
      `https://pubchem.ncbi.nlm.nih.gov/rest/autocomplete/compound/${encodeURIComponent(name)}/JSON?limit=3`
    );
    if (!resp.ok) return null;
    const data = await resp.json();
    const suggestions = data?.dictionary_terms?.compound;
    if (!suggestions || suggestions.length === 0) return null;
    // Use the first autocomplete suggestion as the canonical name
    return await fetchCIDByName(suggestions[0]);
  } catch {
    return null;
  }
}

async function fetchCID(drugName: string): Promise<number | null> {
  // Skip expensive lookups for biologics
  if (isBiologic(drugName)) return null;

  const names = generateNameVariations(drugName);

  // Phase 1: Try exact name matches (fast)
  for (const n of names) {
    const cid = await fetchCIDByName(n);
    if (cid) return cid;
  }

  // Phase 2: Try PubChem autocomplete search (more forgiving)
  for (const n of names.slice(0, 3)) {
    const cid = await fetchCIDBySearch(n);
    if (cid) return cid;
  }

  return null;
}

async function fetchMolData(cid: number): Promise<{ data: string; format: string } | null> {
  const urls = [
    { url: `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/${cid}/SDF?record_type=3d`, fmt: "sdf" },
    { url: `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/${cid}/SDF?record_type=2d`, fmt: "sdf" },
  ];

  for (const { url, fmt } of urls) {
    try {
      const resp = await fetch(url);
      if (!resp.ok) continue;
      const text = await resp.text();
      if (text.length > 100) return { data: text, format: fmt };
    } catch { /* try next */ }
  }
  return null;
}

// Inline SVG of a generic molecule for the fallback
function MoleculeFallbackIcon({ size = 64, className = "" }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" className={className}>
      <circle cx="32" cy="20" r="6" fill="currentColor" opacity="0.25" />
      <circle cx="18" cy="40" r="5" fill="currentColor" opacity="0.2" />
      <circle cx="46" cy="40" r="5" fill="currentColor" opacity="0.2" />
      <circle cx="32" cy="52" r="4" fill="currentColor" opacity="0.15" />
      <line x1="32" y1="26" x2="20" y2="36" stroke="currentColor" strokeWidth="1.5" opacity="0.2" />
      <line x1="32" y1="26" x2="44" y2="36" stroke="currentColor" strokeWidth="1.5" opacity="0.2" />
      <line x1="20" y1="44" x2="30" y2="50" stroke="currentColor" strokeWidth="1.5" opacity="0.15" />
      <line x1="44" y1="44" x2="34" y2="50" stroke="currentColor" strokeWidth="1.5" opacity="0.15" />
    </svg>
  );
}

export default function MoleculeViewer({
  drugName,
  size = { width: 220, height: 220 },
  delay = 0,
}: MoleculeViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const viewerRef = useRef<any>(null);
  const [status, setStatus] = useState<"loading" | "3d" | "none">("loading");

  useEffect(() => {
    let cancelled = false;

    const init = async () => {
      if (delay > 0) await new Promise((r) => setTimeout(r, delay));
      if (cancelled) return;

      const cid = await fetchCID(drugName);
      if (cancelled) return;
      if (!cid) { setStatus("none"); return; }

      await load3DmolScript();
      if (cancelled) return;
      if (!window.$3Dmol || !containerRef.current) { setStatus("none"); return; }

      const mol = await fetchMolData(cid);
      if (cancelled || !containerRef.current) return;
      if (!mol) { setStatus("none"); return; }

      try {
        if (viewerRef.current) {
          try { viewerRef.current.clear(); } catch { /* ok */ }
        }
        containerRef.current.innerHTML = "";
        const viewer = window.$3Dmol.createViewer(containerRef.current, {
          backgroundColor: "0xf8f8fa",
          antialias: true,
        });
        viewer.addModel(mol.data, mol.format);
        viewer.setStyle({}, {
          stick: { radius: 0.11, colorscheme: "Jmol" },
          sphere: { scale: 0.25, colorscheme: "Jmol" },
        });
        viewer.zoomTo();
        viewer.spin("y", 0.4);
        viewer.render();
        viewerRef.current = viewer;
        setStatus("3d");
      } catch {
        setStatus("none");
      }
    };

    init();
    return () => {
      cancelled = true;
      if (viewerRef.current) {
        try { viewerRef.current.clear(); } catch { /* ok */ }
        viewerRef.current = null;
      }
    };
  }, [drugName, delay]);

  return (
    <div
      className="relative flex items-center justify-center overflow-hidden rounded-xl bg-[#f8f8fa]"
      style={{ width: size.width, height: size.height }}
    >
      <div
        ref={containerRef}
        className="absolute inset-0"
        style={{ display: status === "3d" ? "block" : "none" }}
      />

      {status === "loading" && (
        <div className="flex flex-col items-center justify-center">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-border border-t-purple" />
          <p className="mt-2 text-[9px] text-muted/50">Loading structure...</p>
        </div>
      )}

      {status === "none" && (
        <div className="flex flex-col items-center justify-center text-center px-3 text-purple/40">
          <MoleculeFallbackIcon size={72} />
          <p className="mt-1 text-[10px] font-medium text-muted/50">{drugName}</p>
        </div>
      )}
    </div>
  );
}
