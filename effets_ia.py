"""Effets visuels « IA » pour la page de connexion et la page d'accueil.

Purement décoratif (aucune fonction d'IA réelle) :
  - fond animé de type réseau de neurones (canvas, particules reliées),
  - halos lumineux animés derrière le contenu,
  - titre en dégradé animé, formulaire « verre dépoli » lumineux,
  - bouton principal avec reflet, image avec balayage lumineux.

Utilisation (dans app.py) :
    import effets_ia
    effets_ia.appliquer("connexion")   # écran de connexion
    effets_ia.appliquer("accueil")     # page d'accueil

Le canvas vit dans le document parent ; il se supprime tout seul dès que
l'iframe qui l'a créé disparaît (changement de page), donc rien à nettoyer
sur les autres pages.
"""
import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------
# CSS (valable en thème clair et sombre : uniquement des couleurs translucides)
# ---------------------------------------------------------------------------
_CSS_COMMUN = """
<style>
@keyframes ia-halo {
  0%   { transform: translate3d(0, 0, 0) scale(1); }
  50%  { transform: translate3d(4%, -3%, 0) scale(1.15); }
  100% { transform: translate3d(0, 0, 0) scale(1); }
}
@keyframes ia-shimmer {
  0%   { background-position: 0% 50%; }
  100% { background-position: 200% 50%; }
}
@keyframes ia-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.45); }
  50%      { box-shadow: 0 0 0 7px rgba(56, 189, 248, 0); }
}
@keyframes ia-glow {
  0%, 100% { box-shadow: 0 0 18px rgba(56, 189, 248, 0.25), 0 0 40px rgba(139, 92, 246, 0.12); }
  50%      { box-shadow: 0 0 28px rgba(56, 189, 248, 0.45), 0 0 60px rgba(139, 92, 246, 0.25); }
}
@keyframes ia-scan {
  0%   { top: -12%; opacity: 0; }
  10%  { opacity: 1; }
  90%  { opacity: 1; }
  100% { top: 108%; opacity: 0; }
}
@keyframes ia-sweep {
  0%   { transform: translateX(-120%) skewX(-20deg); }
  100% { transform: translateX(260%) skewX(-20deg); }
}

/* Halos lumineux animés derrière tout le contenu */
.stApp::before, .stApp::after {
  content: "";
  position: fixed;
  z-index: 0;
  width: 55vmax;
  height: 55vmax;
  border-radius: 50%;
  filter: blur(80px);
  pointer-events: none;
  animation: ia-halo 14s ease-in-out infinite;
}
.stApp::before {
  top: -22vmax; left: -18vmax;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.28), transparent 65%);
}
.stApp::after {
  bottom: -26vmax; right: -20vmax;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.26), transparent 65%);
  animation-delay: -7s;
}

/* Titres en dégradé animé */
.stApp h1 {
  background: linear-gradient(90deg, #0ea5e9, #6366f1, #a855f7, #0ea5e9);
  background-size: 200% auto;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: ia-shimmer 6s linear infinite;
}

/* Le canvas « réseau neuronal » est posé par le script ci-dessous */
#lpee-ia-canvas {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  pointer-events: none;
  opacity: 0.65;
}

/* L'iframe qui porte le script ne doit pas laisser de trou dans la page */
div[data-testid="stElementContainer"]:has(iframe[height="0"]),
div.element-container:has(iframe[height="0"]) {
  position: absolute !important;
  height: 0 !important;
  margin: 0 !important;
  overflow: hidden !important;
}

/* Pastille d'état */
.ia-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 0.82rem;
  letter-spacing: 0.02em;
  border: 1px solid rgba(56, 189, 248, 0.45);
  background: rgba(56, 189, 248, 0.10);
  backdrop-filter: blur(6px);
}
.ia-status .ia-dot {
  width: 9px; height: 9px; border-radius: 50%;
  background: #22c55e;
  animation: ia-pulse 2s ease-out infinite;
}

@media (prefers-reduced-motion: reduce) {
  .stApp::before, .stApp::after, .stApp h1,
  .ia-status .ia-dot, [data-testid="stForm"],
  [data-testid="stImage"]::after, button[kind="primary"]::after {
    animation: none !important;
  }
}
</style>
"""

