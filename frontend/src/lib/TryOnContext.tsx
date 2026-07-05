"use client";

import React, { createContext, useContext, useState } from "react";

interface TryOnState {
  mode: "single" | "complete_outfit";
  personImage: File | null;
  garmentImage: File | null; // Used for single mode or top garment
  bottomImage: File | null;  // Used for complete_outfit mode lower garment
  tuckIn: boolean;
  resultImageUrl: string | null;
  isProcessing: boolean;
  globalError: string | null;
  setMode: (mode: "single" | "complete_outfit") => void;
  setPersonImage: (file: File | null) => void;
  setGarmentImage: (file: File | null) => void;
  setBottomImage: (file: File | null) => void;
  setTuckIn: (tucked: boolean) => void;
  setResultImageUrl: (url: string | null) => void;
  setIsProcessing: (status: boolean) => void;
  setGlobalError: (err: string | null) => void;
}

const TryOnContext = createContext<TryOnState | undefined>(undefined);

export function TryOnProvider({ children }: { children: React.ReactNode }) {
  const [mode, setMode] = useState<"single" | "complete_outfit">("single");
  const [personImage, setPersonImage] = useState<File | null>(null);
  const [garmentImage, setGarmentImage] = useState<File | null>(null);
  const [bottomImage, setBottomImage] = useState<File | null>(null);
  const [tuckIn, setTuckIn] = useState(false);
  const [resultImageUrl, setResultImageUrl] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);

  return (
    <TryOnContext.Provider
      value={{
        mode,
        personImage,
        garmentImage,
        bottomImage,
        tuckIn,
        resultImageUrl,
        isProcessing,
        globalError,
        setMode,
        setPersonImage,
        setGarmentImage,
        setBottomImage,
        setTuckIn,
        setResultImageUrl,
        setIsProcessing,
        setGlobalError,
      }}
    >
      {children}
    </TryOnContext.Provider>
  );
}

export function useTryOn() {
  const context = useContext(TryOnContext);
  if (context === undefined) {
    throw new Error("useTryOn must be used within a TryOnProvider");
  }
  return context;
}
