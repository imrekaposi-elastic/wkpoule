type ExpertStyle = {
  initials: string;
  skin: string;
  hair: string;
  jacket: string;
  shirt: string;
  accent: string;
  hairStyle: "swoop" | "short" | "curly" | "cap" | "ponytail" | "silver" | "balding" | "beret";
  accessory?: "tie" | "glasses" | "beard" | "mustache" | "mic" | "card" | "collar" | "goatee";
  expression?: "smile" | "smirk" | "serious";
};

const EXPERT_STYLES: Record<string, ExpertStyle> = {
  trump: {
    initials: "DT",
    skin: "#f2c28f",
    hair: "#f4c542",
    jacket: "#1e3a8a",
    shirt: "#ffffff",
    accent: "#dc2626",
    hairStyle: "swoop",
    accessory: "tie",
    expression: "smirk",
  },
  burr: {
    initials: "BB",
    skin: "#efb58a",
    hair: "#9a3412",
    jacket: "#334155",
    shirt: "#e5e7eb",
    accent: "#111827",
    hairStyle: "short",
    accessory: "mic",
    expression: "smirk",
  },
  sponder: {
    initials: "YS",
    skin: "#d6a77b",
    hair: "#1f2937",
    jacket: "#0f766e",
    shirt: "#ecfeff",
    accent: "#f59e0b",
    hairStyle: "short",
    accessory: "glasses",
    expression: "serious",
  },
  cantona: {
    initials: "EC",
    skin: "#e7b27e",
    hair: "#5b4636",
    jacket: "#b91c1c",
    shirt: "#fee2e2",
    accent: "#7f1d1d",
    hairStyle: "short",
    accessory: "collar",
    expression: "serious",
  },
  klopp: {
    initials: "JK",
    skin: "#efbd8d",
    hair: "#a16207",
    jacket: "#dc2626",
    shirt: "#fef2f2",
    accent: "#111827",
    hairStyle: "cap",
    accessory: "glasses",
    expression: "smile",
  },
  zlatan: {
    initials: "ZI",
    skin: "#d49a6a",
    hair: "#18181b",
    jacket: "#111827",
    shirt: "#f9fafb",
    accent: "#f59e0b",
    hairStyle: "ponytail",
    accessory: "goatee",
    expression: "serious",
  },
  hudson: {
    initials: "RH",
    skin: "#f0c7a0",
    hair: "#d1d5db",
    jacket: "#2563eb",
    shirt: "#eff6ff",
    accent: "#38bdf8",
    hairStyle: "silver",
    accessory: "mic",
    expression: "smile",
  },
  seinfeld: {
    initials: "JS",
    skin: "#e8b78d",
    hair: "#27272a",
    jacket: "#64748b",
    shirt: "#ffffff",
    accent: "#0f172a",
    hairStyle: "short",
    accessory: "mic",
    expression: "smile",
  },
  carr: {
    initials: "JC",
    skin: "#e9b184",
    hair: "#050505",
    jacket: "#111827",
    shirt: "#f9fafb",
    accent: "#ef4444",
    hairStyle: "short",
    expression: "smile",
  },
  maradona: {
    initials: "DM",
    skin: "#c98254",
    hair: "#111111",
    jacket: "#60a5fa",
    shirt: "#ffffff",
    accent: "#0284c7",
    hairStyle: "curly",
    accessory: "beard",
    expression: "smirk",
  },
  gijp: {
    initials: "RG",
    skin: "#e9b88f",
    hair: "#ca8a04",
    jacket: "#166534",
    shirt: "#f0fdf4",
    accent: "#fbbf24",
    hairStyle: "short",
    accessory: "glasses",
    expression: "smile",
  },
  derksen: {
    initials: "JD",
    skin: "#e7b991",
    hair: "#d1d5db",
    jacket: "#3f3f46",
    shirt: "#f4f4f5",
    accent: "#a16207",
    hairStyle: "balding",
    accessory: "mustache",
    expression: "serious",
  },
  lineker: {
    initials: "GL",
    skin: "#e6b58b",
    hair: "#78716c",
    jacket: "#0f172a",
    shirt: "#ffffff",
    accent: "#facc15",
    hairStyle: "silver",
    accessory: "card",
    expression: "smile",
  },
  al_sahhaf: {
    initials: "MS",
    skin: "#b7794f",
    hair: "#111827",
    jacket: "#14532d",
    shirt: "#ecfdf5",
    accent: "#dc2626",
    hairStyle: "beret",
    accessory: "mustache",
    expression: "serious",
  },
};

