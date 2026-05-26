# -*- coding: utf-8 -*-
"""
run_md.py — Markdown → HTML pipeline
Versão com sistema de auto-linking para 4 portais.

Novas funcionalidades:
  • Auto-linking: palavras-chave no texto viram links <a> para busca no portal
  • Seletor de portal no editor bar: alterna entre os 4 blogs dinamicamente
  • [PIXABAY: query] vira card de sugestão visual
  • Todas as outras funções do editor permanecem intactas

Portais suportados:
  • ia.bio.br        → https://www.ia.bio.br/search?q=TERMO        (Blogger)
  • maiquelgomes     → https://maiquelgomes.com.br/?s=TERMO         (WordPress)
  • traineai         → https://blog.traineai.com.br/search?q=TERMO  (Blogger)
  • ia.pro.br        → https://ia.pro.br/?s=TERMO                   (WordPress)
"""

import os
import re
import glob
import markdown

# ===================== CONFIGURAÇÕES =====================
PIXABAY_KEY   = " "
GITHUB_TOKEN  = " "
GITHUB_OWNER  = "cursoarteatuarial"
GITHUB_REPO   = "blogs"
GITHUB_FOLDER = "blog"

IMG_WIDTH      = 1200
IMG_HEIGHT     = 630
COVER_WIDTH    = 1600
COVER_HEIGHT   = 900
IMG_QUALITY    = 82
SEARCH_LANG    = "pt"
# =========================================================

# ─────────────────────────────────────────────
#  PORTAIS DE BUSCA
# ─────────────────────────────────────────────
PORTALS = [
    {
        "id":      "iabio",
        "name":    "ia.bio.br",
        "label":   "🤖 ia.bio.br",
        "base":    "https://www.ia.bio.br/search?q=",
        "engine":  "blogger",
        "color":   "#2563eb",
    },
    {
        "id":      "maiquel",
        "name":    "maiquelgomes.com.br",
        "label":   "👤 maiquelgomes",
        "base":    "https://maiquelgomes.com.br/?s=",
        "engine":  "wordpress",
        "color":   "#7c3aed",
    },
    {
        "id":      "traineai",
        "name":    "blog.traineai.com.br",
        "label":   "🎓 traineai",
        "base":    "https://blog.traineai.com.br/search?q=",
        "engine":  "blogger",
        "color":   "#059669",
    },
    {
        "id":      "iapro",
        "name":    "ia.pro.br",
        "label":   "⚡ ia.pro.br",
        "base":    "https://ia.pro.br/?s=",
        "engine":  "wordpress",
        "color":   "#dc2626",
    },
]

# ─────────────────────────────────────────────
#  PALAVRAS-CHAVE PARA AUTO-LINKING (314 termos)
# ─────────────────────────────────────────────
KEYWORDS = [
    # IA / Machine Learning
    "inteligência artificial", "machine learning", "aprendizado de máquina",
    "deep learning", "aprendizado profundo", "rede neural", "redes neurais",
    "processamento de linguagem natural", "visão computacional",
    "reconhecimento de imagem", "geração de texto", "modelo de linguagem",
    "large language model", "transformer", "embeddings", "fine-tuning",
    "prompt engineering", "engenharia de prompts",
    "retrieval augmented generation", "agentes de IA", "agente autônomo",
    "IA generativa", "IA conversacional", "chatbot", "assistente virtual",
    "ChatGPT", "Gemini", "Mistral", "Copilot", "Midjourney",
    "Stable Diffusion", "OpenAI", "Anthropic", "Google DeepMind",
    "Meta AI", "Hugging Face", "algoritmo", "algoritmos",
    "modelo preditivo", "inferência", "dataset", "conjunto de dados",
    "anotação de dados", "supervised learning", "unsupervised learning",
    "reinforcement learning", "aprendizado por reforço",
    "transfer learning", "aprendizado por transferência",
    "overfitting", "underfitting", "viés algorítmico", "fairness",
    "explicabilidade", "IA explicável", "interpretabilidade",
    "IA responsável", "IA ética", "ética em IA", "regulamentação de IA",
    "multimodal", "modelo multimodal", "síntese de voz", "deepfake",
    "AGI", "inteligência artificial geral", "superinteligência",
    "singularidade tecnológica", "aceleração tecnológica",
    "detecção de IA", "conteúdo sintético", "IA no Brasil",
    "política de IA", "regulação de IA", "impacto social da IA",
    "sustentabilidade em IA", "IA verde", "consumo energético de IA",
    "TensorFlow", "PyTorch", "scikit-learn", "LangChain",
    "LlamaIndex", "Ollama", "AutoML",
    # Tecnologia / Software
    "tecnologia", "software", "hardware", "cloud computing",
    "computação em nuvem", "edge computing", "computação de borda",
    "serverless", "microserviços", "integração", "open source",
    "código aberto", "DevOps", "MLOps", "container", "Docker",
    "Kubernetes", "infraestrutura", "banco de dados",
    "data lake", "data warehouse", "pipeline de dados",
    "Python", "JavaScript", "TypeScript", "Rust",
    "framework", "biblioteca", "computação quântica",
    "quantum computing", "blockchain", "web3", "criptomoeda",
    "Bitcoin", "Ethereum", "IoT", "internet das coisas",
    "smart home", "realidade aumentada", "realidade virtual",
    "metaverso", "conectividade", "banda larga",
    "cibersegurança", "segurança digital", "ransomware", "phishing",
    "criptografia", "autenticação", "zero trust", "LGPD", "GDPR",
    "privacidade de dados", "proteção de dados",
    # Computação / Infraestrutura
    "processador", "semicondutor", "NVIDIA", "AMD", "Intel",
    "servidor", "datacenter", "data center", "supercomputador",
    "computação de alto desempenho", "paralelismo",
    "robótica", "robô", "cobot", "automação industrial",
    "indústria 4.0", "manufatura inteligente", "fábrica do futuro",
    "gêmeo digital", "digital twin", "simulação",
    "computação neuromórfica", "computação fotônica",
    # Mercado / Negócios
    "transformação digital", "digitalização", "inovação", "disrupção",
    "startup", "unicórnio", "ecossistema de inovação",
    "venture capital", "investimento em tecnologia",
    "produto digital", "SaaS", "plataforma digital", "marketplace",
    "e-commerce", "comércio eletrônico", "fintech", "fintechs",
    "healthtech", "edtech", "legaltech", "agritech", "govtech",
    "automação", "automação de processos", "hiperautomação",
    "atendimento ao cliente", "analytics", "business intelligence",
    "dashboard", "big data", "ciência de dados", "data science",
    "engenharia de dados", "personalização",
    "algoritmo de recomendação", "marketing digital",
    "conteúdo gerado por IA", "produtividade", "eficiência operacional",
    # Emprego / Futuro do Trabalho
    "futuro do trabalho", "mercado de trabalho", "emprego",
    "desemprego tecnológico", "requalificação", "upskilling", "reskilling",
    "habilidades digitais", "letramento digital", "alfabetização em IA",
    "trabalho remoto", "trabalho híbrido", "freelancer", "gig economy",
    "profissões do futuro", "engenheiro de IA", "cientista de dados",
    "engenheiro de dados", "desenvolvedor","desenvolvedores","programador",
    "prompt engineer", "analista de dados", "gestor de inovação",
    "gerente de produto", "soft skills", "hard skills",
    "liderança tecnológica", "diversidade em tecnologia",
    "inclusão digital", "educação tecnológica", "ensino de programação",
    "bootcamp", "cursos online", "aprendizado contínuo",
    "certificação em IA", "certificação em cloud","empresas",
    "desigualdade digital","empresa",
    # Siglas (curtas, cuidado com falsos positivos)
    "NLP", "PLN", "RAG", "LLM", "XAI", "RPA", "BI", "IoT",
    "AR", "VR", "XR", "API", "SaaS", "GPU", "TPU", "HPC",
    "SDK", "SEO", "UX", "CX", "ROI", "KPI", "ETL",
    # Ciência
    "ciência", "pesquisa científica", "cientista", "laboratório", "experimento",
    "hipótese", "metodologia científica", "publicação científica", "artigo científico",
    "peer review", "revisão por pares", "Nature", "Science", "arxiv",
    "neurociência", "bioinformática", "física quântica", "astrofísica",
    "genômica", "proteômica", "CRISPR", "edição genética", "biotecnologia",
    "nanotecnologia", "física computacional", "simulação científica",
    "telescópio", "acelerador de partículas", "CERN", "NASA", "ESA",
    "clima", "mudança climática", "aquecimento global", "carbono",
    "energia renovável", "energia solar", "fusão nuclear", "física nuclear",
    "química computacional", "modelagem molecular", "biologia sintética",
    "inteligência coletiva", "complexidade", "sistemas complexos",
    "ciência aberta", "open science", "reprodutibilidade", "metanálise",

    # Universidade
    "universidade", "faculdade", "instituição de ensino superior", "campus",
    "graduação", "pós-graduação", "mestrado", "doutorado", "pós-doutorado",
    "professor", "pesquisador", "orientador", "dissertação", "tese",
    "bolsa de pesquisa", "CAPES", "CNPq", "FAPESP", "lattes",
    "USP", "UNICAMP", "UFRJ", "UFMG", "UFRGS", "UnB", "UFSC",
    "MIT", "Stanford", "Harvard", "Oxford", "Cambridge",
    "ensino superior", "educação superior", "acesso à universidade",
    "ENEM", "vestibular", "cotas universitárias", "ProUni", "FIES",
    "extensão universitária", "iniciação científica", "TCC",
    "laboratório universitário", "spin-off acadêmico", "transferência de tecnologia",
    "ranking universitário", "QS World Rankings", "Times Higher Education",
    "interdisciplinaridade", "núcleo de inovação", "parque tecnológico",

    # Internet
    "internet", "web", "world wide web", "banda larga", "fibra óptica",
    "protocolo", "HTTP", "DNS", "IP", "TCP",
    "navegador", "browser", "Chrome", "Firefox", "Safari",
    "rede social", "mídias sociais", "Instagram", "LinkedIn", "X",
    "YouTube", "TikTok", "WhatsApp", "Telegram", "Discord",
    "streaming", "podcast", "newsletter", "feed", "algoritmo de feed",
    "influencer", "criador de conteúdo", "economia criativa",
    "dark web", "deep web", "tor", "VPN", "proxy",
    "nuvem", "armazenamento em nuvem", "Google Drive", "OneDrive", "Dropbox",
    "e-mail", "spam", "phishing por e-mail", "inbox",
    "domínio", "hospedagem", "servidor web", "CDN", "cache",
    "velocidade de internet", "latência de rede", "throughput",
    "neutralidade da rede", "governança da internet", "ICANN", "CGI.br",
    "acesso digital", "exclusão digital", "democratização da internet",
    "internet das coisas", "web semântica", "web 3.0",
    # Profissões
    "médico", "advogado", "engenheiro", "arquiteto", "psicólogo",
    "enfermeiro", "farmacêutico", "veterinário", "nutricionista", "fisioterapeuta",
    "contador", "economista", "administrador", "jornalista", "publicitário",
    "designer", "designer gráfico", "UX designer", "UI designer",
    "fotógrafo", "videomaker", "editor de vídeo", "motion designer",
    "professor", "pedagogo", "educador", "tutor", "instrutor",
    "desenvolvedor", "programador", "engenheiro de software", "arquiteto de software",
    "engenheiro de dados", "cientista de dados", "analista de dados",
    "engenheiro de IA", "engenheiro de machine learning", "pesquisador em IA",
    "prompt engineer", "AI trainer", "engenheiro de prompt",
    "analista de sistemas", "analista de segurança", "pentester",
    "DevOps engineer", "SRE", "engenheiro de infraestrutura",
    "product manager", "product owner", "scrum master", "agile coach",
    "growth hacker", "analista de marketing", "SEO specialist",
    "social media manager", "community manager", "gestor de tráfego",
    "empreendedor", "fundador", "CEO", "CTO", "CFO", "COO",
    "consultor", "freelancer", "autônomo", "MEI",
    "trader", "analista financeiro", "gestor de investimentos",
    "biólogo", "químico", "físico", "matemático", "estatístico",
    "geógrafo", "geólogo", "oceanógrafo", "meteorologista",
    "assistente virtual", "operador de IA", "curador de dados",
]

