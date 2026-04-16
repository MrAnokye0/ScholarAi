"""ScholarAI - Futuristic Landing Page 2026"""
import streamlit as st


def render_home():
    if st.query_params.get("go") == "app":
        st.query_params.clear()
        st.session_state.show_home = False
        st.rerun()

    # Kill all Streamlit chrome
    st.markdown("""<style>
[data-testid="stSidebar"],[data-testid="stHeader"],[data-testid="stToolbar"],
.stMainHeader,footer,#MainMenu,[data-testid="stDecoration"]{display:none!important}
.stApp{background:#0B0F19!important}
.main .block-container{padding:0!important;margin:0!important;max-width:100%!important;width:100%!important}
.main{padding:0!important}
section.main>div{padding:0!important}
/* Remove Streamlit default top padding/margin that causes white space */
.stApp > header{display:none!important}
.stApp{overflow-x:hidden!important}
iframe{border:none!important}

/* Force all links to open in same tab */
a{text-decoration:none !important}
a[href]{target:_self !important}

/* Mobile-first responsive design */
@media(max-width:768px){
  html,body{font-size:14px!important}
}
@media(max-width:480px){
  html,body{font-size:13px!important}
}
</style>""", unsafe_allow_html=True)

    # ── ANIMATED FLOATING ISLAND BACKGROUND + NAV + HERO ──────────────────────────────
    # Add base tag to force same-tab navigation
    st.markdown('<base target="_self">', unsafe_allow_html=True)
    
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Inter:wght@300;400;500;600;700&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --c1:#4361EE;--c2:#7209B7;--c3:#06D6A0;--c4:#F72585;
  --bg:#0B0F19;--bg2:#0D1117;--wh:#F1F5F9;--mu:#64748B;--mu2:#94A3B8;
  --glass:rgba(255,255,255,0.04);--glass2:rgba(255,255,255,0.07);
  --border:rgba(255,255,255,0.08);--border2:rgba(67,97,238,0.35);
  --glow1:rgba(67,97,238,0.5);--glow2:rgba(114,9,183,0.4);
  --ease:cubic-bezier(0.16,1,0.3,1);
}
html,body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--wh);overflow-x:hidden;scroll-behavior:smooth}

/* ANIMATED FLOATING ISLAND BACKGROUND */
#floating-bg{
  position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;
  background:linear-gradient(180deg, #0B0F19 0%, #1a1f35 50%, #2d1b3d 100%);
  overflow:hidden;
}
/* Main floating island - centered */
#floating-bg::before{
  content:'';
  position:absolute;
  top:50%;left:50%;
  transform:translate(-50%,-50%);
  width:700px;height:700px;
  background-image:url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800"><defs><linearGradient id="sky" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" style="stop-color:%234361EE;stop-opacity:0.4"/><stop offset="100%" style="stop-color:%237209B7;stop-opacity:0.2"/></linearGradient><linearGradient id="island" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" style="stop-color:%2306D6A0;stop-opacity:0.5"/><stop offset="50%" style="stop-color:%234361EE;stop-opacity:0.4"/><stop offset="100%" style="stop-color:%237209B7;stop-opacity:0.3"/></linearGradient><radialGradient id="glow"><stop offset="0%" style="stop-color:%234361EE;stop-opacity:0.7"/><stop offset="100%" style="stop-color:%234361EE;stop-opacity:0"/></radialGradient></defs><ellipse cx="400" cy="650" rx="350" ry="120" fill="url(%23island)" opacity="0.6"/><ellipse cx="400" cy="500" rx="280" ry="200" fill="url(%23sky)" opacity="0.5"/><circle cx="400" cy="350" r="150" fill="url(%23glow)" opacity="0.4"/><ellipse cx="350" cy="400" rx="120" ry="100" fill="%2306D6A0" opacity="0.35"/><ellipse cx="450" cy="420" rx="100" ry="80" fill="%234361EE" opacity="0.4"/><circle cx="400" cy="300" r="80" fill="%23F72585" opacity="0.3"/><ellipse cx="370" cy="320" rx="50" ry="40" fill="%2306D6A0" opacity="0.45"/><ellipse cx="430" cy="340" rx="45" ry="35" fill="%237209B7" opacity="0.4"/><circle cx="400" cy="280" r="35" fill="%234361EE" opacity="0.5"/><circle cx="380" cy="290" r="20" fill="%2306D6A0" opacity="0.4"/><circle cx="420" cy="310" r="18" fill="%23F72585" opacity="0.35"/></svg>');
  background-size:contain;
  background-repeat:no-repeat;
  background-position:center;
  opacity:0.25;
  filter:blur(1px);
  animation:float-island 25s ease-in-out infinite;
}
.floating-island{
  position:absolute;
  width:600px;height:600px;
  background-image:url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400"><defs><linearGradient id="g1" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" style="stop-color:%2306D6A0;stop-opacity:0.4"/><stop offset="100%" style="stop-color:%234361EE;stop-opacity:0.2"/></linearGradient></defs><ellipse cx="200" cy="300" rx="180" ry="80" fill="url(%23g1)" opacity="0.7"/><ellipse cx="200" cy="200" rx="150" ry="150" fill="%237209B7" opacity="0.3"/><circle cx="200" cy="150" r="80" fill="%2306D6A0" opacity="0.4"/><circle cx="180" cy="140" r="40" fill="%234361EE" opacity="0.5"/><circle cx="220" cy="160" r="30" fill="%23F72585" opacity="0.4"/></svg>');
  background-size:contain;background-repeat:no-repeat;background-position:center;
  animation:float-island 20s ease-in-out infinite;
  opacity:0.18;filter:blur(30px);
}
.floating-island:nth-child(1){top:10%;left:10%;animation-delay:0s}
.floating-island:nth-child(2){top:60%;right:15%;animation-delay:-7s;width:500px;height:500px}
.floating-island:nth-child(3){bottom:10%;left:50%;animation-delay:-14s;width:400px;height:400px}

@keyframes float-island{
  0%,100%{transform:translateY(0) rotate(0deg) scale(1)}
  25%{transform:translateY(-30px) rotate(2deg) scale(1.05)}
  50%{transform:translateY(-50px) rotate(-2deg) scale(1.1)}
  75%{transform:translateY(-30px) rotate(1deg) scale(1.05)}
}

