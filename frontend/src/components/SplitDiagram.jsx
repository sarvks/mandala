// Visual diagram of "one offering → many beneficiaries"
export default function SplitDiagram({ size = 360 }) {
  const cx = size / 2;
  const cy = size / 2;
  const sourceR = 30;
  const ringR = size / 2 - 32;
  const targets = 8;

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      aria-hidden="true"
      className="overflow-visible"
    >
      <defs>
        <radialGradient id="srcGrad" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#D4AF37" />
          <stop offset="100%" stopColor="#7C191E" />
        </radialGradient>
        <linearGradient id="strokeGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#7C191E" stopOpacity="0.7" />
          <stop offset="100%" stopColor="#D4AF37" stopOpacity="0.15" />
        </linearGradient>
      </defs>

      {/* Decorative rings */}
      <g fill="none" stroke="#D4AF37" strokeWidth="0.5" opacity="0.4">
        <circle cx={cx} cy={cy} r={ringR} />
        <circle cx={cx} cy={cy} r={ringR - 24} strokeDasharray="2 5" />
      </g>

      {/* Spokes */}
      {Array.from({ length: targets }).map((_, i) => {
        const a = (i * 2 * Math.PI) / targets - Math.PI / 2;
        const x = cx + Math.cos(a) * ringR;
        const y = cy + Math.sin(a) * ringR;
        const xStart = cx + Math.cos(a) * sourceR;
        const yStart = cy + Math.sin(a) * sourceR;
        return (
          <g key={i}>
            <line
              x1={xStart}
              y1={yStart}
              x2={x}
              y2={y}
              stroke="url(#strokeGrad)"
              strokeWidth="1.2"
            >
              <animate
                attributeName="stroke-dashoffset"
                from="0"
                to="-12"
                dur="2.4s"
                repeatCount="indefinite"
              />
            </line>
            <circle cx={x} cy={y} r="9" fill="#fff" stroke="#7C191E" strokeWidth="1.4" />
            <circle cx={x} cy={y} r="3.5" fill="#7C191E" />
          </g>
        );
      })}

      {/* Source */}
      <circle cx={cx} cy={cy} r={sourceR} fill="url(#srcGrad)" />
      <circle cx={cx} cy={cy} r={sourceR + 8} fill="none" stroke="#D4AF37" strokeWidth="1" opacity="0.6">
        <animate attributeName="r" from={sourceR + 8} to={sourceR + 20} dur="2.4s" repeatCount="indefinite" />
        <animate attributeName="opacity" from="0.7" to="0" dur="2.4s" repeatCount="indefinite" />
      </circle>
      <text x={cx} y={cy + 5} textAnchor="middle" fill="#fff" fontFamily="Cormorant Garamond" fontSize="18" fontWeight="500">
        ₹
      </text>
    </svg>
  );
}
