"use client";

import {
  useState,
  useCallback,
  useRef,
  useMemo,
  useEffect,
  useReducer,
} from "react";
import { Canvas, ThreeEvent, useThree } from "@react-three/fiber";
import { OrbitControls, Html } from "@react-three/drei";
import * as THREE from "three";
import { motion } from "framer-motion";
import {
  X,
  Undo2,
  Redo2,
  MousePointer2,
  Plus,
  Eraser,
  Link2,
  Download,
  Loader2,
  PlusCircle,
} from "lucide-react";

/* ─── Types ─── */

interface MolAtom {
  id: number;
  element: string;
  x: number;
  y: number;
  z: number;
}

interface MolBond {
  id: number;
  from: number;
  to: number;
  type: number;
}

interface MolState {
  atoms: MolAtom[];
  bonds: MolBond[];
  nextAtomId: number;
  nextBondId: number;
}

type Tool = "select" | "add" | "bond" | "delete";

/* ─── Constants ─── */

const ELEMENTS = ["C", "N", "O", "S", "H", "F", "Cl", "P", "Br"] as const;

const EL_COLOR: Record<string, string> = {
  C: "#555555", N: "#3050F8", O: "#FF0D0D", H: "#cccccc",
  S: "#c4a000", P: "#FF8000", F: "#6fbf4a", Cl: "#1eb01e",
  Br: "#A62929", _: "#FF69B4",
};

const EL_RADIUS: Record<string, number> = {
  C: 0.4, N: 0.38, O: 0.35, H: 0.25, S: 0.5,
  P: 0.45, F: 0.3, Cl: 0.45, Br: 0.5, _: 0.4,
};

const BOND_LEN = 1.5;
const EMPTY: MolState = { atoms: [], bonds: [], nextAtomId: 1, nextBondId: 1 };

/* ─── SDF Parser ─── */

function parseSDF(text: string): MolState {
  const lines = text.split("\n");
  let ci = 3;
  for (let i = 0; i < Math.min(lines.length, 10); i++) {
    if (/V[23]000/.test(lines[i])) { ci = i; break; }
  }
  const cl = lines[ci] || "";
  const ac = parseInt(cl.substring(0, 3).trim()) || 0;
  const bc = parseInt(cl.substring(3, 6).trim()) || 0;

  const atoms: MolAtom[] = [];
  for (let i = 0; i < ac; i++) {
    const l = lines[ci + 1 + i];
    if (!l) continue;
    atoms.push({
      id: i + 1,
      element: l.substring(31, 34).trim() || "C",
      x: parseFloat(l.substring(0, 10)) || 0,
      y: parseFloat(l.substring(10, 20)) || 0,
      z: parseFloat(l.substring(20, 30)) || 0,
    });
  }

  const bonds: MolBond[] = [];
  for (let i = 0; i < bc; i++) {
    const l = lines[ci + 1 + ac + i];
    if (!l) continue;
    bonds.push({
      id: i + 1,
      from: parseInt(l.substring(0, 3).trim()) || 0,
      to: parseInt(l.substring(3, 6).trim()) || 0,
      type: parseInt(l.substring(6, 9).trim()) || 1,
    });
  }

  return { atoms, bonds, nextAtomId: ac + 1, nextBondId: bc + 1 };
}

/* ─── Utility ─── */

function centerMol(s: MolState): MolState {
  if (!s.atoms.length) return s;
  const n = s.atoms.length;
  const cx = s.atoms.reduce((a, b) => a + b.x, 0) / n;
  const cy = s.atoms.reduce((a, b) => a + b.y, 0) / n;
  const cz = s.atoms.reduce((a, b) => a + b.z, 0) / n;
  return { ...s, atoms: s.atoms.map(a => ({ ...a, x: a.x - cx, y: a.y - cy, z: a.z - cz })) };
}

