"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTryOn } from "@/lib/TryOnContext";

const SINGLE_STAGES = [
  { label: "Removing background", duration: 8000 },
  { label: "Analysing your pose", duration: 10000 },
  { label: "Generating your look", duration: null },
];

const OUTFIT_STAGES = [
  { label: "Processing garments", duration: 10000 },
  { label: "Analysing your pose", duration: 10000 },
  { label: "Generating top garment", duration: 30000 },
  { label: "Generating bottom garment", duration: null },
];

export default function ProcessingPage() {
  const router = useRouter();
  const { isProcessing, resultImageUrl, mode, globalError, setGlobalError } = useTryOn();

  const stages = mode === "complete_outfit" ? OUTFIT_STAGES : SINGLE_STAGES;

  // When result is ready, navigate to result page
  useEffect(() => {
    if (!isProcessing && !globalError) {
      if (resultImageUrl) {
        router.push("/result");
      } else {
        // If we somehow ended up here not processing and no result, go back
        router.push("/upload");
      }
    }
  }, [isProcessing, resultImageUrl, router, globalError]);

  if (globalError) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-screen px-6 py-12">
        <div className="max-w-md w-full bg-red-50 border border-red-200 text-red-800 p-6 rounded-2xl shadow-sm text-center">
          <svg className="w-12 h-12 text-red-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h2 className="text-xl font-semibold mb-2">Something went wrong</h2>
          <p className="mb-6">{globalError}</p>
          <button
            onClick={() => {
              setGlobalError(null);
              router.push("/upload");
            }}
            className="px-6 py-3 bg-[#4D0E13] text-[#EEE4DA] font-semibold rounded-full hover:bg-[#3A0A0E] transition-all"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col items-center justify-center min-h-screen px-6 py-12 animate-in fade-in duration-700">
      {/* Top progress bar */}
      <div className="fixed top-0 left-0 right-0 h-1 bg-[#4D0E13]/10">
        <div className="h-1 bg-[#4D0E13] animate-progress-bar" />
      </div>

      <div className="flex flex-col items-center gap-8 max-w-sm text-center">
        {/* Spinner */}
        <div className="relative w-24 h-24">
          <div className="absolute inset-0 rounded-full border-4 border-[#4D0E13]/10" />
          <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-[#4D0E13] animate-spin" />
          <div className="absolute inset-2 rounded-full border-4 border-transparent border-t-[#4D0E13]/40 animate-spin-slow" />
        </div>

        {/* Stage labels */}
        <div className="flex flex-col gap-3 w-full">
          {stages.map((stage, i) => (
            <StageLabel key={stage.label} label={stage.label} index={i} />
          ))}
        </div>

        <p className="text-sm text-[#171717]/40">
          This may take up to 2 minutes on first run while the AI model warms up.
        </p>
      </div>
    </div>
  );
}

function StageLabel({ label, index }: { label: string; index: number }) {
  return (
    <div
      className="flex items-center gap-3 px-5 py-3 rounded-xl bg-white/60 backdrop-blur-sm border border-[#4D0E13]/10 text-sm text-[#171717]/70 animate-in fade-in slide-in-from-left-3 duration-700"
      style={{ animationDelay: `${index * 0.8}s`, animationFillMode: "both" }}
    >
      <span className="w-2 h-2 rounded-full bg-[#4D0E13]/40 animate-pulse flex-shrink-0" />
      {label}...
    </div>
  );
}
