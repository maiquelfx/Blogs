# -*- coding: utf-8 -*-
import base64
import io
import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import requests

# ===================== CONFIGURAÇÕES =====================
PIXABAY_KEY   = "-"
GITHUB_TOKEN  = " "
GITHUB_OWNER  = "cursoarteatuarial"
GITHUB_REPO   = "blogs"
GITHUB_FOLDER = "blog"

IMG_WIDTH, IMG_HEIGHT       = 1200, 630   # post
COVER_WIDTH, COVER_HEIGHT   = 1600, 900   # capa
IMG_QUALITY   = 82
SEARCH_LANG   = "pt"
# =========================================================

def cover_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    img = img.convert("RGB")
    src_ratio = img.width / img.height
    tgt_ratio = target_w / target_h
    if src_ratio > tgt_ratio:
        new_h = target_h
        new_w = int(new_h * src_ratio)
    else:
        new_w = target_w
        new_h = int(new_w / src_ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))

def to_webp_bytes(img: Image.Image, target_w: int, target_h: int, keep_original: bool = False) -> bytes:
    img = img.convert("RGB") # Garante compatibilidade de cores pro formato WEBP
    if not keep_original:
        img = cover_crop(img, target_w, target_h)
    
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=IMG_QUALITY)
    return buf.getvalue()