_CSS_CONNEXION = """
<style>
/* Formulaire de connexion : verre dépoli avec lueur */
[data-testid="stForm"] {
  position: relative;
  padding: 1.4rem 1.4rem 1.1rem 1.4rem;
  border-radius: 18px;
  border: 1px solid rgba(56, 189, 248, 0.45);
  background: rgba(255, 255, 255, 0.10);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  animation: ia-glow 5s ease-in-out infinite;
}
/* Bouton « Se connecter » : dégradé + reflet qui passe */
button[kind="primary"],
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-primaryFormSubmit"] {
  position: relative;
  overflow: hidden;
  border: none !important;
  background: linear-gradient(90deg, #0ea5e9, #6366f1, #a855f7) !important;
  background-size: 200% auto !important;
  transition: background-position 0.5s, transform 0.15s;
}
button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-primaryFormSubmit"]:hover {
  background-position: 100% 0 !important;
  transform: translateY(-1px);
}
button[kind="primary"]::after,
[data-testid="stBaseButton-primary"]::after,
[data-testid="stBaseButton-primaryFormSubmit"]::after {
  content: "";
  position: absolute;
  top: 0; bottom: 0; left: 0;
  width: 35%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.45), transparent);
  animation: ia-sweep 3.6s ease-in-out infinite;
}
</style>
"""

_CSS_ACCUEIL = """
<style>
/* Image d'accueil : cadre lumineux + balayage « scanner » */
[data-testid="stImage"] {
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  border: 1px solid rgba(56, 189, 248, 0.45);
  animation: ia-glow 6s ease-in-out infinite;
}
[data-testid="stImage"]::after {
  content: "";
  position: absolute;
  left: 0; right: 0;
  height: 10%;
  pointer-events: none;
  background: linear-gradient(180deg, transparent, rgba(56, 189, 248, 0.30), transparent);
  animation: ia-scan 5.5s ease-in-out infinite;
}
</style>
"""

# ---------------------------------------------------------------------------
# Script : réseau de particules (exécuté dans le document parent)
# ---------------------------------------------------------------------------
# Étape 1 (iframe) : mémorise l'iframe courante puis injecte le code ci-dessous
# comme <script> du parent, pour qu'il survive à la disparition de l'iframe.
_JS_LANCEUR = """
<script>
(function () {
  try {
    var P = window.parent, D = P.document;
    P.__lpeeIAFrame = window.frameElement;
    var ancien = D.getElementById('lpee-ia-script');
    if (ancien) ancien.remove();
    var s = D.createElement('script');
    s.id = 'lpee-ia-script';
    s.textContent = %s;
    D.head.appendChild(s);
  } catch (e) { /* effet décoratif : on ignore toute erreur */ }
})();
</script>
"""