export const EXPERT_STYLE_KEYS = Object.keys(EXPERT_STYLES) as ExpertStyleKey[];

export type ExpertStyleKey = keyof typeof EXPERT_STYLES;

type Props = {
  styleKey: string;
  label: string;
  size?: "sm" | "md" | "lg";
};

function Hair({ expert }: { expert: ExpertStyle }) {
  switch (expert.hairStyle) {
    case "swoop":
      return (
        <>
          <path d="M31 37c7-22 40-24 54-8-15-3-27 2-38 12 12-3 24-2 35 3-17 4-36 3-51-7Z" fill={expert.hair} />
          <path d="M30 42c4-8 13-15 27-18-7 9-15 16-27 18Z" fill="#f8d66d" opacity="0.85" />
        </>
      );
    case "curly":
      return (
        <>
          {[
            [29, 38, 13],
            [42, 28, 15],
            [58, 25, 16],
            [74, 30, 14],
            [85, 42, 12],
            [35, 51, 11],
          ].map(([cx, cy, r]) => (
            <circle key={`${cx}-${cy}`} cx={cx} cy={cy} r={r} fill={expert.hair} />
          ))}
        </>
      );
    case "cap":
      return (
        <>
          <path d="M29 36c8-18 42-20 57 0v8H29v-8Z" fill={expert.jacket} />
          <path d="M70 37c17-1 26 3 30 8-11 1-22 1-32-2Z" fill={expert.jacket} />
        </>
      );
    case "ponytail":
      return (
        <>
          <path d="M29 37c8-18 40-21 55 1 1 11-5 17-12 19-6-14-25-17-41-8Z" fill={expert.hair} />
          <path d="M84 47c14 7 15 27 3 35-7-9-8-23-3-35Z" fill={expert.hair} />
        </>
      );
    case "silver":
      return <path d="M30 39c8-18 39-20 55-2 0 5-2 8-5 11-11-9-30-10-45-1-3-2-5-5-5-8Z" fill={expert.hair} />;
    case "balding":
      return (
        <>
          <path d="M33 37c8-11 36-13 49 1-3 4-7 7-13 8-7-6-19-6-27 0-5-2-8-5-9-9Z" fill={expert.hair} />
          <path d="M44 31c7-4 21-5 29 0-7 5-20 6-29 0Z" fill="#f2d0b0" opacity="0.75" />
        </>
      );
    case "beret":
      return (
        <>
          <path d="M28 35c12-15 44-17 62-2-12 9-39 12-62 2Z" fill={expert.jacket} />
          <path d="M62 23l9 9-18 1Z" fill={expert.jacket} />
        </>
      );
    default:
      return <path d="M31 38c8-18 39-20 54 0v10c-13-10-36-10-54 0V38Z" fill={expert.hair} />;
  }
}

function FaceAccessory({ expert }: { expert: ExpertStyle }) {
  switch (expert.accessory) {
    case "glasses":
      return (
        <>
          <circle cx="48" cy="67" r="8" fill="none" stroke="#111827" strokeWidth="3" />
          <circle cx="72" cy="67" r="8" fill="none" stroke="#111827" strokeWidth="3" />
          <path d="M56 67h8" stroke="#111827" strokeWidth="3" strokeLinecap="round" />
        </>
      );
    case "beard":
      return <path d="M40 78c8 21 33 21 41 0-9 7-31 7-41 0Z" fill={expert.hair} opacity="0.9" />;
    case "mustache":
      return <path d="M45 79c6-7 13-5 15 0 3-5 11-7 16 0-6 5-12 5-16 1-4 4-10 4-15-1Z" fill={expert.hair} />;
    case "goatee":
      return (
        <>
          <path d="M48 78c4-5 8-4 12 0 4-4 9-5 13 0-8 4-17 4-25 0Z" fill={expert.hair} />
          <path d="M55 86c3 9 8 9 11 0Z" fill={expert.hair} />
        </>
      );
    default:
      return null;
  }
}

