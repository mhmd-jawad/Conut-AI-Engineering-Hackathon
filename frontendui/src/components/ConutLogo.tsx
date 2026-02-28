const ConutLogo = ({ className = "h-8 w-8" }: { className?: string }) => (
  <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
    {/* Coffee cup body */}
    <path d="M8 18h24v4c0 8.837-5.373 16-12 16S8 30.837 8 22v-4z" fill="hsl(var(--caramel))" />
    {/* Cup rim */}
    <rect x="6" y="16" width="28" height="4" rx="2" fill="hsl(var(--copper))" />
    {/* Handle */}
    <path d="M32 20h3a5 5 0 010 10h-3" stroke="hsl(var(--copper))" strokeWidth="2.5" strokeLinecap="round" fill="none" />
    {/* Steam lines */}
    <path d="M15 12c0-3 2-4 0-7" stroke="hsl(var(--pistachio))" strokeWidth="1.5" strokeLinecap="round" />
    <path d="M20 10c0-3 2-4 0-7" stroke="hsl(var(--pistachio))" strokeWidth="1.5" strokeLinecap="round" />
    <path d="M25 12c0-3 2-4 0-7" stroke="hsl(var(--pistachio))" strokeWidth="1.5" strokeLinecap="round" />
    {/* Donut */}
    <circle cx="36" cy="36" r="8" fill="hsl(var(--caramel))" />
    <circle cx="36" cy="36" r="3" fill="hsl(var(--cream))" />
    {/* Sprinkles */}
    <rect x="33" y="29" width="2" height="4" rx="1" fill="hsl(var(--pistachio))" transform="rotate(-20 34 31)" />
    <rect x="39" y="30" width="2" height="3" rx="1" fill="hsl(var(--deep-teal))" transform="rotate(15 40 31)" />
  </svg>
);

export default ConutLogo;