# Ordena do mais longo para o mais curto → evita substituição parcial
KEYWORDS_SORTED = sorted(set(KEYWORDS), key=lambda k: -len(k))


# ─────────────────────────────────────────────
#  UTILITÁRIOS
# ─────────────────────────────────────────────
def slugify(text):
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_]+", "-", text).strip("-")[:60]


def slugify_keyword(kw):
    """Transforma keyword em formato de URL (slug para busca)."""
    kw = kw.lower().strip()
    kw = re.sub(r"[^\w\s-]", "", kw)
    return re.sub(r"\s+", "+", kw).strip("+")


# ─────────────────────────────────────────────
#  AUTO-LINKING: injeta links no HTML gerado
# ─────────────────────────────────────────────
def build_autolink_data():
    """
    Retorna lista de (keyword, slug) ordenada do maior para menor termo,
    para substituição segura (evita substituir parte de um termo maior).
    """
    result = []
    for kw in KEYWORDS_SORTED:
        result.append((kw, slugify_keyword(kw)))
    return result


# ─────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────
CSS = """
  :root{
    --accent:#2563eb;--bg:#ffffff;--text:#1e1e2e;--muted:#6b7280;
    --tip-bg:#eff6ff;--tip-border:#2563eb;--cta-bg:#1e40af;--cta-text:#ffffff;
    --faq-bg:#f9fafb;--editor-bar:#1e1e2e;--editor-bar-text:#f9fafb;
    --portal-color:#2563eb;
  }
  *{box-sizing:border-box;margin:0;padding:0;}
  body{font-family:Georgia,serif;background:var(--bg);color:var(--text);line-height:1.75;font-size:1.05rem;max-width:860px;margin:2rem auto;padding:0 1.2rem 6rem;}

  .main-article-title{font-size:2.4rem;margin:1rem 0 2rem;line-height:1.2;font-weight:800;color:#111827;}

  h2{font-size:1.5rem;margin:2.5rem 0 .8rem;padding-bottom:.4rem;border-bottom:2px solid #e5e7eb;}
  h3{font-size:1.2rem;margin:1.8rem 0 .6rem;color:#374151;}
  p{margin:.75rem 0;}ul,ol{margin:.75rem 0 .75rem 1.5rem;}li{margin:.4rem 0;}
  a{color:var(--accent);text-decoration:none;}a:hover{text-decoration:underline;}
  strong{font-weight:700;}em{font-style:italic;}

  /* ── Auto-links de palavras-chave ── */
  a.kw-link{
    color:var(--portal-color);
    text-decoration:none;
    border-bottom:1px dotted var(--portal-color);
    transition:all .2s;
    font-weight:inherit;
  }
  a.kw-link:hover{
    border-bottom-style:solid;
    background:rgba(37,99,235,.06);
    border-radius:2px;
    padding:0 1px;
  }

  .post-img-wrap{position:relative;margin:1.5rem 0;}
  .post-img-wrap img{width:100%;height:auto;border-radius:8px;display:block;box-shadow:0 2px 12px rgba(0,0,0,.08);}

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

  /* ══ SELETOR DE PORTAL ══ */
  .portal-selector{
    display:flex;align-items:center;gap:.35rem;flex-wrap:wrap;
  }
  .portal-selector .ps-label{
    font-size:.72rem;font-weight:700;letter-spacing:.5px;opacity:.6;
    text-transform:uppercase;margin-right:.1rem;
  }
  .portal-btn{
    border:none;padding:.3rem .7rem;border-radius:20px;
    font-size:.75rem;font-weight:700;cursor:pointer;
    transition:all .2s;opacity:.55;
    font-family:system-ui,sans-serif;
    white-space:nowrap;
  }
  .portal-btn:hover{opacity:.85;transform:translateY(-1px);}
  .portal-btn.active{opacity:1;box-shadow:0 2px 8px rgba(0,0,0,.25);}
  .portal-btn.off{
    background:#374151 !important;color:#9ca3af !important;
    border:1px solid #4b5563;opacity:.45;
  }
  .portal-btn.off.active{
    background:#1e1e2e !important;color:#f9fafb !important;
    opacity:.7;border-color:#6b7280;
  }

  /* Badge de links ativos */
  #link-count-badge{
    font-size:.72rem;background:#10b981;color:#fff;
    border-radius:20px;padding:.15rem .55rem;
    font-weight:700;margin-left:.25rem;
    display:none;
  }
  #link-count-badge.visible{display:inline-block;}

  /* ══ EDITOR VISUAL ══ */
  #editor-bar{
    position:sticky;top:0;z-index:8000;
    background:var(--editor-bar);color:var(--editor-bar-text);
    display:flex;align-items:center;gap:.5rem;
    padding:.55rem 1rem;font-size:.85rem;
    border-radius:0 0 10px 10px;
    box-shadow:0 3px 12px rgba(0,0,0,.3);
    margin:-2rem -1.2rem 1.5rem;
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

  .img-edit-overlay{
    display:none;position:absolute;inset:0;
    background:rgba(0,0,0,.55);border-radius:8px;
    align-items:center;justify-content:center;flex-direction:column;gap:.6rem;
    z-index:100;
  }
  .img-edit-overlay button{
    background:#fff;color:#111;border:none;padding:.5rem 1.1rem;
    border-radius:8px;font-weight:700;font-size:.85rem;cursor:pointer;
    transition:background .2s;width:200px;text-align:center;
  }
  .img-edit-overlay button:hover{background:#e5e7eb;}
  .img-edit-overlay button.danger{background:#ef4444;color:#fff;}
  .img-edit-overlay button.danger:hover{background:#dc2626;}
  .img-edit-overlay button.upload-btn{background:#f59e0b;color:#fff;}
  .img-edit-overlay button.upload-btn:hover{background:#d97706;}
  .img-edit-overlay button.local-btn{background:#8b5cf6;color:#fff;}
  .img-edit-overlay button.local-btn:hover{background:#7c3aed;}
  .img-edit-overlay button.download-btn{background:#0ea5e9;color:#fff;}
  .img-edit-overlay button.download-btn:hover{background:#0284c7;}

  body.edit-mode .post-img-wrap:hover .img-edit-overlay,
  body.edit-mode .featured-cover:hover .img-edit-overlay{display:flex;}
  body.edit-mode .post-img-wrap,
  body.edit-mode .featured-cover{cursor:pointer;}
  body.edit-mode .post-img-wrap:hover img,
  body.edit-mode .featured-cover:hover img{opacity:.55;transition:opacity .2s;}

  .insert-img-btn{
    display:none;
    width:100%;margin:.3rem 0;
    background:none;border:2px dashed #d1d5db;color:#9ca3af;
    padding:.4rem;border-radius:8px;font-size:.8rem;cursor:pointer;
    transition:all .2s;
  }
  .insert-img-btn:hover{border-color:var(--accent);color:var(--accent);background:#eff6ff;}
  body.edit-mode .insert-img-btn{display:block;}

  .img-status-badge{
    position:absolute;top:8px;left:8px;
    font-size:.7rem;font-weight:700;padding:.2rem .5rem;border-radius:20px;
    pointer-events:none;z-index:50;
  }
  .img-status-badge.github{background:#10b981;color:#fff;}
  .img-status-badge.external{background:#f59e0b;color:#fff;}
  body:not(.edit-mode) .img-status-badge{display:none;}

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
  .btn-upload{background:#f59e0b;color:#fff;}
  .btn-upload:hover{background:#d97706;}
  .btn-local{background:#8b5cf6;color:#fff;}
  .btn-local:hover{background:#7c3aed;}
  .btn-paste-url{background:#2563eb;color:#fff;border:none;padding:.6rem .8rem;border-radius:8px;font-weight:700;font-size:.85rem;cursor:pointer;transition:background .2s;white-space:nowrap;}
  .btn-paste-url:hover{background:#1d4ed8;}
  .btn-paste-url.pasted{background:#10b981;}
  .btn-clear-url{background:#f3f4f6;color:#6b7280;border:none;padding:.6rem .65rem;border-radius:8px;font-weight:900;font-size:.9rem;cursor:pointer;transition:background .2s;line-height:1;}
  .btn-clear-url:hover{background:#fecaca;color:#ef4444;}
  .btn-copy-url{background:#6b7280;color:#fff;border:none;padding:.6rem .8rem;border-radius:8px;font-weight:700;font-size:.85rem;cursor:pointer;transition:background .2s;white-space:nowrap;}
  .btn-copy-url:hover{background:#4b5563;}
  .btn-copy-url.copied{background:#10b981;}

  .pxb-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.5rem;margin-top:.8rem;max-height:240px;overflow-y:auto;}
  .pxb-grid img{width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:6px;cursor:pointer;border:2px solid transparent;transition:border .15s,transform .15s;}
  .pxb-grid img:hover{border-color:var(--accent);transform:scale(1.03);}
  .pxb-grid img.selected{border-color:#10b981;}
  .pxb-status{font-size:.8rem;color:#6b7280;margin-top:.4rem;min-height:1.2em;}

  .local-upload-zone{
    border:2px dashed #d1d5db;border-radius:10px;padding:1.5rem;text-align:center;
    color:#6b7280;font-size:.88rem;cursor:pointer;transition:all .2s;margin-top:.8rem;
    background:#fafafa;
  }
  .local-upload-zone:hover,.local-upload-zone.dragover{
    border-color:#8b5cf6;background:#f5f3ff;color:#8b5cf6;
  }
  .local-upload-zone .icon{font-size:2rem;display:block;margin-bottom:.5rem;}
  .local-preview{display:none;margin-top:.8rem;border-radius:8px;overflow:hidden;border:2px solid #10b981;}
  .local-preview img{width:100%;height:140px;object-fit:cover;display:block;}
  .local-preview-name{font-size:.78rem;color:#374151;padding:.4rem .6rem;background:#f9fafb;font-weight:600;}

  #toast{
    position:fixed;top:70px;right:20px;z-index:99999;
    background:#1e1e2e;color:#fff;
    padding:.7rem 1.2rem;border-radius:10px;font-size:.88rem;font-weight:600;
    box-shadow:0 4px 20px rgba(0,0,0,.3);
    transform:translateY(-10px);opacity:0;
    transition:all .3s ease;pointer-events:none;
  }
  #toast.show{transform:translateY(0);opacity:1;}
  #toast.success{border-left:4px solid #10b981;}
  #toast.error{border-left:4px solid #ef4444;}
  #toast.info{border-left:4px solid #2563eb;}

  /* ══ APAGAR BLOCOS ══ */
  body.delete-mode #post-content > *:not(.insert-img-btn){
    cursor:pointer;outline:2px dashed transparent;transition:outline .15s,background .15s;
    border-radius:4px;
  }
  body.delete-mode #post-content > *:not(.insert-img-btn):hover{
    outline:2px dashed #ef4444;background:rgba(239,68,68,.05);
  }
  body.delete-mode #post-content > *.selected-for-delete{
    outline:2px solid #ef4444 !important;background:rgba(239,68,68,.12) !important;
  }
  .delete-mode-bar{
    display:none;position:fixed;bottom:80px;left:50%;transform:translateX(-50%);
    background:#1e1e2e;color:#fff;border-radius:50px;padding:.6rem 1.2rem;
    box-shadow:0 4px 20px rgba(0,0,0,.4);z-index:9998;align-items:center;gap:.8rem;
    font-size:.85rem;font-weight:600;white-space:nowrap;
  }
  body.delete-mode .delete-mode-bar{display:flex;}
  .delete-mode-bar span{opacity:.8;}
  .delete-mode-bar button{border:none;border-radius:20px;padding:.4rem 1rem;font-weight:700;font-size:.82rem;cursor:pointer;transition:background .2s;}
  .delete-mode-bar .btn-del-confirm{background:#ef4444;color:#fff;}
  .delete-mode-bar .btn-del-confirm:hover{background:#dc2626;}
  .delete-mode-bar .btn-del-cancel{background:#374151;color:#fff;}
  .delete-mode-bar .btn-del-cancel:hover{background:#4b5563;}
  .delete-mode-bar .del-count{background:#ef4444;color:#fff;border-radius:20px;padding:.1rem .55rem;font-size:.8rem;min-width:24px;text-align:center;}

  .url-input-row{display:flex;gap:.4rem;align-items:center;}
  .url-input-row input{flex:1;}

  /* ══ EDITAR TEXTO (contenteditable) ══ */
  body.text-edit-mode #post-content{
    outline:2px dashed #f59e0b;outline-offset:4px;border-radius:6px;
  }
  body.text-edit-mode #post-content *:not(.insert-img-btn):not(.img-edit-overlay):not(.img-edit-overlay *):not(.img-status-badge):not(.img-suggestion-card):not(.img-suggestion-card *){
    cursor:text;
  }
  body.text-edit-mode #post-content [contenteditable=true]:focus{
    outline:2px solid #f59e0b;border-radius:3px;background:rgba(245,158,11,.04);
  }
  .text-edit-hint{
    display:none;position:fixed;bottom:130px;left:50%;transform:translateX(-50%);
    background:#f59e0b;color:#1e1e2e;border-radius:50px;padding:.5rem 1.2rem;
    font-size:.8rem;font-weight:700;z-index:9997;box-shadow:0 3px 12px rgba(245,158,11,.4);
    white-space:nowrap;pointer-events:none;
  }
  body.text-edit-mode .text-edit-hint{display:block;}

  /* ══ CARD DE SUGESTÃO DE IMAGEM ══ */
  .img-suggestion-card{
    position:relative;margin:1.5rem 0;
    border:2px dashed #c7d2fe;border-radius:12px;
    background:linear-gradient(135deg,#eef2ff 0%,#f0fdf4 100%);
    padding:1.2rem 1.5rem;display:flex;align-items:center;gap:1rem;
    cursor:pointer;transition:all .25s ease;user-select:none;
  }
  .img-suggestion-card:hover{
    border-color:#6366f1;
    background:linear-gradient(135deg,#e0e7ff 0%,#dcfce7 100%);
    box-shadow:0 4px 20px rgba(99,102,241,.15);transform:translateY(-1px);
  }
  .img-suggestion-card:active{transform:translateY(0);}
  .img-suggestion-card .card-icon{
    font-size:2rem;flex-shrink:0;width:52px;height:52px;background:#fff;
    border-radius:10px;display:flex;align-items:center;justify-content:center;
    box-shadow:0 2px 8px rgba(0,0,0,.08);
  }
  .img-suggestion-card .card-body{flex:1;min-width:0;}
  .img-suggestion-card .card-label{
    font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.8px;
    color:#6366f1;margin-bottom:.25rem;font-family:system-ui,sans-serif;
  }
  .img-suggestion-card .card-query{
    font-size:1rem;font-weight:700;color:#1e1e2e;font-family:Georgia,serif;
    line-height:1.3;margin-bottom:.25rem;
  }
  .img-suggestion-card .card-hint{font-size:.75rem;color:#6b7280;font-family:system-ui,sans-serif;}
  .img-suggestion-card .card-actions{display:flex;flex-direction:column;gap:.4rem;flex-shrink:0;}
  .img-suggestion-card .btn-card-copy{
    background:#6366f1;color:#fff;border:none;padding:.4rem .9rem;border-radius:20px;
    font-size:.78rem;font-weight:700;cursor:pointer;font-family:system-ui,sans-serif;
    transition:background .2s;white-space:nowrap;
  }
  .img-suggestion-card .btn-card-copy:hover{background:#4f46e5;}
  .img-suggestion-card .btn-card-copy.copied{background:#10b981;}
  .img-suggestion-card .btn-card-insert{
    background:#10b981;color:#fff;border:none;padding:.4rem .9rem;border-radius:20px;
    font-size:.78rem;font-weight:700;cursor:pointer;font-family:system-ui,sans-serif;
    transition:background .2s;white-space:nowrap;
  }
  .img-suggestion-card .btn-card-insert:hover{background:#059669;}
  @keyframes card-pulse{0%,100%{border-color:#c7d2fe;}50%{border-color:#6366f1;}}
  .img-suggestion-card{animation:card-pulse 3s ease-in-out infinite;}
  .img-suggestion-card:hover{animation:none;}
  .img-suggestion-card.done{
    opacity:.4;filter:grayscale(1);pointer-events:none;animation:none;
    border-style:solid;border-color:#d1d5db;
  }
  .img-suggestion-card.done::after{
    content:'✅ Imagem inserida';position:absolute;inset:0;
    display:flex;align-items:center;justify-content:center;
    background:rgba(255,255,255,.7);border-radius:10px;
    font-weight:700;color:#374151;font-family:system-ui,sans-serif;font-size:.9rem;
  }
"""

