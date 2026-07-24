# -*- coding: utf-8 -*-
import base64
import io
import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import requests

# ===================== CONFIGURAÇÕES =====================
PIXABAY_KEY   = " - "
GITHUB_TOKEN  = " "
GITHUB_OWNER  = "cursoarteatuarial"
GITHUB_REPO   = "blogs"
GITHUB_FOLDER = "blog"

IMG_WIDTH, IMG_HEIGHT       = 1200, 630   # post
COVER_WIDTH, COVER_HEIGHT   = 1600, 900   # capa
IMG_QUALITY   = 82
SEARCH_LANG   = "pt"
# =========================================================

# Garante que a pasta de logos exista
if not os.path.exists("logos"):
    os.makedirs("logos")

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
    
    resample_filter = getattr(Image, 'Resampling', Image).LANCZOS
    img = img.resize((new_w, new_h), resample_filter)
    
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))

def aplicar_assinatura(imagem_base: Image.Image, caminho_logo: str, alinhamento: str = "centro") -> Image.Image:
    try:
        if not os.path.exists(caminho_logo):
            return imagem_base.convert("RGB")

        imagem_base = imagem_base.convert("RGBA")
        logo = Image.open(caminho_logo).convert("RGBA")
        
        nova_largura = imagem_base.width
        proporcao = nova_largura / float(logo.width)
        nova_altura = int(float(logo.height) * float(proporcao))
        
        resample_filter = getattr(Image, 'Resampling', Image).LANCZOS
        logo_ajustada = logo.resize((nova_largura, nova_altura), resample_filter)
        
        if alinhamento == "topo":
            pos_y = 0
        elif alinhamento == "base":
            pos_y = imagem_base.height - nova_altura
        else: # centro
            pos_y = (imagem_base.height - nova_altura) // 2
        
        imagem_base.paste(logo_ajustada, (0, pos_y), logo_ajustada)
        return imagem_base.convert("RGB")
    except Exception as e:
        print(f"Erro ao aplicar logo: {e}")
        return imagem_base.convert("RGB")

def aplicar_titulo(imagem_base: Image.Image, titulo: str, logo_file: str = "none") -> Image.Image:
    if not titulo:
        return imagem_base
        
    try:
        imagem_base = imagem_base.convert("RGBA")
        
        # Tenta carregar uma fonte legal do sistema, senão usa a padrão
        tamanho_fonte = max(30, int(imagem_base.height * 0.06))
        try:
            fonte = ImageFont.truetype("arial.ttf", tamanho_fonte)
        except IOError:
            fonte = ImageFont.load_default()
            
        # Define a ordem de busca do background
        caminhos_bg = []
        if logo_file and logo_file != "none":
            nome_logo = os.path.splitext(logo_file)[0] # Ex: tira o .png de sg.png -> vira sg
            caminhos_bg.append(os.path.join("logos", f"background_{nome_logo}.png"))
        
        caminhos_bg.append(os.path.join("logos", "background.png")) # Genérico como fallback secundário
        
        bg_aplicado = False
        
        for bg_path in caminhos_bg:
            if os.path.exists(bg_path):
                bg = Image.open(bg_path).convert("RGBA")
                nova_largura_bg = imagem_base.width
                proporcao_bg = nova_largura_bg / float(bg.width)
                nova_altura_bg = int(float(bg.height) * float(proporcao_bg))
                
                resample = getattr(Image, 'Resampling', Image).LANCZOS
                bg_ajustado = bg.resize((nova_largura_bg, nova_altura_bg), resample)
                
                pos_y_bg = imagem_base.height - nova_altura_bg
                imagem_base.paste(bg_ajustado, (0, pos_y_bg), bg_ajustado)
                bg_aplicado = True
                break # Se achou e aplicou, para a busca
                
        if not bg_aplicado:
            # Fallback elegante: cria um gradiente/fundo escuro se os arquivos não existirem
            overlay = Image.new("RGBA", imagem_base.size, (0,0,0,0))
            draw = ImageDraw.Draw(overlay)
            altura_tarja = tamanho_fonte * 3
            draw.rectangle([(0, imagem_base.height - altura_tarja), (imagem_base.width, imagem_base.height)], fill=(0,0,0, 160))
            imagem_base = Image.alpha_composite(imagem_base, overlay)

        # Escreve o texto à esquerda, na base da imagem
        draw = ImageDraw.Draw(imagem_base)
        margem_x = int(imagem_base.width * 0.05)
        margem_y = imagem_base.height - tamanho_fonte - int(tamanho_fonte * 0.8)
        
        # Efeito de sombra leve para garantir leitura
        draw.text((margem_x + 2, margem_y + 2), titulo, font=fonte, fill=(0,0,0,200))
        draw.text((margem_x, margem_y), titulo, font=fonte, fill=(255,255,255,255))
        
        return imagem_base.convert("RGB")
    except Exception as e:
        print(f"Erro ao aplicar título: {e}")
        return imagem_base.convert("RGB")

