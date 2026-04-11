"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { X, Loader2, Copy, Check, FileText } from "lucide-react";
import { API_BASE } from "@/lib/config";

interface GrantAbstractModalProps {
  drugName: string;
  diseaseName: string;
  onClose: () => void;
}

export default function GrantAbstractModal({ drugName, diseaseName, onClose }: GrantAbstractModalProps) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    fetch(
      `${API_BASE}/api/grant-abstract/${encodeURIComponent(drugName)}?disease=${encodeURIComponent(diseaseName)}`
    )
      .then((r) => r.json())
      .then((d) => {
        if (cancelled) return;
        setText(d.abstract || "");
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setError(true);
        setLoading(false);
      });

    return () => { cancelled = true; };
  }, [drugName, diseaseName]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* fallback: select all */
    }
  };

  return (
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-black/30 backdrop-blur-sm"
        onClick={onClose}
      />
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        className="fixed inset-x-4 top-[10%] z-50 mx-auto max-w-2xl overflow-hidden rounded-2xl border border-border bg-white shadow-2xl sm:inset-x-auto"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <div className="flex items-center gap-2">
            <FileText size={16} className="text-purple" />
            <div>
              <h3 className="text-sm font-bold text-foreground">Grant Abstract Draft</h3>
              <p className="text-[10px] text-muted">
                NIH R21 Specific Aims — {drugName} for {diseaseName}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-muted hover:bg-subtle hover:text-foreground"
          >
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="max-h-[60vh] overflow-y-auto p-6">
          {loading && (
            <div className="flex flex-col items-center justify-center py-16">
              <Loader2 size={24} className="animate-spin text-purple" />
              <p className="mt-3 text-xs text-muted">
                Drafting grant abstract from evidence...
              </p>
              <p className="mt-1 text-[10px] text-muted/50">
                This may take 10-15 seconds
              </p>
            </div>
          )}

          {error && !loading && (
            <div className="py-16 text-center">
              <p className="text-sm text-red">Failed to generate abstract.</p>
              <p className="mt-1 text-xs text-muted">Check that the backend is running.</p>
            </div>
          )}

          {!loading && !error && (
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={16}
              className="w-full resize-y rounded-xl border border-border bg-subtle/30 p-4 font-serif text-sm leading-relaxed text-foreground focus:border-purple/30 focus:outline-none"
            />
          )}
        </div>

        {/* Footer */}
        {!loading && !error && (
          <div className="flex items-center justify-between border-t border-border px-6 py-3">
            <p className="text-[9px] text-muted/50">
              AI-generated draft — review and edit before submitting
            </p>
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 rounded-lg bg-foreground px-4 py-2 text-xs font-medium text-white transition-opacity hover:opacity-85"
            >
              {copied ? <Check size={12} /> : <Copy size={12} />}
              {copied ? "Copied!" : "Copy to Clipboard"}
            </button>
          </div>
        )}
      </motion.div>
    </>
  );
}