function BodyAccessory({ expert }: { expert: ExpertStyle }) {
  switch (expert.accessory) {
    case "tie":
      return <path d="M58 106h8l5 34-9 11-9-11Z" fill={expert.accent} />;
    case "mic":
      return (
        <g transform="rotate(-24 94 118)">
          <rect x="91" y="102" width="7" height="33" rx="3.5" fill="#111827" />
          <circle cx="94.5" cy="99" r="8" fill="#374151" />
        </g>
      );
    case "collar":
      return <path d="M37 110h50l-10 15-15-10-15 10Z" fill={expert.accent} />;
    case "card":
      return <rect x="84" y="105" width="15" height="22" rx="2" fill={expert.accent} transform="rotate(10 91.5 116)" />;
    default:
      return null;
  }
}

function Mouth({ expression = "smile" }: { expression?: ExpertStyle["expression"] }) {
  if (expression === "serious") {
    return <path d="M52 84h17" stroke="#7c2d12" strokeWidth="3" strokeLinecap="round" />;
  }
  if (expression === "smirk") {
    return <path d="M51 82c5 6 14 7 22 1" stroke="#7c2d12" strokeWidth="3" strokeLinecap="round" fill="none" />;
  }
  return <path d="M49 82c6 10 22 10 28 0" stroke="#7c2d12" strokeWidth="3" strokeLinecap="round" fill="none" />;
}

export default function ExpertAvatar({ styleKey, label, size = "md" }: Props) {
  const expert = EXPERT_STYLES[styleKey as ExpertStyleKey] ?? EXPERT_STYLES.lineker;
  const sizeClass = size === "lg" ? "h-28 w-24" : size === "sm" ? "h-16 w-14" : "h-24 w-20";
  const idSafe = styleKey.replace(/[^a-z0-9_-]/gi, "");

  return (
    <svg
      viewBox="0 0 120 160"
      className={`${sizeClass} shrink-0 drop-shadow-lg`}
      role="img"
      aria-label={label}
    >
      <title>{label}</title>
      <defs>
        <linearGradient id={`avatar-bg-${idSafe}`} x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stopColor="#fef3c7" />
          <stop offset="100%" stopColor={expert.accent} stopOpacity="0.45" />
        </linearGradient>
      </defs>
      <rect x="4" y="4" width="112" height="152" rx="34" fill={`url(#avatar-bg-${idSafe})`} />
      <path d="M24 132c5-23 20-34 38-34s33 11 38 34v24H24Z" fill={expert.jacket} />
      <path d="M46 103h32l-7 53H53Z" fill={expert.shirt} />
      <BodyAccessory expert={expert} />
      <ellipse cx="60" cy="62" rx="34" ry="39" fill={expert.skin} />
      <path d="M29 63c-6 2-9 9-6 16 2 6 8 8 12 5M91 63c6 2 9 9 6 16-2 6-8 8-12 5" fill={expert.skin} />
      <Hair expert={expert} />
      <path d="M45 61c4-4 9-4 14-1M70 60c5-3 10-3 14 1" stroke="#3f2a1f" strokeWidth="3" strokeLinecap="round" />
      <circle cx="49" cy="68" r="3" fill="#111827" />
      <circle cx="72" cy="68" r="3" fill="#111827" />
      <path d="M60 70c-2 6-4 10-2 13 2 2 6 2 8 0" stroke="#a16207" strokeWidth="2.5" strokeLinecap="round" fill="none" />
      <FaceAccessory expert={expert} />
      <Mouth expression={expert.expression} />
      <rect x="42" y="136" width="36" height="14" rx="7" fill="rgba(255,255,255,0.82)" />
      <text x="60" y="146" textAnchor="middle" fontSize="10" fontWeight="900" fill="#0f172a">
        {expert.initials}
      </text>
    </svg>
  );
}
