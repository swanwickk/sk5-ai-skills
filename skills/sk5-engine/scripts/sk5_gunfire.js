// Driver for the verbatim site JS (sk5_site.js, extracted from https://sk5.swanwick.site/).
// Usage: node sk5_gunfire.js cases.json [--seed N]
// cases.json: [{id, hit:{shell_count, base_fc, visibility, time_of_day, moonlight,
//   target_profile, target_distance, ship_type, on_fire, using_searchlight, blind_fire,
//   battle_smoke, boiler_smoke, evasion, fire_history, multi_ship_fire,
//   normal_fire_groups, concentrated_fire_groups, target_size, spotter_plane,
//   battle_rating, radar, other_modifiers},
//  dmg:{bore, ship_penetration, shell_type, damage_factor, launch_date, armor:{1H..9V}}}]
// Output: JSON array with result_text / damage_result_text / summary_text per case.
'use strict';
const fs = require('fs');

function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---- DOM stub ----
function makeEl(id) {
  return {
    id, value: '', checked: false, textContent: '',
    style: {}, classList: { add() {}, remove() {} },
    addEventListener() {}, focus() {}, select() {},
  };
}
const __els = {};
global.document = {
  getElementById(id) { return __els[id] || (__els[id] = makeEl(id)); },
  createElement() { return makeEl('tmp'); },
  body: { appendChild() {}, removeChild() {} },
  execCommand() { return false; },
  querySelectorAll() { return []; },
  querySelector() { return null; },
};
global.window = global.window || { isSecureContext: false };
try { global.navigator = global.navigator || {}; } catch (e) { /* node>=21 只读, 站点仅读clipboard可跳过 */ }

function loadSite() {
  const src = fs.readFileSync(__dirname + '/sk5_site.js', 'utf8');
  const fn = new Function('document', 'window', 'navigator', 'setTimeout', 'clearTimeout', src + `
;return { calculateHits, calculateDamage, generateSummary, DE_TABLE,
          getState: () => ({ lastHitsState, lastLocationStats, lastDamageState }),
          // 通用DE查询：queryDE(era, roll, col)，era=1905/1922/1945/CV，col=1-9/G/F/T
          queryDE: (era, roll, col) => { const t = DE_TABLE[era]; if (!t) return null;
            for (const b of t) if (roll >= b.l && roll <= b.h) return b.v[col] !== undefined ? b.v[col] : null;
            return null; } };`);
  return fn(global.document, global.window, global.navigator, setTimeout, clearTimeout);
}

function setHitInputs(h) {
  const E = (id) => document.getElementById(id);
  E('shell_count').value = String(h.shell_count);
  E('base_fire_control').value = String(h.base_fc);
  E('visibility').value = h.visibility || '6-7 (0)';
  E('time_of_day').value = h.time_of_day || '夜间';
  E('moonlight').value = h.moonlight || '有月光 (-2)';
  E('sun_position').value = h.sun_position || '无影响 (0)';
  E('target_profile').value = h.target_profile || '宽';
  E('target_distance').value = h.target_distance || '中';
  E('ship_type').value = h.ship_type || '炮舰';
  E('on_fire').checked = !!h.on_fire;
  E('using_searchlight').checked = !!h.using_searchlight;
  E('blind_fire').checked = !!h.blind_fire;
  E('battle_smoke').value = h.battle_smoke == null ? '' : String(h.battle_smoke);
  E('boiler_smoke').value = h.boiler_smoke == null ? '' : String(h.boiler_smoke);
  E('evasion').value = h.evasion || '无 (0)';
  E('fire_history').value = h.fire_history || '无 (0)';
  E('multi_ship_fire').checked = !!h.multi_ship_fire;
  E('normal_fire_groups').value = h.normal_fire_groups == null ? '' : String(h.normal_fire_groups);
  E('concentrated_fire_groups').value = h.concentrated_fire_groups == null ? '' : String(h.concentrated_fire_groups);
  E('target_size').value = String(h.target_size == null ? 0 : h.target_size);
  E('spotter_plane').checked = !!h.spotter_plane;
  E('battle_rating').value = h.battle_rating == null ? '' : String(h.battle_rating);
  E('radar').value = h.radar == null ? '' : String(h.radar);
  E('other_modifiers').value = h.other_modifiers == null ? '' : String(h.other_modifiers);
}

function setDmgInputs(g) {
  const E = (id) => document.getElementById(id);
  E('bore').value = g.bore;
  E('ship_penetration').value = g.ship_penetration;
  E('shell_type').value = g.shell_type;
  E('damage_factor').value = String(g.damage_factor);
  E('launch_date').value = g.launch_date;
  for (const k of ['1H', '2H', '3H', '4V', '5V', '6V', '7V', '8V', '9V']) {
    document.getElementById('armor_' + k).value = (g.armor && g.armor[k] != null) ? String(g.armor[k]) : '';
  }
}

function main() {
  const args = process.argv.slice(2);
  const seedArg = args.indexOf('--seed');
  const seed = seedArg >= 0 ? parseInt(args[seedArg + 1], 10) : 12345;
  const file = args[0];
  const cases = JSON.parse(fs.readFileSync(file, 'utf8'));
  const api = loadSite();
  const out = [];
  cases.forEach((c, i) => {
    Math.random = mulberry32(seed + i); // ponytail: deterministic rolls per case; drop --seed for true random
    setHitInputs(c.hit);
    api.calculateHits();
    const r = { id: c.id, result_text: document.getElementById('result_text').value };
    const st = api.getState();
    r.hits = st.lastHitsState.hits;
    r.locations = st.lastLocationStats;
    if (c.dmg && st.lastHitsState.hits > 0) {
      setDmgInputs(c.dmg);
      api.calculateDamage();
      r.damage_result_text = document.getElementById('damage_result_text').value;
      api.generateSummary();
      r.summary_text = document.getElementById('summary_text').value;
      r.totalDamage = api.getState().lastDamageState.totalDamage;
    }
    out.push(r);
  });
  console.log(JSON.stringify(out, null, 1));
}

main();