# ─────────────────────────────────────────────
#  DADOS DOS PORTAIS PARA JS
# ─────────────────────────────────────────────
def build_portals_js():
    """Gera o objeto JS com os dados dos portais."""
    lines = ["const PORTALS = ["]
    for p in PORTALS:
        lines.append(f"  {{ id:{p['id']!r}, name:{p['name']!r}, label:{p['label']!r}, base:{p['base']!r}, engine:{p['engine']!r}, color:{p['color']!r} }},")
    lines.append("];")
    return "\n".join(lines)


def build_keywords_js():
    """Gera o array JS de keywords."""
    items = [f"  {repr(kw)}" for kw in KEYWORDS_SORTED]
    return "const KEYWORDS = [\n" + ",\n".join(items) + "\n];"


# ─────────────────────────────────────────────
#  JS DO EDITOR
# ─────────────────────────────────────────────
JS_EDITOR = r"""
<script>
/* ════════════════════════════════════════════════════
   EDITOR VISUAL — run_md pipeline
   v2: sistema de auto-linking por portal
════════════════════════════════════════════════════ */

const PIXABAY_KEY    = "PIXABAY_KEY_PLACEHOLDER";
const GITHUB_TOKEN   = "GITHUB_TOKEN_PLACEHOLDER";
const GITHUB_OWNER   = "GITHUB_OWNER_PLACEHOLDER";
const GITHUB_REPO    = "GITHUB_REPO_PLACEHOLDER";
const GITHUB_FOLDER  = "GITHUB_FOLDER_PLACEHOLDER";

PORTALS_DATA_PLACEHOLDER

KEYWORDS_DATA_PLACEHOLDER

/* ── Utilitários ── */
function $(sel, ctx){ return (ctx||document).querySelector(sel); }
function $$(sel, ctx){ return [...(ctx||document).querySelectorAll(sel)]; }

function showToast(msg, type='info', duration=3500){
  const t = $('#toast');
  t.textContent = msg;
  t.className = 'show ' + type;
  clearTimeout(t._timer);
  t._timer = setTimeout(() => { t.className = ''; }, duration);
}

function isGithubUrl(src){
  return src && (
    src.includes('raw.githubusercontent.com') ||
    src.includes('cdn.jsdelivr.net/gh/')
  );
}

/* ═══════════════════════════════════════════════════
   AUTO-LINKING POR PORTAL
═══════════════════════════════════════════════════ */
let activePortalId = null; /* null = links desativados */

function slugifyKeyword(kw){
  return kw.toLowerCase().trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '+')
    .replace(/^-+|-+$/g, '');
}

function getPortalSearchUrl(portalId, keyword){
  const p = PORTALS.find(x => x.id === portalId);
  if(!p) return null;
  return p.base + encodeURIComponent(keyword).replace(/%20/g, '+');
}

function applyAutoLinks(portalId){
  /* Remove links existentes primeiro (unwrap) */
  removeAutoLinks();

  if(!portalId){ updateLinkBadge(0); return; }

  const portal = PORTALS.find(p => p.id === portalId);
  if(!portal) return;

  /* Aplica cor do portal */
  document.documentElement.style.setProperty('--portal-color', portal.color);

  /* Seleciona todos os nós de texto dentro de parágrafos, li, h2, h3
     mas fora de: code, pre, a, .img-suggestion-card, .insert-img-btn */
  const ALLOWED_PARENTS = 'p, li, h2, h3, h4, td, th, blockquote';
  const SKIP_INSIDE = 'code, pre, a, .img-suggestion-card, .img-edit-overlay, .insert-img-btn, .img-status-badge';

  let linkCount = 0;

  document.querySelectorAll(`#post-content ${ALLOWED_PARENTS}`).forEach(el => {
    /* Pula se está dentro de elemento não permitido */
    if(el.closest(SKIP_INSIDE)) return;

    /* Cada keyword pode aparecer UMA VEZ por parágrafo → melhor UX */
    const usedInBlock = new Set();

    /* Percorre nós de texto */
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, {
      acceptNode: n => {
        if(n.parentElement.closest(SKIP_INSIDE)) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });

    const nodes = [];
    let n;
    while((n = walker.nextNode())) nodes.push(n);

    nodes.forEach(textNode => {
      let text = textNode.nodeValue;
      let changed = false;
      const frag = document.createDocumentFragment();
      let lastIdx = 0;

      /* Tenta cada keyword (já ordenada do maior para o menor) */
      /* Para cada nó, substitui SOMENTE A PRIMEIRA OCORRÊNCIA de cada keyword */
      const matchList = [];
      KEYWORDS.forEach(kw => {
        if(usedInBlock.has(kw.toLowerCase())) return;
        const regex = new RegExp(`(?<![\\w\\-])${escapeReg(kw)}(?![\\w\\-])`, 'gi');
        let m;
        while((m = regex.exec(text)) !== null){
          /* Verifica sobreposição com match já encontrado */
          const overlap = matchList.some(ex =>
            m.index < ex.end && (m.index + m[0].length) > ex.start
          );
          if(!overlap){
            matchList.push({ start: m.index, end: m.index + m[0].length, kw, matched: m[0] });
            usedInBlock.add(kw.toLowerCase());
          }
          break; /* só a primeira ocorrência por nó */
        }
      });

      if(!matchList.length) return;
      matchList.sort((a,b) => a.start - b.start);

      matchList.forEach(({ start, end, kw, matched }) => {
        if(start > lastIdx){
          frag.appendChild(document.createTextNode(text.slice(lastIdx, start)));
        }
        const a = document.createElement('a');
        a.href = getPortalSearchUrl(portalId, kw);
        a.className = 'kw-link';
        a.dataset.kw = kw;
        a.dataset.portal = portalId;
        a.textContent = matched;
        a.target = '_blank';
        a.rel = 'noopener';
        a.title = `Buscar "${kw}" em ${portal.name}`;
        frag.appendChild(a);
        lastIdx = end;
        linkCount++;
        changed = true;
      });

      if(changed){
        if(lastIdx < text.length){
          frag.appendChild(document.createTextNode(text.slice(lastIdx)));
        }
        textNode.parentNode.replaceChild(frag, textNode);
      }
    });
  });

  updateLinkBadge(linkCount);
  showToast(`🔗 ${linkCount} links aplicados → ${portal.name}`, 'success', 3500);
}

function removeAutoLinks(){
  $$('.kw-link').forEach(a => {
    const parent = a.parentNode;
    while(a.firstChild) parent.insertBefore(a.firstChild, a);
    parent.removeChild(a);
    /* Normaliza texto adjacente */
    parent.normalize();
  });
  document.documentElement.style.removeProperty('--portal-color');
}

function escapeReg(str){
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function updateLinkBadge(count){
  const badge = $('#link-count-badge');
  if(count > 0){
    badge.textContent = `🔗 ${count} links`;
    badge.classList.add('visible');
  } else {
    badge.classList.remove('visible');
  }
}

function selectPortal(portalId){
  const btns = $$('.portal-btn');

  if(activePortalId === portalId){
    /* Toggle: clicou no mesmo → desativa */
    activePortalId = null;
    btns.forEach(b => { b.classList.remove('active'); b.classList.add('off'); });
    removeAutoLinks();
    updateLinkBadge(0);
    showToast('🔗 Links desativados', 'info', 2500);
    return;
  }

  activePortalId = portalId;
  const portal = PORTALS.find(p => p.id === portalId);

  btns.forEach(b => {
    const isActive = b.dataset.portal === portalId;
    b.classList.toggle('active', isActive);
    b.classList.toggle('off', !isActive);
    if(isActive && portal){
      b.style.background = portal.color;
      b.style.color = '#fff';
    } else {
      b.style.background = '';
      b.style.color = '';
    }
  });

  applyAutoLinks(portalId);
}

/* Re-aplica links quando o usuário altera o portal sem ter links */
function initPortalSelector(){
  $$('.portal-btn').forEach(btn => {
    btn.classList.add('off');
  });
}

/* ═══════════════════════════════════════════════════
   RESTANTE DO EDITOR (inalterado)
═══════════════════════════════════════════════════ */

let editMode = false;
let currentTarget = null;
let selectedPixabayUrl = null;
let insertTarget = null;
let insertFromLocal = false;
let localFileData = null;
let insertTargetIsCard = false;

/* ── Cards de sugestão ── */
function setupSuggestionCards(){
  $$('.img-suggestion-card').forEach(card => {
    const query = card.dataset.query || '';
    const btnCopy = card.querySelector('.btn-card-copy');
    if(btnCopy){ btnCopy.addEventListener('click', e => { e.stopPropagation(); copySuggestion(query, btnCopy); }); }
    const btnInsert = card.querySelector('.btn-card-insert');
    if(btnInsert){ btnInsert.addEventListener('click', e => { e.stopPropagation(); openInsertFromCard(card, query); }); }
    card.addEventListener('click', () => { copySuggestion(query, btnCopy); openInsertFromCard(card, query); });
  });
}

function copySuggestion(query, btn){
  navigator.clipboard.writeText(query).then(() => {
    if(btn){ const orig = btn.textContent; btn.textContent = '✅ Copiado!'; btn.classList.add('copied'); setTimeout(() => { btn.textContent = orig; btn.classList.remove('copied'); }, 2200); }
    showToast(`📋 Sugestão copiada: "${query}"`, 'success', 3000);
  }).catch(() => { showToast('Cole manualmente: ' + query, 'info', 5000); });
}

function openInsertFromCard(card, query){
  insertTarget = card; insertTargetIsCard = true;
  selectedPixabayUrl = null;
  $('#insert-query').value = query;
  $('#insert-url-input').value = '';
  $('#insert-pxb-grid').innerHTML = '';
  $('#insert-pxb-status').textContent = '';
  $('#modal-insert').classList.add('open');
  setTimeout(() => searchInsertPixabay(true), 100);
}

/* ── Modo edição ── */
function toggleEditMode(){
  editMode = !editMode;
  document.body.classList.toggle('edit-mode', editMode);
  $('#btn-edit-mode').classList.toggle('active', editMode);
  $('#btn-edit-mode').textContent = editMode ? '✏️ Edição ON' : '✏️ Modo Edição';
  updateAllBadges();
}

function updateAllBadges(){
  $$('.img-status-badge').forEach(b => b.remove());
  if(!editMode) return;
  $$('.post-img-wrap img, .featured-cover > img').forEach(img => {
    const badge = document.createElement('span');
    badge.className = 'img-status-badge ' + (isGithubUrl(img.src) ? 'github' : 'external');
    badge.textContent = isGithubUrl(img.src) ? '✅ GitHub' : '⚠️ Externa';
    img.closest('.post-img-wrap, .featured-cover').appendChild(badge);
  });
}

function prepareImages(){
  $$('.post-img-wrap').forEach(wrap => {
    if(wrap.querySelector('.img-edit-overlay')) return;
    wrap.style.position = 'relative';
    wrap.appendChild(makeOverlay(false));
  });
  const cover = $('.featured-cover');
  if(cover && !cover.querySelector('.img-edit-overlay')){
    cover.style.position = 'relative';
    cover.appendChild(makeOverlay(true));
  }
}

function makeOverlay(isCover){
  const div = document.createElement('div');
  div.className = 'img-edit-overlay';
  div.innerHTML = `
    <button onclick="openImgModal(this,'url')">🔗 Colar URL</button>
    <button onclick="openImgModal(this,'pixabay')">🔍 Buscar Pixabay</button>
    <button class="upload-btn" onclick="uploadCurrentToGitHub(this)">☁️ Enviar pro GitHub</button>
    <button class="local-btn" onclick="openLocalUploadModal(this)">📁 Upload do PC → GitHub</button>
    <button class="download-btn" onclick="downloadCurrentImage(this)">⬇️ Download imagem</button>
    <button class="danger" onclick="removeImg(this)">🗑️ Remover</button>
  `;
  return div;
}

async function downloadCurrentImage(btn){
  const overlay = btn.closest('.img-edit-overlay');
  const wrap    = overlay.closest('.post-img-wrap, .featured-cover');
  const img     = wrap.querySelector('img:not(.img-edit-overlay img)');
  if(!img || !img.src){ showToast('Nenhuma imagem para baixar.', 'error'); return; }
  btn.textContent = '⏳ Preparando…'; btn.disabled = true;
  try {
    const resp = await fetch(img.src);
    if(!resp.ok) throw new Error('fetch falhou');
    const blob = await resp.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    const ext  = img.src.split('.').pop().split('?')[0] || 'jpg';
    a.href = url; a.download = `imagem-${Date.now()}.${ext}`;
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
    showToast('✅ Download iniciado!', 'success');
  } catch(e) {
    window.open(img.src, '_blank');
    showToast('⚠️ CORS bloqueou o download automático — imagem aberta em nova aba.', 'info', 6000);
  } finally { btn.textContent = '⬇️ Download imagem'; btn.disabled = false; }
}

async function uploadCurrentToGitHub(btn){
  const overlay = btn.closest('.img-edit-overlay');
  const wrap    = overlay.closest('.post-img-wrap, .featured-cover');
  const img     = wrap.querySelector('img:not(.img-edit-overlay img)');
  if(!img || !img.src){ showToast('Nenhuma imagem para enviar.', 'error'); return; }
  if(isGithubUrl(img.src)){ showToast('Esta imagem já está no GitHub! ✅', 'success'); return; }
  btn.textContent = '⏳ Enviando…'; btn.disabled = true;
  showToast('Buscando e enviando imagem…', 'info');
  try {
    let imageData;
    try {
      const resp = await fetch(img.src);
      if(!resp.ok) throw new Error('fetch falhou');
      imageData = await resp.arrayBuffer();
    } catch(e) {
      const canvas = document.createElement('canvas');
      const ctx2   = canvas.getContext('2d');
      canvas.width  = img.naturalWidth  || 1200;
      canvas.height = img.naturalHeight || 630;
      ctx2.drawImage(img, 0, 0);
      const dataUrl = canvas.toDataURL('image/webp', 0.85);
      const b64 = dataUrl.split(',')[1];
      imageData = Uint8Array.from(atob(b64), c => c.charCodeAt(0)).buffer;
    }
    const bytes = new Uint8Array(imageData);
    let binary = ''; bytes.forEach(b => binary += String.fromCharCode(b));
    const b64content = btoa(binary);
    const ts = Date.now();
    const filename = `img-editor-${ts}.webp`;
    const apiUrl = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${GITHUB_FOLDER}/${filename}`;
    const resp = await fetch(apiUrl, {
      method: 'PUT',
      headers: { 'Authorization': `token ${GITHUB_TOKEN}`, 'Accept': 'application/vnd.github.v3+json', 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: `editor: upload ${filename}`, content: b64content })
    });
    if(resp.status === 201 || resp.status === 200){
      const newUrl = `https://raw.githubusercontent.com/${GITHUB_OWNER}/${GITHUB_REPO}/main/${GITHUB_FOLDER}/${filename}`;
      img.src = newUrl; updateAllBadges();
      showToast('✅ Imagem salva no GitHub com sucesso!', 'success', 4000);
    } else {
      const err = await resp.json().catch(() => ({}));
      showToast(`❌ Erro GitHub: ${err.message || resp.status}`, 'error', 5000);
    }
  } catch(e) { showToast(`❌ Erro: ${e.message}`, 'error', 5000); }
  finally { btn.textContent = '☁️ Enviar pro GitHub'; btn.disabled = false; }
}

function openLocalUploadModal(btn){
  const overlay = btn.closest('.img-edit-overlay');
  const wrap    = overlay.closest('.post-img-wrap, .featured-cover');
  currentTarget = { wrap, img: wrap.querySelector('img:not(.img-edit-overlay img)'), isCover: wrap.classList.contains('featured-cover') };
  localFileData = null;
  $('#local-preview').style.display = 'none';
  $('#local-preview img').src = '';
  $('#local-preview-name').textContent = '';
  $('#btn-confirm-local').disabled = true;
  $('#modal-local').classList.add('open');
}

function openLocalUploadFromInsert(){
  localFileData = null; insertFromLocal = true;
  $('#local-preview').style.display = 'none';
  $('#local-preview img').src = ''; $('#local-preview-name').textContent = '';
  $('#btn-confirm-local').disabled = true;
  $('#modal-insert').classList.remove('open');
  $('#modal-local').classList.add('open');
}

function setupLocalInput(){
  const zone  = $('#local-upload-zone');
  const input = $('#local-file-input');
  zone.addEventListener('click', () => input.click());
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => { e.preventDefault(); zone.classList.remove('dragover'); const file = e.dataTransfer.files[0]; if(file) handleLocalFile(file); });
  input.addEventListener('change', () => { if(input.files[0]) handleLocalFile(input.files[0]); });
}

function handleLocalFile(file){
  if(!file.type.startsWith('image/')){ showToast('Selecione um arquivo de imagem válido.', 'error'); return; }
  const reader = new FileReader();
  reader.onload = e => {
    const previewUrl = e.target.result;
    const reader2 = new FileReader();
    reader2.onload = e2 => {
      localFileData = { arrayBuffer: e2.target.result, name: file.name };
      $('#local-preview').style.display = 'block';
      $('#local-preview img').src = previewUrl;
      $('#local-preview-name').textContent = `${file.name} (${(file.size/1024).toFixed(0)} KB)`;
      $('#btn-confirm-local').disabled = false;
    };
    reader2.readAsArrayBuffer(file);
  };
  reader.readAsDataURL(file);
}

async function confirmLocalUpload(){
  if(!localFileData){ showToast('Selecione uma imagem primeiro.', 'error'); return; }
  const btn = $('#btn-confirm-local');
  btn.textContent = '⏳ Enviando…'; btn.disabled = true;
  showToast('Enviando para o GitHub…', 'info');
  try {
    const bytes = new Uint8Array(localFileData.arrayBuffer);
    let binary = '';
    const CHUNK = 8192;
    for(let i = 0; i < bytes.length; i += CHUNK){ binary += String.fromCharCode(...bytes.subarray(i, i + CHUNK)); }
    const b64content = btoa(binary);
    const ts = Date.now(); const filename = `img-editor-${ts}.webp`;
    const apiUrl = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${GITHUB_FOLDER}/${filename}`;
    const ghResp = await fetch(apiUrl, {
      method: 'PUT',
      headers: { 'Authorization': `token ${GITHUB_TOKEN}`, 'Accept': 'application/vnd.github.v3+json', 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: `editor: upload ${filename}`, content: b64content })
    });
    if(ghResp.status === 201 || ghResp.status === 200){
      const newUrl = `https://raw.githubusercontent.com/${GITHUB_OWNER}/${GITHUB_REPO}/main/${GITHUB_FOLDER}/${filename}`;
      if(insertFromLocal){
        const refEl = (insertTargetIsCard && insertTarget) ? insertTarget : document.querySelector('#post-content > *:last-child');
        insertImageWrap(newUrl, refEl, insertTargetIsCard);
        insertFromLocal = false;
      } else if(currentTarget && currentTarget.img){ currentTarget.img.src = newUrl; }
      updateAllBadges();
      showToast('✅ Imagem salva no GitHub com sucesso!', 'success', 4000);
      $('#modal-local').classList.remove('open'); localFileData = null;
    } else {
      const err = await ghResp.json().catch(() => ({}));
      showToast(`❌ Erro GitHub: ${err.message || ghResp.status}`, 'error', 5000);
    }
  } catch(e) { showToast(`❌ Erro: ${e.message}`, 'error', 5000); }
  finally { btn.textContent = '☁️ Enviar pro GitHub'; btn.disabled = false; }
}

function openImgModal(btn, mode){
  const overlay = btn.closest('.img-edit-overlay');
  const wrap    = overlay.closest('.post-img-wrap, .featured-cover');
  currentTarget = { wrap, img: wrap.querySelector('img'), isCover: wrap.classList.contains('featured-cover') };
  selectedPixabayUrl = null;
  if(mode === 'url') showUrlModal(); else showPixabayModal();
}

function showUrlModal(){
  $('#url-input').value = currentTarget.img ? currentTarget.img.src : '';
  $('#modal-url').classList.add('open');
}
function applyUrlImage(){
  const url = $('#url-input').value.trim();
  if(!url){ alert('Cole uma URL válida.'); return; }
  applyImage(url); $('#modal-url').classList.remove('open'); updateAllBadges();
  if(!isGithubUrl(url)) showToast('⚠️ URL externa — use "Enviar pro GitHub" para fixá-la permanentemente.', 'info', 5000);
}
function copyUrlFromInput(){
  const url = $('#url-input').value.trim();
  if(!url){ showToast('Nenhuma URL para copiar.', 'error'); return; }
  navigator.clipboard.writeText(url).then(() => {
    const btn = $('#btn-copy-url'); btn.textContent = '✅ Copiada!'; btn.classList.add('copied');
    showToast('URL copiada!', 'success');
    setTimeout(() => { btn.textContent = '⎘ Copiar'; btn.classList.remove('copied'); }, 2500);
  }).catch(() => { $('#url-input').select(); showToast('Selecione e copie manualmente (Ctrl+C).', 'info'); });
}
async function pasteUrlFromClipboard(){
  const btn = $('#btn-paste-url');
  try {
    const text = await navigator.clipboard.readText();
    $('#url-input').value = text.trim();
    btn.textContent = '✅ Colado!'; btn.classList.add('pasted');
    setTimeout(() => { btn.textContent = '📋 Colar'; btn.classList.remove('pasted'); }, 2000);
  } catch(e) { $('#url-input').focus(); $('#url-input').select(); showToast('Clique no campo e use Ctrl+V para colar.', 'info', 4000); }
}
function clearUrlInput(){ $('#url-input').value = ''; $('#url-input').focus(); }

function showPixabayModal(){
  $('#pxb-query').value = ''; $('#pxb-grid').innerHTML = ''; $('#pxb-status').textContent = '';
  selectedPixabayUrl = null; $('#modal-pixabay').classList.add('open');
}
async function searchPixabay(){
  const q = $('#pxb-query').value.trim();
  if(!q){ alert('Digite o que buscar.'); return; }
  $('#pxb-status').textContent = 'Buscando…'; $('#pxb-grid').innerHTML = '';
  const url = `https://pixabay.com/api/?key=${PIXABAY_KEY}&q=${encodeURIComponent(q)}&image_type=photo&orientation=horizontal&safesearch=true&per_page=12&lang=pt`;
  try {
    const res = await fetch(url); const data = await res.json(); const hits = data.hits || [];
    if(!hits.length){ $('#pxb-status').textContent = 'Nenhuma imagem encontrada.'; return; }
    $('#pxb-status').textContent = `${hits.length} resultados — clique para selecionar`;
    hits.forEach(h => {
      const img = document.createElement('img');
      img.src = h.previewURL; img.title = h.tags; img.dataset.large = h.largeImageURL || h.webformatURL;
      img.onclick = () => { $$('#pxb-grid img').forEach(i => i.classList.remove('selected')); img.classList.add('selected'); selectedPixabayUrl = img.dataset.large; };
      $('#pxb-grid').appendChild(img);
    });
  } catch(e){ $('#pxb-status').textContent = 'Erro na busca: ' + e.message; }
}
function applyPixabayImage(){
  if(!selectedPixabayUrl){ alert('Selecione uma imagem.'); return; }
  applyImage(selectedPixabayUrl); $('#modal-pixabay').classList.remove('open'); updateAllBadges();
  showToast('⚠️ Imagem do Pixabay é temporária — clique em "Enviar pro GitHub" para fixá-la!', 'info', 6000);
}

function applyImage(src){
  if(!currentTarget) return;
  const {wrap, img, isCover} = currentTarget;
  if(img){ img.src = src; }
  else {
    const newImg = document.createElement('img');
    newImg.src = src; newImg.style.cssText = 'width:100%;height:auto;border-radius:8px;display:block;';
    if(isCover){ const textOverlay = wrap.querySelector('.featured-cover-overlay'); wrap.insertBefore(newImg, textOverlay); }
    else { wrap.insertBefore(newImg, wrap.firstChild); }
    currentTarget.img = newImg;
  }
}

function removeImg(btn){
  if(!confirm('Remover esta imagem do artigo?')) return;
  const overlay = btn.closest('.img-edit-overlay');
  const wrap    = overlay.closest('.post-img-wrap, .featured-cover');
  const img     = wrap.querySelector('img:not(.img-edit-overlay img)');
  if(img) img.remove();
}

function openInsertModal(btn){
  insertTarget = btn; insertTargetIsCard = false;
  selectedPixabayUrl = null; currentTarget = null;
  $('#insert-query').value = ''; $('#insert-url-input').value = '';
  $('#insert-pxb-grid').innerHTML = ''; $('#insert-pxb-status').textContent = '';
  $('#modal-insert').classList.add('open');
}

async function searchInsertPixabay(autoSearch){
  const q = $('#insert-query').value.trim();
  if(!q){ if(!autoSearch) alert('Digite o que buscar.'); return; }
  $('#insert-pxb-status').textContent = 'Buscando…'; $('#insert-pxb-grid').innerHTML = '';
  const url = `https://pixabay.com/api/?key=${PIXABAY_KEY}&q=${encodeURIComponent(q)}&image_type=photo&orientation=horizontal&safesearch=true&per_page=9&lang=pt`;
  try {
    const res = await fetch(url); const data = await res.json(); const hits = data.hits || [];
    if(!hits.length){ $('#insert-pxb-status').textContent = 'Nenhuma imagem.'; return; }
    $('#insert-pxb-status').textContent = `${hits.length} resultados — clique para selecionar`;
    hits.forEach(h => {
      const img = document.createElement('img');
      img.src = h.previewURL; img.dataset.large = h.largeImageURL || h.webformatURL;
      img.onclick = () => { $$('#insert-pxb-grid img').forEach(i => i.classList.remove('selected')); img.classList.add('selected'); selectedPixabayUrl = img.dataset.large; $('#insert-url-input').value = img.dataset.large; };
      $('#insert-pxb-grid').appendChild(img);
    });
  } catch(e){ $('#insert-pxb-status').textContent = 'Erro: ' + e.message; }
}

function insertImageWrap(url, refEl, replaceCard){
  const wrap = document.createElement('div');
  wrap.className = 'post-img-wrap'; wrap.style.position = 'relative';
  const img = document.createElement('img');
  img.src = url; img.style.cssText = 'width:100%;height:auto;border-radius:8px;display:block;box-shadow:0 2px 12px rgba(0,0,0,.08);';
  wrap.appendChild(img); wrap.appendChild(makeOverlay(false));
  if(replaceCard && refEl && refEl.classList.contains('img-suggestion-card')){
    refEl.classList.add('done'); refEl.after(wrap);
  } else {
    const btnAbove = makeInsertBtn(); const btnBelow = makeInsertBtn();
    refEl.after(wrap); wrap.before(btnAbove); wrap.after(btnBelow);
  }
}

function confirmInsertImage(){
  const url = $('#insert-url-input').value.trim() || selectedPixabayUrl;
  if(!url){ alert('Informe uma URL ou selecione uma imagem.'); return; }
  if(insertTargetIsCard && insertTarget){ insertImageWrap(url, insertTarget, true); }
  else { const refEl = insertTarget || document.querySelector('#post-content > *:last-child'); insertImageWrap(url, refEl, false); }
  $('#modal-insert').classList.remove('open');
  insertTarget = null; insertTargetIsCard = false; updateAllBadges();
  if(!isGithubUrl(url)) showToast('⚠️ Imagem inserida! Ative edição e clique em "Enviar pro GitHub".', 'info', 6000);
}

function makeInsertBtn(){
  const btn = document.createElement('button');
  btn.className = 'insert-img-btn'; btn.textContent = '+ Inserir imagem aqui';
  btn.onclick = () => openInsertModal(btn); return btn;
}

function injectInsertButtons(){
  const content = $('#post-content');
  [...content.children].forEach(child => {
    if(child.classList.contains('insert-img-btn')) return;
    if(child.classList.contains('img-suggestion-card')) return;
    const btn = makeInsertBtn(); child.after(btn);
  });
}

/* ── Apagar blocos ── */
let deleteMode = false; let deleteSelected = new Set();
function toggleDeleteMode(){
  deleteMode = !deleteMode;
  document.body.classList.toggle('delete-mode', deleteMode);
  const btn = $('#btn-delete-mode');
  btn.classList.toggle('active', deleteMode);
  btn.textContent = deleteMode ? '🗑️ Apagar ON' : '🗑️ Apagar Blocos';
  if(!deleteMode){ deleteSelected.forEach(el => el.classList.remove('selected-for-delete')); deleteSelected.clear(); updateDeleteBar(); return; }
  updateDeleteBar();
}
function setupDeleteClicks(){
  $('#post-content').addEventListener('click', function(e){
    if(!deleteMode) return;
    const el = e.target.closest('#post-content > *');
    if(!el) return; if(el.classList.contains('insert-img-btn')) return;
    e.stopPropagation(); e.preventDefault();
    if(deleteSelected.has(el)){ deleteSelected.delete(el); el.classList.remove('selected-for-delete'); }
    else { deleteSelected.add(el); el.classList.add('selected-for-delete'); }
    updateDeleteBar();
  }, true);
}
function updateDeleteBar(){
  const bar = $('#delete-mode-bar');
  $('#del-count').textContent = deleteSelected.size;
  bar.querySelector('.btn-del-confirm').disabled = deleteSelected.size === 0;
}
function confirmDeleteBlocks(){
  if(!deleteSelected.size) return;
  if(!confirm(`Apagar ${deleteSelected.size} bloco(s) selecionado(s)? Esta ação não pode ser desfeita.`)) return;
  deleteSelected.forEach(el => el.remove()); deleteSelected.clear(); updateDeleteBar();
  showToast(`✅ Bloco(s) apagado(s) com sucesso.`, 'success');
}
function cancelDeleteMode(){
  deleteMode = false; document.body.classList.remove('delete-mode');
  $('#btn-delete-mode').classList.remove('active'); $('#btn-delete-mode').textContent = '🗑️ Apagar Blocos';
  deleteSelected.forEach(el => el.classList.remove('selected-for-delete'));
  deleteSelected.clear(); updateDeleteBar();
}

/* ── Copy Rich Text ── */
function copyPostHTML(){
  var container = document.getElementById('post-content');
  var clone = container.cloneNode(true);
  ['.insert-img-btn','.img-edit-overlay','.img-status-badge','.img-suggestion-card:not(.done)','.img-suggestion-card.done'].forEach(sel => {
    clone.querySelectorAll(sel).forEach(el => el.remove());
  });
  /* Converte kw-links em links reais (mantém o href do portal ativo) */
  clone.querySelectorAll('a.kw-link').forEach(a => { /* já são <a> reais — manter */ });
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
  clone.querySelectorAll('.post-img-wrap, .featured-cover').forEach(el => { el.style.position = ''; });
  var blobHtml = new Blob([clone.innerHTML], {type:'text/html'});
  var blobText = new Blob([clone.innerText], {type:'text/plain'});
  navigator.clipboard.write([new ClipboardItem({'text/html':blobHtml,'text/plain':blobText})]).then(() => {
    var btn = document.getElementById('copyBtn');
    btn.innerText = '✅ Conteúdo Copiado (Cole no Visual)!'; btn.classList.add('copied');
    setTimeout(() => { btn.innerText = '📋 Copiar Rich Text (P/ WP)'; btn.classList.remove('copied'); }, 3000);
  }).catch(err => { alert('Bloqueado. Selecione o texto e dê Ctrl+C.'); });
}

/* ── Editar Texto ── */
let textEditMode = false;
function toggleTextEdit(){
  textEditMode = !textEditMode;
  document.body.classList.toggle('text-edit-mode', textEditMode);
  const btn = $('#btn-text-edit');
  btn.classList.toggle('active', textEditMode);
  btn.textContent = textEditMode ? '✍️ Texto ON' : '✍️ Editar Texto';
  $$('#post-content > *').forEach(el => {
    if(el.classList.contains('insert-img-btn') || el.classList.contains('post-img-wrap') ||
       el.classList.contains('featured-cover') || el.classList.contains('img-suggestion-card')) return;
    if(textEditMode){ el.setAttribute('contenteditable', 'true'); el.setAttribute('spellcheck', 'false'); }
    else { el.removeAttribute('contenteditable'); el.removeAttribute('spellcheck'); }
  });
  if(textEditMode) showToast('✍️ Modo texto ativo — edite direto na página. Desative antes de copiar.', 'info', 5000);
  else showToast('✅ Edição de texto desativada. Pronto para copiar!', 'success', 3000);
}

/* ── Back to top ── */
(function(){
  var btn = document.getElementById('backToTopBtn');
  window.addEventListener('scroll', () => btn.classList.toggle('visible', scrollY > 400));
  btn.addEventListener('click', () => window.scrollTo({top:0,behavior:'smooth'}));
})();

/* ── Init ── */
document.addEventListener('DOMContentLoaded', function(){
  prepareImages();
  injectInsertButtons();
  setupLocalInput();
  setupDeleteClicks();
  setupSuggestionCards();
  initPortalSelector();
});
</script>
"""

