"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import UploadCard from "@/components/UploadCard";
import ModeSelector from "@/components/ModeSelector";
import TuckToggle from "@/components/TuckToggle";
import { useTryOn } from "@/lib/TryOnContext";
import { runTryOn } from "@/lib/api";

export default function UploadPage() {
  const router = useRouter();
  const {
    mode,
    setMode,
    personImage,
    garmentImage,
    bottomImage,
    tuckIn,
    setPersonImage,
    setGarmentImage,
    setBottomImage,
    setTuckIn,
    setResultImageUrl,
    setIsProcessing,
    setGlobalError,
  } = useTryOn();

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Clear result and processing states on mount of the upload page.
  // This solves the race condition where navigating back to upload 
  // without using 'TRY ANOTHER' keeps the old result image in state, 
  // causing '/processing' to immediately redirect to `/result` showing the old image.
  useEffect(() => {
    setResultImageUrl(null);
    setIsProcessing(false);
    setGlobalError(null);
  }, [setResultImageUrl, setIsProcessing, setGlobalError]);

  const canGenerate =
    mode === "single"
      ? !!personImage && !!garmentImage
      : !!personImage && !!garmentImage && !!bottomImage;

  const handleGenerate = async () => {
    if (!canGenerate) return;
    setSubmitting(true);
    setError(null);
    setGlobalError(null);
    setIsProcessing(true);
    setResultImageUrl(null);
    router.push("/processing");

    try {
      const result = await runTryOn(personImage!, garmentImage, bottomImage, mode, tuckIn);
      if (result.success && result.result_image) {
        setResultImageUrl(`data:image/jpeg;base64,${result.result_image}`);
      } else {
        setGlobalError(result.error || "Generation failed. Please try again.");
        setError(result.error || "Generation failed. Please try again.");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "An unexpected error occurred.";
      if (msg.includes("Timeout") || msg.includes("fetch failed") || msg.includes("Failed to fetch")) {
        setGlobalError("The AI model was cold-starting and hit a timeout. Please try again—it should be warm now and much faster!");
      } else {
        setGlobalError(msg);
      }
      setError(msg);
    } finally {
      setSubmitting(false);
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen px-6 py-12 animate-in fade-in slide-in-from-bottom-5 duration-700">
      {/* Step indicator */}
      <div className="max-w-5xl mx-auto w-full mb-10">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-sm font-semibold uppercase tracking-widest text-[#4D0E13]/60">
            Step 1 of 2
          </span>
        </div>
        <div className="h-1 bg-[#4D0E13]/10 rounded-full">
          <div className="h-1 w-1/2 bg-[#4D0E13] rounded-full transition-all duration-500" />
        </div>
      </div>

      <div className="max-w-5xl mx-auto w-full flex flex-col gap-8">
        <div className="text-center md:text-left">
          <h1 className="text-4xl font-serif text-[#4D0E13] mb-2">Upload Your Photos</h1>
          <p className="text-[#171717]/60">
            Upload a clear full-body photo of yourself and the garments you want to try on.
          </p>
        </div>

        <ModeSelector mode={mode} onChange={setMode} />

        {/* Upload cards */}
        <div className={`grid grid-cols-1 sm:grid-cols-2 gap-8 ${mode === "complete_outfit" ? "md:grid-cols-3" : ""}`}>
          <UploadCard label="Your Photo" onFileSelect={setPersonImage} initialFile={personImage} />
          
          {mode === "single" ? (
            <UploadCard label="Garment Photo" onFileSelect={setGarmentImage} initialFile={garmentImage} />
          ) : (
            <>
              <UploadCard label="Top Garment" onFileSelect={setGarmentImage} initialFile={garmentImage} />
              <UploadCard label="Bottom Garment" onFileSelect={setBottomImage} initialFile={bottomImage} />
            </>
          )}
        </div>

        {/* Tuck Toggle (only show if top garment is provided) */}
        {mode === "complete_outfit" && (
          <div className="mt-4 border-t border-[#4D0E13]/10 pt-8">
            <TuckToggle tucked={tuckIn} onChange={setTuckIn} />
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Generate button */}
        <div className="flex justify-end pb-24">
          <button
            onClick={handleGenerate}
            disabled={!canGenerate || submitting}
            className={`px-10 py-4 rounded-full font-semibold text-base transition-all duration-300 ${
              canGenerate && !submitting
                ? "bg-[#4D0E13] text-[#EEE4DA] hover:bg-[#3A0A0E] hover:scale-105 hover:shadow-xl cursor-pointer"
                : "bg-[#4D0E13]/20 text-[#4D0E13]/40 cursor-not-allowed"
            }`}
          >
            {submitting ? "Generating..." : "Generate Look →"}
          </button>
        </div>
      </div>
    </div>
  );
}
