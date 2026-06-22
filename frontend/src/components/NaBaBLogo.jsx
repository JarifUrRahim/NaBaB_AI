// NaBaB monogram — emerald disc with gold "N" + sparkle
export const NaBaBLogo = ({ size = 40, withText = false, dark = false }) => (
  <div className="flex items-center gap-2.5">
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="goldGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#F4D078" />
          <stop offset="50%" stopColor="#D4AF37" />
          <stop offset="100%" stopColor="#9C7C1F" />
        </linearGradient>
      </defs>
      <circle cx="32" cy="32" r="30" fill="#064E3B" />
      <circle cx="32" cy="32" r="28" fill="none" stroke="url(#goldGrad)" strokeWidth="1" opacity="0.7" />
      {/* Stylized N */}
      <path
        d="M20 46 L20 18 L24 18 L40 38 L40 18 L44 18 L44 46 L40 46 L24 26 L24 46 Z"
        fill="url(#goldGrad)"
      />
      {/* Crown sparkle */}
      <path d="M32 8 L33.5 11 L36.5 11 L34 13 L35 16 L32 14 L29 16 L30 13 L27.5 11 L30.5 11 Z" fill="url(#goldGrad)" />
    </svg>
    {withText && (
      <div className="flex flex-col leading-none">
        <span className={`font-display text-2xl tracking-tight ${dark ? "text-cream" : "text-emerald"}`}>
          NaBaB
        </span>
        <span className={`text-[10px] tracking-widest uppercase ${dark ? "text-gold" : "text-gold"}`}>
          বাঙ্গালী বাবা
        </span>
      </div>
    )}
  </div>
);