def upload_to_github(webp_bytes: bytes, slug: str) -> str:
    ts = time.strftime("%Y%m%d-%H%M")
    filename = f"{slug or 'img'}-{ts}.webp"
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{GITHUB_FOLDER}/{filename}"
    content_b64 = base64.b64encode(webp_bytes).decode()
    resp = requests.put(url, headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }, json={"message": f"upload via app: {filename}", "content": content_b64})
    
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"GitHub {resp.status_code}: {resp.json().get('message', resp.text)}")
    return f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main/{GITHUB_FOLDER}/{filename}"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Upload de Imagens - GitHub")
        self.geometry("1200x950")
        self.minsize(800, 600)
        
        # Ativa o visual moderno do sistema operacional
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
            
        fonte_padrao = ("Segoe UI", 11)  # Se achar pequeno, mude o 11 para 12
        self.option_add("*Font", fonte_padrao)
        style.configure(".", font=fonte_padrao)
        
        self.current_image = None      
        self.thumb_refs = []           
        self.preview_ref = None

        # Container Principal
        self.main_container = ttk.Frame(self, padding=20)
        self.main_container.pack(fill="both", expand=True)

        self._build_top_section()
        self._build_results_area()
        self._build_preview_and_upload()

    # ---------- SEÇÃO 1: BUSCA E ARQUIVOS ----------
    def _build_top_section(self):
        top_frame = ttk.LabelFrame(self.main_container, text=" 1. Escolher Imagem ", padding=15)
        top_frame.pack(fill="x", pady=(0, 15))

        # Linha Pixabay
        row1 = ttk.Frame(top_frame)
        row1.pack(fill="x", pady=5)
        ttk.Label(row1, text="🔍 Pixabay:", width=15).pack(side="left")
        self.search_entry = ttk.Entry(row1)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.search_pixabay())
        ttk.Button(row1, text="Buscar", command=self.search_pixabay, width=15).pack(side="left")

        # Linha URL
        row2 = ttk.Frame(top_frame)
        row2.pack(fill="x", pady=5)
        ttk.Label(row2, text="🔗 URL Direta:", width=15).pack(side="left")
        self.url_entry = ttk.Entry(row2)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(row2, text="Carregar", command=lambda: self.load_from_url(self.url_entry.get().strip()), width=15).pack(side="left")

        # Linha PC
        row3 = ttk.Frame(top_frame)
        row3.pack(fill="x", pady=5)
        ttk.Label(row3, text="📁 Arquivo Local:", width=15).pack(side="left")
        ttk.Button(row3, text="Procurar no Computador...", command=self.load_from_pc).pack(side="left", padx=5)

    def search_pixabay(self):
        query = self.search_entry.get().strip()
        if not query:
            return
        
        self.status_label.config(text="Buscando no Pixabay...", foreground="blue")
        self.update()
        
        try:
            resp = requests.get("https://pixabay.com/api/", params={
                "key": PIXABAY_KEY, "q": query, "image_type": "photo",
                "orientation": "horizontal", "safesearch": "true",
                "per_page": 10, "lang": SEARCH_LANG,
            }, timeout=15)
            resp.raise_for_status()
            hits = resp.json().get("hits", [])
            self._render_results(hits)
            self.status_label.config(text=f"{len(hits)} resultados encontrados.", foreground="green")
        except Exception as e:
            messagebox.showerror("Pixabay", f"Falha na busca: {e}")
            self.status_label.config(text="Erro na busca.", foreground="red")

    # ---------- SEÇÃO 2: RESULTADOS PIXABAY ----------
    def _build_results_area(self):
        # Frame com scroll para os resultados do Pixabay
        wrapper = ttk.Frame(self.main_container)
        wrapper.pack(fill="x", pady=(0, 15))
        
        canvas = tk.Canvas(wrapper, height=280, highlightthickness=0, bg="#f0f0f0")
        scroll = ttk.Scrollbar(wrapper, orient="vertical", command=canvas.yview)
        
        self.results_inner = ttk.Frame(canvas)
        self.results_inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=self.results_inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        
        canvas.pack(side="left", fill="x", expand=True)
        scroll.pack(side="right", fill="y")

    def _render_results(self, hits):
        for w in self.results_inner.winfo_children():
            w.destroy()
        
        self.thumb_refs.clear()
        
        if not hits:
            ttk.Label(self.results_inner, text="Nenhuma imagem encontrada.").grid(row=0, column=0, padx=10, pady=10)
            return
            
        cols = 5
        for i, hit in enumerate(hits):
            try:
                thumb_resp = requests.get(hit["previewURL"], timeout=10)
                pil_thumb = Image.open(io.BytesIO(thumb_resp.content))
                pil_thumb.thumbnail((140, 140))
                tk_thumb = ImageTk.PhotoImage(pil_thumb)
            except Exception:
                continue
                
            self.thumb_refs.append(tk_thumb) # Salva a referência na memória
            
            btn = tk.Button(self.results_inner, image=tk_thumb, cursor="hand2", relief="flat", bg="#f0f0f0",
                            command=lambda url=hit["largeImageURL"]: self.load_from_url(url))
            btn.grid(row=i // cols, column=i % cols, padx=5, pady=5)

    # ---------- FUNÇÕES DE CARREGAMENTO ----------
    def load_from_url(self, url):
        if not url: return
        self.status_label.config(text="Baixando imagem...", foreground="blue")
        self.update()
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            self.current_image = Image.open(io.BytesIO(resp.content))
            self._update_preview()
            self.status_label.config(text="Imagem selecionada com sucesso.", foreground="green")
        except Exception as e:
            messagebox.showerror("Imagem", f"Não consegui carregar essa URL: {e}")
            self.status_label.config(text="Erro ao carregar URL.", foreground="red")

    def load_from_pc(self):
        try:
            # CORREÇÃO 1: Adicionado parent=self para o Spyder não se perder
            # CORREÇÃO 2: Trocado os espaços por ; nos filetypes (padrão do Windows)
            path = filedialog.askopenfilename(
                parent=self,
                title="Escolher imagem",
                filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.webp;*.gif"), ("Todos os arquivos", "*.*")]
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro no seletor: {e}")
            return
            
        if not path:
            return
            
        try:
            self.current_image = Image.open(path)
            self.current_image.load()
            self._update_preview()
            
            nome_arquivo = os.path.basename(path)
            self.status_label.config(text=f"Arquivo selecionado: {nome_arquivo}", foreground="green")
        except Exception as e:
            messagebox.showerror("Imagem", f"Não consegui abrir o arquivo: {e}")

    # ---------- SEÇÃO 3: PREVIEW E UPLOAD ----------
    def _build_preview_and_upload(self):
        bottom_frame = ttk.Frame(self.main_container)
        bottom_frame.pack(fill="both", expand=True)

        # Esquerda: Preview
        preview_frame = ttk.LabelFrame(bottom_frame, text=" Preview da Imagem ", padding=10)
        preview_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.preview_label = ttk.Label(preview_frame, text="Nenhuma imagem selecionada", anchor="center")
        self.preview_label.pack(fill="both", expand=True)

        # Direita: Configurações de Upload
        upload_frame = ttk.LabelFrame(bottom_frame, text=" 2. Configurar e Enviar ", padding=15)
        upload_frame.pack(side="right", fill="y")

        ttk.Label(upload_frame, text="Slug do artigo:").pack(anchor="w", pady=(0, 5))
        self.slug_entry = ttk.Entry(upload_frame)
        self.slug_entry.pack(fill="x", pady=(0, 15))

        ttk.Label(upload_frame, text="Formato de recorte:").pack(anchor="w", pady=(0, 5))
        self.size_var = tk.StringVar(value="post")
        
        rb_frame = ttk.Frame(upload_frame)
        rb_frame.pack(fill="x", pady=(0, 20))
        ttk.Radiobutton(rb_frame, text=f"Post ({IMG_WIDTH}x{IMG_HEIGHT})", variable=self.size_var, value="post").pack(anchor="w")
        ttk.Radiobutton(rb_frame, text=f"Capa ({COVER_WIDTH}x{COVER_HEIGHT})", variable=self.size_var, value="cover").pack(anchor="w")
        ttk.Radiobutton(rb_frame, text="Original (Sem cortes)", variable=self.size_var, value="original").pack(anchor="w", pady=(5, 0))

        # Botão Hero
        style = ttk.Style()
        style.configure("Hero.TButton", font=("Segoe UI", 10, "bold"), padding=8)
        
        self.btn_upload = ttk.Button(upload_frame, text="☁️ Enviar para o GitHub", style="Hero.TButton", command=self.send_to_github)
        self.btn_upload.pack(fill="x", pady=(0, 20))

        ttk.Label(upload_frame, text="Link Final (Raw):").pack(anchor="w", pady=(0, 5))
        link_frame = ttk.Frame(upload_frame)
        link_frame.pack(fill="x")
        
        self.link_entry = ttk.Entry(link_frame)
        self.link_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(link_frame, text="📋 Copiar", command=self.copy_link, width=8).pack(side="right")

        self.status_label = ttk.Label(upload_frame, text="Aguardando...", font=("Segoe UI", 9, "italic"), foreground="gray")
        self.status_label.pack(side="bottom", anchor="w", pady=10)

    def _update_preview(self):
        if self.current_image is None:
            return
            
        thumb = self.current_image.copy()
        thumb.thumbnail((450, 300))
        self.preview_ref = ImageTk.PhotoImage(thumb) # Salva a referência ativamente!
        self.preview_label.config(image=self.preview_ref, text="")

    def copy_link(self):
        link = self.link_entry.get().strip()
        if not link: return
        self.clipboard_clear()
        self.clipboard_append(link)
        self.status_label.config(text="📋 Link copiado!", foreground="green")

    def send_to_github(self):
        if self.current_image is None:
            messagebox.showwarning("Atenção", "Selecione uma imagem primeiro.")
            return
            
        if not GITHUB_TOKEN.strip():
            messagebox.showerror("Erro de Auth", "Você esqueceu de preencher o GITHUB_TOKEN no código.")
            return
            
        # --- TRECHO ATUALIZADO DENTRO DO send_to_github ---
        size_choice = self.size_var.get()
        keep_original = (size_choice == "original")
        
        target_w, target_h = (COVER_WIDTH, COVER_HEIGHT) if size_choice == "cover" else (IMG_WIDTH, IMG_HEIGHT)
        slug = self.slug_entry.get().strip()
        
        self.btn_upload.config(state="disabled")
        self.status_label.config(text="Processando e enviando para o GitHub...", foreground="orange")
        self.update()
        
        try:
            # Passamos a nova flag keep_original
            webp_bytes = to_webp_bytes(self.current_image, target_w, target_h, keep_original=keep_original)
            link = upload_to_github(webp_bytes, slug)
            
            self.link_entry.delete(0, "end")
            self.link_entry.insert(0, link)
            
            self.clipboard_clear()
            self.clipboard_append(link)
            self.status_label.config(text="✅ Enviado! Copiado para a área de transferência.", foreground="green")
        except Exception as e:
            self.status_label.config(text=f"❌ Erro ao enviar.", foreground="red")
            messagebox.showerror("Erro no Upload", str(e))
        finally:
            self.btn_upload.config(state="normal")

if __name__ == "__main__":
    App().mainloop()
