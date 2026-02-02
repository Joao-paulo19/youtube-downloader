import os
import sys
import re
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
import logging
from pathlib import Path
import time
from datetime import datetime, timedelta
import json
import requests
from queue import Queue
import random


class ProxyManager:
    """Gerenciador de proxies gratuitos com validação HTTPS"""

    def __init__(self):
        self.proxies = []
        self.proxy_queue = Queue()
        self.is_fetching = False
        self.blacklist = []

    def fetch_proxies_async(self, callback=None):
        """Busca proxies em segundo plano (threading)"""
        if self.is_fetching:
            return

        def worker():
            self.is_fetching = True
            try:
                proxies = self._fetch_from_sources()
                self.proxies = proxies
                for proxy in proxies:
                    self.proxy_queue.put(proxy)
                if callback:
                    callback(len(proxies))
            except Exception as e:
                print(f"Erro ao buscar proxies: {e}")
            finally:
                self.is_fetching = False

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def _fetch_from_sources(self):
        """Busca proxies de fontes públicas"""
        proxies = []

        try:
            # Fonte 1: ProxyScrape
            url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                proxy_list = response.text.strip().split('\n')
                proxies.extend(
                    [f"http://{p.strip()}" for p in proxy_list if p.strip()])
        except Exception as e:
            print(f"Erro ao buscar de ProxyScrape: {e}")

        try:
            # Fonte 2: Free-Proxy-List (backup)
            url = "https://www.proxy-list.download/api/v1/get?type=http"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                proxy_list = response.text.strip().split('\n')
                proxies.extend(
                    [f"http://{p.strip()}" for p in proxy_list if p.strip()])
        except Exception as e:
            print(f"Erro ao buscar de Proxy-List: {e}")

        # Remover duplicatas e limitar quantidade
        proxies = list(set(proxies))[:50]  # Máximo de 50 proxies
        random.shuffle(proxies)

        return proxies

    def get_next_proxy(self):
        """Retorna o próximo proxy da fila"""
        try:
            if not self.proxy_queue.empty():
                return self.proxy_queue.get_nowait()
            elif self.proxies:
                return random.choice(self.proxies)
        except Exception:
            pass
        return None

    def validate_proxy(self, proxy):
        """Valida o proxy e registra o tempo de resposta"""
        try:
            inicio = time.time()
            response = requests.get(
                "https://www.google.com",
                proxies={"http": proxy, "https": proxy},
                timeout=5
            )
            fim = time.time()
            tempo_resposta = fim - inicio

            if response.status_code == 200:
                print(f"Proxy {proxy} OK - Resposta: {tempo_resposta:.2f}s")
                return True
            return False
        except Exception:
            self.blacklist.append(proxy)  # Marca como ruim
            return False


