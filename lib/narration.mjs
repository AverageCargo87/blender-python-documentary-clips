// Narration for any clip via ElevenLabs text-to-speech with per-character timestamps.
//   node lib/narration.mjs <clip>/data/narration.json <work root> [--price]
//
// mode "phrases" (clips 1 and 2): one request per phrase ->
//   <root>/golos/<id>.wav (24 kHz mono) + <root>/golos/slova.json  {id: {dlit, slova: [{w, s, e}]}}
// mode "groups" (clip 3): phrases are read in groups for a connected intonation and cut into sentences by letter timings ->
//   <root>/golos/<group>.wav + <root>/golos/frazy.json  {group: {dlit, frazy: [{id, s, e, txt}]}}
// Cache: <root>/golos/cache, so unchanged text spends no credits. '+' after a vowel is converted to a stress mark (U+0301).
// Config only via environment (or a .env file in the repository root): ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID.
import {readFileSync, writeFileSync, mkdirSync, existsSync} from 'node:fs';
import {join, dirname, resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';

const REPO = join(dirname(fileURLToPath(import.meta.url)), '..');

export function loadEnv(file = join(REPO, '.env')) {
  if (!existsSync(file)) return;
  for (const line of readFileSync(file, 'utf8').split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*["']?([^"'\r\n#]*)["']?\s*$/);
    if (m && !(m[1] in process.env)) process.env[m[1]] = m[2].trim();
  }
}

export const stress = s => s.replace(/\+/g, '́');

export function wavBytes(pcm, rate) {
  const hdr = Buffer.alloc(44); hdr.write('RIFF', 0); hdr.writeUInt32LE(36 + pcm.length, 4); hdr.write('WAVE', 8); hdr.write('fmt ', 12);
  hdr.writeUInt32LE(16, 16); hdr.writeUInt16LE(1, 20); hdr.writeUInt16LE(1, 22); hdr.writeUInt32LE(rate, 24); hdr.writeUInt32LE(rate * 2, 28);
  hdr.writeUInt16LE(2, 32); hdr.writeUInt16LE(16, 34); hdr.write('data', 36); hdr.writeUInt32LE(pcm.length, 40);
  return Buffer.concat([hdr, pcm]);
}

// word timings from the character alignment (stress marks and whitespace are not words)
export function words(al) {
  const slova = []; let cur = null;
  for (let i = 0; i < al.characters.length; i++) {
    const c = al.characters[i];
    if (/\s/.test(c)) { if (cur) { slova.push(cur); cur = null; } continue; }
    if (c === '́') continue;
    if (!cur) cur = {w: '', s: al.character_start_times_seconds[i], e: 0};
    cur.w += c; cur.e = al.character_end_times_seconds[i];
  }
  if (cur) slova.push(cur);
  return slova;
}

// sentence boundaries in a group: walk the returned characters and the group text in step
export function sentences(al, phrases) {
  const ch = al.characters, st = al.character_start_times_seconds, en = al.character_end_times_seconds;
  const frazy = []; let i = 0;
  for (const {id, text} of phrases) {
    const txt = stress(text); while (i < ch.length && /\s/.test(ch[i])) i++;
    const i0 = i; let k = 0;
    while (i < ch.length && k < txt.length) { if (ch[i] === txt[k]) k++; i++; }
    if (k < txt.length) console.log('warning: letters did not line up for', id);
    frazy.push({id, s: st[i0], e: en[i - 1], txt: text.replace(/\+/g, '')});
  }
  return frazy;
}

async function main() {
  const [cfgPath, ROOT] = process.argv.slice(2); const PRICE = process.argv.includes('--price');
  if (!cfgPath || !ROOT) { console.log('usage: node lib/narration.mjs <narration.json> <work root> [--price]'); process.exit(2); }
  loadEnv();
  const cfg = JSON.parse(readFileSync(cfgPath, 'utf8'));
  const key = process.env.ELEVENLABS_API_KEY || process.env.ELEVENLABS_TTS_API_KEY;
  const VOICE = cfg.voice.startsWith('$') ? process.env[cfg.voice.slice(1)] : cfg.voice;
  if (!key) throw new Error('ELEVENLABS_API_KEY is not set (see .env.example)');
  if (!VOICE) throw new Error(`${cfg.voice.slice(1)} is not set (see .env.example)`);
  const RATE = cfg.sample_rate || 24000, LIMIT = cfg.credit_cap || Infinity;
  const groups = cfg.mode === 'groups' ? cfg.groups : cfg.phrases.map(p => ({id: p.id, phrases: [p]}));
  console.log('characters', groups.flatMap(g => g.phrases).reduce((a, p) => a + p.text.replace(/[+́]/g, '').length, 0));

  async function api(url, opts = {}) {
    for (let i = 0; i < 14; i++) {
      const r = await fetch(url, {redirect: 'manual', ...opts, headers: {'xi-api-key': key, 'Content-Type': 'application/json', ...(opts.headers || {})}});
      if (r.status === 302 || r.status === 429 || r.status >= 500) { await new Promise(s => setTimeout(s, 1200 + 600 * i)); continue; }
      const t = await r.text();
      if (!r.ok) throw new Error(`${r.status} ${t.slice(0, 300)}`);
      return {t, cost: r.headers.get('character-cost')};
    }
    throw new Error('ElevenLabs did not answer in 14 attempts');
  }
  const sub = JSON.parse((await api('https://api.elevenlabs.io/v1/user/subscription')).t);
  console.log('ElevenLabs credits left', sub.character_limit - sub.character_count, 'of', sub.character_limit);
  if (PRICE) return;

  const D = join(ROOT, 'golos'), C = join(D, 'cache'); mkdirSync(C, {recursive: true});
  const out = {}; let spent = 0;
  for (const g of groups) {
    const say = g.phrases.map(p => stress(p.text)).join(' ');
    const body = {text: say, model_id: cfg.model, language_code: cfg.language, voice_settings: cfg.voice_settings};
    const f = join(C, createHash('sha1').update(JSON.stringify([VOICE, body])).digest('hex').slice(0, 14) + '.json');
    let j;
    if (existsSync(f)) j = JSON.parse(readFileSync(f, 'utf8'));
    else {
      if (spent > LIMIT) throw new Error(`credit cap ${LIMIT}: spent ${spent}`);
      const r = await api(`https://api.elevenlabs.io/v1/text-to-speech/${VOICE}/with-timestamps?output_format=pcm_${RATE}`, {method: 'POST', body: JSON.stringify(body)});
      spent += Number(r.cost) || 0; console.log(g.id, 'cost', r.cost); writeFileSync(f, r.t); j = JSON.parse(r.t);
    }
    const pcm = Buffer.from(j.audio_base64, 'base64');
    writeFileSync(join(D, g.id + '.wav'), wavBytes(pcm, RATE));
    const dlit = pcm.length / 2 / RATE;
    out[g.id] = cfg.mode === 'groups' ? {dlit, frazy: sentences(j.alignment, g.phrases)} : {dlit, slova: words(j.alignment)};
    console.log(g.id, dlit.toFixed(2), 's');
  }
  writeFileSync(join(D, cfg.mode === 'groups' ? 'frazy.json' : 'slova.json'), JSON.stringify(out, null, 1));
  console.log('done; credits spent:', spent);
}

if (process.argv[1] && resolve(process.argv[1]).toLowerCase() === fileURLToPath(import.meta.url).toLowerCase()) await main();
