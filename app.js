/* M2CATS — conceptual orbital animation for the hero.
   The scenario explorer from the previous version was removed with its
   section; only the globe animation remains. */
const canvas=document.getElementById('orbit'),ctx=canvas.getContext('2d'),reduce=matchMedia('(prefers-reduced-motion: reduce)');
let paused=reduce.matches,frame=0,w=0,h=0,t=0;
const motion=document.getElementById('motion');
function syncButton(){motion.textContent=paused?'Resume motion':'Pause motion';motion.setAttribute('aria-pressed',String(paused))}
syncButton();
function resize(){const dpr=Math.min(devicePixelRatio||1,2);w=canvas.clientWidth;h=canvas.clientHeight;canvas.width=w*dpr;canvas.height=h*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);draw()}
new ResizeObserver(resize).observe(canvas);
function project(x,y,z){const a=.32;return [w*.51+(x*Math.cos(a)+z*Math.sin(a)),h*.5+y*.94-(z*Math.cos(a)-x*Math.sin(a))*.16,z]}
function draw(){ctx.clearRect(0,0,w,h);const r=Math.min(w*.34,h*.35);ctx.lineWidth=.7;for(let latitude=-75;latitude<=75;latitude+=15){const lat=latitude*Math.PI/180;ctx.beginPath();for(let j=0;j<=120;j++){const a=j/120*Math.PI*2,p=project(r*Math.cos(lat)*Math.cos(a),r*Math.sin(lat),r*Math.cos(lat)*Math.sin(a));j?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1])}ctx.strokeStyle='#24445880';ctx.stroke()}for(let meridian=0;meridian<180;meridian+=15){ctx.beginPath();for(let j=0;j<=120;j++){const a=j/120*Math.PI*2,b=meridian*Math.PI/180,p=project(r*Math.cos(a)*Math.cos(b),r*Math.sin(a),r*Math.cos(a)*Math.sin(b));j?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1])}ctx.strokeStyle='#24445870';ctx.stroke()}const nodes=[];for(let plane=0;plane<4;plane++){const inclination=(plane*39+20)*Math.PI/180,rad=r*(1.21+plane*.018);function point(a){return project(rad*Math.cos(a)*Math.cos(inclination)-rad*.38*Math.sin(a)*Math.sin(inclination),rad*Math.cos(a)*Math.sin(inclination)+rad*.38*Math.sin(a)*Math.cos(inclination),rad*.7*Math.sin(a))}ctx.beginPath();for(let j=0;j<=150;j++){const p=point(j/150*Math.PI*2);j?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1])}ctx.strokeStyle=plane===1?'#b692505c':'#668b9b45';ctx.stroke();for(let n=0;n<7;n++){const p=point(n/7*Math.PI*2+t+plane*.3);nodes.push(p);ctx.fillStyle=plane===1?'#f0bc70':'#8cbbca';ctx.shadowColor=ctx.fillStyle;ctx.shadowBlur=9;ctx.beginPath();ctx.arc(p[0],p[1],2.5,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0}}for(let i=0;i<nodes.length;i++){for(let j=i+1;j<nodes.length;j++){const a=nodes[i],b=nodes[j],d=Math.hypot(a[0]-b[0],a[1]-b[1]);if(d<r*.57&&d>r*.2&&a[2]>0&&b[2]>0){ctx.beginPath();ctx.moveTo(a[0],a[1]);ctx.lineTo(b[0],b[1]);ctx.strokeStyle='#70b7c625';ctx.stroke()}}}ctx.fillStyle='#7394a7';ctx.font='10px monospace';ctx.fillText('CONCEPTUAL ORBITAL GEOMETRY',w*.2,h*.9)}
function animate(){if(!paused){t+=.0015;draw()}frame=requestAnimationFrame(animate)}
motion.addEventListener('click',()=>{paused=!paused;syncButton()});
reduce.addEventListener('change',e=>{paused=e.matches;syncButton()});
resize();animate();