/* Animated particles */
.particle{
  position:absolute;width:4px;height:4px;border-radius:50%;
  background:radial-gradient(circle,rgba(99,120,255,0.8),transparent);
  animation:particle-float 15s linear infinite;
}
@keyframes particle-float{
  0%{transform:translateY(100vh) translateX(0) scale(0);opacity:0}
  10%{opacity:1}
  90%{opacity:1}
  100%{transform:translateY(-100vh) translateX(100px) scale(1);opacity:0}
}

/* CANVAS for additional effects */
#bg-canvas{position:fixed;top:0;left:0;width:100%;height:100%;z-index:1;pointer-events:none;opacity:0.4}

/* NAV */
.xnav{
  position:fixed;top:0;left:0;right:0;z-index:1000;
  display:flex;align-items:center;justify-content:space-between;
  padding:0 48px;height:64px;
  background:rgba(11,15,25,0.7);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  border-bottom:1px solid var(--border);
  transition:transform .4s var(--ease),background .3s;
}
.xnav.hide{transform:translateY(-100%)}
.xnav-logo{display:flex;align-items:center;gap:10px;text-decoration:none;position:relative;z-index:1;cursor:pointer}
.xnav-icon{
  width:36px;height:36px;border-radius:9px;
  background:linear-gradient(135deg,var(--c1),var(--c2));
  display:flex;align-items:center;justify-content:center;
  box-shadow:0 0 20px var(--glow1);transition:.3s;
}
.xnav-logo:hover .xnav-icon{box-shadow:0 0 32px var(--glow1),0 0 60px var(--glow2);transform:scale(1.08)}
.xnav-name{font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:800;color:var(--wh);letter-spacing:-.01em}
.xnav-links{display:flex;align-items:center;gap:6px}
.xnav-links a{
  color:var(--mu2);text-decoration:none;font-size:0.875rem;font-weight:500;
  padding:6px 14px;border-radius:8px;transition:.2s;position:relative;cursor:pointer;
}
.xnav-links a:hover{color:var(--wh);background:rgba(255,255,255,0.06)}
.xnav-right{display:flex;align-items:center;gap:10px}
@media(max-width:768px){
  .xnav{padding:0 20px!important}
  .xnav-links{display:none!important}
  .xnav-signin{display:none!important}
}
.xnav-signin{
  color:var(--mu2);text-decoration:none;font-size:0.875rem;font-weight:500;
  padding:8px 18px;border-radius:8px;border:1px solid var(--border);
  background:transparent;transition:.2s;display:inline-block;cursor:pointer;
}
.xnav-signin:hover{color:var(--wh);border-color:rgba(255,255,255,0.2);background:var(--glass)}
.xnav-cta{
  padding:8px 20px;border-radius:8px;border:none;cursor:pointer;
  font-weight:600;font-size:0.875rem;font-family:'Inter',sans-serif;
  background:linear-gradient(135deg,var(--c1),var(--c2));color:#fff;
  box-shadow:0 0 20px var(--glow1);transition:.25s;text-decoration:none;display:inline-block;
  position:relative;overflow:hidden;
}
.xnav-cta::after{content:'';position:absolute;inset:0;background:linear-gradient(135deg,rgba(255,255,255,0.15),transparent);opacity:0;transition:.2s}
.xnav-cta:hover{transform:translateY(-1px);box-shadow:0 0 32px var(--glow1),0 4px 20px rgba(67,97,238,0.4);color:#fff}
.xnav-cta:hover::after{opacity:1}

/* HERO */
.xhero{
  min-height:100vh;display:flex;flex-direction:column;align-items:center;
  justify-content:center;text-align:center;padding:120px 24px 80px;
  position:relative;z-index:1;
}
@media(max-width:768px){
  .xhero{padding:100px 20px 60px;min-height:auto}
}
@media(max-width:480px){
  .xhero{padding:90px 16px 50px}
}
.xhero-eyebrow{
  display:inline-flex;align-items:center;gap:8px;
  padding:6px 16px;border-radius:999px;
  background:rgba(67,97,238,0.1);border:1px solid rgba(67,97,238,0.3);
  font-size:0.75rem;font-weight:600;color:#818cf8;letter-spacing:.08em;text-transform:uppercase;
  margin-bottom:32px;
  animation:fadeUp .8s var(--ease) both;
}
@media(max-width:480px){
  .xhero-eyebrow{font-size:0.65rem;padding:5px 12px;gap:6px;margin-bottom:24px}
}
.xhero-dot{width:6px;height:6px;border-radius:50%;background:var(--c3);display:inline-block;animation:xpulse 2s infinite}
.xhero-h1{
  font-family:'Syne',sans-serif;
  font-size:clamp(2rem,8vw,5.5rem);
  font-weight:800;line-height:1.05;letter-spacing:-.04em;
  margin-bottom:24px;
  animation:fadeUp .9s .1s var(--ease) both;
}
@media(max-width:768px){
  .xhero-h1{font-size:clamp(2rem,10vw,3.5rem);margin-bottom:20px}
}
@media(max-width:480px){
  .xhero-h1{font-size:clamp(1.8rem,12vw,2.5rem);margin-bottom:16px}
}
.xhero-h1 .line2{
  background:linear-gradient(90deg,#818cf8 0%,#c77dff 40%,var(--c3) 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  background-size:200% auto;animation:shimmer 4s linear infinite;
}
.xhero-sub{
  max-width:580px;font-size:1.1rem;color:var(--mu2);line-height:1.8;
  margin-bottom:48px;font-weight:400;
  animation:fadeUp 1s .2s var(--ease) both;
}
@media(max-width:768px){
  .xhero-sub{font-size:1rem;margin-bottom:36px;max-width:90%}
}
@media(max-width:480px){
  .xhero-sub{font-size:0.9rem;margin-bottom:32px;line-height:1.6}
}
.xhero-btns{
  display:flex;gap:14px;flex-wrap:wrap;justify-content:center;
  animation:fadeUp 1s .3s var(--ease) both;
}
@media(max-width:480px){
  .xhero-btns{gap:10px;width:100%;flex-direction:column;max-width:300px}
}
.xhero-note{
  margin-top:20px;font-size:0.78rem;color:rgba(100,116,139,0.8);
  animation:fadeUp 1s .4s var(--ease) both;
}
@media(max-width:480px){
  .xhero-note{font-size:0.7rem;margin-top:16px;padding:0 10px}
}

/* BUTTONS */
.xbtn-p{
  padding:14px 32px;border-radius:10px;border:none;cursor:pointer;
  background:linear-gradient(135deg,var(--c1),var(--c2));color:#fff;
  font-weight:700;font-size:0.95rem;font-family:'Inter',sans-serif;
  box-shadow:0 0 24px var(--glow1);transition:.25s;
  text-decoration:none !important;display:inline-flex;align-items:center;gap:8px;
  position:relative;overflow:hidden;justify-content:center;
}
@media(max-width:480px){
  .xbtn-p{padding:12px 24px;font-size:0.9rem;width:100%}
}
.xbtn-p::before{content:'';position:absolute;top:0;left:-100%;width:100%;height:100%;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.15),transparent);transition:.5s}
.xbtn-p:hover{transform:translateY(-2px);box-shadow:0 0 40px var(--glow1),0 8px 30px rgba(67,97,238,0.4);color:#fff;text-decoration:none !important}
.xbtn-p:hover::before{left:100%}
.xbtn-s{
  padding:14px 32px;border-radius:10px;
  border:1px solid rgba(255,255,255,0.12);cursor:pointer;
  background:rgba(255,255,255,0.05);color:var(--wh);
  font-weight:600;font-size:0.95rem;font-family:'Inter',sans-serif;
  backdrop-filter:blur(12px);transition:.25s;
  text-decoration:none !important;display:inline-flex;align-items:center;gap:8px;
  justify-content:center;
}
@media(max-width:480px){
  .xbtn-s{padding:12px 24px;font-size:0.9rem;width:100%}
}
.xbtn-s:hover{background:rgba(255,255,255,0.09);border-color:rgba(255,255,255,0.22);color:var(--wh);transform:translateY(-2px);text-decoration:none !important}
/* kill ALL link underlines on this page */
a{text-decoration:none !important}
a:hover{text-decoration:none !important}

/* Force all links to open in same tab */
a[href]{
  target: _self !important;
}
a[href*="?go=app"]{
  target: _self !important;
}

/* FLOATING HERO CARD */
.xhero-card{
  margin-top:64px;
  background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);
  border-radius:20px;padding:24px 32px;
  display:inline-flex;align-items:center;gap:20px;
  backdrop-filter:blur(20px);
  box-shadow:0 20px 60px rgba(0,0,0,0.4),0 0 0 1px rgba(255,255,255,0.05);
  animation:fadeUp 1s .5s var(--ease) both,float 6s ease-in-out infinite 1.5s;
  flex-wrap:wrap;justify-content:center;
}
@media(max-width:900px){
  .xhero-card{padding:20px 24px;gap:16px;margin-top:48px}
}
@media(max-width:768px){
  .xhero-card{padding:16px 20px;gap:12px;margin-top:40px;max-width:90%}
}
@media(max-width:600px){
  .xhero-card{flex-direction:column;gap:16px;padding:20px;width:90%;max-width:350px}
}
.xhero-card-step{
  display:flex;align-items:center;gap:10px;padding:0 20px;
  border-right:1px solid rgba(255,255,255,0.08);
}
@media(max-width:900px){
  .xhero-card-step{padding:0 12px;gap:8px}
}
@media(max-width:600px){
  .xhero-card-step{border-right:none;border-bottom:1px solid rgba(255,255,255,0.08);padding:12px 0;width:100%;justify-content:center}
  .xhero-card-step:last-child{border-bottom:none}
}
.xhero-card-step:last-child{border-right:none}
.xhero-card-num{
  width:32px;height:32px;border-radius:8px;
  background:linear-gradient(135deg,var(--c1),var(--c2));
  display:flex;align-items:center;justify-content:center;
  font-size:0.8rem;font-weight:800;color:#fff;flex-shrink:0;
}
@media(max-width:480px){
  .xhero-card-num{width:28px;height:28px;font-size:0.75rem}
}
.xhero-card-label{font-size:0.8rem;font-weight:600;color:var(--mu2)}
@media(max-width:480px){
  .xhero-card-label{font-size:0.75rem}
}

