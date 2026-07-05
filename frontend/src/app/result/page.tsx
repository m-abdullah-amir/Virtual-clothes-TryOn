"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { useTryOn } from "@/lib/TryOnContext";

export default function ResultPage() {
  const router = useRouter();
  const { resultImageUrl, personImage, setGarmentImage, setBottomImage, setResultImageUrl } = useTryOn();

  // Guard: if no result, go back to upload
  useEffect(() => {
    if (!resultImageUrl) {
      router.push("/upload");
    }
  }, [resultImageUrl, router]);

  const handleDownload = () => {
    if (!resultImageUrl) return;
    const link = document.createElement("a");
    link.href = resultImageUrl;
    link.download = "tryon-result.jpg";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleTryAnother = () => {
    // Keep person image, clear garment + result
    setGarmentImage(null);
    setBottomImage(null);
    setResultImageUrl(null);
    router.push("/upload");
  };

  if (!resultImageUrl) return null;

  return (
    <div className="flex-1 flex flex-col min-h-screen px-6 py-12 animate-in fade-in slide-in-from-bottom-5 duration-700">
      {/* Blurred background */}
      <div
        className="fixed inset-0 -z-10 scale-110 blur-3xl opacity-30"
        style={{
          backgroundImage: `url(${resultImageUrl})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      />
      <div className="fixed inset-0 -z-10 bg-[#EEE4DA]/60" />

      <div className="max-w-5xl mx-auto w-full grid grid-cols-1 md:grid-cols-2 gap-12 items-center flex-1">
        {/* Result image */}
        <div className="relative aspect-[3/4] w-full max-w-sm mx-auto rounded-2xl overflow-hidden shadow-2xl">
          <Image
            src={resultImageUrl}
            alt="Your virtual try-on result"
            fill
            className="object-cover"
            priority
          />
        </div>

        {/* Action panel */}
        <div className="flex flex-col gap-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-[#4D0E13]/60 mb-2">
              Your Look ✨
            </p>
            <h1 className="text-4xl font-serif text-[#4D0E13] leading-tight">
              Here&apos;s How It Looks On You
            </h1>
            <p className="mt-3 text-[#171717]/60">
              Your AI-generated try-on is ready. Download it or try a different garment.
            </p>
          </div>

          <div className="flex flex-col gap-3">
            <button
              id="download-btn"
              onClick={handleDownload}
              className="w-full px-8 py-4 bg-emerald-700 text-white font-semibold rounded-full hover:bg-emerald-800 hover:scale-105 hover:shadow-xl transition-all duration-300 flex items-center justify-center gap-2"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" x2="12" y1="15" y2="3" />
              </svg>
              DOWNLOAD
            </button>

            <button
              id="try-another-btn"
              onClick={handleTryAnother}
              className="w-full px-8 py-4 border-2 border-[#4D0E13] text-[#4D0E13] font-semibold rounded-full hover:bg-[#4D0E13] hover:text-[#EEE4DA] hover:scale-105 transition-all duration-300"
            >
              TRY ANOTHER GARMENT
            </button>
          </div>

          {/* Person photo thumbnail */}
          {personImage && (
            <div className="flex items-center gap-3 mt-2">
              <div className="relative w-12 h-12 rounded-full overflow-hidden border-2 border-[#4D0E13]/20 flex-shrink-0">
                <Image
                  src={URL.createObjectURL(personImage)}
                  alt="Your photo"
                  fill
                  className="object-cover"
                />
              </div>
              <p className="text-sm text-[#171717]/50">
                Your photo is saved for the next try-on
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
