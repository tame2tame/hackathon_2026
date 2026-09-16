/** Deterministic vector sculpture: linked modules, never presented as analytics. */
export function NetworkSculpture() {
  const project = (x: number, y: number, z: number) => [
    255 + (x - y) * 31,
    300 + (x + y) * 15 - z * 31,
  ];
  const points = (values: number[][]) =>
    values.map((v) => project(v[0], v[1], v[2]).join(",")).join(" ");
  const blocks = Array.from({ length: 64 }, (_, i) => ({
    x: i % 4,
    y: Math.floor(i / 4) % 4,
    z: Math.floor(i / 16),
  })).filter(({ x, y, z }) => !((x + y + z) % 7 === 0));
  return (
    <div className="network-sculpture" aria-hidden="true">
      <div className="sculpture-label">
        <span>+ СЕТЬ ВЗАИМОДЕЙСТВИЙ</span>
        <span>ВУЗ × ПРОГРАММА × ПРОДУКТ</span>
      </div>
      <svg viewBox="0 0 520 470" fill="none">
        <defs>
          <pattern
            id="technical-grid"
            width="26"
            height="26"
            patternUnits="userSpaceOnUse"
          >
            <path d="M26 0H0V26" stroke="#d8d8da" strokeWidth=".5" />
          </pattern>
          <pattern
            id="scan-lines"
            width="4"
            height="4"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M0 1H4"
              stroke="white"
              strokeOpacity=".2"
              strokeWidth=".6"
            />
          </pattern>
        </defs>
        <rect
          x="40"
          y="45"
          width="440"
          height="370"
          fill="url(#technical-grid)"
        />
        <path
          d="M40 110L455 320M60 330L395 65M125 425V50M418 55V400"
          stroke="#777"
          strokeWidth=".6"
          strokeDasharray="2 6"
        />
        {blocks
          .sort((a, b) => a.x + a.y + a.z - (b.x + b.y + b.z))
          .map(({ x, y, z }, i) => {
            const accent =
              (x === 3 && y === 1 && z === 2) ||
              (x === 0 && y === 2 && z === 3);
            const orange = x === 3 && y === 3 && z === 0;
            const shades = accent
              ? ["#ad63f5", "#8308e9", "#5f06ab"]
              : orange
                ? ["#ff986e", "#ff5012", "#c63500"]
                : ["#d0d0d2", "#68686b", "#252527"];
            return (
              <g key={i} opacity={z === 3 && x < 2 ? 0.55 : 1}>
                <polygon
                  points={points([
                    [x, y, z + 1],
                    [x + 1, y, z + 1],
                    [x + 1, y + 1, z + 1],
                    [x, y + 1, z + 1],
                  ])}
                  fill={shades[0]}
                  stroke="#fff"
                  strokeWidth=".5"
                />
                <polygon
                  points={points([
                    [x, y, z],
                    [x + 1, y, z],
                    [x + 1, y, z + 1],
                    [x, y, z + 1],
                  ])}
                  fill={shades[1]}
                  stroke="#fff"
                  strokeWidth=".35"
                />
                <polygon
                  points={points([
                    [x + 1, y, z],
                    [x + 1, y + 1, z],
                    [x + 1, y + 1, z + 1],
                    [x + 1, y, z + 1],
                  ])}
                  fill={shades[2]}
                  stroke="#fff"
                  strokeWidth=".35"
                />
                <polygon
                  points={points([
                    [x, y, z],
                    [x + 1, y, z],
                    [x + 1, y, z + 1],
                    [x, y, z + 1],
                  ])}
                  fill="url(#scan-lines)"
                />
              </g>
            );
          })}
        <path
          d="M73 184h50v-50H73zM378 99h38v38h-38z"
          fill="#8308e9"
          fillOpacity=".38"
        />
        <path
          d="M80 348h31v31H80zM413 289h24v24h-24z"
          fill="#ff5012"
          fillOpacity=".85"
        />
        {[
          [65, 75],
          [420, 56],
          [460, 214],
          [53, 290],
          [405, 397],
          [183, 63],
        ].map(([x, y], i) => (
          <path
            key={i}
            d={`M${x - 5} ${y}h10M${x} ${y - 5}v10`}
            stroke={i % 2 ? "#8308e9" : "#161616"}
            strokeWidth="1"
          />
        ))}
        <path d="M40 415H480" stroke="#aaa" strokeDasharray="1 4" />
        <text
          x="40"
          y="442"
          fill="#161616"
          fontSize="10"
          fontFamily="monospace"
        >
          // CONNECTION_MAP
        </text>
        <text
          x="410"
          y="442"
          fill="#8308e9"
          fontSize="10"
          fontFamily="monospace"
        >
          СХЕМА_01
        </text>
      </svg>
      <div className="sculpture-stamp">
        14 ЭТАПОВ
        <br />
        ЕДИНЫЙ ПРОЦЕСС <span>↗</span>
      </div>
    </div>
  );
}
