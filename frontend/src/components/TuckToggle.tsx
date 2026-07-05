"use client";

interface TuckToggleProps {
  tucked: boolean;
  onChange: (tucked: boolean) => void;
}

export default function TuckToggle({ tucked, onChange }: TuckToggleProps) {
  return (
    <label className="flex items-center gap-3 cursor-pointer group mt-4 justify-center">
      <div className="relative">
        <input
          type="checkbox"
          className="sr-only"
          checked={tucked}
          onChange={(e) => onChange(e.target.checked)}
        />
        <div
          className={`block w-12 h-7 rounded-full transition-colors duration-300 ${
            tucked ? "bg-[#4D0E13]" : "bg-[#4D0E13]/20"
          }`}
        ></div>
        <div
          className={`absolute left-1 top-1 bg-[#EEE4DA] w-5 h-5 rounded-full transition-transform duration-300 ${
            tucked ? "translate-x-5" : "translate-x-0"
          }`}
        ></div>
      </div>
      <div className="text-sm font-medium text-[#4D0E13]">
        Tuck in shirt
        <span className="block text-xs text-[#171717]/50 font-normal">
          AI will attempt to tuck the upper garment into the lower garment
        </span>
      </div>
    </label>
  );
}