MODALS_HTML = """
<div id="modal-url" class="img-modal-backdrop">
  <div class="img-modal">
    <h3>🔗 Trocar imagem por URL</h3>
    <label>URL da imagem</label>
    <div class="url-input-row">
      <input type="text" id="url-input" placeholder="https://exemplo.com/imagem.jpg" />
      <button class="btn-paste-url" id="btn-paste-url" onclick="pasteUrlFromClipboard()" title="Colar URL do clipboard">📋 Colar</button>
      <button class="btn-clear-url" id="btn-clear-url" onclick="clearUrlInput()" title="Limpar campo">✕</button>
      <button class="btn-copy-url" id="btn-copy-url" onclick="copyUrlFromInput()" title="Copiar URL do campo">⎘ Copiar</button>
    </div>
    <div class="modal-actions">
      <button class="btn-primary" onclick="applyUrlImage()">Aplicar</button>
      <button class="btn-secondary" onclick="$('#modal-url').classList.remove('open')">Cancelar</button>
    </div>
  </div>
</div>

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

<div id="modal-insert" class="img-modal-backdrop">
  <div class="img-modal">
    <h3>➕ Inserir nova imagem</h3>
    <label>Buscar no Pixabay</label>
    <div style="display:flex;gap:.5rem;">
      <input type="text" id="insert-query" placeholder="ex: data science graph" style="flex:1;" onkeydown="if(event.key==='Enter') searchInsertPixabay(false)" />
      <button class="btn-primary" style="flex:0;padding:.6rem 1rem;" onclick="searchInsertPixabay(false)">Buscar</button>
    </div>
    <div class="pxb-grid" id="insert-pxb-grid"></div>
    <div class="pxb-status" id="insert-pxb-status"></div>
    <label style="margin-top:.8rem;">— ou cole uma URL diretamente —</label>
    <div style="margin-top:.8rem;">
      <button class="btn-local" style="width:100%;padding:.6rem;" onclick="openLocalUploadFromInsert()">📁 Upload do PC → GitHub</button>
    </div>
    <input type="text" id="insert-url-input" placeholder="https://exemplo.com/foto.jpg" />
    <div class="modal-actions">
      <button class="btn-primary" onclick="confirmInsertImage()">✅ Inserir</button>
      <button class="btn-secondary" onclick="$('#modal-insert').classList.remove('open')">Cancelar</button>
    </div>
  </div>
</div>

<div id="modal-local" class="img-modal-backdrop">
  <div class="img-modal">
    <h3>📁 Upload do PC → GitHub</h3>
    <p style="font-size:.82rem;color:#6b7280;margin-bottom:.5rem;">
      Selecione ou arraste uma imagem do seu computador. Ela será salva permanentemente no GitHub.
    </p>
    <input type="file" id="local-file-input" accept="image/*" style="display:none;" />
    <div class="local-upload-zone" id="local-upload-zone">
      <span class="icon">🖼️</span>
      <strong>Clique para selecionar</strong> ou arraste aqui<br>
      <small style="color:#9ca3af;">JPG, PNG, WebP, GIF — qualquer formato</small>
    </div>
    <div class="local-preview" id="local-preview">
      <img src="" alt="preview" />
      <div class="local-preview-name" id="local-preview-name"></div>
    </div>
    <div class="modal-actions" style="margin-top:1rem;">
      <button class="btn-local" id="btn-confirm-local" onclick="confirmLocalUpload()" disabled>☁️ Enviar pro GitHub</button>
      <button class="btn-secondary" onclick="$('#modal-local').classList.remove('open')">Cancelar</button>
    </div>
  </div>
</div>
"""


