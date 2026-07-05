"use client";

import { useState, useRef, useEffect } from "react";
import Image from "next/image";

interface UploadCardProps {
  label: string;
  onFileSelect: (file: File | null) => void;
  initialFile?: File | null;
  accept?: string;
  maxSizeMB?: number;
}

export default function UploadCard({
  label,
  onFileSelect,
  initialFile = null,
  accept = "image/jpeg, image/png, image/webp",
  maxSizeMB = 10,
}: UploadCardProps) {
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (initialFile) {
      const previewUrl = URL.createObjectURL(initialFile);
      setPreview(previewUrl);
      return () => {
        URL.revokeObjectURL(previewUrl);
      };
    } else {
      setPreview(null);
    }
  }, [initialFile]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    setError(null);

    if (!file) {
      setPreview(null);
      onFileSelect(null);
      return;
    }

    if (file.size > maxSizeMB * 1024 * 1024) {
      setError(`File size must be less than ${maxSizeMB}MB`);
      setPreview(null);
      onFileSelect(null);
      return;
    }

    onFileSelect(file);
  };

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    setPreview(null);
    setError(null);
    onFileSelect(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="flex flex-col gap-2 w-full">
      <p className="text-sm font-medium text-[#4D0E13] uppercase tracking-wide">
        {label}
      </p>

      <div
        onClick={() => !preview && fileInputRef.current?.click()}
        className={`relative w-full aspect-[3/4] rounded-xl border-2 border-dashed transition-all duration-300 overflow-hidden group ${
          preview
            ? "border-transparent bg-black/5"
            : "border-[#4D0E13]/20 bg-white/50 hover:bg-white hover:border-[#4D0E13]/40 cursor-pointer shadow-sm hover:shadow-md"
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept={accept}
          className="hidden"
        />

        {preview ? (
          <>
            <Image
              src={preview}
              alt={label}
              fill
              className="object-cover"
            />
            <button
              onClick={handleRemove}
              className="absolute top-3 right-3 bg-white/90 backdrop-blur-sm text-[#4D0E13] w-8 h-8 rounded-full flex items-center justify-center font-bold text-xl hover:bg-white hover:scale-110 shadow-lg transition-all"
              title="Remove image"
            >
              ×
            </button>
          </>
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center gap-3">
            <div className="w-12 h-12 rounded-full bg-[#4D0E13]/5 flex items-center justify-center text-[#4D0E13]/50 group-hover:scale-110 group-hover:bg-[#4D0E13]/10 transition-all">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" x2="12" y1="3" y2="15" />
              </svg>
            </div>
            <p className="text-sm font-medium text-[#171717]/60">
              Click to upload
            </p>
            <p className="text-xs text-[#171717]/40">
              JPEG, PNG, WEBP up to {maxSizeMB}MB
            </p>
          </div>
        )}
      </div>

      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
    </div>
  );
}