function findFreePos(atom: MolAtom, bonds: MolBond[], atoms: MolAtom[]): [number, number, number] {
  const c = new THREE.Vector3(atom.x, atom.y, atom.z);
  const nIds = bonds
    .filter(b => b.from === atom.id || b.to === atom.id)
    .map(b => (b.from === atom.id ? b.to : b.from));
  const ns = nIds.map(id => atoms.find(a => a.id === id)).filter(Boolean) as MolAtom[];

  if (!ns.length) return [c.x + BOND_LEN, c.y, c.z];

  const avg = new THREE.Vector3();
  ns.forEach(n => avg.add(new THREE.Vector3(n.x - c.x, n.y - c.y, n.z - c.z).normalize()));

  let dir: THREE.Vector3;
  if (avg.length() < 0.01) {
    const ref = new THREE.Vector3(ns[0].x - c.x, ns[0].y - c.y, ns[0].z - c.z).normalize();
    const up = Math.abs(ref.y) < 0.99 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(1, 0, 0);
    dir = new THREE.Vector3().crossVectors(ref, up).normalize();
  } else {
    dir = avg.normalize().negate();
  }
  return c.clone().add(dir.multiplyScalar(BOND_LEN)).toArray() as [number, number, number];
}

function molecularFormula(atoms: MolAtom[]): string {
  const c: Record<string, number> = {};
  atoms.forEach(a => { c[a.element] = (c[a.element] || 0) + 1; });
  const p: string[] = [];
  if (c.C) { p.push(`C${c.C > 1 ? c.C : ""}`); delete c.C; }
  if (c.H) { p.push(`H${c.H > 1 ? c.H : ""}`); delete c.H; }
  Object.keys(c).sort().forEach(e => p.push(`${e}${c[e] > 1 ? c[e] : ""}`));
  return p.join("") || "—";
}

function toSDF(atoms: MolAtom[], bonds: MolBond[]): string {
  const l = ["Modified Molecule", "  PharmaSynapse 3D Editor", ""];
  l.push(`${String(atoms.length).padStart(3)}${String(bonds.length).padStart(3)}  0  0  0  0  0  0  0  0999 V2000`);
  const m = new Map(atoms.map((a, i) => [a.id, i + 1]));
  atoms.forEach(a => l.push(
    `${a.x.toFixed(4).padStart(10)}${a.y.toFixed(4).padStart(10)}${a.z.toFixed(4).padStart(10)} ${a.element.padEnd(3)} 0  0  0  0  0  0  0  0  0  0  0  0`,
  ));
  bonds.forEach(b => l.push(
    `${String(m.get(b.from) || 0).padStart(3)}${String(m.get(b.to) || 0).padStart(3)}${String(b.type).padStart(3)}  0`,
  ));
  l.push("M  END", "$$$$");
  return l.join("\n");
}

/* ─── Reducer ─── */

interface Hist { past: MolState[]; present: MolState; future: MolState[] }

type Act =
  | { type: "INIT"; state: MolState }
  | { type: "ADD_BONDED"; target: number; el: string }
  | { type: "ADD_ALONE"; el: string }
  | { type: "BOND"; from: number; to: number }
  | { type: "DEL_ATOM"; id: number }
  | { type: "UNDO" }
  | { type: "REDO" };

function push(h: Hist, next: MolState): Hist {
  return { past: [...h.past, h.present], present: next, future: [] };
}