def build_editor_bar_html():
    """Gera o editor bar com o seletor de portais embutido."""
    portal_btns = ""
    for p in PORTALS:
        pid   = p["id"]
        pname = p["name"]
        plbl  = p["label"]
        pcol  = p["color"]
        portal_btns += (
            f'<button class="portal-btn" data-portal="{pid}" '
            f'style="background:{pcol};color:#fff;" '
            f'onclick="selectPortal(\'{pid}\')" '
            f'title="Ativar links para {pname}">'
            f'{plbl}'
            f'</button>\n        '
        )

    return f"""
<div id="editor-bar">
  <span class="label">🛠 EDITOR</span>
  <button id="btn-edit-mode" onclick="toggleEditMode()">✏️ Modo Edição</button>
  <div class="sep"></div>
  <button onclick="openInsertModal(document.querySelector('#post-content > *:last-child'))">➕ Inserir imagem</button>
  <div class="sep"></div>
  <button id="btn-delete-mode" onclick="toggleDeleteMode()">🗑️ Apagar Blocos</button>
  <div class="sep"></div>
  <button id="btn-text-edit" onclick="toggleTextEdit()">✍️ Editar Texto</button>
  <div class="sep"></div>
  <div class="portal-selector">
    <span class="ps-label">🔗 Links:</span>
    {portal_btns}
    <span id="link-count-badge"></span>
  </div>
</div>

<div class="delete-mode-bar" id="delete-mode-bar">
  <span>🗑️ Modo apagar — clique nos blocos para selecionar</span>
  <span class="del-count" id="del-count">0</span>
  <span>selecionado(s)</span>
  <button class="btn-del-confirm" onclick="confirmDeleteBlocks()" disabled>Apagar selecionados</button>
  <button class="btn-del-cancel" onclick="cancelDeleteMode()">Cancelar</button>
</div>

<div class="text-edit-hint">✍️ Clique em qualquer texto para editar — desative antes de copiar</div>
"""


