"use client";

import { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float, OrbitControls } from "@react-three/drei";
import * as THREE from "three";

const COLORS = ["#7c3aed", "#3b82f6", "#10b981", "#f59e0b", "#ec4899"];

function seededRandom(seed: number) {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

const rng = seededRandom(42);

function generateAtoms() {
  const nodes: { pos: [number, number, number]; color: string; r: number }[] = [];
  const rand = (min: number, max: number) => min + rng() * (max - min);
  for (let i = 0; i < 60; i++) {
    nodes.push({
      pos: [rand(-3.5, 3.5), rand(-3, 3), rand(-3, 3)],
      color: COLORS[Math.floor(rng() * COLORS.length)],
      r: rand(0.08, 0.2),
    });
  }
  return nodes;
}

function generateBonds(atoms: ReturnType<typeof generateAtoms>) {
  const b: { start: [number, number, number]; end: [number, number, number] }[] = [];
  for (let i = 0; i < atoms.length; i++) {
    for (let j = i + 1; j < atoms.length; j++) {
      const d = Math.hypot(
        atoms[i].pos[0] - atoms[j].pos[0],
        atoms[i].pos[1] - atoms[j].pos[1],
        atoms[i].pos[2] - atoms[j].pos[2]
      );
      if (d < 1.4) b.push({ start: atoms[i].pos, end: atoms[j].pos });
    }
  }
  return b;
}

function generateParticlePositions(count: number) {
  const arr = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    arr[i * 3] = (rng() - 0.5) * 16;
    arr[i * 3 + 1] = (rng() - 0.5) * 12;
    arr[i * 3 + 2] = (rng() - 0.5) * 10;
  }
  return arr;
}

const ATOM_DATA = generateAtoms();
const BOND_DATA = generateBonds(ATOM_DATA);
const PARTICLE_POSITIONS = generateParticlePositions(300);
const ATOM_SPEEDS = ATOM_DATA.map(() => 0.3 + rng() * 0.5);
const ATOM_OFFSETS = ATOM_DATA.map(() => rng() * Math.PI * 2);

function Atom({ index, position, color, radius }: { index: number; position: [number, number, number]; color: string; radius: number }) {
  const ref = useRef<THREE.Mesh>(null!);
  const speed = ATOM_SPEEDS[index];
  const offset = ATOM_OFFSETS[index];

  useFrame(({ clock }) => {
    ref.current.position.y = position[1] + Math.sin(clock.getElapsedTime() * speed + offset) * 0.2;
  });

  return (
    <mesh ref={ref} position={position}>
      <sphereGeometry args={[radius, 32, 32]} />
      <meshStandardMaterial
        color={color}
        roughness={0.2}
        metalness={0.7}
        transparent
        opacity={0.9}
      />
    </mesh>
  );
}

function Bond({ start, end }: { start: [number, number, number]; end: [number, number, number] }) {
  const s = new THREE.Vector3(...start);
  const e = new THREE.Vector3(...end);
  const mid = s.clone().add(e).multiplyScalar(0.5);
  const dir = new THREE.Vector3().subVectors(e, s);
  const len = dir.length();
  const q = new THREE.Quaternion().setFromUnitVectors(
    new THREE.Vector3(0, 1, 0),
    dir.normalize()
  );

  return (
    <mesh position={mid} quaternion={q}>
      <cylinderGeometry args={[0.02, 0.02, len, 8]} />
      <meshStandardMaterial color="#d4d4d8" transparent opacity={0.35} />
    </mesh>
  );
}

function MoleculeCluster() {
  const group = useRef<THREE.Group>(null!);

  useFrame(({ clock }) => {
    group.current.rotation.y = clock.getElapsedTime() * 0.06;
  });

  return (
    <Float speed={1.2} rotationIntensity={0.15} floatIntensity={0.2}>
      <group ref={group}>
        {ATOM_DATA.map((a, i) => (
          <Atom key={`a${i}`} index={i} position={a.pos} color={a.color} radius={a.r} />
        ))}
        {BOND_DATA.map((b, i) => (
          <Bond key={`b${i}`} start={b.start} end={b.end} />
        ))}
      </group>
    </Float>
  );
}

function Particles() {
  const ref = useRef<THREE.Points>(null!);

  useFrame(({ clock }) => {
    ref.current.rotation.y = clock.getElapsedTime() * 0.015;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[PARTICLE_POSITIONS, 3]} />
      </bufferGeometry>
      <pointsMaterial size={0.025} color="#a78bfa" transparent opacity={0.4} sizeAttenuation />
    </points>
  );
}

export default function HeroScene({ className }: { className?: string }) {
  return (
    <div className={className}>
      <Canvas
        camera={{ position: [0, 0, 9], fov: 50 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true }}
        style={{ background: "transparent" }}
      >
        <ambientLight intensity={0.5} />
        <directionalLight position={[5, 5, 5]} intensity={0.9} />
        <directionalLight position={[-3, -2, -5]} intensity={0.3} color="#a78bfa" />
        <pointLight position={[0, 0, 4]} intensity={0.4} color="#7c3aed" />
        <MoleculeCluster />
        <Particles />
        <OrbitControls
          enableZoom={false}
          enablePan={false}
          autoRotate
          autoRotateSpeed={0.4}
          maxPolarAngle={Math.PI * 0.75}
          minPolarAngle={Math.PI * 0.25}
        />
      </Canvas>
    </div>
  );
}
