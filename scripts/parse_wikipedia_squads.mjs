import { readFileSync, writeFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const wikiPath =
  process.argv[2] ||
  join(
    __dirname,
    "..",
    ".cursor",
    "projects",
    "c-Users-ImreKaposi-OneDrive-kaposi-net-Documenten-wkpoule",
    "agent-tools",
    "b0279c37-64dd-45dd-bafa-81a746f70f63.txt",
  );
const outPath = join(__dirname, "..", "backend", "app", "data", "team_squads_data.py");

const NAME_TO_CODE = {
  "Czech Republic": "CZE",
  Mexico: "MEX",
  "South Africa": "RSA",
  "South Korea": "KOR",
  "Bosnia and Herzegovina": "BIH",
  Canada: "CAN",
  Qatar: "QAT",
  Switzerland: "SUI",
  Brazil: "BRA",
  Haiti: "HAI",
  Morocco: "MAR",
  Scotland: "SCO",
  Australia: "AUS",
  Paraguay: "PAR",
  Turkey: "TUR",
  "United States": "USA",
  Curaçao: "CUW",
  Ecuador: "ECU",
  Germany: "GER",
  "Ivory Coast": "CIV",
  Japan: "JPN",
  Netherlands: "NED",
  Sweden: "SWE",
  Tunisia: "TUN",
  Belgium: "BEL",
  Egypt: "EGY",
  Iran: "IRN",
  "New Zealand": "NZL",
  "Cape Verde": "CPV",
  "Saudi Arabia": "KSA",
  Spain: "ESP",
  Uruguay: "URU",
  France: "FRA",
  Iraq: "IRQ",
  Norway: "NOR",
  Senegal: "SEN",
  Algeria: "ALG",
  Argentina: "ARG",
  Austria: "AUT",
  Jordan: "JOR",
  Colombia: "COL",
  "DR Congo": "COD",
  Portugal: "POR",
  Uzbekistan: "UZB",
  Croatia: "CRO",
  England: "ENG",
  Ghana: "GHA",
  Panama: "PAN",
};

const POS_MAP = { "1 GK": "GK", "2 DF": "DF", "3 MF": "MF", "4 FW": "FW" };
const ROW_RE =
  /^\|\s*(?:(\d+)\s*\|)?\s*(1 GK|2 DF|3 MF|4 FW)\s*\|\s*(.+?)\s*\|\s*\([^)]+\)[^|]*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*$/;

function cleanName(raw) {
  return raw.replace("(captain)", "").replace(/\[\d+\]/g, "").trim();
}

function parsePlayers(text) {
  const players = [];
  let sortOrder = 0;
  for (const line of text.split("\n")) {
    const m = line.trim().match(ROW_RE);
    if (!m) continue;
    const [, numStr, posKey, nameRaw, caps, , club] = m;
    players.push({
      name: cleanName(nameRaw),
      position: POS_MAP[posKey],
      shirt_number: numStr ? parseInt(numStr, 10) : sortOrder + 1,
      club: club.trim(),
      height_cm: 0,
      weight_kg: 0,
      caps: parseInt(caps, 10),
      sort_order: sortOrder,
    });
    sortOrder += 1;
  }
  return players;
}

const content = readFileSync(wikiPath, "utf8");
const sections = content.split("\n### ").slice(1);
const squads = {};

for (const section of sections) {
  const country = section.split("\n")[0].trim();
  if (country === "Age" || country === "Coach representation by country") continue;
  const code = NAME_TO_CODE[country];
  if (!code) continue;
  const players = parsePlayers(section);
  if (players.length) squads[code] = players;
}

const lines = [
  '"""Real player squads from national team announcements (Wikipedia 2026 squads, May 2026)."""',
  "",
  "TEAM_SQUADS: dict[str, list[dict]] = {",
];

for (const code of Object.keys(squads).sort()) {
  lines.push(`    "${code}": [`);
  for (const p of squads[code]) {
    lines.push(
      `        {${Object.entries(p)
        .map(([k, v]) => (typeof v === "string" ? `"${k}": ${JSON.stringify(v)}` : `"${k}": ${v}`))
        .join(", ")}},`,
    );
  }
  lines.push("    ],");
}
lines.push("}", "");

writeFileSync(outPath, lines.join("\n"), "utf8");
console.log(`Wrote ${Object.keys(squads).length} squads to ${outPath}`);
