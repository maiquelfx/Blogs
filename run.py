# -*- coding: utf-8 -*-
"""
Created on Sun May 10 20:54:38 2026

@author: Win
"""

# -*- coding: utf-8 -*-
import os
import re
import glob
import time
import base64
import urllib.parse
import requests
import markdown
from io import BytesIO
from PIL import Image

# ===================== CONFIGURAÇÕES =====================
PIXABAY_KEY   = "..."
GITHUB_TOKEN  = "..."
GITHUB_OWNER  = "..."
GITHUB_REPO   = "..."
GITHUB_FOLDER = "..."

IMG_WIDTH      = 1200
IMG_HEIGHT     = 630
COVER_WIDTH    = 1600
COVER_HEIGHT   = 900
IMG_QUALITY    = 82
SEARCH_LANG    = "pt"
# =========================================================


# ─────────────────────────────────────────────
#  IMAGENS PIXABAY -> GITHUB CDN
# ─────────────────────────────────────────────
def slugify(text):
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_]+", "-", text).strip("-")[:60]

def search_pixabay(query, seen_urls):
    print(f"    Pixabay: '{query}'")
    url = (
        f"https://pixabay.com/api/?key={PIXABAY_KEY}"
        f"&q={urllib.parse.quote(query)}"
        f"&image_type=photo&orientation=horizontal&safesearch=true&per_page=10&lang={SEARCH_LANG}"
    )
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            hits = r.json().get("hits", [])
            for hit in hits:
                img_url = hit.get("largeImageURL") or hit.get("webformatURL")
                if img_url not in seen_urls:
                    seen_urls.add(img_url)
                    return img_url
            if hits:
                return hits[0].get("largeImageURL") or hits[0]["webformatURL"]
            print("    Nenhuma imagem encontrada.")
        else:
            print(f"    Pixabay HTTP {r.status_code}")
    except Exception as e:
        print(f"    Erro Pixabay: {e}")
    return None

