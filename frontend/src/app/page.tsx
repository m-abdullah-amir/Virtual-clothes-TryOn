import Link from "next/link";

export default function Home() {
  return (
    <div className="relative min-h-screen w-full overflow-hidden">
      <img
        src="/images/hero-image.png"
        alt="Virtual Try-On"
        className="absolute inset-0 w-full h-full object-cover"
      />

      {/* Invisible clickable area, positioned over the "TRY IT NOW" 
          button already drawn into the image */}
      <Link
        href="/upload"
        aria-label="Try It Now"
        className="absolute left-[12%] top-[70%] w-[10%] h-[5%]"
      />
    </div>
  );
}