import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { match, ko, tpl } from "../_es_it_data.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const out = path.join(__dirname, "..", "match_comments_locale_es_it.py");

function pyStr(s) {
  return JSON.stringify(s);
}

function renderDict(name, obj, keyQuote) {
  const lines = [`${name} = {`];
  for (const [k, v] of Object.entries(obj)) {
    const key = keyQuote === "str" ? pyStr(k) : k;
    lines.push(`    ${key}: {`);
    lines.push(`        "es": ${pyStr(v.es)},`);
    lines.push(`        "it": ${pyStr(v.it)},`);
    lines.push(`    },`);
  }
  lines.push(`}`);
  return lines.join("\n");
}

const body = `"""Native Spanish and Italian fun-comment texts (hand-quality translations)."""

${renderDict("MATCH_COMMENTS_ES_IT", match, "num")}

${renderDict("KNOCKOUT_MATCH_COMMENTS_ES_IT", ko, "num")}

${renderDict("KNOCKOUT_TEMPLATES_ES_IT", tpl, "str")}


def merge_into(match_comments, knockout_comments, knockout_templates):
    """Inject native es/it texts into the comment dicts (called from match_comments)."""
    for mn, loc in MATCH_COMMENTS_ES_IT.items():
        if mn in match_comments:
            match_comments[mn]["es"] = loc["es"]
            match_comments[mn]["it"] = loc["it"]
    for mn, loc in KNOCKOUT_MATCH_COMMENTS_ES_IT.items():
        if mn in knockout_comments:
            knockout_comments[mn]["es"] = loc["es"]
            knockout_comments[mn]["it"] = loc["it"]
    for style, loc in KNOCKOUT_TEMPLATES_ES_IT.items():
        if style in knockout_templates:
            knockout_templates[style]["es"] = loc["es"]
            knockout_templates[style]["it"] = loc["it"]
`;

fs.writeFileSync(out, body, "utf8");
console.log(`Wrote ${out}`);
console.log(`Counts: match=${Object.keys(match).length} ko=${Object.keys(ko).length} tpl=${Object.keys(tpl).length}`);
