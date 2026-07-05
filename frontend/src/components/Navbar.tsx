"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navbar() {
  const pathname = usePathname();

  const links = [
    { href: "/", label: "Home" },
    { href: "/upload", label: "Upload" },
    { href: "/processing", label: "Processing" },
    { href: "/result", label: "Result" },
  ];

  return (
    <nav className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50">
      <div className="bg-[#EEE4DA]/80 backdrop-blur-md px-2 py-2 rounded-full border border-[#4D0E13]/10 shadow-lg flex items-center gap-1">
        {links.map((link) => {
          const isActive = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`px-6 py-2.5 rounded-full text-sm font-medium transition-all duration-300 ${
                isActive
                  ? "bg-[#4D0E13] text-[#EEE4DA] shadow-md scale-105"
                  : "text-[#171717]/60 hover:text-[#171717] hover:bg-black/5"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
