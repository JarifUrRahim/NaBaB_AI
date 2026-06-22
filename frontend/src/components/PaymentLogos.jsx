// Inline SVG logos for bKash / Upay / Bank
export const BkashLogo = ({ className = "h-6" }) => (
  <svg viewBox="0 0 120 40" className={className} xmlns="http://www.w3.org/2000/svg" aria-label="bKash">
    <text
      x="0"
      y="28"
      fontFamily="Outfit, sans-serif"
      fontSize="26"
      fontWeight="700"
      fill="#E2136E"
      letterSpacing="-1"
    >
      bKash
    </text>
    <path
      d="M88 8 L98 20 L88 32 L78 20 Z"
      fill="#E2136E"
    />
    <path d="M88 14 L94 20 L88 26 L82 20 Z" fill="#FFF" />
  </svg>
);

export const UpayLogo = ({ className = "h-6" }) => (
  <svg viewBox="0 0 120 40" className={className} xmlns="http://www.w3.org/2000/svg" aria-label="Upay">
    <text
      x="0"
      y="28"
      fontFamily="Outfit, sans-serif"
      fontSize="26"
      fontWeight="800"
      fill="#F58220"
      letterSpacing="-0.5"
    >
      Upay
    </text>
    <circle cx="92" cy="20" r="10" fill="#F58220" />
    <circle cx="92" cy="20" r="5" fill="#FFF" />
  </svg>
);

export const BankLogo = ({ className = "h-6" }) => (
  <svg viewBox="0 0 120 40" className={className} xmlns="http://www.w3.org/2000/svg" aria-label="Bank">
    <path d="M10 14 L30 4 L50 14 L50 16 L10 16 Z" fill="#064E3B" />
    <rect x="12" y="18" width="4" height="14" fill="#064E3B" />
    <rect x="22" y="18" width="4" height="14" fill="#064E3B" />
    <rect x="32" y="18" width="4" height="14" fill="#064E3B" />
    <rect x="42" y="18" width="4" height="14" fill="#064E3B" />
    <rect x="8" y="33" width="44" height="3" fill="#064E3B" />
    <text x="60" y="28" fontFamily="Outfit, sans-serif" fontSize="14" fontWeight="700" fill="#064E3B">
      UCB Bank
    </text>
  </svg>
);