TOAST_HTML = '<div id="toast"></div>'


def build_html(title, meta, body_html, pixabay_key):
    prism_css = '<link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet" />'
    prism_js = (
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>\n'
        '  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>\n'
        '  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-javascript.min.js"></script>'
    )
    content_with_title = f'<h1 class="main-article-title">{title}</h1>\n' + body_html

    portals_js  = build_portals_js()
    keywords_js = build_keywords_js()

    js_final = (JS_EDITOR
        .replace("PIXABAY_KEY_PLACEHOLDER",   pixabay_key)
        .replace("GITHUB_TOKEN_PLACEHOLDER",  GITHUB_TOKEN)
        .replace("GITHUB_OWNER_PLACEHOLDER",  GITHUB_OWNER)
        .replace("GITHUB_REPO_PLACEHOLDER",   GITHUB_REPO)
        .replace("GITHUB_FOLDER_PLACEHOLDER", GITHUB_FOLDER)
        .replace("PORTALS_DATA_PLACEHOLDER",  portals_js)
        .replace("KEYWORDS_DATA_PLACEHOLDER", keywords_js)
    )

    editor_bar = build_editor_bar_html()

    return (
        f"<!DOCTYPE html>\n<html lang='pt-BR'>\n<head>\n"
        f"  <meta charset='UTF-8'/>\n"
        f"  <meta name='viewport' content='width=device-width,initial-scale=1.0'/>\n"
        f"  <meta name='description' content='{meta}'/>\n"
        f"  <title>{title}</title>\n"
        f"  {prism_css}\n"
        f"  <style>{CSS}</style>\n"
        f"</head>\n<body>\n"
        f"  {TOAST_HTML}\n"
        f"  {editor_bar}\n"
        f"  <div id='post-content'>\n{content_with_title}\n  </div>\n\n"
        f"  {MODALS_HTML}\n"
        f"  <button id='copyBtn' class='floating-copy-btn' onclick='copyPostHTML()'>📋 Copiar Rich Text (P/ WP)</button>\n"
        f"  <button id='backToTopBtn' class='back-to-top' title='Voltar ao topo'>&#9650;</button>\n\n"
        f"  {prism_js}\n"
        f"  {js_final}\n"
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
#  CARD HTML DE SUGESTÃO DE IMAGEM
# ─────────────────────────────────────────────
def make_suggestion_card(query):
    safe_query = query.replace('"', '&quot;').replace("'", "&#39;")
    return (
        f'<div class="img-suggestion-card" data-query="{safe_query}">'
        f'  <div class="card-icon">🖼️</div>'
        f'  <div class="card-body">'
        f'    <div class="card-label">💡 Sugestão de imagem</div>'
        f'    <div class="card-query">{query}</div>'
        f'    <div class="card-hint">Clique para buscar e inserir uma imagem aqui</div>'
        f'  </div>'
        f'  <div class="card-actions">'
        f'    <button class="btn-card-copy">📋 Copiar</button>'
        f'    <button class="btn-card-insert">🔍 Inserir imagem</button>'
        f'  </div>'
        f'</div>'
    )


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

    # ── Capa ──
    cover_html  = ""
    cover_match = re.search(r"\[COVER:\s*(.+?)\s*\]", raw, re.IGNORECASE)
    if cover_match:
        query = cover_match.group(1)
        print(f"\n  [CAPA] sugestão: '{query}'")
        safe_query = query.replace('"', '&quot;').replace("'", "&#39;")
        cover_html = (
            f'<div class="img-suggestion-card" data-query="{safe_query}" '
            f'style="border-radius:12px;margin:0 0 2.5rem;background:linear-gradient(135deg,#1e1e2e 0%,#374151 100%);border-color:#4b5563;">'
            f'  <div class="card-icon" style="background:rgba(255,255,255,.1);">🏞️</div>'
            f'  <div class="card-body">'
            f'    <div class="card-label" style="color:#a5b4fc;">💡 Sugestão — Imagem de CAPA</div>'
            f'    <div class="card-query" style="color:#f9fafb;">{query}</div>'
            f'    <div class="card-hint" style="color:#9ca3af;">Clique para buscar e inserir a imagem de capa</div>'
            f'  </div>'
            f'  <div class="card-actions">'
            f'    <button class="btn-card-copy">📋 Copiar</button>'
            f'    <button class="btn-card-insert">🔍 Inserir imagem</button>'
            f'  </div>'
            f'</div>\n'
        )
        raw = re.sub(r"\[COVER:\s*" + re.escape(query) + r"\s*\]", "", raw, flags=re.IGNORECASE)

    # ── Imagens do corpo ──
    image_placeholders = {}

    def replace_pixabay(m):
        query = m.group(1).strip()
        print(f"  [IMG] sugestão: '{query}'")
        key = f"IMGPLACEHOLDER{len(image_placeholders)}"
        image_placeholders[key] = make_suggestion_card(query)
        return f"\n\n{key}\n\n"

    raw = re.sub(r"\[PIXABAY:\s*(.+?)\s*\]", replace_pixabay, raw, flags=re.IGNORECASE)

    body_html = markdown.markdown(raw, extensions=["tables", "fenced_code", "sane_lists"])

    for key, card_html in image_placeholders.items():
        body_html = body_html.replace(f"<p>{key}</p>", card_html)
        body_html = body_html.replace(key, card_html)

    final_html = build_html(title, meta, cover_html + body_html, PIXABAY_KEY)
    html_path  = f"{slug}.html"
    with open(html_path, "w", encoding="utf-8", errors="replace") as f:
        f.write(final_html)

    print(f"  HTML gerado: {html_path}")


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
