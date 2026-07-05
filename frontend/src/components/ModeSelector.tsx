"use client";

interface ModeSelectorProps {
  mode: "single" | "complete_outfit";
  onChange: (mode: "single" | "complete_outfit") => void;
}

export default function ModeSelector({ mode, onChange }: ModeSelectorProps) {
  return (
    <div className="flex bg-[#4D0E13]/10 p-1 rounded-full w-full max-w-sm mx-auto mb-8">
      <button
        onClick={() => onChange("single")}
        className={`flex-1 py-3 px-6 rounded-full text-sm font-semibold transition-all duration-300 ${
          mode === "single"
            ? "bg-[#4D0E13] text-[#EEE4DA] shadow-md"
            : "text-[#4D0E13]/60 hover:text-[#4D0E13]"
        }`}
      >
        Single Garment
      </button>
      <button
        onClick={() => onChange("complete_outfit")}
        className={`flex-1 py-3 px-6 rounded-full text-sm font-semibold transition-all duration-300 ${
          mode === "complete_outfit"
            ? "bg-[#4D0E13] text-[#EEE4DA] shadow-md"
            : "text-[#4D0E13]/60 hover:text-[#4D0E13]"
        }`}
      >
        Complete Outfit
      </button>
    </div>
  );
}
