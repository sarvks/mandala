export const MandalaMotif = ({ size = 240, className = "", stroke = "#D4AF37", opacity = 0.35 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 200 200"
    className={className}
    aria-hidden="true"
  >
    <g
      fill="none"
      stroke={stroke}
      strokeWidth="0.6"
      strokeLinecap="round"
      opacity={opacity}
    >
      <circle cx="100" cy="100" r="96" />
      <circle cx="100" cy="100" r="76" />
      <circle cx="100" cy="100" r="56" />
      <circle cx="100" cy="100" r="36" />
      <circle cx="100" cy="100" r="16" />
      {Array.from({ length: 24 }).map((_, i) => {
        const a = (i * Math.PI) / 12;
        return (
          <line
            key={i}
            x1={100 + Math.cos(a) * 16}
            y1={100 + Math.sin(a) * 16}
            x2={100 + Math.cos(a) * 96}
            y2={100 + Math.sin(a) * 96}
          />
        );
      })}
      {Array.from({ length: 8 }).map((_, i) => {
        const a = (i * Math.PI) / 4;
        return (
          <path
            key={`p-${i}`}
            d={`M ${100 + Math.cos(a) * 36} ${100 + Math.sin(a) * 36} Q ${100 + Math.cos(a + 0.25) * 56} ${100 + Math.sin(a + 0.25) * 56}, ${100 + Math.cos(a + 0.5) * 36} ${100 + Math.sin(a + 0.5) * 36}`}
          />
        );
      })}
    </g>
  </svg>
);

export default MandalaMotif;