function reducer(h: Hist, a: Act): Hist {
  switch (a.type) {
    case "INIT":
      return { past: [], present: a.state, future: [] };
    case "ADD_BONDED": {
      const t = h.present.atoms.find(x => x.id === a.target);
      if (!t) return h;
      const [x, y, z] = findFreePos(t, h.present.bonds, h.present.atoms);
      const na: MolAtom = { id: h.present.nextAtomId, element: a.el, x, y, z };
      const nb: MolBond = { id: h.present.nextBondId, from: a.target, to: na.id, type: 1 };
      return push(h, {
        atoms: [...h.present.atoms, na],
        bonds: [...h.present.bonds, nb],
        nextAtomId: h.present.nextAtomId + 1,
        nextBondId: h.present.nextBondId + 1,
      });
    }
    case "ADD_ALONE": {
      const spread = h.present.atoms.length * 2;
      const na: MolAtom = { id: h.present.nextAtomId, element: a.el, x: spread, y: 0, z: 0 };
      return push(h, { ...h.present, atoms: [...h.present.atoms, na], nextAtomId: h.present.nextAtomId + 1 });
    }
    case "BOND": {
      if (a.from === a.to) return h;
      if (h.present.bonds.some(b => (b.from === a.from && b.to === a.to) || (b.from === a.to && b.to === a.from))) return h;
      return push(h, {
        ...h.present,
        bonds: [...h.present.bonds, { id: h.present.nextBondId, from: a.from, to: a.to, type: 1 }],
        nextBondId: h.present.nextBondId + 1,
      });
    }
    case "DEL_ATOM":
      return push(h, {
        ...h.present,
        atoms: h.present.atoms.filter(x => x.id !== a.id),
        bonds: h.present.bonds.filter(b => b.from !== a.id && b.to !== a.id),
      });
    case "UNDO":
      if (!h.past.length) return h;
      return { past: h.past.slice(0, -1), present: h.past[h.past.length - 1], future: [h.present, ...h.future] };
    case "REDO":
      if (!h.future.length) return h;
      return { past: [...h.past, h.present], present: h.future[0], future: h.future.slice(1) };
    default:
      return h;
  }
}

/* ─── 3D: Bond ─── */

function BondCyl({ bond, atoms }: { bond: MolBond; atoms: MolAtom[] }) {
  const a = atoms.find(x => x.id === bond.from);
  const b = atoms.find(x => x.id === bond.to);

  const geo = useMemo(() => {
    if (!a || !b) return null;
    const pA = new THREE.Vector3(a.x, a.y, a.z);
    const pB = new THREE.Vector3(b.x, b.y, b.z);
    const mid = pA.clone().add(pB).multiplyScalar(0.5);
    const dir = pB.clone().sub(pA);
    const len = dir.length();
    if (len < 0.001) return null;
    dir.normalize();

    const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
    const e = new THREE.Euler().setFromQuaternion(q);
    const up = Math.abs(dir.y) > 0.99 ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 1, 0);
    const perp = new THREE.Vector3().crossVectors(dir, up).normalize();

    const r = 0.06;
    const off = 0.12;
    let positions: THREE.Vector3[];
    if (bond.type === 2) {
      positions = [mid.clone().addScaledVector(perp, off), mid.clone().addScaledVector(perp, -off)];
    } else if (bond.type >= 3) {
      positions = [mid.clone(), mid.clone().addScaledVector(perp, off * 1.3), mid.clone().addScaledVector(perp, -off * 1.3)];
    } else {
      positions = [mid];
    }
    return { positions, euler: [e.x, e.y, e.z] as [number, number, number], len, r };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [a?.x, a?.y, a?.z, b?.x, b?.y, b?.z, bond.type]);

  if (!geo) return null;
  return (
    <group>
      {geo.positions.map((p, i) => (
        <mesh key={i} position={p.toArray() as [number, number, number]} rotation={geo.euler}>
          <cylinderGeometry args={[geo.r, geo.r, geo.len, 8]} />
          <meshPhongMaterial color="#b0b0b0" shininess={30} />
        </mesh>
      ))}
    </group>
  );
}

/* ─── 3D: Camera fit ─── */