@keyframes fadeUp{from{opacity:0;transform:translateY(28px)}to{opacity:1;transform:translateY(0)}}
@keyframes xpulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.3;transform:scale(.8)}}
@keyframes shimmer{0%{background-position:0% center}100%{background-position:200% center}}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
</style>

<div id="floating-bg">
  <div class="floating-island"></div>
  <div class="floating-island"></div>
  <div class="floating-island"></div>
</div>

<canvas id="bg-canvas"></canvas>

<nav class="xnav" id="xnav">
  <a class="xnav-logo" href="?go=app">
    <div class="xnav-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3.33 1.67 8.67 1.67 12 0v-5"/></svg></div>
    <span class="xnav-name">ScholarAI</span>
  </a>
  <div class="xnav-links">
    <a href="#xfeatures">Features</a>
    <a href="#xhow">How It Works</a>
    <a href="#xpricing">Pricing</a>
  </div>
  <div class="xnav-right">
    <a class="xnav-signin" href="?go=app">Sign In</a>
    <a class="xnav-cta" href="?go=app">Get Started</a>
  </div>
</nav>

<div class="xhero">
  <div class="xhero-eyebrow"><span class="xhero-dot"></span>&nbsp;AI-Powered Academic Research &nbsp;&#x2022;&nbsp; 2026</div>
  <h1 class="xhero-h1">
    Literature Reviews<br/>
    <span class="line2">Faster. Deeper. Smarter.</span>
  </h1>
  <p class="xhero-sub">ScholarAI synthesizes your academic sources into a fully-cited, publication-ready literature review in seconds &mdash; not weeks.</p>
  <div class="xhero-btns">
    <a class="xbtn-p" href="?go=app">Start for Free</a>
    <a class="xbtn-s" href="#xhow">See How It Works</a>
  </div>
  <p class="xhero-note">No credit card required &nbsp;&bull;&nbsp; Free tier available &nbsp;&bull;&nbsp; Powered by Gemini &amp; GPT-4o</p>
  <div class="xhero-card">
    <div class="xhero-card-step">
      <div class="xhero-card-num">01</div>
      <span class="xhero-card-label">Define Topic</span>
    </div>
    <div class="xhero-card-step">
      <div class="xhero-card-num">02</div>
      <span class="xhero-card-label">Upload PDFs</span>
    </div>
    <div class="xhero-card-step">
      <div class="xhero-card-num">03</div>
      <span class="xhero-card-label">Generate Review</span>
    </div>
    <div class="xhero-card-step">
      <div class="xhero-card-num">04</div>
      <span class="xhero-card-label">Export &amp; Submit</span>
    </div>
  </div>