class PoTokenGenerator:
    """Gerador de Proof of Token usando deno.exe"""

    def __init__(self, deno_path):
        self.deno_path = deno_path
        self.visitor_data = None
        self.po_token = None

    def generate_tokens(self):
        """Gera visitor_data e po_token usando deno"""
        try:
            # Script TypeScript para geração de PoToken
            script_content = """
// Importar biblioteca bgutils-js
import { BG } from "https://esm.sh/bgutils-js@1.5.1";

async function generatePoToken() {
  try {
    const requestKey = "O43z0dpjhgX20SCx4KAo";
    const visitorData = BG.generateVisitorData(requestKey);
    const poToken = await BG.generatePoToken(visitorData);
    
    console.log(JSON.stringify({
      visitor_data: visitorData,
      po_token: poToken
    }));
  } catch (error) {
    console.error(JSON.stringify({ error: error.message }));
  }
}

generatePoToken();
"""

            # Criar arquivo temporário com o script
            script_path = os.path.join(os.path.dirname(
                self.deno_path), "generate_token.ts")
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)

            # Executar deno
            comando = [
                self.deno_path,
                "run",
                "--allow-net",
                "--allow-read",
                script_path
            ]

            processo = subprocess.Popen(
                comando,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            stdout, stderr = processo.communicate(timeout=30)

            # Limpar arquivo temporário
            try:
                os.remove(script_path)
            except:
                pass

            # Parsear resultado
            if processo.returncode == 0 and stdout:
                try:
                    result = json.loads(stdout.strip())
                    if 'visitor_data' in result and 'po_token' in result:
                        self.visitor_data = result['visitor_data']
                        self.po_token = result['po_token']
                        return True
                except json.JSONDecodeError:
                    pass

            return False

        except Exception as e:
            print(f"Erro ao gerar PoToken: {e}")
            return False


class BrowserCookieManager:
    """Gerenciador de cookies de navegadores"""

    @staticmethod
    def detect_browsers():
        """Detecta navegadores instalados no sistema"""
        browsers = []

        if os.name == 'nt':  # Windows
            # Chrome
            chrome_path = os.path.expandvars(
                r"%LOCALAPPDATA%\Google\Chrome\User Data")
            if os.path.exists(chrome_path):
                browsers.append("chrome")

            # Edge
            edge_path = os.path.expandvars(
                r"%LOCALAPPDATA%\Microsoft\Edge\User Data")
            if os.path.exists(edge_path):
                browsers.append("edge")

            # Firefox
            firefox_path = os.path.expandvars(r"%APPDATA%\Mozilla\Firefox")
            if os.path.exists(firefox_path):
                browsers.append("firefox")

            # Brave
            brave_path = os.path.expandvars(
                r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data")
            if os.path.exists(brave_path):
                browsers.append("brave")
        else:  # Linux/Mac
            home = os.path.expanduser("~")

            # Chrome
            chrome_paths = [
                f"{home}/.config/google-chrome",
                f"{home}/Library/Application Support/Google/Chrome"
            ]
            if any(os.path.exists(p) for p in chrome_paths):
                browsers.append("chrome")

            # Firefox
            firefox_paths = [
                f"{home}/.mozilla/firefox",
                f"{home}/Library/Application Support/Firefox"
            ]
            if any(os.path.exists(p) for p in firefox_paths):
                browsers.append("firefox")

            # Brave
            brave_paths = [
                f"{home}/.config/BraveSoftware/Brave-Browser",
                f"{home}/Library/Application Support/BraveSoftware/Brave-Browser"
            ]
            if any(os.path.exists(p) for p in brave_paths):
                browsers.append("brave")

        return browsers


class YouTubeDownloader:
    def __init__(self, root):
        # Configuração principal da janela
        self.root = root
        self.root.title("YouTube Downloader")

        # Dimensões otimizadas para notebooks
        largura = 620
        altura = 680

        # Cálculo para centralização automática
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (largura // 2)
        y = (screen_height // 2) - (altura // 2)

        # Aplica a geometria centralizada
        self.root.geometry(f"{largura}x{altura}+{x}+{y}")

        # Variáveis para Limites e Timeouts
        self.limite_velocidade_var = tk.StringVar(value="7M")
        self.intervalo_requisicoes_var = tk.StringVar(value="1.5")
        self.socket_timeout_var = tk.StringVar(value="60")

        # Variáveis de formato
        self.formato_video_var = tk.StringVar(value="mp4")  # Padrão mp4
        self.formato_audio_var = tk.StringVar(value="mp3")  # Padrão mp3

        self.root.configure(bg="#f0f0f0")
        self.root.resizable(True, True)

        # Variáveis
        self.url_var = tk.StringVar()
        self.pasta_destino_var = tk.StringVar()
        self.qualidade_video_var = tk.StringVar()
        self.qualidade_audio_var = tk.StringVar()
        self.formato_audio_var = tk.StringVar(value="mp3")
        self.modo_download_var = tk.StringVar(value="video")
        self.modo_emulacao_var = tk.StringVar(value="padrão")

        # NOVO: Variáveis para camadas de contingência
        self.usar_potoken_var = tk.BooleanVar(value=False)
        self.usar_proxy_var = tk.BooleanVar(value=False)
        self.navegador_cookies_var = tk.StringVar(value="Nenhum")

        self.processo_ativo = None
        self.cancelar_download = False

        # NOVO: Inicializar gerenciadores
        self.proxy_manager = ProxyManager()
        self.potoken_generator = None
        self.tentativas_proxy = 0
        self.max_tentativas_proxy = 5

        # Qualidades
        self.qualidades_video_padrao = [
            "2160p (4K)", "1440p (2K)", "1080p (Full HD)",
            "720p (HD)", "480p (SD)", "360p", "240p", "144p"
        ]

        self.qualidades_audio_padrao = [
            "320kbps", "256kbps", "192kbps", "128kbps", "96kbps"
        ]

        self.mapeamento_qualidade_video = {
            "2160p (4K)": "bestvideo[height<=2160]+bestaudio[ext=m4a]/bestvideo[height<=2160]+bestaudio/best",
            "1440p (2K)": "bestvideo[height<=1440]+bestaudio[ext=m4a]/bestvideo[height<=1440]+bestaudio/best",
            "1080p (Full HD)": "bestvideo[height<=1080]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best",
            "720p (HD)": "bestvideo[height<=720]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best",
            "480p (SD)": "bestvideo[height<=480]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best",
            "360p": "bestvideo[height<=360]+bestaudio[ext=m4a]/bestvideo[height<=360]+bestaudio/best",
            "240p": "bestvideo[height<=240]+bestaudio[ext=m4a]/bestvideo[height<=240]+bestaudio/best",
            "144p": "bestvideo[height<=144]+bestaudio[ext=m4a]/bestvideo[height<=144]+bestaudio/best"
        }

        self.mapeamento_qualidade_audio = {
            "320kbps": "bestaudio/best",
            "256kbps": "bestaudio/best",
            "192kbps": "bestaudio/best",
            "128kbps": "bestaudio/best",
            "96kbps": "bestaudio/best"
        }

        self.qualidade_video_var.set(self.qualidades_video_padrao[2])
        self.qualidade_audio_var.set(self.qualidades_audio_padrao[0])

        # Verificar dependências
        if not self.verificar_dependencias():
            messagebox.showerror(
                "Erro", "Dependências necessárias não encontradas (yt-dlp.exe, ffmpeg.exe ou deno.exe)")
            return

        # NOVO: Iniciar busca de proxies em segundo plano
        self.proxy_manager.fetch_proxies_async(self.on_proxies_loaded)

        # Criar a interface
        self.criar_interface()

    def on_proxies_loaded(self, count):
        """Callback quando proxies são carregados"""
        try:
            self.root.after(0, lambda: self.status_proxy_label.config(
                text=f"✓ {count} proxies disponíveis"))
        except:
            pass

    def recurso_caminho(self, relativo):
        """Detecta o caminho de recursos dentro do .exe"""
        try:
            if hasattr(sys, '_MEIPASS'):
                caminho = os.path.join(sys._MEIPASS, relativo)
            else:
                caminho = os.path.join(os.path.abspath("."), relativo)

            if os.path.exists(caminho):
                return caminho
            else:
                import shutil
                return shutil.which(relativo.replace('.exe', ''))
        except Exception as e:
            return None

    def verificar_dependencias(self):
        """Verifica se as dependências necessárias estão disponíveis"""
        try:
            yt_dlp_path = self.recurso_caminho("yt-dlp.exe")
            ffmpeg_path = self.recurso_caminho("ffmpeg.exe")
            deno_path = self.recurso_caminho("deno.exe")

            if not yt_dlp_path or not ffmpeg_path:
                return False

            # NOVO: Inicializar gerador de PoToken se deno estiver disponível
            if deno_path:
                self.potoken_generator = PoTokenGenerator(deno_path)

            return True
        except Exception as e:
            return False

    def validar_url(self, url):
        """Valida se a URL é do YouTube"""
        padroes_youtube = [
            r'youtube\.com/watch\?v=',
            r'youtube\.com/playlist\?list=',
            r'youtu\.be/',
            r'youtube\.com/channel/',
            r'youtube\.com/user/',
            r'youtube\.com/live/'
        ]

        for padrao in padroes_youtube:
            if re.search(padrao, url, re.IGNORECASE):
                return True
        return False

    def criar_interface(self):
        """Cria a interface gráfica do aplicativo com suporte a rolagem"""
        try:
            estilo = ttk.Style()
            estilo.configure("TButton", font=("Segoe UI", 10))
            estilo.configure("TLabel", font=(
                "Segoe UI", 10), background="#f0f0f0")
            estilo.configure("Header.TLabel", font=(
                "Segoe UI", 12, "bold"), background="#f0f0f0")
            estilo.configure("TFrame", background="#f0f0f0")
            estilo.configure("TRadiobutton", background="#f0f0f0")
            estilo.configure("TCheckbutton", background="#f0f0f0")

            # 1. Criar o Container Principal para a Barra de Rolagem
            container = ttk.Frame(self.root)
            container.pack(fill=tk.BOTH, expand=True)

            # 2. Criar o Canvas e a Scrollbar
            self.canvas = tk.Canvas(
                container, bg="#f0f0f0", highlightthickness=0)
            self.scrollbar = ttk.Scrollbar(
                container, orient="vertical", command=self.canvas.yview)

            # 3. Criar o Frame que conterá o conteúdo (este substitui o antigo main_frame)
            self.scrollable_frame = ttk.Frame(self.canvas, padding=20)

            # Configurar o Canvas para redimensionar o conteúdo
            self.scrollable_frame.bind(
                "<Configure>",
                lambda e: self.canvas.configure(
                    scrollregion=self.canvas.bbox("all"))
            )

            # Criar a janela dentro do canvas para o frame rolável
            self.canvas_window = self.canvas.create_window(
                (0, 0), window=self.scrollable_frame, anchor="nw")

            # Ajustar largura do frame rolável para acompanhar o canvas
            def _configure_canvas(event):
                if self.scrollable_frame.winfo_reqwidth() != event.width:
                    self.canvas.itemconfigure(
                        self.canvas_window, width=event.width)
            self.canvas.bind('<Configure>', _configure_canvas)

            self.canvas.configure(yscrollcommand=self.scrollbar.set)

            # Posicionar Canvas e Scrollbar
            self.canvas.pack(side="left", fill="both", expand=True)
            self.scrollbar.pack(side="right", fill="y")

            # Suporte para a rodinha do mouse
            def _on_mousewheel(event):
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

            # Redefinimos a variável main_frame para apontar para o novo frame rolável
            # Isso evita erros nas linhas de código abaixo
            main_frame = self.scrollable_frame

            # --- Daqui em diante, o código segue a lógica original montada no main_frame ---

            # Título
            titulo_label = ttk.Label(main_frame, text="YouTube Downloader",
                                     style="Header.TLabel", font=("Segoe UI", 16, "bold"))
            titulo_label.pack(pady=(0, 20))

            # Frame para URL
            url_frame = ttk.Frame(main_frame)
            url_frame.pack(fill=tk.X, pady=5)

            ttk.Label(url_frame, text="URL do YouTube:").pack(
                side=tk.LEFT, padx=(0, 10))
            self.entry_url = ttk.Entry(
                url_frame, textvariable=self.url_var, width=50)
            self.entry_url.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Seletor de modo de emulação
            emulacao_frame = ttk.Frame(main_frame)
            emulacao_frame.pack(fill=tk.X, pady=10)

            ttk.Label(emulacao_frame, text="Modo de Emulação:").pack(
                side=tk.LEFT, padx=(0, 10))
            modos_emulacao = ["padrão", "android_vr",
                              "ios", "android", "web_safari"]
            self.combo_emulacao = ttk.Combobox(emulacao_frame, textvariable=self.modo_emulacao_var,
                                               values=modos_emulacao, width=15, state="readonly")
            self.combo_emulacao.pack(side=tk.LEFT)
            self.combo_emulacao.current(0)

            # Configurações de contingência
            contingencia_frame = ttk.LabelFrame(
                main_frame, text="⚡ Camadas de Contingência", padding=10)
            contingencia_frame.pack(fill=tk.X, pady=10)

            # Camada 1: PoToken
            potoken_frame = ttk.Frame(contingencia_frame)
            potoken_frame.pack(fill=tk.X, pady=2)
            self.check_potoken = ttk.Checkbutton(
                potoken_frame, text="🔒 Camada 1: PoToken (Anonimato)", variable=self.usar_potoken_var)
            self.check_potoken.pack(side=tk.LEFT)

            if not self.potoken_generator:
                self.check_potoken.config(state=tk.DISABLED)
                ttk.Label(potoken_frame, text="⚠ deno.exe não encontrado", foreground="red", font=(
                    "Segoe UI", 8)).pack(side=tk.LEFT, padx=10)

            # Camada 2: Proxies
            proxy_frame = ttk.Frame(contingencia_frame)
            proxy_frame.pack(fill=tk.X, pady=2)
            self.check_proxy = ttk.Checkbutton(
                proxy_frame, text="🌐 Camada 2: Rotação de Proxies (Evasão)", variable=self.usar_proxy_var)
            self.check_proxy.pack(side=tk.LEFT)
            self.status_proxy_label = ttk.Label(
                proxy_frame, text="⏳ Carregando proxies...", font=("Segoe UI", 8), foreground="gray")
            self.status_proxy_label.pack(side=tk.LEFT, padx=10)

            # Camada 3: Browser Cookies
            browser_frame = ttk.Frame(contingencia_frame)
            browser_frame.pack(fill=tk.X, pady=2)
            ttk.Label(browser_frame, text="🔑 Camada 3: Cookies do Navegador:").pack(
                side=tk.LEFT, padx=(0, 10))
            browsers = BrowserCookieManager.detect_browsers()
            if browsers:
                self.combo_browser = ttk.Combobox(browser_frame, textvariable=self.navegador_cookies_var, values=[
                                                  "Nenhum"] + browsers, width=15, state="readonly")
                self.combo_browser.pack(side=tk.LEFT)
                self.combo_browser.current(0)
            else:
                ttk.Label(browser_frame, text="⚠ Nenhum navegador detectado",
                          foreground="red", font=("Segoe UI", 8)).pack(side=tk.LEFT)

            # Frame de Ajustes de Rede
            rede_frame = ttk.LabelFrame(
                main_frame, text="⚙️ Ajustes de Rede (Avançado)", padding=10)
            rede_frame.pack(fill=tk.X, pady=10)

            # Linha 1: Limite e Intervalo
            linha1_rede = ttk.Frame(rede_frame)
            linha1_rede.pack(fill=tk.X, pady=2)

            ttk.Label(linha1_rede, text="Limite (ex: 7M):").pack(
                side=tk.LEFT, padx=5)
            ttk.Entry(linha1_rede, textvariable=self.limite_velocidade_var, width=8).pack(
                side=tk.LEFT, padx=5)

            ttk.Label(linha1_rede, text="Intervalo (s):").pack(
                side=tk.LEFT, padx=5)
            ttk.Entry(linha1_rede, textvariable=self.intervalo_requisicoes_var, width=8).pack(
                side=tk.LEFT, padx=5)

            # Linha 2: Timeout
            linha2_rede = ttk.Frame(rede_frame)
            linha2_rede.pack(fill=tk.X, pady=2)

            ttk.Label(linha2_rede, text="Timeout (s):").pack(
                side=tk.LEFT, padx=5)
            ttk.Entry(linha2_rede, textvariable=self.socket_timeout_var,
                      width=8).pack(side=tk.LEFT, padx=5)

            # Modo de download
            modo_frame = ttk.Frame(main_frame)
            modo_frame.pack(fill=tk.X, pady=10)
            ttk.Label(modo_frame, text="Modo de download:").pack(
                side=tk.LEFT, padx=(0, 10))
            ttk.Radiobutton(modo_frame, text="Vídeo", variable=self.modo_download_var,
                            value="video", command=self.alternar_modo).pack(side=tk.LEFT, padx=10)
            ttk.Radiobutton(modo_frame, text="Áudio", variable=self.modo_download_var,
                            value="audio", command=self.alternar_modo).pack(side=tk.LEFT, padx=10)

            # Notebook
            self.notebook = ttk.Notebook(main_frame)
            self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
            self.aba_video = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(self.aba_video, text="Download de Vídeo")
            self.aba_audio = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(self.aba_audio, text="Download de Áudio")

            self.configurar_aba_video()
            self.configurar_aba_audio()

            # Pasta de destino
            pasta_frame = ttk.Frame(main_frame)
            pasta_frame.pack(fill=tk.X, pady=10)
            ttk.Label(pasta_frame, text="Pasta de destino:").pack(
                side=tk.LEFT, padx=(0, 10))
            ttk.Entry(pasta_frame, textvariable=self.pasta_destino_var,
                      width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Button(pasta_frame, text="Escolher...", command=self.escolher_pasta).pack(
                side=tk.LEFT, padx=(10, 0))

            # Progresso
            progresso_frame = ttk.Frame(main_frame)
            progresso_frame.pack(fill=tk.X, pady=10)
            self.progresso_label = ttk.Label(progresso_frame, text="Pronto")
            self.progresso_label.pack(fill=tk.X)
            self.barra_progresso = ttk.Progressbar(
                progresso_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
            self.barra_progresso.pack(fill=tk.X, pady=5)

            # Botões de Ação
            botao_frame = ttk.Frame(main_frame)
            botao_frame.pack(fill=tk.X, pady=10)
            self.botao_cancelar = ttk.Button(
                botao_frame, text="Cancelar", command=self.cancelar_operacao, width=20, state=tk.DISABLED)
            self.botao_cancelar.pack(side=tk.RIGHT, padx=(10, 0))
            self.botao_download = ttk.Button(
                botao_frame, text="Baixar", command=self.iniciar_download, width=20)
            self.botao_download.pack(side=tk.RIGHT)

            self.alternar_modo()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao criar interface: {e}")

    def configurar_aba_video(self):
        """Configura os widgets da aba de vídeo"""
        try:
            qualidade_frame = ttk.Frame(self.aba_video)
            qualidade_frame.pack(fill=tk.X, pady=10)

            ttk.Label(qualidade_frame, text="Qualidade:").pack(
                side=tk.LEFT, padx=(0, 5))
            self.combo_qualidade_video = ttk.Combobox(
                qualidade_frame, textvariable=self.qualidade_video_var,
                values=self.qualidades_video_padrao, width=20, state="readonly"
            )
            self.combo_qualidade_video.pack(side=tk.LEFT, padx=5)

            # NOVO: Seletor de Formato de Vídeo
            ttk.Label(qualidade_frame, text="Formato:").pack(
                side=tk.LEFT, padx=(10, 5))
            formatos_video = ["mp4", "mkv", "mov", "avi", "wmv", "webm"]
            self.combo_formato_video = ttk.Combobox(
                qualidade_frame, textvariable=self.formato_video_var,
                values=formatos_video, width=8, state="readonly"
            )
            self.combo_formato_video.pack(side=tk.LEFT, padx=5)
            # Fim do novo seletor

            info_frame = ttk.Frame(self.aba_video)
            info_frame.pack(fill=tk.X, pady=10)
            ttk.Label(info_frame, text="Selecione a resolução e o formato. O sistema converterá automaticamente se necessário.",
                      wraplength=500, justify=tk.LEFT).pack(fill=tk.X)
        except Exception as e:
            messagebox.showerror(
                "Erro", f"Erro ao configurar aba de vídeo: {e}")

    def configurar_aba_audio(self):
        """Configura os widgets da aba de áudio"""
        try:
            qualidade_frame = ttk.Frame(self.aba_audio)
            qualidade_frame.pack(fill=tk.X, pady=10)

            ttk.Label(qualidade_frame, text="Qualidade do áudio:").pack(
                side=tk.LEFT, padx=(0, 10))
            self.combo_qualidade_audio = ttk.Combobox(
                qualidade_frame,
                textvariable=self.qualidade_audio_var,
                values=self.qualidades_audio_padrao,
                width=25,
                state="readonly"
            )
            self.combo_qualidade_audio.pack(side=tk.LEFT)
            self.combo_qualidade_audio.current(0)

            formato_frame = ttk.Frame(self.aba_audio)
            formato_frame.pack(fill=tk.X, pady=10)

            ttk.Label(formato_frame, text="Formato de saída:").pack(
                side=tk.LEFT, padx=(0, 10))
            formatos = ["mp3", "m4a", "wav", "opus", "flac"]
            self.combo_formato_audio = ttk.Combobox(
                formato_frame,
                textvariable=self.formato_audio_var,
                values=formatos,
                width=10,
                state="readonly"
            )
            self.combo_formato_audio.pack(side=tk.LEFT)
            self.combo_formato_audio.current(0)

            info_frame = ttk.Frame(self.aba_audio)
            info_frame.pack(fill=tk.X, pady=10)

            info_text = ("Este modo extrai apenas o áudio do vídeo YouTube.\n"
                         "O áudio será salvo no formato escolhido.")

            ttk.Label(info_frame, text=info_text, wraplength=500,
                      justify=tk.LEFT).pack(fill=tk.X)
        except Exception as e:
            messagebox.showerror(
                "Erro", f"Erro ao configurar aba de áudio: {e}")

    def alternar_modo(self):
        """Alterna entre o modo de download de vídeo e áudio"""
        try:
            modo = self.modo_download_var.get()

            for i in range(self.notebook.index("end")):
                self.notebook.forget(0)

            if modo == "video":
                self.notebook.add(self.aba_video, text="Download de Vídeo")
                self.notebook.select(self.aba_video)
            else:
                self.notebook.add(self.aba_audio, text="Download de Áudio")
                self.notebook.select(self.aba_audio)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao alternar modo: {e}")

    def escolher_pasta(self):
        """Abre diálogo para escolher pasta de destino"""
        try:
            pasta = filedialog.askdirectory(
                initialdir=self.pasta_destino_var.get())
            if pasta:
                self.pasta_destino_var.set(pasta)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao selecionar pasta: {e}")

    def cancelar_operacao(self):
        """Cancela o download em andamento"""
        self.cancelar_download = True
        if self.processo_ativo:
            try:
                self.processo_ativo.terminate()
            except:
                pass

    def iniciar_download(self):
        """Inicia o processo de download em uma thread separada"""
        try:
            url = self.url_var.get().strip()
            pasta_destino = self.pasta_destino_var.get()

            if not url:
                messagebox.showwarning("Aviso", "Por favor, insira uma URL")
                return

            if not self.validar_url(url):
                messagebox.showwarning(
                    "Aviso", "URL inválida. Use uma URL do YouTube")
                return

            if not pasta_destino:
                messagebox.showwarning(
                    "Aviso", "Por favor, escolha uma pasta de destino")
                return

            self.botao_download.config(state=tk.DISABLED)
            self.barra_progresso.config(value=0)
            self.progresso_label.config(text="Iniciando download...")

            # Resetar contador de tentativas
            self.tentativas_proxy = 0

            thread = threading.Thread(
                target=self.executar_download_com_contingencias, daemon=True)
            thread.start()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao iniciar download: {e}")
            self.botao_download.config(state=tk.NORMAL)

    def executar_download_com_contingencias(self):
        """Executa download direto e aciona camadas apenas se solicitado e necessário"""
        try:
            self.cancelar_download = False
            self.root.after(
                0, lambda: self.botao_cancelar.config(state=tk.NORMAL))

            # --- PASSO 0: TENTATIVA DIRETA (SEM NADA) ---
            self.root.after(0, lambda: self.progresso_label.config(
                text="🚀 Tentando download direto..."))
            resultado = self.executar_download(
                use_potoken=False, proxy=None, browser_cookies=None)

            if resultado['sucesso']:
                self.finalizar_download(resultado)
                return

            # Se falhou e NÃO for erro de Bot (ex: erro de URL ou rede), encerra aqui
            if not self.is_bot_error(resultado.get('erro', '')):
                self.finalizar_download(resultado)
                return

            # --- SE DEU ERRO DE BOT, TESTAR AS CAMADAS MARCADAS PELO USUÁRIO ---

            # CAMADA 1: PoToken (Só se o Checkbox estiver ativo)
            if self.usar_potoken_var.get() and self.potoken_generator:
                self.root.after(0, lambda: self.progresso_label.config(
                    text="🔒 Camada 1: Usando PoToken..."))
                if self.potoken_generator.generate_tokens():
                    resultado = self.executar_download(
                        use_potoken=True, proxy=None, browser_cookies=None)
                    if resultado['sucesso']:
                        self.finalizar_download(resultado)
                        return

            # CAMADA 2: Proxy (Só se o Checkbox estiver ativo)
            if self.usar_proxy_var.get():
                self.tentativas_proxy = 0  # Resetar contador antes de começar
                while self.tentativas_proxy < self.max_tentativas_proxy:
                    proxy = self.proxy_manager.get_next_proxy()
                    if not proxy:
                        break

                    self.tentativas_proxy += 1
                    self.root.after(0, lambda t=self.tentativas_proxy: self.progresso_label.config(
                        text=f"🌐 Camada 2: Proxy ({t}/{self.max_tentativas_proxy})..."))

                    resultado = self.executar_download(
                        use_potoken=False, proxy=proxy, browser_cookies=None)
                    if resultado['sucesso']:
                        self.finalizar_download(resultado)
                        return
                    # Se der um erro que não é bot durante o uso do proxy, cancela essa camada
                    if not self.is_bot_error(resultado.get('erro', '')):
                        break
                    time.sleep(1)

            # CAMADA 3: Cookies (Só se um navegador estiver selecionado no menu)
            navegador = self.navegador_cookies_var.get()
            if navegador and navegador != "Nenhum":
                self.root.after(0, lambda: self.progresso_label.config(
                    text=f"🔑 Camada 3: Usando cookies do {navegador}..."))
                resultado = self.executar_download(
                    use_potoken=False, proxy=None, browser_cookies=navegador)
                if resultado['sucesso']:
                    self.finalizar_download(resultado)
                    return

            # Se chegou aqui, o direto falhou e as camadas ativas também falharam
            self.finalizar_download(resultado)

        except Exception as e:
            self.root.after(0, lambda: self.progresso_label.config(
                text="❌ Erro crítico no processo"))
            self.root.after(0, lambda: messagebox.showerror(
                "Erro Fatal", f"Ocorreu um erro: {str(e)}"))
        finally:
            self.root.after(
                0, lambda: self.botao_download.config(state=tk.NORMAL))
            self.root.after(
                0, lambda: self.botao_cancelar.config(state=tk.DISABLED))
            if hasattr(self, 'processo_ativo'):
                self.processo_ativo = None

    def is_bot_error(self, erro_msg):
        """Verifica se o erro é relacionado a detecção de bot"""
        padroes_bot = [
            r'Sign in to confirm you\'re not a bot',
            r'Sign in to confirm your age',
            r'HTTP Error 403',
            r'Forbidden',
            r'bot',
            r'captcha'
        ]

        for padrao in padroes_bot:
            if re.search(padrao, erro_msg, re.IGNORECASE):
                return True
        return False

    def executar_download(self, use_potoken=False, proxy=None, browser_cookies=None):
        """Executa o download com configurações específicas e coleta metadados"""
        try:
            url = self.url_var.get().strip()
            pasta_destino = self.pasta_destino_var.get()
            modo = self.modo_download_var.get()

            yt_dlp_exe = self.recurso_caminho("yt-dlp.exe")
            ffmpeg_exe = self.recurso_caminho("ffmpeg.exe")

            if not yt_dlp_exe or not ffmpeg_exe:
                return {'sucesso': False, 'erro': "Dependências não encontradas"}

            output_template = self.criar_template_saida(
                pasta_destino, modo,
                self.qualidade_video_var.get() if modo == "video" else self.qualidade_audio_var.get()
            )

            comando = [
                yt_dlp_exe,
                "--ffmpeg-location", ffmpeg_exe,
                "-o", output_template,
                "--ignore-errors",
                "--yes-playlist",
                "--restrict-filenames",
                "--no-warnings",
                "--progress",
                "--newline"
            ]

            # Medidas anti-bot (Agora pegando valores da interface)
            limite = self.limite_velocidade_var.get() or "7M"
            intervalo = self.intervalo_requisicoes_var.get() or "1.5"
            timeout = self.socket_timeout_var.get() or "60"

            comando.extend([
                "--limit-rate", limite,
                "--sleep-requests", intervalo,
                "--socket-timeout", timeout
            ])

            if use_potoken and self.potoken_generator:
                if self.potoken_generator.visitor_data and self.potoken_generator.po_token:
                    comando.extend([
                        "--extractor-args",
                        f"youtube:po_token={self.potoken_generator.po_token};"
                        f"visitor_data={self.potoken_generator.visitor_data}"
                    ])

            if proxy:
                comando.extend(["--proxy", proxy])

            browsers_suportados = ['brave', 'chrome', 'chromium',
                                   'edge', 'firefox', 'opera', 'safari', 'vivaldi', 'whale']
            if browser_cookies and str(browser_cookies).lower() in browsers_suportados:
                comando.extend(["--cookies-from-browser", browser_cookies])

            modo_emulacao = self.modo_emulacao_var.get()
            if modo_emulacao != "padrão":
                comando.extend(
                    ["--extractor-args", f"youtube:player_client={modo_emulacao}"])

            comando.append(url)

            if modo == "video":
                qualidade = self.qualidade_video_var.get()
                formato_ext = self.formato_video_var.get()

                formato_selecao = self.mapeamento_qualidade_video.get(
                    qualidade, "bestvideo+bestaudio/best"
                )

                comando.insert(-1, "-f")
                comando.insert(-1, formato_selecao)

                # NOVO: Garante compatibilidade total com o Windows (Filmes e TV)
                comando.insert(-1, "--merge-output-format")
                comando.insert(-1, formato_ext)

                # Converte o áudio para aac durante a união para garantir que toque em qualquer player
                comando.insert(-1, "--audio-format")
                comando.insert(-1, "aac")

                comando.insert(-1, "--remux-video")
                comando.insert(-1, formato_ext)
            else:
                formato_audio = self.formato_audio_var.get()
                comando.insert(-1, "-f")
                # Melhor áudio disponível (evita erro de formato)
                comando.insert(-1, "ba/b")
                comando.insert(-1, "--extract-audio")
                comando.insert(-1, "--audio-format")
                comando.insert(-1, formato_audio)
                comando.insert(-1, "--audio-quality")
                comando.insert(-1, "0")
                comando.extend(["--fragment-retries", "10"])

            falhas_youtube = []
            titulo_atual = "Desconhecido"
            erro_geral = ""
            log_completo = []

            # Coleta de metadados
            camada_atual = "PoToken" if use_potoken else (
                "Proxy" if proxy else ("Cookies" if browser_cookies else "Padrão"))
            metadados = {
                'url': url,
                'camada': camada_atual,
                'emulacao': modo_emulacao,
                'proxy': proxy,
                'navegador': browser_cookies,
                'limite': limite,      # Adicionado
                'intervalo': intervalo,  # Adicionado
                'timeout': timeout,     # Adicionado
                'nota_tecnica': "Se o vídeo estiver mudo no Windows, tente abrir com o VLC Media Player."
            }

            padroes_erro_youtube = [
                (r'Video is private', 'Vídeo privado'),
                (r'This video is not available', 'Vídeo não disponível'),
                (r'Video unavailable', 'Vídeo indisponível'),
                (r'Sign in to confirm you\'re not a bot',
                 'Verificação de bot necessária'),
                (r'HTTP Error 403', 'Erro 403: Acesso negado'),
                (r'Could not copy.*cookie database',
                 'Navegador aberto (feche o navegador)'),
                (r'Requested format is not available',
                 'Qualidade indisponível para este vídeo')
            ]

            self.processo_ativo = subprocess.Popen(
                comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            for linha in self.processo_ativo.stdout:
                log_completo.append(linha)
                if self.cancelar_download:
                    self.processo_ativo.terminate()
                    return {'sucesso': False, 'erro': 'Cancelado', 'falhas': [], 'log': log_completo, 'metadados': metadados}

                if linha.strip():
                    # Capturar título do vídeo
                    if "[youtube]" in linha and "Downloading webpage" in linha:
                        match_titulo = re.search(
                            r'\[youtube\] ([^:]+):', linha)
                        if match_titulo:
                            titulo_atual = match_titulo.group(1).strip()

                    # Verificar erros específicos
                    for padrao, descricao in padroes_erro_youtube:
                        if re.search(padrao, linha, re.IGNORECASE):
                            erro_geral = descricao
                            falhas_youtube.append(
                                {'titulo': titulo_atual, 'erro': descricao})
                            break

                    # Atualizar Barra de Progresso
                    if "%" in linha and "ETA" in linha:
                        match = re.search(r'(\d+(?:\.\d+)?)%', linha)
                        if match:
                            porcentagem = float(match.group(1))
                            self.root.after(
                                0, lambda p=porcentagem: self.atualizar_progresso(p))

            codigo_saida = self.processo_ativo.wait()
            return {
                'sucesso': codigo_saida == 0 and not falhas_youtube,
                'codigo_saida': codigo_saida,
                'falhas': falhas_youtube,
                'erro': erro_geral,
                'log': log_completo,
                'metadados': metadados
            }

        except Exception as e:
            return {'sucesso': False, 'erro': str(e), 'falhas': [], 'metadados': locals().get('metadados', {})}

    def finalizar_download(self, resultado):
        """Finaliza o processo de download e exibe resultados"""
        try:
            if resultado['sucesso']:
                self.root.after(0, lambda: self.progresso_label.config(
                    text="✓ Download concluído com sucesso!"))
                self.root.after(
                    0, lambda: self.barra_progresso.config(value=100))
                self.root.after(0, lambda: messagebox.showinfo(
                    "Sucesso", "Download concluído com sucesso!"))
            else:
                falhas = resultado.get('falhas', [])
                erro = resultado.get('erro', 'Erro desconhecido')

                if falhas:
                    mensagem = f"Download finalizado com {len(falhas)} problema(s):\n\n"
                    for i, falha in enumerate(falhas, 1):
                        mensagem += f"{i}. {falha['titulo']} - {falha['erro']}\n"
                    self.root.after(0, lambda: messagebox.showwarning(
                        "Problemas Encontrados", mensagem))
                else:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Erro", f"Falha no download: {erro}"))

                self.root.after(0, lambda: self.progresso_label.config(
                    text=f"❌ Falha: {erro[:50]}"))

                self.root.after(100, lambda: self.gerenciar_log_erro(
                    resultado.get('log', []), resultado.get('metadados', {})))
        except Exception as e:
            print(f"Erro ao finalizar download: {e}")

    def gerenciar_log_erro(self, log_lista, metadados):
        """Pergunta ao usuário se deseja salvar o log de erro com cabeçalho detalhado"""
        if not log_lista:
            return

        if messagebox.askyesno("Salvar Log", "Ocorreu um erro no processo. Deseja salvar o log de depuração?"):
            caminho_log = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Arquivo de texto", "*.txt")],
                title="Salvar Log de Erro",
                initialfile=f"log_erro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )

            if caminho_log:
                try:
                    cabecalho = [
                        "==========================================================\n",
                        f"RELATÓRIO DE ERRO - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n",
                        "==========================================================\n",
                        f"URL Tentada: {metadados.get('url')}\n",
                        f"Camada Ativa: {metadados.get('camada')}\n",
                        f"Modo Emulação: {metadados.get('emulacao')}\n",
                        f"Proxy Utilizado: {metadados.get('proxy', 'Nenhum')}\n",
                        f"Navegador (Cookies): {metadados.get('navegador', 'Nenhum')}\n",
                        f"Ajustes de Rede: Limite={metadados.get('limite')}, Intervalo={metadados.get('intervalo')}s, Timeout={metadados.get('timeout')}s\n",
                        f"Software: Python {sys.version.split()[0]}, FFmpeg detectado em: {self.recurso_caminho('ffmpeg.exe')}\n",
                        f"Compatibilidade: Áudio forçado para AAC em downloads de vídeo.\n",
                        f"DICA DE COMPATIBILIDADE: {metadados.get('nota_tecnica')}\n",
                        "----------------------------------------------------------\n",
                        "LOG DO TERMINAL (yt-dlp):\n",
                        "----------------------------------------------------------\n"
                    ]
                    with open(caminho_log, 'w', encoding='utf-8') as f:
                        f.writelines(cabecalho)
                        f.writelines(log_lista)
                    messagebox.showinfo(
                        "Sucesso", "Log detalhado salvo com sucesso!")
                except Exception as e:
                    messagebox.showerror(
                        "Erro", f"Não foi possível salvar o arquivo: {e}")

    def atualizar_progresso(self, valor):
        """Atualiza a barra de progresso e garante visibilidade"""
        try:
            self.barra_progresso["value"] = min(valor, 100)
            self.progresso_label.config(text=f"Baixando... {valor:.1f}%")

            # Se for o início do download (ex: 1%), rola o canvas para o final
            if valor < 2:
                self.canvas.yview_moveto(1.0)
        except Exception as e:
            print(f"Erro ao atualizar progresso: {e}")

    def criar_template_saida(self, pasta_destino, modo, qualidade):
        """Cria template de saída diferenciando por modo e qualidade escolhida"""
        if modo == "audio":
            ext_escolhida = self.formato_audio_var.get()
            sufixo = f"_{qualidade.replace(' ', '_')}"
        else:
            ext_escolhida = self.formato_video_var.get()
            sufixo = f"_{qualidade.replace(' ', '_')}"

        # O sufixo ajuda o usuário a identificar o arquivo, mas a extensão final é gerada pelo sistema
        template = os.path.join(
            pasta_destino, f"%(title).100s{sufixo}.%(ext)s")
        return template


def main():
    try:
        root = tk.Tk()

        # Configurar ícone se disponível
        try:
            if hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
            else:
                icon_path = 'icon.ico'

            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
        except:
            pass

        # Configurar comportamento de fechamento
        def on_closing():
            if messagebox.askokcancel("Sair", "Deseja realmente sair do aplicativo?"):
                root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        # Criar aplicação
        app = YouTubeDownloader(root)

        # Centralizar janela na tela
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")

        root.mainloop()

    except Exception as e:
        messagebox.showerror(
            "Erro Crítico", f"Erro ao inicializar aplicação: {e}")
        print(f"Erro crítico: {e}")


if __name__ == "__main__":
    main()