def download_and_convert(image_url, width, height, label=""):
    print(f"    Baixando WebP {width}x{height} {label}...")
    try:
        r = requests.get(image_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if r.status_code != 200:
            return None
        img = Image.open(BytesIO(r.content)).convert("RGB")
        target_ratio, orig_ratio = width / height, img.width / img.height
        if orig_ratio > target_ratio:
            new_h = height; new_w = int(new_h * orig_ratio)
        else:
            new_w = width; new_h = int(new_w / orig_ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        left, top = (new_w - width) // 2, (new_h - height) // 2
        img = img.crop((left, top, left + width, top + height))
        buf = BytesIO()
        img.save(buf, format="WEBP", quality=IMG_QUALITY, method=6)
        return buf.getvalue()
    except Exception as e:
        print(f"    Erro imagem: {e}")
        return None

def upload_github(webp_bytes, filename):
    print(f"    Subindo '{filename}' no GitHub...")
    api_url = (
        f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
        f"/contents/{GITHUB_FOLDER}/{filename}"
    )
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "message": f"blog pipeline: {filename}",
        "content": base64.b64encode(webp_bytes).decode("utf-8")
    }
    try:
        r = requests.put(api_url, headers=headers, json=payload, timeout=30)
        if r.status_code in (200, 201):
            return (
                f"https://cdn.jsdelivr.net/gh/{GITHUB_OWNER}/{GITHUB_REPO}"
                f"@main/{GITHUB_FOLDER}/{filename}"
            )
    except Exception as e:
        print(f"    Erro GitHub: {e}")
    return None

def process_image(query, slug, width, height, seen_urls, label=""):
    url = search_pixabay(query, seen_urls)
    if not url:
        return None
    webp = download_and_convert(url, width, height, label)
    if not webp:
        return None
    filename = f"{slug}-{int(time.time())}.webp"
    cdn_url  = upload_github(webp, filename)
    time.sleep(1)
    return cdn_url


# ─────────────────────────────────────────────
#  CSS & JS — EDITOR VISUAL EMBUTIDO
# ─────────────────────────────────────────────
CSS = """
  :root{
    --accent:#2563eb;--bg:#ffffff;--text:#1e1e2e;--muted:#6b7280;
    --tip-bg:#eff6ff;--tip-border:#2563eb;--cta-bg:#1e40af;--cta-text:#ffffff;
    --faq-bg:#f9fafb;--editor-bar:#1e1e2e;--editor-bar-text:#f9fafb;
  }
  *{box-sizing:border-box;margin:0;padding:0;}
  body{font-family:Georgia,serif;background:var(--bg);color:var(--text);line-height:1.75;font-size:1.05rem;max-width:860px;margin:2rem auto;padding:0 1.2rem 6rem;}

  .main-article-title{font-size:2.4rem;margin:1rem 0 2rem;line-height:1.2;font-weight:800;color:#111827;}

  h2{font-size:1.5rem;margin:2.5rem 0 .8rem;padding-bottom:.4rem;border-bottom:2px solid #e5e7eb;}
  h3{font-size:1.2rem;margin:1.8rem 0 .6rem;color:#374151;}
  p{margin:.75rem 0;}ul,ol{margin:.75rem 0 .75rem 1.5rem;}li{margin:.4rem 0;}
  a{color:var(--accent);text-decoration:none;}a:hover{text-decoration:underline;}
  strong{font-weight:700;}em{font-style:italic;}

  /* ── Imagens do post ── */
  .post-img-wrap{
    position:relative;margin:1.5rem 0;
  }
  .post-img-wrap img{
    width:100%;height:auto;border-radius:8px;display:block;
    box-shadow:0 2px 12px rgba(0,0,0,.08);
  }

  /* ── Capa ── */
  .featured-cover{position:relative;width:100%;margin:0 0 2.5rem;border-radius:12px;overflow:hidden;background:#1e1e2e;}
  .featured-cover img{width:100%;height:auto;display:block;opacity:.85;}
  .featured-cover-overlay{position:absolute;bottom:0;left:0;right:0;padding:2rem 1.5rem;background:linear-gradient(to top,rgba(0,0,0,.78) 0%,transparent 100%);}
  .featured-cover-title{color:#fff;font-size:1.7rem;font-weight:700;line-height:1.3;margin:0;}

  blockquote{border-left:4px solid var(--accent);background:#f9fafb;padding:1rem 1.5rem;margin:1.5rem 0;font-style:italic;border-radius:0 8px 8px 0;}
  table{width:100%;border-collapse:collapse;margin:1.5rem 0;font-size:.95rem;}
  th{background:var(--accent);color:#fff;padding:.8rem;text-align:left;}
  td{padding:.8rem;border-bottom:1px solid #e5e7eb;}
  tr:nth-child(even) td{background:#f9fafb;}
  :not(pre) > code{background:#f1f5f9;color:#e11d48;padding:.2rem .4rem;border-radius:4px;font-size:.9em;font-family:monospace;}

  /* ── Botões fixos ── */
  .floating-copy-btn{position:fixed;bottom:20px;right:20px;background:#10b981;color:#fff;border:none;padding:1rem 1.5rem;font-size:1rem;font-weight:bold;border-radius:50px;cursor:pointer;box-shadow:0 4px 15px rgba(16,185,129,.4);transition:all .3s ease;z-index:9999;}
  .floating-copy-btn:hover{background:#059669;transform:translateY(-2px);}
  .floating-copy-btn.copied{background:#2563eb;box-shadow:0 4px 15px rgba(37,99,235,.4);}
  .back-to-top{position:fixed;bottom:80px;right:20px;background:#1e1e2e;color:#fff;border:none;width:44px;height:44px;font-size:1.1rem;line-height:1;border-radius:50%;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,.25);transition:all .3s ease;z-index:9999;display:flex;align-items:center;justify-content:center;opacity:0;pointer-events:none;}
  .back-to-top.visible{opacity:1;pointer-events:auto;}
  .back-to-top:hover{background:#374151;transform:translateY(-2px);}

  /* ══════════════════════════════════════
     EDITOR VISUAL — novos estilos
  ══════════════════════════════════════ */

  /* Barra superior do editor */
  #editor-bar{
    position:sticky;top:0;z-index:8000;
    background:var(--editor-bar);color:var(--editor-bar-text);
    display:flex;align-items:center;gap:.5rem;
    padding:.55rem 1rem;font-size:.85rem;
    border-radius:0 0 10px 10px;
    box-shadow:0 3px 12px rgba(0,0,0,.3);
    margin:-2rem -1.2rem 1.5rem;          /* sangra até as bordas do body */
    flex-wrap:wrap;
  }
  #editor-bar span.label{font-weight:700;letter-spacing:.5px;opacity:.7;margin-right:.25rem;}
  #editor-bar button{
    background:#374151;color:#f9fafb;border:none;padding:.35rem .8rem;
    border-radius:6px;cursor:pointer;font-size:.8rem;font-weight:600;
    transition:background .2s;white-space:nowrap;
  }
  #editor-bar button:hover{background:#4b5563;}
  #editor-bar button.active{background:var(--accent);}
  #editor-bar .sep{width:1px;height:22px;background:#4b5563;margin:0 .25rem;}

  /* Overlay de troca de imagem (ao clicar na img) */
  .img-edit-overlay{
    display:none;position:absolute;inset:0;
    background:rgba(0,0,0,.55);border-radius:8px;
    align-items:center;justify-content:center;flex-direction:column;gap:.6rem;
    z-index:100;
  }
  .img-edit-overlay button{
    background:#fff;color:#111;border:none;padding:.5rem 1.1rem;
    border-radius:8px;font-weight:700;font-size:.85rem;cursor:pointer;
    transition:background .2s;width:180px;text-align:center;
  }
  .img-edit-overlay button:hover{background:#e5e7eb;}
  .img-edit-overlay button.danger{background:#ef4444;color:#fff;}
  .img-edit-overlay button.danger:hover{background:#dc2626;}

  /* Modo edição: imagens clicáveis */
  body.edit-mode .post-img-wrap:hover .img-edit-overlay,
  body.edit-mode .featured-cover:hover .img-edit-overlay{
    display:flex;
  }
  body.edit-mode .post-img-wrap,
  body.edit-mode .featured-cover{cursor:pointer;}
  body.edit-mode .post-img-wrap:hover img,
  body.edit-mode .featured-cover:hover img{opacity:.55;transition:opacity .2s;}

  /* Botão "Inserir imagem" entre parágrafos */
  .insert-img-btn{
    display:none;
    width:100%;margin:.3rem 0;
    background:none;border:2px dashed #d1d5db;color:#9ca3af;
    padding:.4rem;border-radius:8px;font-size:.8rem;cursor:pointer;
    transition:all .2s;
  }
  .insert-img-btn:hover{border-color:var(--accent);color:var(--accent);background:#eff6ff;}
  body.edit-mode .insert-img-btn{display:block;}

  /* Modal genérico */
  .img-modal-backdrop{
    display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);
    z-index:10000;align-items:center;justify-content:center;
  }
  .img-modal-backdrop.open{display:flex;}
  .img-modal{
    background:#fff;border-radius:14px;padding:1.5rem;width:min(520px,95vw);
    box-shadow:0 8px 40px rgba(0,0,0,.35);
  }
  .img-modal h3{margin-bottom:1rem;font-size:1.1rem;color:#111;}
  .img-modal label{display:block;font-size:.85rem;color:#374151;margin:.8rem 0 .3rem;font-weight:600;}
  .img-modal input[type=text]{
    width:100%;padding:.6rem .8rem;border:1.5px solid #d1d5db;border-radius:8px;
    font-size:.9rem;outline:none;transition:border .2s;
  }
  .img-modal input[type=text]:focus{border-color:var(--accent);}
  .img-modal .modal-actions{display:flex;gap:.6rem;margin-top:1.2rem;flex-wrap:wrap;}
  .img-modal .modal-actions button{
    flex:1;padding:.6rem;border:none;border-radius:8px;font-weight:700;
    font-size:.88rem;cursor:pointer;transition:background .2s;min-width:100px;
  }
  .btn-primary{background:var(--accent);color:#fff;}
  .btn-primary:hover{background:#1d4ed8;}
  .btn-secondary{background:#f3f4f6;color:#374151;}
  .btn-secondary:hover{background:#e5e7eb;}
  .btn-danger{background:#ef4444;color:#fff;}
  .btn-danger:hover{background:#dc2626;}

  /* Grid de resultados Pixabay no modal */
  .pxb-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.5rem;margin-top:.8rem;max-height:240px;overflow-y:auto;}
  .pxb-grid img{width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:6px;cursor:pointer;border:2px solid transparent;transition:border .15s,transform .15s;}
  .pxb-grid img:hover{border-color:var(--accent);transform:scale(1.03);}
  .pxb-grid img.selected{border-color:#10b981;}
  .pxb-status{font-size:.8rem;color:#6b7280;margin-top:.4rem;min-height:1.2em;}
"""

# A chave Pixabay exposta no JS é intencional (já estava no script original)
JS_EDITOR = r"""
<script>
/* ════════════════════════════════════════════════════
   EDITOR VISUAL DE IMAGENS — run_md pipeline
   Funcionalidades:
     • Modo edição: ativa/desativa via barra superior
     • Clique na imagem: troca por URL ou busca Pixabay
     • Inserir imagem: botão entre blocos no modo edição
     • Remover imagem
     • Copiar Rich Text para WP (igual ao original)
════════════════════════════════════════════════════ */

const PIXABAY_KEY = "PIXABAY_KEY_PLACEHOLDER";

/* ── Utilitários ── */
function $(sel, ctx){ return (ctx||document).querySelector(sel); }
function $$(sel, ctx){ return [...(ctx||document).querySelectorAll(sel)]; }

/* ── Estado ── */
let editMode = false;
let currentTarget = null;   // {wrap, img, isCover}
let selectedPixabayUrl = null;

/* ── Barra de edição ── */
function toggleEditMode(){
  editMode = !editMode;
  document.body.classList.toggle('edit-mode', editMode);
  $('#btn-edit-mode').classList.toggle('active', editMode);
  $('#btn-edit-mode').textContent = editMode ? '✏️ Edição ON' : '✏️ Modo Edição';
}

/* ── Prepara todas as imagens existentes ── */
function prepareImages(){
  /* Imagens do corpo */
  $$('.post-img-wrap').forEach(wrap => {
    if(wrap.querySelector('.img-edit-overlay')) return;
    const overlay = makeOverlay(false);
    wrap.style.position = 'relative';
    wrap.appendChild(overlay);
  });

  /* Capa */
  const cover = $('.featured-cover');
  if(cover && !cover.querySelector('.img-edit-overlay')){
    const overlay = makeOverlay(true);
    cover.style.position = 'relative';
    cover.appendChild(overlay);
  }
}

function makeOverlay(isCover){
  const div = document.createElement('div');
  div.className = 'img-edit-overlay';
  div.innerHTML = `
    <button onclick="openImgModal(this,'url')">🔗 Colar URL</button>
    <button onclick="openImgModal(this,'pixabay')">🔍 Buscar Pixabay</button>
    <button class="danger" onclick="removeImg(this)">🗑️ Remover</button>
  `;
  return div;
}

/* ── Abre modal de edição de imagem ── */
function openImgModal(btn, mode){
  const overlay = btn.closest('.img-edit-overlay');
  const wrap    = overlay.closest('.post-img-wrap, .featured-cover');
  currentTarget = {
    wrap,
    img:     wrap.querySelector('img'),
    isCover: wrap.classList.contains('featured-cover')
  };
  selectedPixabayUrl = null;

  if(mode === 'url') showUrlModal();
  else               showPixabayModal();
}

/* ── Modal URL ── */
function showUrlModal(){
  const m = $('#modal-url');
  $('#url-input').value = currentTarget.img ? currentTarget.img.src : '';
  m.classList.add('open');
}

function applyUrlImage(){
  const url = $('#url-input').value.trim();
  if(!url){ alert('Cole uma URL válida.'); return; }
  applyImage(url);
  $('#modal-url').classList.remove('open');
}

/* ── Modal Pixabay ── */
function showPixabayModal(){
  const m = $('#modal-pixabay');
  $('#pxb-query').value = '';
  $('#pxb-grid').innerHTML = '';
  $('#pxb-status').textContent = '';
  selectedPixabayUrl = null;
  m.classList.add('open');
}

async function searchPixabay(){
  const q = $('#pxb-query').value.trim();
  if(!q){ alert('Digite o que buscar.'); return; }
  $('#pxb-status').textContent = 'Buscando…';
  $('#pxb-grid').innerHTML = '';
  selectedPixabayUrl = null;

  const url = `https://pixabay.com/api/?key=${PIXABAY_KEY}&q=${encodeURIComponent(q)}&image_type=photo&orientation=horizontal&safesearch=true&per_page=12&lang=pt`;
  try {
    const res  = await fetch(url);
    const data = await res.json();
    const hits = data.hits || [];
    if(!hits.length){ $('#pxb-status').textContent = 'Nenhuma imagem encontrada.'; return; }
    $('#pxb-status').textContent = `${hits.length} resultados — clique para selecionar`;
    hits.forEach(h => {
      const img = document.createElement('img');
      img.src   = h.previewURL;
      img.title = h.tags;
      img.dataset.large = h.largeImageURL || h.webformatURL;
      img.onclick = () => {
        $$('#pxb-grid img').forEach(i => i.classList.remove('selected'));
        img.classList.add('selected');
        selectedPixabayUrl = img.dataset.large;
      };
      $('#pxb-grid').appendChild(img);
    });
  } catch(e){
    $('#pxb-status').textContent = 'Erro na busca: ' + e.message;
  }
}

function applyPixabayImage(){
  if(!selectedPixabayUrl){ alert('Selecione uma imagem.'); return; }
  applyImage(selectedPixabayUrl);
  $('#modal-pixabay').classList.remove('open');
}

/* ── Aplica nova imagem ao DOM ── */
function applyImage(src){
  if(!currentTarget) return;
  const {wrap, img, isCover} = currentTarget;

  if(img){
    img.src = src;
  } else {
    /* Imagem foi removida antes — recria */
    const newImg = document.createElement('img');
    newImg.src   = src;
    newImg.style.cssText = 'width:100%;height:auto;border-radius:8px;display:block;';
    if(isCover){
      /* Insere antes do overlay de texto */
      const textOverlay = wrap.querySelector('.featured-cover-overlay');
      wrap.insertBefore(newImg, textOverlay);
    } else {
      wrap.insertBefore(newImg, wrap.firstChild);
    }
    currentTarget.img = newImg;
  }
}

/* ── Remove imagem ── */
function removeImg(btn){
  if(!confirm('Remover esta imagem do artigo?')) return;
  const overlay = btn.closest('.img-edit-overlay');
  const wrap    = overlay.closest('.post-img-wrap, .featured-cover');
  const img     = wrap.querySelector('img:not(.img-edit-overlay img)');
  if(img) img.remove();
}

/* ── Inserir imagem entre blocos ── */
let insertTarget = null;   /* elemento após o qual inserir */

function openInsertModal(btn){
  insertTarget = btn;
  selectedPixabayUrl = null;
  currentTarget = null;

  /* Abre o modal de inserção */
  $('#insert-query').value = '';
  $('#insert-url-input').value = '';
  $('#insert-pxb-grid').innerHTML = '';
  $('#insert-pxb-status').textContent = '';
  $('#modal-insert').classList.add('open');
}

async function searchInsertPixabay(){
  const q = $('#insert-query').value.trim();
  if(!q){ alert('Digite o que buscar.'); return; }
  $('#insert-pxb-status').textContent = 'Buscando…';
  $('#insert-pxb-grid').innerHTML = '';

  const url = `https://pixabay.com/api/?key=${PIXABAY_KEY}&q=${encodeURIComponent(q)}&image_type=photo&orientation=horizontal&safesearch=true&per_page=9&lang=pt`;
  try {
    const res  = await fetch(url);
    const data = await res.json();
    const hits = data.hits || [];
    if(!hits.length){ $('#insert-pxb-status').textContent = 'Nenhuma imagem.'; return; }
    $('#insert-pxb-status').textContent = `${hits.length} resultados`;
    hits.forEach(h => {
      const img = document.createElement('img');
      img.src   = h.previewURL;
      img.dataset.large = h.largeImageURL || h.webformatURL;
      img.onclick = () => {
        $$('#insert-pxb-grid img').forEach(i => i.classList.remove('selected'));
        img.classList.add('selected');
        selectedPixabayUrl = img.dataset.large;
        $('#insert-url-input').value = img.dataset.large;
      };
      $('#insert-pxb-grid').appendChild(img);
    });
  } catch(e){
    $('#insert-pxb-status').textContent = 'Erro: ' + e.message;
  }
}

function confirmInsertImage(){
  const url = $('#insert-url-input').value.trim() || selectedPixabayUrl;
  if(!url){ alert('Informe uma URL ou selecione uma imagem.'); return; }

  const wrap = document.createElement('div');
  wrap.className = 'post-img-wrap';
  wrap.style.position = 'relative';

  const img = document.createElement('img');
  img.src   = url;
  img.style.cssText = 'width:100%;height:auto;border-radius:8px;display:block;box-shadow:0 2px 12px rgba(0,0,0,.08);';
  wrap.appendChild(img);

  /* Overlay de edição na nova imagem */
  const overlay = makeOverlay(false);
  wrap.appendChild(overlay);

  /* Botão de inserir acima e abaixo da nova imagem */
  const btnAbove = makeInsertBtn();
  const btnBelow = makeInsertBtn();
  insertTarget.after(wrap);
  wrap.before(btnAbove);
  wrap.after(btnBelow);

  $('#modal-insert').classList.remove('open');
  insertTarget = null;
}

function makeInsertBtn(){
  const btn = document.createElement('button');
  btn.className = 'insert-img-btn';
  btn.textContent = '+ Inserir imagem aqui';
  btn.onclick = () => openInsertModal(btn);
  return btn;
}

/* ── Insere botões "+" entre todos os blocos do post-content ── */
function injectInsertButtons(){
  const content = $('#post-content');
  const children = [...content.children];
  children.forEach(child => {
    if(child.classList.contains('insert-img-btn')) return;
    const btn = makeInsertBtn();
    child.after(btn);
  });
}

/* ── Copy Rich Text — clone limpo, sem elementos de edição ── */
function copyPostHTML(){
  var container = document.getElementById('post-content');

  /* Clona o conteúdo sem modificar o DOM real */
  var clone = container.cloneNode(true);

  /* Remove todos os elementos de UI do editor do clone */
  var editorSelectors = [
    '.insert-img-btn',
    '.img-edit-overlay',
  ];
  editorSelectors.forEach(function(sel){
    clone.querySelectorAll(sel).forEach(function(el){ el.remove(); });
  });

  /* Converte o overlay do titulo da capa em elemento visivel simples,
     logo abaixo da imagem — mantém o titulo branco funcionando no WP */
  var coverOverlay = clone.querySelector('.featured-cover-overlay');
  if(coverOverlay){
    var coverTitleEl = coverOverlay.querySelector('.featured-cover-title');
    var coverTitleText = coverTitleEl ? coverTitleEl.textContent.trim() : '';
    coverOverlay.remove();
    if(coverTitleText){
      var titleNode = document.createElement('p');
      titleNode.style.cssText = 'font-size:1.7rem;font-weight:700;line-height:1.3;color:#ffffff;background:#1e1e2e;padding:1rem 1.5rem;margin:0 0 1.5rem;border-radius:0 0 10px 10px;';
      titleNode.textContent = coverTitleText;
      var coverDiv = clone.querySelector('.featured-cover');
      if(coverDiv) coverDiv.after(titleNode);
    }
  }

  /* Inline styles: remove position:relative injetado nos wrappers de imagem
     para nao poluir o HTML colado no WP */
  clone.querySelectorAll('.post-img-wrap, .featured-cover').forEach(function(el){
    el.style.position = '';
  });

  /* ── Inlineia cores do Prism nos blocos de código ──
     Mapeia cada classe token → cor, e aplica como style inline no clone.
     Assim o código vai colorido ao colar no WP/Blogger. */
  var PRISM_COLORS = {
    'comment':        '#6272a4', 'prolog':         '#6272a4',
    'doctype':        '#6272a4', 'cdata':          '#6272a4',
    'punctuation':    '#f8f8f2', 'property':       '#ff79c6',
    'tag':            '#ff79c6', 'boolean':        '#bd93f9',
    'number':         '#bd93f9', 'constant':       '#bd93f9',
    'symbol':         '#bd93f9', 'deleted':        '#ff5555',
    'selector':       '#50fa7b', 'attr-name':      '#50fa7b',
    'string':         '#f1fa8c', 'char':           '#f1fa8c',
    'builtin':        '#50fa7b', 'inserted':       '#50fa7b',
    'operator':       '#ff79c6', 'entity':         '#f8f8f2',
    'url':            '#8be9fd', 'variable':       '#8be9fd',
    'atrule':         '#ff79c6', 'attr-value':     '#f1fa8c',
    'function':       '#50fa7b', 'class-name':     '#8be9fd',
    'keyword':        '#ff79c6', 'regex':          '#ffb86c',
    'important':      '#ffb86c', 'bold':           '#ffb86c',
    'italic':         '#f1fa8c', 'namespace':      '#f8f8f2',
    'parameter':      '#ffb86c', 'decorator':      '#50fa7b',
  };

  /* Estiliza cada bloco <pre><code> com fundo escuro */
  clone.querySelectorAll('pre').forEach(function(pre){
    pre.style.cssText = [
      'background:#282a36','color:#f8f8f2','padding:1.2rem 1.4rem',
      'border-radius:8px','font-size:.88rem','line-height:1.6',
      'overflow-x:auto','margin:1.2rem 0','font-family:monospace',
    ].join(';');
    var code = pre.querySelector('code');
    if(code) code.style.cssText = 'background:none;color:inherit;padding:0;font-size:inherit;font-family:monospace;';
  });

  /* Inlineia a cor de cada token span */
  clone.querySelectorAll('span[class]').forEach(function(span){
    var classes = span.className.split(/\s+/);
    for(var i = 0; i < classes.length; i++){
      var cls = classes[i].replace('token','').trim();
      if(PRISM_COLORS[cls]){
        span.style.color = PRISM_COLORS[cls];
        break;
      }
    }
  });

  var cleanHtml = clone.innerHTML;
  var cleanText = clone.innerText;

  var blobHtml = new Blob([cleanHtml], { type:'text/html' });
  var blobText = new Blob([cleanText], { type:'text/plain' });
  var data = [new ClipboardItem({'text/html':blobHtml,'text/plain':blobText})];

  navigator.clipboard.write(data).then(function(){
    var btn = document.getElementById('copyBtn');
    btn.innerText = '\u2705 Conte\u00FAdo Copiado (Cole no Visual)!';
    btn.classList.add('copied');
    setTimeout(function(){
      btn.innerText = '\U0001f4cb Copiar Rich Text (P/ WP)';
      btn.classList.remove('copied');
    }, 3000);
  }).catch(function(err){
    console.error('Erro: ', err);
    alert('Bloqueado. Selecione o texto e d\u00EA Ctrl+C.');
  });
}

/* ── Back to top ── */
(function(){
  var btn = document.getElementById('backToTopBtn');
  window.addEventListener('scroll', function(){
    btn.classList.toggle('visible', window.scrollY > 400);
  });
  btn.addEventListener('click', function(){
    window.scrollTo({top:0,behavior:'smooth'});
  });
})();

/* ── Init ── */
document.addEventListener('DOMContentLoaded', function(){
  prepareImages();
  injectInsertButtons();
});
</script>
"""

# Modal HTML (injetado no body)
MODALS_HTML = """
<!-- ══ Modal: Trocar por URL ══ -->
<div id="modal-url" class="img-modal-backdrop">
  <div class="img-modal">
    <h3>🔗 Trocar imagem por URL</h3>
    <label>URL da imagem</label>
    <input type="text" id="url-input" placeholder="https://exemplo.com/imagem.jpg" />
    <div class="modal-actions">
      <button class="btn-primary" onclick="applyUrlImage()">Aplicar</button>
      <button class="btn-secondary" onclick="$('#modal-url').classList.remove('open')">Cancelar</button>
    </div>
  </div>
</div>

<!-- ══ Modal: Buscar Pixabay (troca) ══ -->
<div id="modal-pixabay" class="img-modal-backdrop">
  <div class="img-modal">
    <h3>🔍 Buscar imagem — Pixabay</h3>
    <label>Pesquisa em inglês</label>
    <div style="display:flex;gap:.5rem;">
      <input type="text" id="pxb-query" placeholder="ex: artificial intelligence tech" style="flex:1;" onkeydown="if(event.key==='Enter') searchPixabay()" />
      <button class="btn-primary" style="flex:0;padding:.6rem 1rem;" onclick="searchPixabay()">Buscar</button>
    </div>
    <div class="pxb-grid" id="pxb-grid"></div>
    <div class="pxb-status" id="pxb-status"></div>
    <div class="modal-actions">
      <button class="btn-primary" onclick="applyPixabayImage()">✅ Usar selecionada</button>
      <button class="btn-secondary" onclick="$('#modal-pixabay').classList.remove('open')">Cancelar</button>
    </div>
  </div>
</div>

<!-- ══ Modal: Inserir nova imagem ══ -->
<div id="modal-insert" class="img-modal-backdrop">
  <div class="img-modal">
    <h3>➕ Inserir nova imagem</h3>
    <label>Buscar no Pixabay (inglês)</label>
    <div style="display:flex;gap:.5rem;">
      <input type="text" id="insert-query" placeholder="ex: data science graph" style="flex:1;" onkeydown="if(event.key==='Enter') searchInsertPixabay()" />
      <button class="btn-primary" style="flex:0;padding:.6rem 1rem;" onclick="searchInsertPixabay()">Buscar</button>
    </div>
    <div class="pxb-grid" id="insert-pxb-grid"></div>
    <div class="pxb-status" id="insert-pxb-status"></div>
    <label style="margin-top:.8rem;">— ou cole uma URL diretamente —</label>
    <input type="text" id="insert-url-input" placeholder="https://exemplo.com/foto.jpg" />
    <div class="modal-actions">
      <button class="btn-primary" onclick="confirmInsertImage()">✅ Inserir</button>
      <button class="btn-secondary" onclick="$('#modal-insert').classList.remove('open')">Cancelar</button>
    </div>
  </div>
</div>
"""

# Barra de ferramentas superior
EDITOR_BAR_HTML = """
<div id="editor-bar">
  <span class="label">🛠 EDITOR</span>
  <button id="btn-edit-mode" onclick="toggleEditMode()">✏️ Modo Edição</button>
  <div class="sep"></div>
  <button onclick="openInsertModal(document.querySelector('#post-content > *:last-child'))">➕ Inserir imagem</button>
  <div class="sep"></div>
  <small style="opacity:.5;margin-left:auto;">Clique nas imagens para trocá-las • Ative o modo edição para ver botões de inserção</small>
</div>
"""

JS_CODE = JS_EDITOR  # substituiu o JS original


def build_html(title, meta, body_html, pixabay_key):
    prism_css = '<link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet" />'
    prism_js = (
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>\n'
        '  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>\n'
        '  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-javascript.min.js"></script>'
    )
    content_with_title = f'<h1 class="main-article-title">{title}</h1>\n' + body_html
    js_with_key = JS_CODE.replace("PIXABAY_KEY_PLACEHOLDER", pixabay_key)
    return (
        f"<!DOCTYPE html>\n<html lang='pt-BR'>\n<head>\n"
        f"  <meta charset='UTF-8'/>\n"
        f"  <meta name='viewport' content='width=device-width,initial-scale=1.0'/>\n"
        f"  <meta name='description' content='{meta}'/>\n"
        f"  <title>{title}</title>\n"
        f"  {prism_css}\n"
        f"  <style>{CSS}</style>\n"
        f"</head>\n<body>\n"
        f"  {EDITOR_BAR_HTML}\n"
        f"  <div id='post-content'>\n{content_with_title}\n  </div>\n\n"
        f"  {MODALS_HTML}\n"
        f"  <button id='copyBtn' class='floating-copy-btn' onclick='copyPostHTML()'>📋 Copiar Rich Text (P/ WP)</button>\n"
        f"  <button id='backToTopBtn' class='back-to-top' title='Voltar ao topo'>&#9650;</button>\n\n"
        f"  {prism_js}\n"
        f"  {js_with_key}\n"
        f"</body>\n</html>"
    )


# ─────────────────────────────────────────────
#  LIMPEZA DO TEXTO BRUTO
# ─────────────────────────────────────────────
def clean_raw(raw):
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    raw = raw.lstrip("\ufeff").strip()
    raw = re.sub(
        r"^```[a-zA-Z]*\n(---\n.*?---\n)```\s*\n?",
        r"\1",
        raw,
        flags=re.DOTALL
    )
    raw = re.sub(r"^```[a-zA-Z]*\n", "", raw)
    raw = re.sub(r"\n```\s*$", "", raw.rstrip())
    return raw.strip()


# ─────────────────────────────────────────────
#  PROCESSAMENTO DE MARKDOWN
# ─────────────────────────────────────────────
def process_markdown_file(filepath):
    print(f"\n{'='*55}\nArquivo: {filepath}\n{'='*55}")
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    raw = clean_raw(raw)

    title = cover_title = meta = slug = ""

    meta_match = re.match(r"^-{3,}\s*\n(.*?)\n-{3,}\s*\n?", raw, re.DOTALL)
    if meta_match:
        for line in meta_match.group(1).split("\n"):
            line = line.strip()
            if not line or ":" not in line:
                continue
            key, _, val = line.partition(":")
            key = key.strip().lower()
            val = val.strip().strip("\"'")
            if key == "title":         title       = val
            elif key == "cover_title": cover_title = val
            elif key == "meta":        meta        = val
            elif key == "slug":        slug        = val
        raw = raw[meta_match.end():].strip()
        print(f"  Frontmatter OK | title={title!r}")
    else:
        print("  Frontmatter nao encontrado — usando valores padrao.")

    if not slug:        slug        = slugify(title)
    if not cover_title: cover_title = title

    raw = re.sub(r"^#\s+.+\n*", "", raw.lstrip())

    seen_urls = set()

    # Processa capa
    cover_html  = ""
    cover_match = re.search(r"\[COVER:\s*(.+?)\s*\]", raw, re.IGNORECASE)
    if cover_match:
        query = cover_match.group(1)
        print(f"\n  [CAPA] '{query}' | cover_title='{cover_title}'")
        cdn_url = process_image(query, f"{slug}-cover", COVER_WIDTH, COVER_HEIGHT, seen_urls, "(capa)")
        if cdn_url:
            cover_html = (
                f'<div class="featured-cover">'
                f'<img src="{cdn_url}" alt="{cover_title}" width="{COVER_WIDTH}" height="{COVER_HEIGHT}" loading="eager"/>'
                f'<div class="featured-cover-overlay">'
                f'<p class="featured-cover-title">{cover_title}</p>'
                f'</div></div>\n'
            )
        raw = re.sub(r"\[COVER:\s*" + re.escape(query) + r"\s*\]", "", raw, flags=re.IGNORECASE)

    # Substitui [PIXABAY:] por placeholders
    image_placeholders = {}

    def replace_pixabay(m):
        query = m.group(1).strip()
        print(f"\n  [IMG] '{query}'")
        cdn_url = process_image(query, slug, IMG_WIDTH, IMG_HEIGHT, seen_urls, "(corpo)")
        key = f"IMGPLACEHOLDER{len(image_placeholders)}"
        if cdn_url:
            image_placeholders[key] = (
                f'<div class="post-img-wrap">'
                f'<img src="{cdn_url}" alt="{query}" '
                f'width="{IMG_WIDTH}" height="{IMG_HEIGHT}" loading="lazy"/>'
                f'</div>'
            )
        else:
            image_placeholders[key] = ""
        return f"\n\n{key}\n\n"

    raw = re.sub(r"\[PIXABAY:\s*(.+?)\s*\]", replace_pixabay, raw, flags=re.IGNORECASE)

    body_html = markdown.markdown(raw, extensions=["tables", "fenced_code", "sane_lists"])

    for key, img_html in image_placeholders.items():
        body_html = body_html.replace(f"<p>{key}</p>", img_html)
        body_html = body_html.replace(key, img_html)

    final_html = build_html(title, meta, cover_html + body_html, PIXABAY_KEY)
    html_path  = f"{slug}.html"
    with open(html_path, "w", encoding="utf-8", errors="replace") as f:
        f.write(final_html)

    print(f"\n  HTML gerado: {html_path}")


def main():
    arquivos = glob.glob("*.md")
    if not arquivos:
        print("Nenhum arquivo .md encontrado nesta pasta.")
        return
    print(f"\nMarkdown Pipeline iniciado — {len(arquivos)} arquivo(s).")
    for filepath in arquivos:
        process_markdown_file(filepath)
    print(f"\n{'='*55}\nPipeline finalizado!\n{'='*55}")

if __name__ == "__main__":
    main()
