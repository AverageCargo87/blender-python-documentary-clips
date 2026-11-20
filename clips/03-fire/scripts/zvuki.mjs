// Clip 3 'Fire': sounds of the storm, campfire, friction, stone strike and animal via ElevenLabs Sound Effects.
//   node zvuki.mjs <root> [--price]
// Output: <root>/zvuk/<name>.mp3. Existing files are not regenerated (no credits spent). Spending cap: LIMIT credits.
import {readFileSync, writeFileSync, mkdirSync, existsSync} from 'node:fs';
import {join} from 'node:path';
const ROOT = process.argv[2], CENA = process.argv.includes('--price');
import {loadEnv} from '../../../lib/narration.mjs';
const LIMIT = 1500;                    // agreed spending cap of about 1000-1500 credits
const ZVUKI = [                        // name, duration (s), description
  ['grom', 6, 'A single close lightning strike at night on an open plain: one sharp electric crack, then deep rolling thunder that slowly fades away. No rain, no music, no voices.'],
  ['veter', 8, 'Night wind blowing steadily through tall dry savanna grass before a storm, soft rustling gusts, wide open space. No rain, no thunder, no animals, no music.'],
  ['koster', 10, 'Close-up of a small campfire burning steadily at night: soft crackling and gentle popping of dry wood, low calm flame. Quiet surroundings, no voices, no music, no wind.'],
  ['trenie', 5, 'Making fire by friction: a wooden stick spun rapidly back and forth by hand in a dry wooden board, fast rhythmic dry wood rubbing and squeaking, close-up. No voices, no music.'],
  ['udar', 1, 'One short sharp click of a flint stone striking another stone, dry, close-up, no reverb.'],
  ['giena', 4, 'A large wild animal in the dark: one low quiet menacing growl, then a short snort and soft retreating steps through dry grass. No music, no other sounds.'],
  ['vspyshka', 3, 'A burning branch collapses in a campfire: a wood crack, a burst of sparks and the flames flare up with a soft whoosh, then crackle. No voices, no music.'],
  ['derevo', 8, 'A big dry tree burning outdoors at night: strong roaring flames, loud crackling and snapping of branches, gusts of wind feeding the fire. No voices, no music, no sirens.'],
  ['golovnya', 6, 'A burning wooden torch carried at night through tall dry grass: the flame flutters and whooshes softly, steady footsteps brushing through the grass. No voices, no music.'],
  ['razgoranie', 3, 'A handful of dry grass tinder catches fire: a soft puff and whoosh as a small flame flares up, then quiet crackling. Close-up, no voices, no music.'],
];
loadEnv(); const key = process.env.ELEVENLABS_API_KEY || process.env.ELEVENLABS_TTS_API_KEY;
if (!key) throw new Error('ELEVENLABS_API_KEY is not set');
async function api(url, opts = {}, bin = false) {
  for (let i = 0; i < 14; i++) {
    const r = await fetch(url, {redirect: 'manual', ...opts, headers: {'xi-api-key': key, 'Content-Type': 'application/json', ...(opts.headers || {})}});
    if (r.status === 302 || r.status === 429 || r.status >= 500) { await new Promise(s => setTimeout(s, 1200 + 600 * i)); continue; }
    if (!r.ok) throw new Error(`${r.status} ${(await r.text()).slice(0, 300)}`);
    return {t: bin ? Buffer.from(await r.arrayBuffer()) : await r.text(), cost: r.headers.get('character-cost')};
  }
  throw new Error('ElevenLabs did not answer in 14 attempts');
}
const ostatok = async () => { const s = JSON.parse((await api('https://api.elevenlabs.io/v1/user/subscription')).t); return s.character_limit - s.character_count; };
const do_ = await ostatok(); console.log('ElevenLabs credits before:', do_);
console.log('total seconds:', ZVUKI.reduce((a, z) => a + z[1], 0));
if (CENA) process.exit(0);
const D = join(ROOT, 'zvuk'); mkdirSync(D, {recursive: true});
let potracheno = 0;
for (const [imya, dlit, opis] of ZVUKI) {
  const f = join(D, imya + '.mp3');
  if (existsSync(f)) { console.log(imya, 'already exists'); continue; }
  const pered = await ostatok();
  if (do_ - pered + dlit * 45 > LIMIT) { console.log('STOP: spending cap reached, not generated:', imya); break; }
  const r = await api('https://api.elevenlabs.io/v1/sound-generation', {method: 'POST', body: JSON.stringify({text: opis, duration_seconds: dlit, prompt_influence: .45})}, true);
  writeFileSync(f, r.t); const posle = await ostatok(); potracheno = do_ - posle;
  console.log(imya, dlit + ' s', 'bytes', r.t.length, 'cost by header', r.cost, 'by counter', pered - posle, 'total', potracheno);
}
console.log('ElevenLabs credits after:', await ostatok(), 'spent', potracheno);
