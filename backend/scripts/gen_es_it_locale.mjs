import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const backend = path.join(__dirname, "..");
const src = fs.readFileSync(path.join(backend, "match_comments.py"), "utf8");

function extractDict(name) {
  const re = new RegExp(`${name}\\s*=\\s*(\\{)`);
  const m = src.match(re);
  if (!m) throw new Error(`Missing ${name}`);
  let start = m.index + m[0].length - 1;
  let depth = 0;
  for (let i = start; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") {
      depth--;
      if (depth === 0) return src.slice(start, i + 1);
    }
  }
  throw new Error(`Unclosed ${name}`);
}

function parseEntries(dictSrc, keyType) {
  const entries = [];
  const keyRe =
    keyType === "num"
      ? /^\s*(\d+)\s*:\s*\{/gm
      : /^\s*"([a-z_]+)"\s*:\s*\{/gm;
  let m;
  while ((m = keyRe.exec(dictSrc))) {
    const key = keyType === "num" ? Number(m[1]) : m[1];
    const blockStart = m.index;
    let depth = 0;
    let i = dictSrc.indexOf("{", blockStart);
    for (; i < dictSrc.length; i++) {
      if (dictSrc[i] === "{") depth++;
      else if (dictSrc[i] === "}") {
        depth--;
        if (depth === 0) {
          const block = dictSrc.slice(blockStart, i + 1);
          const enM = block.match(/"en"\s*:\s*"((?:\\.|[^"\\])*)"/);
          if (!enM) throw new Error(`No en for ${key}`);
          entries.push({ key, en: JSON.parse(`"${enM[1]}"`) });
          break;
        }
      }
    }
  }
  return entries;
}

const match = parseEntries(extractDict("MATCH_COMMENTS"), "num");
const ko = parseEntries(extractDict("KNOCKOUT_MATCH_COMMENTS"), "num");
const tpl = parseEntries(extractDict("KNOCKOUT_TEMPLATES"), "str");

console.log(JSON.stringify({ match: match.length, ko: ko.length, tpl: tpl.length }));
fs.writeFileSync(
  path.join(backend, "_en_entries.json"),
  JSON.stringify({ match, ko, tpl }, null, 2)
);