# Étape 2 (parent) : le canvas lui-même.
_JS_PARENT = r"""
(function () {
  var st = window.__lpeeIA;
  if (!st) { st = window.__lpeeIA = { canvas: null, raf: 0, fails: 0, timer: 0 }; }
  st.fails = 0;                                   // l'iframe vient d'être (re)créée
  if (st.canvas && document.body.contains(st.canvas)) return;   // déjà actif

  var cv = document.createElement('canvas');
  cv.id = 'lpee-ia-canvas';
  document.body.appendChild(cv);
  st.canvas = cv;
  var ctx = cv.getContext('2d');
  var W = 0, H = 0, DPR = Math.min(window.devicePixelRatio || 1, 2);
  var pts = [], mouse = { x: -9999, y: -9999 };
  var reduit = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var LIEN = 140;

  function taille() {
    W = window.innerWidth; H = window.innerHeight;
    cv.width = W * DPR; cv.height = H * DPR;
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    var n = Math.max(30, Math.min(90, Math.round(W * H / 16000)));
    while (pts.length < n) pts.push({
      x: Math.random() * W, y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.45, vy: (Math.random() - 0.5) * 0.45,
      r: 1.2 + Math.random() * 1.8, v: Math.random() < 0.3
    });
    pts.length = n;
  }
  taille();
  window.addEventListener('resize', taille);
  window.addEventListener('mousemove', function (e) { mouse.x = e.clientX; mouse.y = e.clientY; });
  window.addEventListener('mouseleave', function () { mouse.x = mouse.y = -9999; });

  function dessiner() {
    ctx.clearRect(0, 0, W, H);
    var i, j, a, b, dx, dy, d, al;
    for (i = 0; i < pts.length; i++) {
      a = pts[i];
      if (!reduit) {
        a.x += a.vx; a.y += a.vy;
        if (a.x < 0 || a.x > W) a.vx *= -1;
        if (a.y < 0 || a.y > H) a.vy *= -1;
      }
      for (j = i + 1; j < pts.length; j++) {
        b = pts[j]; dx = a.x - b.x; dy = a.y - b.y; d = Math.sqrt(dx * dx + dy * dy);
        if (d < LIEN) {
          al = (1 - d / LIEN) * 0.55;
          ctx.strokeStyle = 'rgba(' + (a.v ? '139,92,246' : '56,189,248') + ',' + al + ')';
          ctx.lineWidth = 1;
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        }
      }
      dx = a.x - mouse.x; dy = a.y - mouse.y; d = Math.sqrt(dx * dx + dy * dy);
      if (d < 180) {                                // le pointeur « active » le réseau
        al = (1 - d / 180) * 0.8;
        ctx.strokeStyle = 'rgba(34,211,238,' + al + ')';
        ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(mouse.x, mouse.y); ctx.stroke();
      }
      ctx.fillStyle = a.v ? 'rgba(139,92,246,0.95)' : 'rgba(56,189,248,0.95)';
      ctx.beginPath(); ctx.arc(a.x, a.y, a.r, 0, 6.2832); ctx.fill();
    }
    if (!reduit) st.raf = requestAnimationFrame(dessiner);
  }
  dessiner();

  // Auto-nettoyage : si l'iframe d'origine a disparu (autre page), on retire le canvas.
  st.timer = setInterval(function () {
    var fr = window.__lpeeIAFrame;
    if (fr && fr.isConnected) { st.fails = 0; return; }
    st.fails++;
    if (st.fails >= 3) {                            // ~2 s sans iframe : on quitte
      cancelAnimationFrame(st.raf); clearInterval(st.timer);
      window.removeEventListener('resize', taille);
      if (cv.parentNode) cv.parentNode.removeChild(cv);
      st.canvas = null;
    }
  }, 700);
})();
"""


def _script_reseau():
  """Code HTML de l'iframe invisible qui lance le fond animé."""
  import json

  return _JS_LANCEUR % json.dumps(_JS_PARENT)


def appliquer(page):
  """Active les effets IA. `page` : "connexion" ou "accueil"."""
  try:
    st.markdown(_CSS_COMMUN, unsafe_allow_html=True)
    if page == "connexion":
      st.markdown(_CSS_CONNEXION, unsafe_allow_html=True)
    elif page == "accueil":
      st.markdown(_CSS_ACCUEIL, unsafe_allow_html=True)
    components.html(_script_reseau(), height=0)
  except Exception:
    # Les effets sont décoratifs : ne jamais bloquer l'application.
    pass


def pastille_statut(texte):
  """Petite pastille « point vert pulsant + texte » (HTML)."""
  st.markdown(
      f'<div class="ia-status"><span class="ia-dot"></span>{texte}</div>',
      unsafe_allow_html=True,
  )