function CamFit({ atoms }: { atoms: MolAtom[] }) {
  const { camera } = useThree();
  const done = useRef(false);
  useEffect(() => {
    if (atoms.length && !done.current) {
      done.current = true;
      const maxR = atoms.reduce((m, a) => Math.max(m, Math.sqrt(a.x ** 2 + a.y ** 2 + a.z ** 2)), 0);
      camera.position.set(0, 0, Math.max(maxR * 2.5, 12));
    }
  }, [atoms, camera]);
  return null;
}

/* ─── 3D: Scene ─── */

function Scene({
  state, tool, element, selectedAtom, setSelectedAtom, bondStart, setBondStart, dispatch,
}: {
  state: MolState; tool: Tool; element: string;
  selectedAtom: number | null; setSelectedAtom: (v: number | null) => void;
  bondStart: number | null; setBondStart: (v: number | null) => void;
  dispatch: React.Dispatch<Act>;
}) {
  const [hovered, setHovered] = useState<number | null>(null);

  const onAtom = useCallback((atom: MolAtom, e: ThreeEvent<PointerEvent>) => {
    e.stopPropagation();
    switch (tool) {
      case "select":
        setSelectedAtom(selectedAtom === atom.id ? null : atom.id);
        break;
      case "add":
        dispatch({ type: "ADD_BONDED", target: atom.id, el: element });
        break;
      case "bond":
        if (bondStart === null) setBondStart(atom.id);
        else { dispatch({ type: "BOND", from: bondStart, to: atom.id }); setBondStart(null); }
        break;
      case "delete":
        dispatch({ type: "DEL_ATOM", id: atom.id }); setSelectedAtom(null);
        break;
    }
  }, [tool, element, bondStart, selectedAtom, dispatch, setSelectedAtom, setBondStart]);

  return (
    <>
      <color attach="background" args={["#fafafa"]} />
      <ambientLight intensity={0.7} />
      <directionalLight position={[10, 10, 10]} intensity={0.9} />
      <directionalLight position={[-5, -5, 5]} intensity={0.3} />

      {state.atoms.map(atom => {
        const col = EL_COLOR[atom.element] || EL_COLOR._;
        const r = EL_RADIUS[atom.element] || EL_RADIUS._;
        const sel = selectedAtom === atom.id;
        const bs = bondStart === atom.id;
        const hov = hovered === atom.id;

        return (
          <mesh
            key={atom.id}
            position={[atom.x, atom.y, atom.z]}
            onPointerDown={e => onAtom(atom, e)}
            onPointerEnter={e => { e.stopPropagation(); setHovered(atom.id); }}
            onPointerLeave={() => setHovered(null)}
          >
            <sphereGeometry args={[r * (hov ? 1.12 : 1), 32, 32]} />
            <meshPhongMaterial
              color={bs ? "#2563eb" : sel ? "#7c3aed" : col}
              emissive={bs ? "#2563eb" : sel ? "#7c3aed" : hov ? col : "#000"}
              emissiveIntensity={bs || sel ? 0.25 : hov ? 0.15 : 0}
              shininess={60}
            />
          </mesh>
        );
      })}

      {state.bonds.map(b => <BondCyl key={b.id} bond={b} atoms={state.atoms} />)}

      {hovered != null && (() => {
        const at = state.atoms.find(a => a.id === hovered);
        if (!at) return null;
        const r = EL_RADIUS[at.element] || EL_RADIUS._;
        return (
          <Html position={[at.x, at.y + r + 0.4, at.z]} center>
            <div className="bg-white/95 border border-border text-foreground text-[10px] px-1.5 py-0.5 rounded shadow-sm pointer-events-none font-medium">
              {at.element}
            </div>
          </Html>
        );
      })()}

      <CamFit atoms={state.atoms} />
      <OrbitControls enableDamping dampingFactor={0.08} />
    </>
  );
}

/* ─── Main ─── */

interface Props { drugName: string; onClose: () => void }

