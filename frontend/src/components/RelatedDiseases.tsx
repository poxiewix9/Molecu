"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Dna, ArrowRight, Loader2 } from "lucide-react";
import { API_BASE } from "@/lib/config";

interface RelatedDisease {
  disease_name: string;
  efo_id: string;
  shared_targets: string[];
  shared_count: number;
}

interface RelatedDiseasesProps {
  diseaseName: string;
  onSelectDisease: (name: string) => void;
}

export default function RelatedDiseases({ diseaseName, onSelectDisease }: RelatedDiseasesProps) {
  const [related, setRelated] = useState<RelatedDisease[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    fetch(`${API_BASE}/api/related-diseases/${encodeURIComponent(diseaseName)}`)
      .then((r) => r.json())
      .then((d) => {
        if (cancelled) return;
        setRelated(d.related || []);
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setError(true);
        setLoading(false);
      });

    return () => { cancelled = true; };
  }, [diseaseName]);

  if (error || (!loading && related.length === 0)) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-8"
    >
      <div className="flex items-center gap-2 mb-3">
        <Dna size={14} className="text-purple" />
        <p className="text-[10px] font-semibold uppercase tracking-widest text-purple">
          Related diseases — shared protein targets
        </p>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 py-4">
          <Loader2 size={14} className="animate-spin text-muted" />
          <span className="text-xs text-muted">Finding diseases with shared targets...</span>
        </div>
      ) : (
        <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin">
          {related.map((d, i) => (
            <motion.button
              key={d.efo_id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              onClick={() => onSelectDisease(d.disease_name)}
              className="group flex-shrink-0 rounded-xl border border-border bg-card p-4 text-left transition-all hover:border-purple/30 hover:shadow-md"
              style={{ minWidth: 200, maxWidth: 260 }}
            >
              <div className="flex items-start justify-between">
                <h4 className="text-sm font-semibold text-foreground leading-snug line-clamp-2">
                  {d.disease_name}
                </h4>
                <ArrowRight size={14} className="mt-0.5 shrink-0 text-muted/30 transition-colors group-hover:text-purple" />
              </div>

              <div className="mt-2 flex items-center gap-1.5">
                <span className="rounded-full bg-purple/10 px-2 py-0.5 text-[10px] font-bold text-purple">
                  {d.shared_count} shared target{d.shared_count !== 1 ? "s" : ""}
                </span>
              </div>

              <div className="mt-2 flex flex-wrap gap-1">
                {d.shared_targets.map((gene) => (
                  <span
                    key={gene}
                    className="rounded-md bg-subtle px-1.5 py-0.5 text-[9px] font-medium text-muted"
                  >
                    {gene}
                  </span>
                ))}
              </div>

              <p className="mt-2 text-[9px] text-muted/50 group-hover:text-purple/50">
                Click to search this disease
              </p>
            </motion.button>
          ))}
        </div>
      )}
    </motion.div>
  );
}