</div>

<script>
// ── PARTICLE CANVAS ──────────────────────────────────────────────
(function(){
  const c=document.getElementById('bg-canvas');
  if(!c)return;
  const ctx=c.getContext('2d');
  let W,H,pts=[];
  function resize(){W=c.width=window.innerWidth;H=c.height=window.innerHeight}
  resize();window.addEventListener('resize',resize);
  const N=90;
  for(let i=0;i<N;i++)pts.push({
    x:Math.random()*W,y:Math.random()*H,
    vx:(Math.random()-.5)*.35,vy:(Math.random()-.5)*.35,
    r:Math.random()*1.8+.4,
    hue:Math.random()<.6?220+Math.random()*40:270+Math.random()*30
  });
  function draw(){
    ctx.clearRect(0,0,W,H);
    // connections
    for(let i=0;i<N;i++){
      for(let j=i+1;j<N;j++){
        const dx=pts[i].x-pts[j].x,dy=pts[i].y-pts[j].y;
        const d=Math.sqrt(dx*dx+dy*dy);
        if(d<140){
          ctx.beginPath();
          ctx.moveTo(pts[i].x,pts[i].y);
          ctx.lineTo(pts[j].x,pts[j].y);
          ctx.strokeStyle=`rgba(99,120,255,${(1-d/140)*.18})`;
          ctx.lineWidth=.6;ctx.stroke();
        }
      }
    }
    // dots
    pts.forEach(p=>{
      ctx.beginPath();
      ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle=`hsla(${p.hue},80%,70%,.55)`;
      ctx.fill();
      p.x+=p.vx;p.y+=p.vy;
      if(p.x<0||p.x>W)p.vx*=-1;
      if(p.y<0||p.y>H)p.vy*=-1;
    });
    requestAnimationFrame(draw);
  }
  draw();
})();

// ── HIDE/SHOW NAV ON SCROLL ──────────────────────────────────────
(function(){
  let last=0;
  window.addEventListener('scroll',()=>{
    const y=window.scrollY;
    const nav=document.getElementById('xnav');
    if(!nav)return;
    if(y>last&&y>80)nav.classList.add('hide');
    else nav.classList.remove('hide');
    last=y;
  },{passive:true});
})();

// ── FORCE SAME-TAB NAVIGATION (AGGRESSIVE FIX) ───────────────────
(function(){
  // Prevent ALL new tabs/windows from opening
  window.open = function(url, target){
    if(url && url.includes('?go=app')){
      window.location.href = url;
      return window;
    }
    return null;
  };
  
  function forceSameTab(){
    // Get all links
    const allLinks = document.querySelectorAll('a');
    
    allLinks.forEach(function(link){
      const href = link.getAttribute('href');
      
      // Only process links with ?go=app
      if(href && href.includes('?go=app')){
        // Remove any target attribute
        link.removeAttribute('target');
        
        // Remove any onclick that might open new tab
        link.removeAttribute('onclick');
        
        // Add our own click handler with highest priority
        link.addEventListener('click', function(e){
          e.preventDefault();
          e.stopImmediatePropagation();
          
          const url = this.getAttribute('href');
          if(url){
            // Force navigation in same window
            window.location.href = url;
          }
          
          return false;
        }, true); // Use capture phase
      }
    });
  }
  
  // Run immediately
  forceSameTab();
  
  // Run multiple times
  setTimeout(forceSameTab, 50);
  setTimeout(forceSameTab, 100);
  setTimeout(forceSameTab, 200);
  setTimeout(forceSameTab, 500);
  setTimeout(forceSameTab, 1000);
  setTimeout(forceSameTab, 2000);
  
  // Watch for DOM changes
  const observer = new MutationObserver(function(){
    forceSameTab();
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['href', 'target']
  });
  
  // Also intercept at document level
  document.addEventListener('click', function(e){
    const target = e.target.closest('a');
    if(target && target.href && target.href.includes('?go=app')){
      e.preventDefault();
      e.stopImmediatePropagation();
      window.location.href = target.href;
      return false;
    }
  }, true);
})();
</script>
""", unsafe_allow_html=True)

    # ── TRUST BAR ───────────────────────────────────────────────────
    st.markdown("""