export default function MoleculeEditor({ drugName, onClose }: Props) {
  const [hist, dispatch] = useReducer(reducer, { past: [], present: EMPTY, future: [] });
  const [loading, setLoading] = useState(true);
  const [tool, setTool] = useState<Tool>("add");
  const [element, setElement] = useState("C");
  const [selectedAtom, setSelectedAtom] = useState<number | null>(null);
  const [bondStart, setBondStart] = useState<number | null>(null);

  useEffect(() => {
    let cancel = false;
    (async () => {
      setLoading(true);
      try {
        const enc = encodeURIComponent(drugName);
        let r = await fetch(`https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/${enc}/SDF?record_type=3d`);
        if (!r.ok) r = await fetch(`https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/${enc}/SDF`);
        if (r.ok && !cancel) dispatch({ type: "INIT", state: centerMol(parseSDF(await r.text())) });
      } catch { /* empty */ }
      if (!cancel) setLoading(false);
    })();
    return () => { cancel = true; };
  }, [drugName]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "z" && !e.shiftKey) { e.preventDefault(); dispatch({ type: "UNDO" }); }
      if ((e.metaKey || e.ctrlKey) && (e.key === "y" || (e.key === "z" && e.shiftKey))) { e.preventDefault(); dispatch({ type: "REDO" }); }
      if (e.key === "Escape") { setBondStart(null); setSelectedAtom(null); onClose(); }
      if ((e.key === "Delete" || e.key === "Backspace") && selectedAtom !== null) {
        dispatch({ type: "DEL_ATOM", id: selectedAtom }); setSelectedAtom(null);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [selectedAtom, onClose]);

  const handleExport = useCallback(() => {
    const sdf = toSDF(hist.present.atoms, hist.present.bonds);
    const blob = new Blob([sdf], { type: "chemical/x-mdl-sdfile" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${drugName.replace(/\s+/g, "_")}_modified.sdf`;
    a.click();
    URL.revokeObjectURL(url);
  }, [hist.present, drugName]);

  const state = hist.present;
  const canUndo = hist.past.length > 0;
  const canRedo = hist.future.length > 0;

  const toolDefs: { id: Tool; icon: typeof MousePointer2; tip: string }[] = [
    { id: "select", icon: MousePointer2, tip: "Select" },
    { id: "add", icon: Plus, tip: "Add" },
    { id: "bond", icon: Link2, tip: "Bond" },
    { id: "delete", icon: Eraser, tip: "Delete" },
  ];

  return (
    <motion.div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/30 backdrop-blur-sm"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="relative bg-card rounded-2xl shadow-2xl border border-border w-[90vw] max-w-[820px] h-[80vh] max-h-[640px] flex flex-col overflow-hidden"
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        transition={{ type: "spring", duration: 0.35 }}
        onClick={e => e.stopPropagation()}
      >
        {/* ── Header ── */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-border">
          <div className="flex items-center gap-3 min-w-0">
            <span className="text-sm font-semibold text-foreground truncate">
              {drugName}
            </span>
            <span className="text-[10px] text-muted font-mono">
              {state.atoms.length} atoms · {state.bonds.length} bonds · {molecularFormula(state.atoms)}
            </span>
          </div>
          <button
            onClick={onClose}
            className="ml-3 p-1.5 rounded-lg text-muted hover:text-foreground hover:bg-subtle transition"
          >
            <X size={16} />
          </button>
        </div>

        {/* ── Toolbar strip ── */}
        <div className="flex items-center gap-1 px-4 py-2 border-b border-border bg-subtle/50 flex-wrap">
          {/* Tools */}
          {toolDefs.map(t => (
            <button
              key={t.id}
              onClick={() => { setTool(t.id); setBondStart(null); }}
              title={t.tip}
              className={`p-1.5 rounded-lg transition ${
                tool === t.id
                  ? "bg-foreground text-card shadow-sm"
                  : "text-muted hover:bg-subtle hover:text-foreground"
              }`}
            >
              <t.icon size={15} />
            </button>
          ))}

          <div className="w-px h-5 bg-border mx-1" />

          {/* Elements */}
          {ELEMENTS.map(el => (
            <button
              key={el}
              onClick={() => setElement(el)}
              title={el}
              className={`w-7 h-7 rounded-md text-[11px] font-bold transition flex items-center justify-center ${
                element === el
                  ? "ring-2 ring-foreground/30 bg-white shadow-sm"
                  : "hover:bg-white/80"
              }`}
              style={{ color: EL_COLOR[el] }}
            >
              {el}
            </button>
          ))}

          <div className="w-px h-5 bg-border mx-1" />

          {/* Undo / Redo */}
          <button
            onClick={() => dispatch({ type: "UNDO" })}
            disabled={!canUndo}
            title="Undo (⌘Z)"
            className="p-1.5 rounded-lg text-muted hover:bg-subtle hover:text-foreground disabled:opacity-25 transition"
          >
            <Undo2 size={15} />
          </button>
          <button
            onClick={() => dispatch({ type: "REDO" })}
            disabled={!canRedo}
            title="Redo (⌘⇧Z)"
            className="p-1.5 rounded-lg text-muted hover:bg-subtle hover:text-foreground disabled:opacity-25 transition"
          >
            <Redo2 size={15} />
          </button>

          <div className="w-px h-5 bg-border mx-1" />

          <button
            onClick={() => dispatch({ type: "ADD_ALONE", el: element })}
            title={`Add standalone ${element}`}
            className="p-1.5 rounded-lg text-muted hover:bg-subtle hover:text-foreground transition"
          >
            <PlusCircle size={15} />
          </button>

          <button
            onClick={handleExport}
            disabled={state.atoms.length === 0}
            title="Export as .SDF"
            className="p-1.5 rounded-lg text-muted hover:bg-subtle hover:text-foreground disabled:opacity-25 transition"
          >
            <Download size={15} />
          </button>

          {/* Contextual hint */}
          <span className="ml-auto text-[10px] text-muted">
            {tool === "select" && "Click to select · Del to remove"}
            {tool === "add" && `Click atom to add ${element}`}
            {tool === "bond" && (bondStart ? "Click second atom" : "Click first atom")}
            {tool === "delete" && "Click atom to remove"}
          </span>
        </div>

        {/* ── Canvas ── */}
        <div className="flex-1 relative" style={{ cursor: tool === "select" ? "default" : "crosshair" }}>
          {loading ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <Loader2 className="animate-spin text-muted" size={24} />
            </div>
          ) : state.atoms.length === 0 ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
              <p className="text-sm text-muted">No structure found for <strong>{drugName}</strong></p>
              <button
                onClick={() => dispatch({ type: "ADD_ALONE", el: element })}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-foreground text-card text-xs font-medium hover:opacity-90 transition"
              >
                <Plus size={14} /> Start with {element}
              </button>
            </div>
          ) : (
            <Canvas camera={{ position: [0, 0, 20], fov: 50 }}>
              <Scene
                state={state} tool={tool} element={element}
                selectedAtom={selectedAtom} setSelectedAtom={setSelectedAtom}
                bondStart={bondStart} setBondStart={setBondStart}
                dispatch={dispatch}
              />
            </Canvas>
          )}

          {bondStart !== null && (
            <div className="absolute top-3 left-1/2 -translate-x-1/2 bg-blue/10 text-blue text-[11px] px-3 py-1 rounded-full border border-blue/20">
              Select second atom · <button onClick={() => setBondStart(null)} className="underline">cancel</button>
            </div>
          )}
        </div>

        {/* ── Footer hint ── */}
        <div className="px-5 py-2 border-t border-border text-[10px] text-muted flex items-center justify-between">
          <span>Scroll to zoom · Drag to rotate · Esc to close</span>
          <span>⌘Z undo · ⌘⇧Z redo</span>
        </div>
      </motion.div>
    </motion.div>
  );
}