def to_webp_bytes(img: Image.Image, target_w: int, target_h: int, keep_original: bool = False, logo_file: str = "none", alinhamento: str = "centro", titulo: str = "") -> bytes:
    img = img.convert("RGB")
    
    if not keep_original:
        img = cover_crop(img, target_w, target_h)
        
    if titulo:
        img = aplicar_titulo(img, titulo, logo_file)
        
    if logo_file != "none":
        caminho_logo = os.path.join("logos", logo_file)
        img = aplicar_assinatura(img, caminho_logo, alinhamento)
    
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
        self.title("Gerenciador de Imagens - GitHub & Assinaturas")
        
        self.geometry("1300x1000")
        self.minsize(900, 700)
        
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
            
        fonte_padrao = ("Segoe UI", 11)
        self.option_add("*Font", fonte_padrao)
        style.configure(".", font=fonte_padrao)
        
        self.current_image = None      
        self.thumb_refs = []           
        self.preview_ref = None

        self.main_container = ttk.Frame(self, padding=20)
        self.main_container.pack(fill="both", expand=True)

        self._build_top_section()
        self._build_results_area()
        self._build_preview_and_upload()

    def _build_top_section(self):
        top_frame = ttk.LabelFrame(self.main_container, text=" 1. Escolher Imagem ", padding=15)
        top_frame.pack(fill="x", pady=(0, 15))

        row1 = ttk.Frame(top_frame)
        row1.pack(fill="x", pady=5)
        ttk.Label(row1, text="🔍 Pixabay:", width=15).pack(side="left")
        self.search_entry = ttk.Entry(row1)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.search_pixabay())
        ttk.Button(row1, text="Buscar", command=self.search_pixabay, width=15).pack(side="left")

        row2 = ttk.Frame(top_frame)
        row2.pack(fill="x", pady=5)
        ttk.Label(row2, text="🔗 URL Direta:", width=15).pack(side="left")
        self.url_entry = ttk.Entry(row2)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        ttk.Button(row2, text="📋 Colar e Carregar", command=self.paste_and_load_url).pack(side="left", padx=(0,5))
        ttk.Button(row2, text="Carregar", command=lambda: self.load_from_url(self.url_entry.get().strip()), width=10).pack(side="left", padx=(0,5))
        ttk.Button(row2, text="🧹 Limpar Tudo", command=self.limpar_tudo).pack(side="left")

        row3 = ttk.Frame(top_frame)
        row3.pack(fill="x", pady=5)
        ttk.Label(row3, text="📁 Arquivo Local:", width=15).pack(side="left")
        ttk.Button(row3, text="Procurar no Computador...", command=self.load_from_pc).pack(side="left", padx=5)

    def paste_and_load_url(self):
        try:
            texto_copiado = self.clipboard_get().strip()
            if texto_copiado:
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, texto_copiado)
                self.load_from_url(texto_copiado)
        except tk.TclError:
            messagebox.showwarning("Colar", "Nenhum texto na área de transferência.")

    def search_pixabay(self):
        query = self.search_entry.get().strip()
        if not query: return
        
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

    def _build_results_area(self):
        wrapper = ttk.Frame(self.main_container)
        wrapper.pack(fill="x", pady=(0, 15))
        
        canvas = tk.Canvas(wrapper, height=200, highlightthickness=0, bg="#f0f0f0")
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
                
            self.thumb_refs.append(tk_thumb)
            btn = tk.Button(self.results_inner, image=tk_thumb, cursor="hand2", relief="flat", bg="#f0f0f0",
                            command=lambda url=hit["largeImageURL"]: self.load_from_url(url))
            btn.grid(row=i // cols, column=i % cols, padx=5, pady=5)

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
            path = filedialog.askopenfilename(
                parent=self,
                title="Escolher imagem",
                filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.webp;*.gif"), ("Todos os arquivos", "*.*")]
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro no seletor: {e}")
            return
            
        if not path: return
            
        try:
            self.current_image = Image.open(path)
            self.current_image.load()
            self._update_preview()
            
            nome_arquivo = os.path.basename(path)
            self.status_label.config(text=f"Arquivo selecionado: {nome_arquivo}", foreground="green")
        except Exception as e:
            messagebox.showerror("Imagem", f"Não consegui abrir o arquivo: {e}")

    def _build_preview_and_upload(self):
        bottom_frame = ttk.Frame(self.main_container)
        bottom_frame.pack(fill="both", expand=True)

        preview_frame = ttk.LabelFrame(bottom_frame, text=" Preview da Imagem ", padding=10)
        preview_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.preview_label = ttk.Label(preview_frame, text="Nenhuma imagem selecionada", anchor="center")
        self.preview_label.pack(fill="both", expand=True)

        upload_frame = ttk.LabelFrame(bottom_frame, text=" 2. Configurações e Envio ", padding=15)
        upload_frame.pack(side="right", fill="y")

        ttk.Label(upload_frame, text="Slug do artigo:").pack(anchor="w", pady=(0, 5))
        self.slug_entry = ttk.Entry(upload_frame)
        self.slug_entry.pack(fill="x", pady=(0, 10))

        ttk.Label(upload_frame, text="Assinatura / Logo:").pack(anchor="w", pady=(5, 5))
        self.logo_var = tk.StringVar(value="none")
        
        logo_frame = ttk.Frame(upload_frame)
        logo_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Radiobutton(logo_frame, text="Nenhuma", variable=self.logo_var, value="none", command=self._update_preview).grid(row=0, column=0, sticky="w", padx=(0,10), pady=2)
        ttk.Radiobutton(logo_frame, text="IA BIO", variable=self.logo_var, value="iabio.png", command=self._update_preview).grid(row=0, column=1, sticky="w", padx=(0,10), pady=2)
        ttk.Radiobutton(logo_frame, text="TraineAI", variable=self.logo_var, value="traineai.png", command=self._update_preview).grid(row=0, column=2, sticky="w", pady=2)

        ttk.Radiobutton(logo_frame, text="IA PRO", variable=self.logo_var, value="iapro.png", command=self._update_preview).grid(row=1, column=0, sticky="w", padx=(0,10), pady=2)
        ttk.Radiobutton(logo_frame, text="Maiquel", variable=self.logo_var, value="maiquel.png", command=self._update_preview).grid(row=1, column=1, sticky="w", padx=(0,10), pady=2)
        ttk.Radiobutton(logo_frame, text="SG", variable=self.logo_var, value="sg.png", command=self._update_preview).grid(row=1, column=2, sticky="w", pady=2)

        self.align_var = tk.StringVar(value="centro")
        align_frame = ttk.Frame(upload_frame)
        align_frame.pack(fill="x", pady=(0, 15))
        ttk.Label(align_frame, text="Alinhamento:").pack(side="left", padx=(0, 5))
        ttk.Radiobutton(align_frame, text="Topo", variable=self.align_var, value="topo", command=self._update_preview).pack(side="left", padx=(0,5))
        ttk.Radiobutton(align_frame, text="Centro", variable=self.align_var, value="centro", command=self._update_preview).pack(side="left", padx=(0,5))
        ttk.Radiobutton(align_frame, text="Base", variable=self.align_var, value="base", command=self._update_preview).pack(side="left")

        ttk.Label(upload_frame, text="Mini Título (opcional):").pack(anchor="w", pady=(5, 2))
        self.title_entry = ttk.Entry(upload_frame)
        self.title_entry.pack(fill="x", pady=(0, 10))
        self.title_entry.bind("<FocusOut>", lambda e: self._update_preview())
        self.title_entry.bind("<Return>", lambda e: self._update_preview())

        ttk.Label(upload_frame, text="Formato de recorte:").pack(anchor="w", pady=(5, 5))
        self.size_var = tk.StringVar(value="post")
        
        rb_frame = ttk.Frame(upload_frame)
        rb_frame.pack(fill="x", pady=(0, 15))
        ttk.Radiobutton(rb_frame, text=f"Post ({IMG_WIDTH}x{IMG_HEIGHT})", variable=self.size_var, value="post", command=self._update_preview).pack(anchor="w")
        ttk.Radiobutton(rb_frame, text=f"Capa ({COVER_WIDTH}x{COVER_HEIGHT})", variable=self.size_var, value="cover", command=self._update_preview).pack(anchor="w")
        ttk.Radiobutton(rb_frame, text="Original (Sem cortes)", variable=self.size_var, value="original", command=self._update_preview).pack(anchor="w", pady=(5, 0))

        btn_frame = ttk.Frame(upload_frame)
        btn_frame.pack(fill="x", pady=(5, 10))

        style = ttk.Style()
        style.configure("Hero.TButton", font=("Segoe UI", 10, "bold"), padding=8)
        
        self.btn_upload = ttk.Button(btn_frame, text="☁️ Enviar para o GitHub", style="Hero.TButton", command=self.send_to_github)
        self.btn_upload.pack(fill="x", pady=(0, 5))

        ttk.Label(upload_frame, text="Link Final (Raw):").pack(anchor="w", pady=(0, 5))
        link_frame = ttk.Frame(upload_frame)
        link_frame.pack(fill="x")
        
        self.link_entry = ttk.Entry(link_frame)
        self.link_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(link_frame, text="📋 Copiar", command=self.copy_link, width=8).pack(side="right")

        self.status_label = ttk.Label(upload_frame, text="Aguardando...", font=("Segoe UI", 9, "italic"), foreground="gray")
        self.status_label.pack(side="bottom", anchor="w", pady=5)

    def _update_preview(self):
        if self.current_image is None: 
            return
            
        preview_img = self.current_image.copy()
        
        size_choice = self.size_var.get()
        logo_choice = self.logo_var.get()
        align_choice = self.align_var.get()
        titulo_texto = self.title_entry.get().strip()
        
        if size_choice != "original":
            target_w, target_h = (COVER_WIDTH, COVER_HEIGHT) if size_choice == "cover" else (IMG_WIDTH, IMG_HEIGHT)
            preview_img = cover_crop(preview_img, target_w, target_h)
            
        if titulo_texto:
            preview_img = aplicar_titulo(preview_img, titulo_texto, logo_choice)
            
        if logo_choice != "none":
            caminho_logo = os.path.join("logos", logo_choice)
            if os.path.exists(caminho_logo):
                preview_img = aplicar_assinatura(preview_img, caminho_logo, align_choice)

        preview_img.thumbnail((600, 400))
        self.preview_ref = ImageTk.PhotoImage(preview_img)
        self.preview_label.config(image=self.preview_ref, text="")

    def copy_link(self):
        link = self.link_entry.get().strip()
        if not link: return
        self.clipboard_clear()
        self.clipboard_append(link)
        self.status_label.config(text="📋 Link copiado!", foreground="green")

    def limpar_tudo(self):
        self.current_image = None
        self.preview_ref = None
        self.preview_label.config(image="", text="Nenhuma imagem selecionada")
        
        self.search_entry.delete(0, tk.END)
        self.url_entry.delete(0, tk.END)
        self.slug_entry.delete(0, tk.END)
        self.link_entry.delete(0, tk.END)
        self.title_entry.delete(0, tk.END)
        
        self.size_var.set("post")
        self.logo_var.set("none")
        self.align_var.set("centro")
        
        for w in self.results_inner.winfo_children():
            w.destroy()
        self.thumb_refs.clear()
        ttk.Label(self.results_inner, text="Resultados limpos.").grid(row=0, column=0, padx=10, pady=10)
        
        self.status_label.config(text="App limpo. Aguardando nova imagem...", foreground="gray")

    def send_to_github(self):
        if self.current_image is None:
            messagebox.showwarning("Atenção", "Selecione uma imagem primeiro.")
            return
            
        if not GITHUB_TOKEN.strip():
            messagebox.showerror("Erro", "Você esqueceu de preencher o GITHUB_TOKEN no código.")
            return
            
        size_choice = self.size_var.get()
        logo_choice = self.logo_var.get()
        align_choice = self.align_var.get()
        titulo_texto = self.title_entry.get().strip()
        keep_original = (size_choice == "original")
        
        if logo_choice != "none":
            caminho_logo = os.path.join("logos", logo_choice)
            if not os.path.exists(caminho_logo):
                messagebox.showerror("Erro", f"A logo não foi encontrada na pasta:\n{caminho_logo}\n\nPor favor, salve a imagem com este nome exato dentro da pasta 'logos'.")
                return

        target_w, target_h = (COVER_WIDTH, COVER_HEIGHT) if size_choice == "cover" else (IMG_WIDTH, IMG_HEIGHT)
        slug = self.slug_entry.get().strip()
        
        self.btn_upload.config(state="disabled")
        self.status_label.config(text="Processando e enviando...", foreground="orange")
        self.update()
        
        try:
            webp_bytes = to_webp_bytes(
                self.current_image, 
                target_w, 
                target_h, 
                keep_original=keep_original,
                logo_file=logo_choice,
                alinhamento=align_choice,
                titulo=titulo_texto
            )
            
            link = upload_to_github(webp_bytes, slug)
            
            self.link_entry.delete(0, "end")
            self.link_entry.insert(0, link)
            
            self.clipboard_clear()
            self.clipboard_append(link)
            self.status_label.config(text="✅ Enviado e copiado!", foreground="green")
            
        except Exception as e:
            self.status_label.config(text=f"❌ Erro ao enviar.", foreground="red")
            messagebox.showerror("Erro no Upload", str(e))
        finally:
            self.btn_upload.config(state="normal")

if __name__ == "__main__":
    App().mainloop()
