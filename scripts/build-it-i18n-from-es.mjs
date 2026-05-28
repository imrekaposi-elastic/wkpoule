/**
 * Rebuild frontend/src/i18n/it.json from es.json (Spanish UI works) via ES→IT replacements.
 * Run: node scripts/build-it-i18n-from-es.mjs
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const i18n = path.join(__dirname, "..", "frontend", "src", "i18n");

const ES_IT = [
  ["Partido de pronósticos Copa del Mundo 2026", "Gioco dei pronostici Mondiale 2026"],
  ["Pronostica cada partido", "Pronostica ogni partita"],
  ["desafía a tus amigos", "sfida gli amici"],
  ["sigue el Mundial como un experto", "segui il Mondiale come un esperto"],
  ["Crea tu propia historia del torneo", "Scrivi la tua storia del torneo"],
  ["información de estadios", "info sugli stadi"],
  ["análisis de expertos en estilo IA", "analisi degli esperti in stile IA"],
  ["subligas privadas", "sottoleghe private"],
  ["chat para tu grupo", "chat per il tuo gruppo"],
  ["Ayuda de pronóstico", "Aiuto pronostico"],
  ["Tu próximo pronóstico", "La tua prossima scelta"],
  ["Consejo del experto", "Suggerimento dell'esperto"],
  ["Compara tu instinto", "Confronta il tuo istinto"],
  ["antes de confirmar tu pronóstico", "prima di confermare il pronostico"],
  ["Todo en una liga", "Tutto in un unico gioco"],
  ["Más que un formulario de marcador", "Più di un modulo per i risultati"],
  ["Información de estadios", "Informazioni sugli stadi"],
  ["Análisis de expertos", "Analisi degli esperti"],
  ["Lee comentarios coloridos", "Leggi commenti colorati"],
  ["antes de elegir", "prima di scegliere"],
  ["Usa sugerencias de marcador", "Usa suggerimenti di risultato"],
  ["basadas en la clasificación", "basate sulla classifica"],
  ["como segunda opinión para cada partido", "come seconda opinione per ogni partita"],
  ["Subligas privadas", "Sottoleghe private"],
  ["Crea una miniliga", "Crea una mini-lega"],
  ["sigue tu propia clasificación", "segui la tua classifica"],
  ["Chat de la subliga", "Chat della sottogruppo"],
  ["mantén viva la competición en tu grupo", "tieni viva la competizione nel gruppo"],
  ["Análisis de expertos de renombre", "Analisi di esperti di fama"],
  ["Conoce el panel de expertos IA", "Il panel di esperti IA"],
  ["Un elenco divertido", "Un gruppo giocoso"],
  ["comentaristas inspirados en IA", "opinionisti ispirati all'IA"],
  ["da personalidad a las previas", "dà personalità alle anteprime delle partite"],
  ["Sus avatares son versiones originales", "I loro avatar sono versioni originali"],
  ["caricatura cápsula hechas para este juego", "cartoon capsule creati per questo gioco"],
  ["¿Listo para unirte a la liga?", "Pronto a unirti al gioco?"],
  ["haz tus primeros pronósticos", "fai i tuoi primi pronostici"],
  ["invita tu subliga", "invita la tua sottogruppo"],
  ["disfruta la Copa 2026 juntos", "goditi il Mondiale 2026 insieme"],
  ["Estilo ", "Stile "],
  ["Predicción del experto", "Pronostico esperto"],
  ["Comentario del experto", "Commento esperto"],
  ["Guardar pronóstico", "Salva pronostico"],
  ["¡Pronóstico guardado!", "Pronostico salvato!"],
  ["Partido eliminatorio", "Partita eliminatoria"],
  ["predice el marcador después de", "pronostica il risultato dopo"],
  ["no cuentan", "non contano"],
  ["¿Quién avanza?", "Chi passa il turno?"],
  ["Partidos", "Partite"],
  ["Partido", "Partita"],
  ["partidos", "partite"],
  ["partido", "partita"],
  ["Clasificación", "Classifica"],
  ["clasificación", "classifica"],
  ["pronóstico", "pronostico"],
  ["pronósticos", "pronostici"],
  ["marcador", "risultato"],
  ["marcadores", "risultati"],
  ["estadio", "stadio"],
  ["estadios", "stadi"],
  ["fútbol", "calcio"],
  ["equipo", "squadra"],
  ["equipos", "squadre"],
  ["Iniciar sesión", "Accedi"],
  ["Crear cuenta", "Crea account"],
  ["Accedi", "Accedi"],
  ["Salir", "Esci"],
  ["Ayuda", "Aiuto"],
  ["Acerca de", "Info"],
  ["Panel", "Dashboard"],
  ["Calendario de partidos", "Calendario partite"],
  ["Visitante", "Trasferta"],
  ["Local", "Casa"],
  ["Grupo ", "Gruppo "],
  ["Subgrupo", "Sottogruppo"],
  ["subgrupo", "sottogruppo"],
  ["Versión", "Versione"],
  ["Cerrar", "Chiudi"],
  ["Cargando", "Caricamento"],
  ["Guardando", "Salvataggio"],
  ["Guardar", "Salva"],
  ["Eliminar", "Elimina"],
  ["No se pudo", "Impossibile"],
  ["no se pudo", "impossibile"],
  ["contraseña", "password"],
  ["usuario", "utente"],
  ["cuenta", "account"],
  ["correo", "email"],
  ["mensaje", "messaggio"],
  ["mensajes", "messaggi"],
  ["invitación", "invito"],
  ["Octavos", "Ottavi"],
  ["Cuartos", "Quarti"],
  ["Semifinales", "Semifinali"],
  ["Tercer puesto", "Terzo posto"],
  ["en curso", "in corso"],
  ["finalizado", "conclusa"],
  ["próximo", "in programma"],
  ["Por determinar", "Da definire"],
  ["Jugador", "Giocatore"],
  ["puntos", "punti"],
  [" — ", " — "],
];

ES_IT.sort((a, b) => b[0].length - a[0].length);

function walk(obj) {
  if (obj && typeof obj === "object" && !Array.isArray(obj)) {
    const out = {};
    for (const key of Object.keys(obj)) {
      out[key] = walk(obj[key]);
    }
    return out;
  }
  if (typeof obj === "string") {
    let s = obj;
    for (const [src, dst] of ES_IT) {
      if (src && s.includes(src)) s = s.split(src).join(dst);
    }
    return s;
  }
  return obj;
}

const es = JSON.parse(fs.readFileSync(path.join(i18n, "es.json"), "utf8"));
const it = walk(es);

Object.assign(it.navbar, {
  dashboard: "Dashboard",
  matches: "Partite",
  rankings: "Classifica",
  logout: "Esci",
  help: "Aiuto",
  about: "Info",
});

Object.assign(it.matchDetail.styles, {
  trump: "Stile Donald Trump",
  burr: "Stile Bill Burr",
  sponder: "Stile Yuh. Sponder",
  cantona: "Stile Eric Cantona",
  klopp: "Stile Jürgen Klopp",
  zlatan: "Stile Zlatan Ibrahimović",
  hudson: "Stile Ray Hudson",
  seinfeld: "Stile Jerry Seinfeld",
  carr: "Stile Jimmy Carr",
  maradona: "Stile Diego Maradona",
  gijp: "Stile René van der Gijp",
  derksen: "Stile Johan Derksen",
  lineker: "Stile Gary Lineker",
  al_sahhaf: "Stile Muhammad al-Sahhaf",
});

fs.writeFileSync(
  path.join(i18n, "it.json"),
  `${JSON.stringify(it, null, 2)}\n`,
  "utf8"
);
console.log("wrote it.json from es.json");
