(function (root) {
const ROW_H=34, ACTOR_W=124, ACTOR_GAP=12, PAD_L=54, ROWNUM_X=42, PAD_R=18,
      GUTTER_GAP=26, ACTOR_H=46, TOP=14, INSET=6, HEAD=7, BAND_H=22, SELF_W=24,
      LEGEND_H=30, RAIL_W=11;
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const tc=t=>t&&t!=='plain'?' t-'+t:'';
function renderSequence(spec){
  const A=spec.actors, S=spec.steps;
  const cx={}; A.forEach((a,i)=>cx[a.id]=PAD_L+i*(ACTOR_W+ACTOR_GAP)+ACTOR_W/2);
  const lastX=PAD_L+(A.length-1)*(ACTOR_W+ACTOR_GAP)+ACTOR_W;
  const hasNote=S.some(s=>s.note);
  const noteX=lastX+GUTTER_GAP;
  const maxNote=Math.max(0,...S.filter(s=>s.note).map(s=>String(s.note).length*6.7));
  const W=(hasNote?noteX+maxNote:lastX)+PAD_R;
  const yOf=[]; let y=TOP+ACTOR_H+16, phases=[];
  S.forEach((s,i)=>{ if(s.phase){ phases.push({y:y+8,label:s.phase}); y+=ROW_H; } yOf[i]=y+ROW_H/2; y+=ROW_H; });
  const bodyEnd=y+6;
  const H=bodyEnd+(spec.legend?LEGEND_H:0)+10;
  let o=`<svg class="seq" role="img" aria-label="${esc(spec.alt||'sequence diagram')}" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">`;
  (spec.rails||[]).forEach(r=>{
    const x=cx[r.actor]-RAIL_W/2, y0=yOf[r.from]-13, y1=yOf[r.to]+13;
    o+=`<rect class="rail${tc(r.tone)}" x="${x}" y="${y0}" width="${RAIL_W}" height="${y1-y0}" rx="2"/>`;
    if(r.label) o+=`<text class="rail-cap${tc(r.tone)}" x="${cx[r.actor]}" y="${y0-5}" text-anchor="middle">${esc(r.label)}</text>`;
  });
  A.forEach((a,i)=>{
    const x=PAD_L+i*(ACTOR_W+ACTOR_GAP), c=x+ACTOR_W/2;
    o+=`<path class="lane" d="M ${c} ${TOP+ACTOR_H} L ${c} ${bodyEnd}"/>`;
    o+=`<rect class="actor-box${tc(a.tone)}" x="${x}" y="${TOP}" width="${ACTOR_W}" height="${ACTOR_H}" rx="3"/>`;
    const lines=a.label.split('\n');
    lines.forEach((ln,k)=>{ o+=`<text class="actor-label" x="${c}" y="${TOP+(lines.length===1?27:18+k*13)}" text-anchor="middle">${esc(ln)}</text>`; });
  });
  phases.forEach(p=>{ o+=`<path class="phase-rule" d="M ${PAD_L-12} ${p.y-9} L ${lastX} ${p.y-9}"/>`+`<text class="phase-label" x="${PAD_L-12}" y="${p.y+4}">${esc(p.label)}</text>`; });
  let n=0;
  S.forEach((s,i)=>{
    const y=yOf[i], t=tc(s.tone);
    if(s.arrow==='band'){
      const xs=s.span?s.span.map(id=>cx[id]):[cx[A[0].id],cx[A[A.length-1].id]];
      const x0=Math.min(...xs)-46, x1=Math.max(...xs)+46;
      o+=`<rect class="band${t}" x="${x0}" y="${y-BAND_H/2}" width="${x1-x0}" height="${BAND_H}" rx="3"/>`+`<text class="band-text${t}" x="${x0+10}" y="${y+4}">${esc(s.label)}</text>`;
      return;
    }
    n++;
    o+=`<text class="row-num" x="${ROWNUM_X}" y="${y+4}" text-anchor="end">${n}</text>`;
    if(s.note) o+=`<text class="row-note${t}" x="${noteX}" y="${y+4}">${esc(s.note)}</text>`;
    if(s.arrow==='self'){
      const c=cx[s.from];
      o+=`<path class="arr${t}${s.dashed?' dashed':''}" d="M ${c} ${y-8} h ${SELF_W} v 16 h ${-SELF_W+INSET}"/>`+`<path class="arr-head${t}" d="M ${c+INSET} ${y+8} l ${HEAD} -3.6 v 7.2 z"/>`+`<text class="arrow-label${t}" x="${c+SELF_W+10}" y="${y-3}">${esc(s.label)}</text>`;
      if(s.sub) o+=`<text class="arrow-sub${t}" x="${c+SELF_W+10}" y="${y+11}">${esc(s.sub)}</text>`;
      return;
    }
    const a=cx[s.from], b=cx[s.to], dir=b>a?1:-1, x0=a+INSET*dir, x1=b-INSET*dir;
    o+=`<path class="arr${t}${s.arrow==='event'?' dashed':''}" d="M ${x0} ${y} L ${x1} ${y}"/>`+`<path class="arr-head${t}" d="M ${x1} ${y} l ${-HEAD*dir} -3.6 v 7.2 z"/>`+`<text class="arrow-label${t}" x="${(x0+x1)/2}" y="${y-6}" text-anchor="middle">${esc(s.label)}</text>`;
    if(s.sub) o+=`<text class="arrow-sub${t}" x="${(x0+x1)/2}" y="${y+13}" text-anchor="middle">${esc(s.sub)}</text>`;
  });
  if(spec.legend){
    let x=PAD_L-2; const ly=bodyEnd+18;
    spec.legend.forEach(l=>{ o+=`<path class="legend-swatch${tc(l.tone)}" d="M ${x} ${ly} h 22"/>`+`<text class="legend-text" x="${x+28}" y="${ly+4}">${esc(l.label)}</text>`; x+=22+8+l.label.length*6.6+24; });
  }
  return o+'</svg>';
}

  const api = { renderSequence };
  root.TxPlay = Object.assign(root.TxPlay || {}, api);
  if (typeof module !== 'undefined') module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