<style>
.xtrust{
  position:relative;z-index:1;
  background:rgba(255,255,255,0.02);
  border-top:1px solid var(--border);border-bottom:1px solid var(--border);
  padding:24px 48px;display:flex;align-items:center;justify-content:center;gap:36px;flex-wrap:wrap;
}
@media(max-width:768px){
  .xtrust{padding:20px 24px;gap:20px}
}
@media(max-width:480px){
  .xtrust{padding:16px 20px;gap:16px;flex-direction:column}
}
.xtrust-lbl{font-size:0.75rem;color:var(--mu);font-weight:600;white-space:nowrap;letter-spacing:.04em}
@media(max-width:480px){
  .xtrust-lbl{font-size:0.7rem;white-space:normal;text-align:center}
}
.xtrust-sep{width:1px;height:24px;background:var(--border)}
@media(max-width:480px){
  .xtrust-sep{display:none}
}
.xtrust-logos{display:flex;align-items:center;gap:32px;flex-wrap:wrap;justify-content:center}
@media(max-width:768px){
  .xtrust-logos{gap:20px}
}
@media(max-width:480px){
  .xtrust-logos{gap:16px}
}
.xtrust-logo{
  font-size:0.75rem;font-weight:700;color:rgba(255,255,255,0.22);
  letter-spacing:.08em;text-transform:uppercase;transition:.3s;cursor:default;
}
@media(max-width:480px){
  .xtrust-logo{font-size:0.65rem}
}
.xtrust-logo:hover{color:rgba(255,255,255,0.55)}
</style>
<div class="xtrust">
  <span class="xtrust-lbl">Trusted by researchers at</span>
  <div class="xtrust-sep"></div>
  <div class="xtrust-logos">
    <span class="xtrust-logo">University of Ghana</span>
    <span class="xtrust-logo">KNUST</span>
    <span class="xtrust-logo">Legon</span>
    <span class="xtrust-logo">UCC</span>
    <span class="xtrust-logo">GIMPA</span>
    <span class="xtrust-logo">UDS</span>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── FEATURES ────────────────────────────────────────────────────
    st.markdown("""
<style>
.xsec{padding:100px 48px;max-width:1200px;margin:0 auto;position:relative;z-index:1}
@media(max-width:768px){
  .xsec{padding:60px 24px}
}
@media(max-width:480px){
  .xsec{padding:50px 20px}
}
.xsec-tag{font-size:0.7rem;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:#818cf8;margin-bottom:12px;display:block}
.xsec-h{font-family:'Syne',sans-serif;font-size:clamp(1.8rem,4vw,2.8rem);font-weight:800;line-height:1.12;letter-spacing:-.03em;margin-bottom:16px;color:var(--wh)}
@media(max-width:480px){
  .xsec-h{font-size:clamp(1.5rem,6vw,2rem);line-height:1.2}
}
.xsec-sub{font-size:0.95rem;color:var(--mu2);line-height:1.75;max-width:520px}
@media(max-width:480px){
  .xsec-sub{font-size:0.85rem;line-height:1.6}
}

.xfgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:56px}
@media(max-width:900px){.xfgrid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:560px){.xfgrid{grid-template-columns:1fr}}

.xfc{
  background:var(--glass);border:1px solid var(--border);border-radius:16px;
  padding:28px;transition:.35s var(--ease);position:relative;overflow:hidden;cursor:default;
}
.xfc::before{
  content:'';position:absolute;inset:0;border-radius:16px;
  background:radial-gradient(circle at 50% 0%,rgba(67,97,238,0.12),transparent 70%);
  opacity:0;transition:.35s;
}
.xfc::after{
  content:'';position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,rgba(99,120,255,0.6),transparent);
  opacity:0;transition:.35s;
}
.xfc:hover{background:var(--glass2);border-color:var(--border2);transform:translateY(-6px);box-shadow:0 24px 48px rgba(0,0,0,0.4),0 0 0 1px rgba(67,97,238,0.15)}
.xfc:hover::before,.xfc:hover::after{opacity:1}

.xfi{
  width:44px;height:44px;border-radius:11px;
  display:flex;align-items:center;justify-content:center;
  margin-bottom:18px;position:relative;
}
.xfi-b{background:rgba(67,97,238,0.15);box-shadow:0 0 20px rgba(67,97,238,0.2)}
.xfi-p{background:rgba(114,9,183,0.15);box-shadow:0 0 20px rgba(114,9,183,0.2)}
.xfi-t{background:rgba(6,214,160,0.12);box-shadow:0 0 20px rgba(6,214,160,0.15)}
.xfi-r{background:rgba(247,37,133,0.12);box-shadow:0 0 20px rgba(247,37,133,0.15)}

.xft{font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;margin-bottom:8px;color:var(--wh)}
.xfd{font-size:0.85rem;color:var(--mu2);line-height:1.65}

/* scroll reveal — visible by default, animate in when .xon added */
.xrev{opacity:1;transform:translateY(0)}
.xrev.xani{opacity:0;transform:translateY(32px);transition:opacity .7s var(--ease),transform .7s var(--ease)}
.xrev.xani.xon{opacity:1;transform:translateY(0)}
.xrev.d1{transition-delay:.05s}.xrev.d2{transition-delay:.12s}.xrev.d3{transition-delay:.19s}
.xrev.d4{transition-delay:.26s}.xrev.d5{transition-delay:.33s}.xrev.d6{transition-delay:.40s}
</style>

<div class="xsec" id="xfeatures">
  <div class="xrev">
    <span class="xsec-tag">What You Get</span>
    <h2 class="xsec-h">From Surface-Level Exploration<br/>to Critical Reading &mdash; All in One Place</h2>
    <p class="xsec-sub">Every tool you need to go from raw PDFs to a polished, cited review.</p>
  </div>
  <div class="xfgrid">
    <div class="xfc xrev d1"><div class="xfi xfi-b"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#818cf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg></div><div class="xft">Multi-Source Synthesis</div><div class="xfd">Upload up to 30 PDFs, DOCX, or TXT files. ScholarAI reads every page and weaves them into a coherent narrative.</div></div>
    <div class="xfc xrev d2"><div class="xfi xfi-p"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#c77dff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg></div><div class="xft">Real Citations, Zero Hallucinations</div><div class="xfd">Every claim is grounded in your uploaded sources. No fabricated references &mdash; only what's in your documents.</div></div>
    <div class="xfc xrev d3"><div class="xfi xfi-t"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#06D6A0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg></div><div class="xft">6 Citation Styles</div><div class="xfd">APA 7th, Harvard, MLA 9th, Chicago 17th, Vancouver, and IEEE &mdash; formatted automatically to your chosen style.</div></div>
    <div class="xfc xrev d4"><div class="xfi xfi-r"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#F72585" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg></div><div class="xft">Dual AI Engines</div><div class="xfd">Powered by Google Gemini (free) and OpenAI GPT-4o (premium), with automatic fallback for uninterrupted generation.</div></div>
    <div class="xfc xrev d5"><div class="xfi xfi-b"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#818cf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg></div><div class="xft">Export to PDF &amp; DOCX</div><div class="xfd">Download your finished review as a formatted PDF or Word document, ready to submit or share.</div></div>
    <div class="xfc xrev d6"><div class="xfi xfi-p"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#c77dff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></div><div class="xft">Private &amp; Secure</div><div class="xfd">Your documents never leave your session. Verified accounts, encrypted storage, and no third-party data sharing.</div></div>
  </div>
</div>

<script>
(function(){
  // Mark elements below the fold as animated, leave visible ones alone
  const io=new IntersectionObserver(entries=>{
    entries.forEach(e=>{
      if(e.isIntersecting){
        e.target.classList.remove('xani');
        e.target.classList.add('xon');
        io.unobserve(e.target);
      }
    });
  },{threshold:.08,rootMargin:'0px 0px -20px 0px'});

  // Only animate elements that are below the current viewport
  document.querySelectorAll('.xrev').forEach(el=>{
    const rect=el.getBoundingClientRect();
    if(rect.top > window.innerHeight){
      el.classList.add('xani');
      io.observe(el);
    }
  });
})();
</script>
""", unsafe_allow_html=True)

    # ── HOW IT WORKS + STATS ────────────────────────────────────────
    st.markdown("""
<style>
.xhow-outer{max-width:1200px;margin:0 auto;padding:0 48px 100px;position:relative;z-index:1}
@media(max-width:768px){.xhow-outer{padding:0 24px 60px!important}}
@media(max-width:480px){.xhow-outer{padding:0 20px 50px!important}}
.xhow-box{
  background:rgba(255,255,255,0.025);border:1px solid var(--border);
  border-radius:24px;padding:72px 56px;position:relative;overflow:hidden;
}
@media(max-width:768px){
  .xhow-box{padding:48px 32px;border-radius:20px}
}
@media(max-width:480px){
  .xhow-box{padding:32px 20px;border-radius:16px}
}
.xhow-box::before{
  content:'';position:absolute;top:-1px;left:10%;right:10%;height:1px;
  background:linear-gradient(90deg,transparent,rgba(99,120,255,0.5),transparent);
}
.xsteps{display:grid;grid-template-columns:repeat(3,1fr);gap:0;margin-top:52px;position:relative}
.xsteps::before{
  content:'';position:absolute;top:28px;left:calc(16.66% + 16px);right:calc(16.66% + 16px);
  height:1px;background:linear-gradient(90deg,rgba(67,97,238,0.4),rgba(114,9,183,0.4));
}
@media(max-width:700px){.xsteps{grid-template-columns:1fr;margin-top:40px}.xsteps::before{display:none}}
.xstep{text-align:center;padding:0 24px}
@media(max-width:700px){
  .xstep{padding:20px 0;border-bottom:1px solid rgba(255,255,255,0.05)}
  .xstep:last-child{border-bottom:none}
}
.xstep-num{
  width:56px;height:56px;border-radius:50%;margin:0 auto 20px;
  display:flex;align-items:center;justify-content:center;
  font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:800;color:#fff;
  background:linear-gradient(135deg,var(--c1),var(--c2));
  box-shadow:0 0 24px var(--glow1),0 0 48px rgba(67,97,238,0.2);
  position:relative;z-index:1;
}
@media(max-width:480px){
  .xstep-num{width:48px;height:48px;font-size:1rem}
}
.xstep-title{font-family:'Syne',sans-serif;font-size:0.95rem;font-weight:700;margin-bottom:8px;color:var(--wh)}
@media(max-width:480px){
  .xstep-title{font-size:0.9rem}
}
.xstep-desc{font-size:0.83rem;color:var(--mu2);line-height:1.65}
@media(max-width:480px){
  .xstep-desc{font-size:0.8rem;line-height:1.6}
}

.xstats{
  display:grid;grid-template-columns:repeat(4,1fr);gap:1px;
  background:var(--border);border-radius:16px;overflow:hidden;margin-top:52px;
}
@media(max-width:700px){.xstats{grid-template-columns:repeat(2,1fr);margin-top:40px}}
@media(max-width:400px){.xstats{grid-template-columns:1fr}}
.xstat{
  background:rgba(255,255,255,0.03);padding:36px 24px;text-align:center;
  transition:.3s;
}
@media(max-width:768px){
  .xstat{padding:28px 20px}
}
@media(max-width:480px){
  .xstat{padding:24px 16px}
}
.xstat:hover{background:rgba(67,97,238,0.08)}
.xstat-val{
  font-family:'Syne',sans-serif;font-size:2.6rem;font-weight:800;
  background:linear-gradient(135deg,#818cf8,#c77dff);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  line-height:1;margin-bottom:8px;
}
@media(max-width:768px){
  .xstat-val{font-size:2.2rem}
}
@media(max-width:480px){
  .xstat-val{font-size:2rem}
}
.xstat-lbl{font-size:0.7rem;color:var(--mu);font-weight:700;text-transform:uppercase;letter-spacing:.1em}
@media(max-width:480px){
  .xstat-lbl{font-size:0.65rem}
}
</style>
<div class="xhow-outer" id="xhow">
  <div class="xhow-box">
    <div style="text-align:center">
      <span class="xsec-tag">The Process</span>
      <h2 class="xsec-h">Three Steps to a Publication-Ready Review</h2>
    </div>
    <div class="xsteps">
      <div class="xstep xrev d1">
        <div class="xstep-num">01</div>
        <div class="xstep-title">Define Your Topic</div>
        <div class="xstep-desc">Enter your research question or hypothesis. The more specific, the sharper the synthesis.</div>
      </div>
      <div class="xstep xrev d2">
        <div class="xstep-num">02</div>
        <div class="xstep-title">Upload Your Sources</div>
        <div class="xstep-desc">Drop in your academic PDFs or documents. ScholarAI extracts and indexes every word.</div>
      </div>
      <div class="xstep xrev d3">
        <div class="xstep-num">03</div>
        <div class="xstep-title">Generate &amp; Export</div>
        <div class="xstep-desc">Hit generate. Get a structured, cited literature review in seconds. Export to PDF or DOCX.</div>
      </div>
    </div>
    <div class="xstats" id="xstats-box">
      <div class="xstat"><div class="xstat-val" id="sc-30" data-target="30" data-suffix="+">0+</div><div class="xstat-lbl">Sources per Review</div></div>
      <div class="xstat"><div class="xstat-val" id="sc-6"  data-target="6"  data-suffix="">6</div><div class="xstat-lbl">Citation Styles</div></div>
      <div class="xstat"><div class="xstat-val" id="sc-60" data-target="60" data-prefix="&lt;" data-suffix="s">&lt;60s</div><div class="xstat-lbl">Generation Time</div></div>
      <div class="xstat"><div class="xstat-val" id="sc-0"  data-target="0"  data-suffix="">0</div><div class="xstat-lbl">Hallucinated Refs</div></div>
    </div>

<style>
.xstat-val{
  font-family:'Syne',sans-serif;font-size:2.6rem;font-weight:800;
  background:linear-gradient(135deg,#818cf8,#c77dff);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  line-height:1;margin-bottom:8px;
  transition:transform .3s;
}
.xstat:hover .xstat-val{transform:scale(1.08)}
</style>
  </div>
</div>
""", unsafe_allow_html=True)

    # Counter animation via components.html (scripts work here)
    import streamlit.components.v1 as _c
    _c.html("""
<script>
(function(){
  var counted = false;
  function easeOut(t){ return 1 - Math.pow(1-t,3); }
  function countUp(el, target, duration, prefix, suffix){
    var start = null;
    function step(ts){
      if(!start) start = ts;
      var p = Math.min((ts-start)/duration, 1);
      el.textContent = (prefix||'') + Math.round(easeOut(p)*target) + (suffix||'');
      if(p < 1) requestAnimationFrame(step);
      else el.textContent = (prefix||'') + target + (suffix||'');
    }
    requestAnimationFrame(step);
  }
  function run(){
    if(counted) return; counted = true;
    var doc = window.parent.document;
    var items = [
      {id:'sc-30', target:30, prefix:'',    suffix:'+'},
      {id:'sc-6',  target:6,  prefix:'',    suffix:''},
      {id:'sc-60', target:60, prefix:'<',   suffix:'s'},
      {id:'sc-0',  target:0,  prefix:'',    suffix:''}
    ];
    items.forEach(function(item, i){
      setTimeout(function(){
        var el = doc.getElementById(item.id);
        if(!el) return;
        if(item.target === 0){ el.textContent = '0'; return; }
        countUp(el, item.target, 1400, item.prefix, item.suffix);
      }, i * 200);
    });
  }
  // Poll until the stats box is visible in parent doc
  function tryObserve(){
    var box = window.parent.document.getElementById('xstats-box');
    if(!box){ setTimeout(tryObserve, 300); return; }
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(e){ if(e.isIntersecting){ run(); io.disconnect(); } });
    },{threshold:0.2,root:null});
    io.observe(box);
  }
  tryObserve();
})();
</script>
""", height=0)

    # ── PRICING ─────────────────────────────────────────────────────
    st.markdown("""
<style>
.xpwrap{max-width:1200px;margin:0 auto;padding:0 48px 100px;position:relative;z-index:1}
@media(max-width:768px){.xpwrap{padding:0 20px 60px!important}}
.xpgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:56px;align-items:start}
@media(max-width:860px){.xpgrid{grid-template-columns:1fr;max-width:380px;margin-left:auto;margin-right:auto}}

.xpc{
  background:var(--glass);border:1px solid var(--border);border-radius:20px;
  padding:36px 28px;text-align:center;transition:.35s var(--ease);position:relative;
}
.xpc:hover{transform:translateY(-5px);box-shadow:0 24px 48px rgba(0,0,0,0.35)}
.xpc.xfeat{
  background:linear-gradient(160deg,rgba(67,97,238,0.12),rgba(114,9,183,0.08));
  border-color:rgba(67,97,238,0.45);
  box-shadow:0 0 0 1px rgba(67,97,238,0.2),0 20px 50px rgba(67,97,238,0.15);
}
.xpc.xfeat:hover{box-shadow:0 0 0 1px rgba(67,97,238,0.4),0 28px 60px rgba(67,97,238,0.25)}
.xpbadge{
  position:absolute;top:-13px;left:50%;transform:translateX(-50%);
  padding:4px 16px;border-radius:999px;font-size:0.68rem;font-weight:700;
  background:linear-gradient(135deg,var(--c1),var(--c2));color:#fff;
  letter-spacing:.08em;white-space:nowrap;
  box-shadow:0 0 16px var(--glow1);
}
.xptier{font-size:0.68rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#818cf8;margin-bottom:12px}
.xpamt{font-family:'Syne',sans-serif;font-size:2.8rem;font-weight:800;margin-bottom:2px;color:var(--wh);line-height:1}
.xpper{font-size:0.8rem;color:var(--mu);margin-bottom:24px}
.xpfeats{list-style:none;text-align:left;margin-bottom:28px}
.xpfeats li{
  font-size:0.83rem;color:var(--mu2);padding:7px 0;
  display:flex;align-items:center;gap:9px;
  border-bottom:1px solid rgba(255,255,255,0.04);
}
.xpfeats li:last-child{border-bottom:none}
.xpfeats li::before{content:'';width:16px;height:16px;border-radius:50%;flex-shrink:0;
  background:rgba(6,214,160,0.15);border:1px solid rgba(6,214,160,0.4);
  display:flex;align-items:center;justify-content:center;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'%3E%3Cpath d='M2 6l3 3 5-5' stroke='%2306D6A0' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:center;background-size:10px;
}
.xpbtn{
  width:100%;padding:13px;border-radius:10px;border:none;cursor:pointer;
  font-weight:700;font-size:0.9rem;font-family:'Inter',sans-serif;
  transition:.25s;text-decoration:none;display:block;text-align:center;
}
.xpbtn.xpp{
  background:linear-gradient(135deg,var(--c1),var(--c2));color:#fff;
  box-shadow:0 0 20px var(--glow1);
}
.xpbtn.xpp:hover{filter:brightness(1.1);transform:translateY(-2px);box-shadow:0 0 32px var(--glow1);color:#fff}
.xpbtn.xps{
  background:rgba(255,255,255,0.06);color:var(--wh);
  border:1px solid rgba(255,255,255,0.1);
}
.xpbtn.xps:hover{background:rgba(255,255,255,0.1);border-color:rgba(255,255,255,0.2);color:var(--wh)}
</style>
<div class="xpwrap" id="xpricing">
  <div style="text-align:center">
    <span class="xsec-tag">Pricing</span>
    <h2 class="xsec-h">Simple, Transparent Plans</h2>
    <p class="xsec-sub" style="margin:0 auto">Start free. Upgrade when you need more power.</p>
  </div>
  <div class="xpgrid">
    <div class="xpc xrev d1">
      <div class="xptier">Free</div>
      <div class="xpamt">GHS 0</div>
      <div class="xpper">forever</div>
      <ul class="xpfeats">
        <li>Up to 12 articles per review</li>
        <li>Google Gemini engine</li>
        <li>APA, Harvard, MLA styles</li>
        <li>PDF &amp; DOCX export</li>
        <li>30 generations included</li>
      </ul>
      <a class="xpbtn xps" href="?go=app">Get Started Free</a>
    </div>
    <div class="xpc xfeat xrev d2">
      <div class="xpbadge">MOST POPULAR</div>
      <div class="xptier">Monthly</div>
      <div class="xpamt">GHS 30</div>
      <div class="xpper">per month</div>
      <ul class="xpfeats">
        <li>Up to 30 articles per review</li>
        <li>GPT-4o + Gemini engines</li>
        <li>All 6 citation styles</li>
        <li>Priority processing</li>
        <li>Unlimited generations</li>
        <li>Full session history</li>
      </ul>
      <a class="xpbtn xpp" href="?go=app">Upgrade to Monthly</a>
    </div>
    <div class="xpc xrev d3">
      <div class="xptier">Yearly</div>
      <div class="xpamt">GHS 300</div>
      <div class="xpper">per year &nbsp;&bull;&nbsp; save 20%</div>
      <ul class="xpfeats">
        <li>Everything in Monthly</li>
        <li>Master access</li>
        <li>Early feature access</li>
        <li>Priority support</li>
        <li>Unlimited generations</li>
      </ul>
      <a class="xpbtn xps" href="?go=app">Get Yearly Access</a>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── CTA + FOOTER ────────────────────────────────────────────────
    st.markdown("""
<style>
.xcta-wrap{max-width:1200px;margin:0 auto;padding:0 48px 100px;position:relative;z-index:1}
@media(max-width:768px){
  .xcta-wrap{padding:0 24px 60px}
}
@media(max-width:480px){
  .xcta-wrap{padding:0 20px 50px}
}
.xcta{
  border-radius:24px;padding:80px 48px;text-align:center;
  background:linear-gradient(135deg,rgba(67,97,238,0.15) 0%,rgba(114,9,183,0.12) 50%,rgba(247,37,133,0.08) 100%);
  border:1px solid rgba(67,97,238,0.25);position:relative;overflow:hidden;
}
@media(max-width:768px){
  .xcta{padding:60px 32px;border-radius:20px}
}
@media(max-width:480px){
  .xcta{padding:40px 24px;border-radius:16px}
}
.xcta::before{
  content:'';position:absolute;top:-1px;left:15%;right:15%;height:1px;
  background:linear-gradient(90deg,transparent,rgba(99,120,255,0.6),rgba(199,119,255,0.6),transparent);
}
.xcta::after{
  content:'';position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
  width:500px;height:500px;
  background:radial-gradient(circle,rgba(67,97,238,0.1),transparent 65%);
  pointer-events:none;
}
.xcta-title{
  font-family:'Syne',sans-serif;font-size:clamp(1.5rem,4vw,2.8rem);
  font-weight:800;margin-bottom:14px;color:var(--wh);position:relative;z-index:1;
}
@media(max-width:480px){
  .xcta-title{font-size:clamp(1.3rem,6vw,2rem);margin-bottom:12px}
}
.xcta-sub{font-size:0.95rem;color:var(--mu2);margin-bottom:36px;position:relative;z-index:1}
@media(max-width:480px){
  .xcta-sub{font-size:0.85rem;margin-bottom:28px}
}
.xcta-row{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;position:relative;z-index:1}
@media(max-width:480px){
  .xcta-row{flex-direction:column;gap:10px;max-width:300px;margin:0 auto}
}

.xfoot{
  border-top:1px solid var(--border);padding:32px 48px;
  display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;
  position:relative;z-index:1;background:rgba(11,15,25,0.5);
}
@media(max-width:768px){
  .xfoot{padding:24px;flex-direction:column;text-align:center}
}
@media(max-width:480px){
  .xfoot{padding:20px;gap:12px}
}
.xfoot-brand{font-family:'Syne',sans-serif;font-size:0.95rem;font-weight:800;color:var(--wh)}
.xfoot-note{font-size:0.75rem;color:var(--mu);margin-top:3px}
@media(max-width:480px){
  .xfoot-note{font-size:0.7rem}
}
.xfoot-links{display:flex;gap:20px;flex-wrap:wrap}
@media(max-width:768px){
  .xfoot-links{justify-content:center}
}
@media(max-width:480px){
  .xfoot-links{gap:12px;font-size:0.85rem}
}
.xfoot-links a{font-size:0.75rem;color:var(--mu);text-decoration:none;transition:.2s}
@media(max-width:480px){
  .xfoot-links a{font-size:0.7rem}
}
.xfoot-links a:hover{color:var(--wh)}
</style>
<div class="xcta-wrap">
  <div class="xcta">
    <h2 class="xcta-title">Ready to Supercharge Your Research?</h2>
    <p class="xcta-sub">Join researchers already writing faster, smarter literature reviews with ScholarAI.</p>
    <div class="xcta-row">
      <a class="xbtn-p" href="?go=app">Start for Free &rarr;</a>
      <a class="xbtn-s" href="?go=app">Sign In</a>
    </div>
  </div>
</div>

<div class="xfoot">
  <div>
    <div class="xfoot-brand">ScholarAI</div>
    <div class="xfoot-note">AI-Powered Literature Review Generator &nbsp;&bull;&nbsp; v2.0</div>
  </div>
  <div class="xfoot-links">
    <a href="#xfeatures">Features</a>
    <a href="#xhow">How It Works</a>
    <a href="#xpricing">Pricing</a>
    <a href="?go=app">Sign In</a>
    <a href="?go=app">Get Started</a>
  </div>
  <div class="xfoot-note">AI draft &mdash; always review before academic submission</div>
</div>
""", unsafe_allow_html=True)
