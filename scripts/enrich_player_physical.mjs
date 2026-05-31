/**
 * Enrich squad players with height (cm) and weight (kg) from Wikidata.
 * Run: node scripts/enrich_player_physical.mjs
 */

import { readFileSync, writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");

function normalizeName(name) {
  return name
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function loadPlayerNames() {
  const names = new Set();
  const squadsPy = readFileSync(join(root, "backend/app/data/team_squads_data.py"), "utf8");
  for (const m of squadsPy.matchAll(/"name": "([^"]+)"/g)) names.add(m[1]);
  const overridesPy = readFileSync(join(root, "backend/app/data/team_squad_overrides.py"), "utf8");
  for (const m of overridesPy.matchAll(/"name": "([^"]+)"/g)) names.add(m[1]);
  return [...names].sort();
}

async function queryWikidata(name) {
  const escaped = name.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
  const query = `
SELECT ?height ?mass WHERE {
  ?person rdfs:label "${escaped}"@en.
  ?person wdt:P106 wd:Q937857.
  OPTIONAL { ?person wdt:P2048 ?height. }
  OPTIONAL { ?person wdt:P2067 ?mass. }
}
LIMIT 1`.trim();

  const url = `https://query.wikidata.org/sparql?format=json&query=${encodeURIComponent(query)}`;
  const res = await fetch(url, {
    headers: { Accept: "application/sparql-results+json", "User-Agent": "wkpoule-squad-enrich/1.0" },
  });
  if (!res.ok) return null;
  const data = await res.json();
  const row = data?.results?.bindings?.[0];
  if (!row) return null;

  let heightCm = row.height?.value ? parseFloat(row.height.value) : null;
  if (heightCm != null && heightCm < 3) heightCm = Math.round(heightCm * 100);
  else if (heightCm != null) heightCm = Math.round(heightCm);

  let weightKg = row.mass?.value ? Math.round(parseFloat(row.mass.value)) : null;
  if (weightKg != null && weightKg > 200) weightKg = null;

  if (heightCm == null && weightKg == null) return null;
  return { height_cm: heightCm, weight_kg: weightKg };
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function main() {
  const names = loadPlayerNames();
  const out = {};
  let found = 0;

  for (let i = 0; i < names.length; i += 1) {
    const name = names[i];
    const key = normalizeName(name);
    if (out[key]) continue;
    try {
      const phys = await queryWikidata(name);
      if (phys) {
        out[key] = phys;
        found += 1;
      }
    } catch {
      // skip failed lookups
    }
    if ((i + 1) % 25 === 0) {
      console.log(`Processed ${i + 1}/${names.length}, found ${found}`);
    }
    await sleep(120);
  }

  const lines = [
    '"""Player height/weight from Wikidata (association football players)."""',
    "",
    "PHYSICAL_BY_NAME: dict[str, dict] = {",
  ];
  for (const key of Object.keys(out).sort()) {
    const p = out[key];
    lines.push(`    ${JSON.stringify(key)}: ${JSON.stringify(p)},`);
  }
  lines.push("}", "");

  const outPath = join(root, "backend/app/data/player_physical_data.py");
  writeFileSync(outPath, lines.join("\n"), "utf8");
  console.log(`Wrote ${found} physical profiles to ${outPath}`);
}

main();
