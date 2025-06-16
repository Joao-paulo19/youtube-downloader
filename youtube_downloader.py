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

class YouTubeDownloader:
    def __init__(self, root):
        # Configuração principal da janela
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("640x600")
        self.root.configure(bg="#f0f0f0")
        self.root.resizable(True, True)
        
        # Configurar logging
        self.configurar_logging()
        
        # Variáveis
        self.url_var = tk.StringVar()
        self.pasta_destino_var = tk.StringVar()
        self.pasta_destino_var.set(os.path.join(os.path.expanduser("~"), "Downloads"))
        self.qualidade_video_var = tk.StringVar()
        self.qualidade_audio_var = tk.StringVar()
        self.formato_audio_var = tk.StringVar(value="mp3")
        self.modo_download_var = tk.StringVar(value="video")
        self.arquivo_conversao_var = tk.StringVar()
        self.formato_conversao_var = tk.StringVar(value="mp3")
        
        # Disponibiliza qualidades de vídeo comuns como padrão
        self.qualidades_video_padrao = [
            "Melhor qualidade",
            "1080p (Full HD)",
            "720p (HD)",
            "480p (SD)",
            "360p (SD Baixa)",
            "240p (Baixa)",
            "144p (Muito Baixa)"
        ]
        
        self.qualidades_audio_padrao = [
            "Melhor qualidade",
            "320kbps",
            "256kbps",
            "192kbps",
            "128kbps",
            "96kbps"
        ]
        
        # Mapeamento de qualidades para códigos do yt-dlp
        self.mapeamento_qualidade_video = {
            "Melhor qualidade": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "1080p (Full HD)": "137+140/bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[height<=1080]",
            "720p (HD)": "22/136+140/bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]",
            "480p (SD)": "135+140/bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best[height<=480]",
            "360p (SD Baixa)": "18/134+140/bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best[height<=360]",
            "240p (Baixa)": "133+140/bestvideo[height<=240][ext=mp4]+bestaudio[ext=m4a]/best[height<=240][ext=mp4]/best[height<=240]",
            "144p (Muito Baixa)": "160+140/bestvideo[height<=144][ext=mp4]+bestaudio[ext=m4a]/best[height<=144][ext=mp4]/best[height<=144]"
        }
        
        self.mapeamento_qualidade_audio = {
            "Melhor qualidade": "bestaudio[ext=m4a]/bestaudio",
            "320kbps": "bestaudio[abr>=320]/bestaudio",
            "256kbps": "bestaudio[abr>=256][abr<320]/bestaudio[abr<320]",
            "192kbps": "bestaudio[abr>=192][abr<256]/bestaudio[abr<256]",
            "128kbps": "bestaudio[abr>=128][abr<192]/bestaudio[abr<192]",
            "96kbps": "bestaudio[abr>=96][abr<128]/bestaudio[abr<128]"
        }
        
        # Inicializar valores padrão
        self.qualidade_video_var.set(self.qualidades_video_padrao[0])
        self.qualidade_audio_var.set(self.qualidades_audio_padrao[0])
        
        # Verificar dependências
        if not self.verificar_dependencias():
            messagebox.showerror("Erro", "Dependências necessárias não encontradas (yt-dlp.exe ou ffmpeg.exe)")
            return
        
        # Criar a interface
        self.criar_interface()
    
    def configurar_logging(self):
        """Configura o sistema de logging"""
        try:
            log_dir = os.path.join(os.path.expanduser("~"), "Downloads", "YouTubeDownloader_Logs")
            os.makedirs(log_dir, exist_ok=True)
            
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(os.path.join(log_dir, 'downloader.log'), encoding='utf-8'),
                    logging.StreamHandler()
                ]
            )
            self.logger = logging.getLogger(__name__)
        except Exception as e:
            print(f"Erro ao configurar logging: {e}")
            self.logger = None
    
    def log_info(self, mensagem):
        """Log de informações"""
        if self.logger:
            self.logger.info(mensagem)
        else:
            print(f"INFO: {mensagem}")
    
    def log_error(self, mensagem):
        """Log de erros"""
        if self.logger:
            self.logger.error(mensagem)
        else:
            print(f"ERRO: {mensagem}")
        
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
                # Tentar encontrar no PATH do sistema
                import shutil
                return shutil.which(relativo.replace('.exe', ''))
        except Exception as e:
            self.log_error(f"Erro ao localizar recurso {relativo}: {e}")
            return None
    
    def verificar_dependencias(self):
        """Verifica se as dependências necessárias estão disponíveis"""
        try:
            yt_dlp_path = self.recurso_caminho("yt-dlp.exe")
            ffmpeg_path = self.recurso_caminho("ffmpeg.exe")
            
            if not yt_dlp_path:
                self.log_error("yt-dlp.exe não encontrado")
                return False
            
            if not ffmpeg_path:
                self.log_error("ffmpeg.exe não encontrado")
                return False
            
            self.log_info("Dependências verificadas com sucesso")
            return True
        except Exception as e:
            self.log_error(f"Erro ao verificar dependências: {e}")
            return False
    
    def validar_url(self, url):
        """Valida se a URL é do YouTube"""
        padroes_youtube = [
            r'youtube\.com/watch\?v=',
            r'youtube\.com/playlist\?list=',
            r'youtu\.be/',
            r'youtube\.com/channel/',
            r'youtube\.com/user/'
        ]
        
        for padrao in padroes_youtube:
            if re.search(padrao, url, re.IGNORECASE):
                return True
        return False
    
    def criar_interface(self):
        """Cria a interface gráfica do aplicativo"""
        try:
            # Estilo para widgets
            estilo = ttk.Style()
            estilo.configure("TButton", font=("Segoe UI", 10))
            estilo.configure("TLabel", font=("Segoe UI", 10), background="#f0f0f0")
            estilo.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), background="#f0f0f0")
            estilo.configure("TFrame", background="#f0f0f0")
            estilo.configure("TRadiobutton", background="#f0f0f0")
            
            # Frame principal
            main_frame = ttk.Frame(self.root, padding=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Título
            titulo_label = ttk.Label(main_frame, text="YouTube Downloader", style="Header.TLabel", font=("Segoe UI", 16, "bold"))
            titulo_label.pack(pady=(0, 20))
            
            # Frame para URL
            url_frame = ttk.Frame(main_frame)
            url_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(url_frame, text="URL do YouTube:").pack(side=tk.LEFT, padx=(0, 10))
            self.entry_url = ttk.Entry(url_frame, textvariable=self.url_var, width=50)
            self.entry_url.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Modo de download (vídeo ou áudio)
            modo_frame = ttk.Frame(main_frame)
            modo_frame.pack(fill=tk.X, pady=10)
            
            ttk.Label(modo_frame, text="Modo de download:").pack(side=tk.LEFT, padx=(0, 10))
            ttk.Radiobutton(modo_frame, text="Vídeo", variable=self.modo_download_var, value="video", command=self.alternar_modo).pack(side=tk.LEFT, padx=10)
            ttk.Radiobutton(modo_frame, text="Áudio", variable=self.modo_download_var, value="audio", command=self.alternar_modo).pack(side=tk.LEFT, padx=10)
            
            # Notebook para abas
            self.notebook = ttk.Notebook(main_frame)
            self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
            
            # Aba para download de vídeo
            self.aba_video = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(self.aba_video, text="Download de Vídeo")
            
            # Aba para download de áudio
            self.aba_audio = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(self.aba_audio, text="Download de Áudio")
            
            # Aba para conversão de áudio
            self.aba_conversao = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(self.aba_conversao, text="Conversão de Áudio")
            
            # Configurar abas
            self.configurar_aba_video()
            self.configurar_aba_audio()
            self.configurar_aba_conversao()
            
            # Frame para pasta de destino
            pasta_frame = ttk.Frame(main_frame)
            pasta_frame.pack(fill=tk.X, pady=10)
            
            ttk.Label(pasta_frame, text="Pasta de destino:").pack(side=tk.LEFT, padx=(0, 10))
            ttk.Entry(pasta_frame, textvariable=self.pasta_destino_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Button(pasta_frame, text="Escolher...", command=self.escolher_pasta).pack(side=tk.LEFT, padx=(10, 0))
            
            # Barra de progresso
            progresso_frame = ttk.Frame(main_frame)
            progresso_frame.pack(fill=tk.X, pady=10)
            
            self.progresso_label = ttk.Label(progresso_frame, text="Pronto")
            self.progresso_label.pack(fill=tk.X)
            
            self.barra_progresso = ttk.Progressbar(progresso_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
            self.barra_progresso.pack(fill=tk.X, pady=5)
            
            # Botão de download
            botao_frame = ttk.Frame(main_frame)
            botao_frame.pack(fill=tk.X, pady=10)
            
            self.botao_download = ttk.Button(botao_frame, text="Baixar", command=self.iniciar_download, width=20)
            self.botao_download.pack(side=tk.RIGHT)
            
            # Selecionar aba adequada conforme o modo
            self.alternar_modo()
            
        except Exception as e:
            self.log_error(f"Erro ao criar interface: {e}")
            messagebox.showerror("Erro", f"Erro ao criar interface: {e}")
        
    def configurar_aba_video(self):
        """Configura os widgets da aba de vídeo"""
        try:
            # Qualidade do vídeo
            qualidade_frame = ttk.Frame(self.aba_video)
            qualidade_frame.pack(fill=tk.X, pady=10)
            
            ttk.Label(qualidade_frame, text="Qualidade do vídeo:").pack(side=tk.LEFT, padx=(0, 10))
            self.combo_qualidade_video = ttk.Combobox(qualidade_frame, textvariable=self.qualidade_video_var, 
                                                     values=self.qualidades_video_padrao, width=25, state="readonly")
            self.combo_qualidade_video.pack(side=tk.LEFT)
            self.combo_qualidade_video.current(0)
            
            # Informações
            info_frame = ttk.Frame(self.aba_video)
            info_frame.pack(fill=tk.X, pady=10)
            
            info_text = ("Este modo baixa vídeos do YouTube na qualidade selecionada.\n"
                        "Selecione 'Melhor qualidade' para obter a melhor resolução disponível.")
            
            ttk.Label(info_frame, text=info_text, wraplength=500, justify=tk.LEFT).pack(fill=tk.X)
        except Exception as e:
            self.log_error(f"Erro ao configurar aba de vídeo: {e}")
    
    def configurar_aba_audio(self):
        """Configura os widgets da aba de áudio"""
        try:
            # Qualidade do áudio
            qualidade_frame = ttk.Frame(self.aba_audio)
            qualidade_frame.pack(fill=tk.X, pady=10)
            
            ttk.Label(qualidade_frame, text="Qualidade do áudio:").pack(side=tk.LEFT, padx=(0, 10))
            self.combo_qualidade_audio = ttk.Combobox(qualidade_frame, textvariable=self.qualidade_audio_var, 
                                                     values=self.qualidades_audio_padrao, width=25, state="readonly")
            self.combo_qualidade_audio.pack(side=tk.LEFT)
            self.combo_qualidade_audio.current(0)
            
            # Formato do áudio
            formato_frame = ttk.Frame(self.aba_audio)
            formato_frame.pack(fill=tk.X, pady=10)
            
            ttk.Label(formato_frame, text="Formato de saída:").pack(side=tk.LEFT, padx=(0, 10))
            formatos = ["mp3", "m4a", "wav", "opus", "flac"]
            self.combo_formato_audio = ttk.Combobox(formato_frame, textvariable=self.formato_audio_var, 
                                                   values=formatos, width=10, state="readonly")
            self.combo_formato_audio.pack(side=tk.LEFT)
            self.combo_formato_audio.current(0)
            
            # Informações
            info_frame = ttk.Frame(self.aba_audio)
            info_frame.pack(fill=tk.X, pady=10)
            
            info_text = ("Este modo extrai apenas o áudio do vídeo YouTube.\n"
                        "O áudio será salvo no formato escolhido.")
            
            ttk.Label(info_frame, text=info_text, wraplength=500, justify=tk.LEFT).pack(fill=tk.X)
        except Exception as e:
            self.log_error(f"Erro ao configurar aba de áudio: {e}")
    
    def configurar_aba_conversao(self):
        """Configura os widgets da aba de conversão"""
        try:
            # Widgets para conversão
            arquivo_frame = ttk.Frame(self.aba_conversao)
            arquivo_frame.pack(fill=tk.X, pady=10)
            
            ttk.Label(arquivo_frame, text="Arquivo de áudio:").pack(side=tk.LEFT, padx=(0, 10))
            ttk.Entry(arquivo_frame, textvariable=self.arquivo_conversao_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Button(arquivo_frame, text="Selecionar...", command=self.selecionar_arquivo_audio).pack(side=tk.LEFT, padx=(10, 0))
            
            # Formato para conversão
            formato_frame = ttk.Frame(self.aba_conversao)
            formato_frame.pack(fill=tk.X, pady=10)
            
            ttk.Label(formato_frame, text="Converter para:").pack(side=tk.LEFT, padx=(0, 10))
            formatos = ["mp3", "m4a", "wav", "opus", "flac", "aac"]
            ttk.Combobox(formato_frame, textvariable=self.formato_conversao_var, 
                        values=formatos, width=10, state="readonly").pack(side=tk.LEFT)
            
            # Botão de conversão
            botao_frame = ttk.Frame(self.aba_conversao)
            botao_frame.pack(fill=tk.X, pady=10)
            
            ttk.Button(botao_frame, text="Converter", command=self.converter_audio, width=20).pack(side=tk.RIGHT)
            
            # Informações
            info_frame = ttk.Frame(self.aba_conversao)
            info_frame.pack(fill=tk.X, pady=10)
            
            info_text = ("Esta função converte arquivos de áudio entre diferentes formatos.\n"
                        "Selecione um arquivo e escolha o formato de saída desejado.")
            
            ttk.Label(info_frame, text=info_text, wraplength=500, justify=tk.LEFT).pack(fill=tk.X)
        except Exception as e:
            self.log_error(f"Erro ao configurar aba de conversão: {e}")
    
    def alternar_modo(self):
        """Alterna entre o modo de download de vídeo e áudio"""
        try:
            modo = self.modo_download_var.get()
            if modo == "video":
                self.notebook.select(self.aba_video)
            else:
                self.notebook.select(self.aba_audio)
        except Exception as e:
            self.log_error(f"Erro ao alternar modo: {e}")
    
    def escolher_pasta(self):
        """Abre diálogo para escolher pasta de destino"""
        try:
            pasta = filedialog.askdirectory(initialdir=self.pasta_destino_var.get())
            if pasta:
                self.pasta_destino_var.set(pasta)
                self.log_info(f"Pasta de destino alterada para: {pasta}")
        except Exception as e:
            self.log_error(f"Erro ao escolher pasta: {e}")
            messagebox.showerror("Erro", f"Erro ao selecionar pasta: {e}")
    
    def selecionar_arquivo_audio(self):
        """Abre diálogo para selecionar arquivo de áudio para conversão"""
        try:
            formatos = [("Arquivos de áudio", "*.mp3 *.m4a *.opus *.webm *.wav *.flac *.aac"),
                       ("Todos os arquivos", "*.*")]
            arquivo = filedialog.askopenfilename(filetypes=formatos, 
                                                initialdir=self.pasta_destino_var.get())
            if arquivo:
                self.arquivo_conversao_var.set(arquivo)
                self.log_info(f"Arquivo selecionado para conversão: {arquivo}")
        except Exception as e:
            self.log_error(f"Erro ao selecionar arquivo: {e}")
            messagebox.showerror("Erro", f"Erro ao selecionar arquivo: {e}")
    
    def iniciar_download(self):
        """Inicia o processo de download em uma thread separada"""
        try:
            url = self.url_var.get().strip()
            if not url:
                messagebox.showerror("Erro", "Por favor, insira a URL do vídeo YouTube.")
                return
            
            if not self.validar_url(url):
                if not messagebox.askyesno("Aviso", "A URL não parece ser do YouTube. Deseja continuar mesmo assim?"):
                    return
            
            pasta_destino = self.pasta_destino_var.get()
            if not os.path.isdir(pasta_destino):
                messagebox.showerror("Erro", "Pasta de destino inválida.")
                return
            
            # Verificar se a pasta é gravável
            if not os.access(pasta_destino, os.W_OK):
                messagebox.showerror("Erro", "Sem permissão de escrita na pasta de destino.")
                return
            
            # Desativar botão durante o download
            self.botao_download.config(state=tk.DISABLED)
            self.progresso_label.config(text="Iniciando download...")
            self.barra_progresso["value"] = 0
            
            # Iniciar download em uma thread separada
            threading.Thread(target=self.executar_download, daemon=True).start()
            
        except Exception as e:
            self.log_error(f"Erro ao iniciar download: {e}")
            messagebox.showerror("Erro", f"Erro ao iniciar download: {e}")
            self.botao_download.config(state=tk.NORMAL)
    
    def executar_download(self):
        """Executa o download com yt-dlp, com suporte a playlist, sanitização e log"""
        try:
            import random
            url = self.url_var.get().strip()
            pasta_destino = self.pasta_destino_var.get()
            modo = self.modo_download_var.get()

            yt_dlp_exe = self.recurso_caminho("yt-dlp.exe")
            ffmpeg_exe = self.recurso_caminho("ffmpeg.exe")
            
            if not yt_dlp_exe or not ffmpeg_exe:
                raise Exception("Dependências não encontradas")
            
            # Criar diretório de logs se não existir
            log_dir = os.path.join(pasta_destino, "YouTubeDownloader_Logs")
            os.makedirs(log_dir, exist_ok=True)
            
            archive_path = os.path.join(log_dir, "baixados.txt")
            log_path = os.path.join(log_dir, "download_log.txt")

            # Criar nome temporário seguro para evitar erro por caracteres inválidos
            base_nome = re.sub(r'[<>:"/\\|?*\n\r\t]', '', url.split("=")[-1])[:50].strip()
            if not base_nome:
                base_nome = f"video_desconhecido_{random.randint(1000,9999)}"
            
            # Template de saída mais seguro
            output_template = os.path.join(pasta_destino, "%(title).100s.%(ext)s")

            comando = [
                yt_dlp_exe,
                "--ffmpeg-location", ffmpeg_exe,
                "-o", output_template,
                "--ignore-errors",
                "--yes-playlist",
                "--download-archive", archive_path,
                "--restrict-filenames",
                "--no-warnings",
                "--progress",
                "--newline",
                url
            ]

            if modo == "video":
                qualidade = self.qualidade_video_var.get()
                formato = self.mapeamento_qualidade_video.get(qualidade, "bestvideo+bestaudio/best")
                comando.extend(["-f", formato])
                self.log_info(f"Iniciando download de vídeo - Qualidade: {qualidade}")
            else:
                qualidade = self.qualidade_audio_var.get()
                formato_audio = self.formato_audio_var.get()
                formato = self.mapeamento_qualidade_audio.get(qualidade, "bestaudio")
                comando.extend([
                    "-f", formato,
                    "--extract-audio",
                    "--audio-format", formato_audio,
                    "--audio-quality", "0"
                ])
                self.log_info(f"Iniciando download de áudio - Qualidade: {qualidade}, Formato: {formato_audio}")

            self.root.after(0, lambda: self.progresso_label.config(text="Baixando..."))
            self.root.after(0, lambda: self.barra_progresso.config(value=10))

            with open(log_path, "w", encoding="utf-8") as log_file:
                processo = subprocess.Popen(
                    comando,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )

                for linha in processo.stdout:
                    if linha.strip():
                        log_file.write(linha)
                        log_file.flush()

                        # Atualizar progresso baseado na saída do yt-dlp
                        if "%" in linha and "ETA" in linha:
                            try:
                                match = re.search(r'(\d+(?:\.\d+)?)%', linha)
                                if match:
                                    porcentagem = float(match.group(1))
                                    self.root.after(0, lambda p=porcentagem: self.atualizar_progresso(p))
                            except ValueError:
                                pass

                codigo_saida = processo.wait()

            if codigo_saida == 0:
                self.root.after(0, lambda: self.progresso_label.config(text="Download concluído com sucesso!"))
                self.root.after(0, lambda: self.barra_progresso.config(value=100))
                self.root.after(0, lambda: messagebox.showinfo("Sucesso", "Download concluído com sucesso!"))
                self.log_info("Download concluído com sucesso")
            else:
                self.root.after(0, lambda: self.progresso_label.config(text="Erros durante o download."))
                self.root.after(0, lambda: messagebox.showwarning("Aviso", f"O download foi concluído com falhas. Veja o log em:\n{log_path}"))
                self.log_error(f"Download concluído com código de saída: {codigo_saida}")

        except subprocess.TimeoutExpired:
            self.root.after(0, lambda: self.progresso_label.config(text="Timeout no download"))
            self.root.after(0, lambda: messagebox.showerror("Erro", "Timeout durante o download"))
            self.log_error("Timeout durante o download")
        except FileNotFoundError as e:
            self.root.after(0, lambda: self.progresso_label.config(text="Arquivo não encontrado"))
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Dependência não encontrada: {e}"))
            self.log_error(f"Dependência não encontrada: {e}")
        except PermissionError as e:
            self.root.after(0, lambda: self.progresso_label.config(text="Erro de permissão"))
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Erro de permissão: {e}"))
            self.log_error(f"Erro de permissão: {e}")
        except Exception as e:
            self.root.after(0, lambda: self.progresso_label.config(text=f"Erro: {str(e)[:50]}..."))
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}"))
            self.log_error(f"Erro durante download: {e}")

        finally:
            self.root.after(0, lambda: self.botao_download.config(state=tk.NORMAL))
    
    def atualizar_progresso(self, valor):
        """Atualiza a barra de progresso"""
        try:
            self.barra_progresso["value"] = min(valor, 100)
            self.progresso_label.config(text=f"Baixando... {valor:.1f}%")
        except Exception as e:
            self.log_error(f"Erro ao atualizar progresso: {e}")
    
    def converter_audio(self):
        """Converte um arquivo de áudio para outro formato"""
        try:
            arquivo_origem = self.arquivo_conversao_var.get()
            formato_destino = self.formato_conversao_var.get()
            
            if not arquivo_origem or not os.path.isfile(arquivo_origem):
                messagebox.showerror("Erro", "Selecione um arquivo de áudio válido.")
                return
            
            # Verificar se o arquivo é acessível
            if not os.access(arquivo_origem, os.R_OK):
                messagebox.showerror("Erro", "Sem permissão para ler o arquivo selecionado.")
                return
            
            # Gerar nome do arquivo de saída
            nome_base = os.path.splitext(arquivo_origem)[0]
            arquivo_destino = f"{nome_base}.{formato_destino}"
            
            # Verificar se o arquivo de saída já existe
            if os.path.exists(arquivo_destino):
                if not messagebox.askyesno("Confirmar", f"O arquivo {os.path.basename(arquivo_destino)} já existe. Deseja substituí-lo?"):
                    return
            
            # Verificar se há espaço suficiente no disco
            pasta_destino = os.path.dirname(arquivo_destino)
            if not os.access(pasta_destino, os.W_OK):
                messagebox.showerror("Erro", "Sem permissão de escrita na pasta de destino.")
                return
            
            # Atualizar interface
            self.progresso_label.config(text="Convertendo áudio...")
            self.barra_progresso["value"] = 30
            self.root.update()
            
            # Caminho do ffmpeg
            ffmpeg_exe = self.recurso_caminho("ffmpeg.exe")
            if not ffmpeg_exe:
                raise Exception("FFmpeg não encontrado")
            
            # Comando para conversão
            comando = [
                ffmpeg_exe,
                "-i", arquivo_origem,
                "-y",  # Sobrescrever arquivo se existir
                "-loglevel", "error",  # Reduzir verbosidade
                arquivo_destino
            ]
            
            self.log_info(f"Iniciando conversão de {arquivo_origem} para {formato_destino}")
            
            # Executar conversão
            processo = subprocess.run(
                comando, 
                check=True, 
                capture_output=True, 
                text=True,
                timeout=300,  # Timeout de 5 minutos
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Verificar se o arquivo foi criado
            if not os.path.exists(arquivo_destino):
                raise Exception("Arquivo de saída não foi criado")
            
            # Atualizar interface após conclusão
            self.progresso_label.config(text="Conversão concluída!")
            self.barra_progresso["value"] = 100
            messagebox.showinfo("Sucesso", f"Arquivo convertido com sucesso para {formato_destino}!")
            self.log_info(f"Conversão concluída: {arquivo_destino}")
            
        except subprocess.TimeoutExpired:
            self.progresso_label.config(text="Timeout na conversão.")
            messagebox.showerror("Erro", "Timeout durante a conversão do áudio.")
            self.log_error("Timeout durante conversão de áudio")
        except subprocess.CalledProcessError as e:
            self.progresso_label.config(text="Erro na conversão.")
            erro_msg = e.stderr if e.stderr else str(e)
            messagebox.showerror("Erro", f"Falha na conversão: {erro_msg}")
            self.log_error(f"Erro na conversão: {erro_msg}")
        except FileNotFoundError:
            self.progresso_label.config(text="FFmpeg não encontrado.")
            messagebox.showerror("Erro", "FFmpeg não encontrado. Verifique se está instalado.")
            self.log_error("FFmpeg não encontrado")
        except PermissionError as e:
            self.progresso_label.config(text="Erro de permissão.")
            messagebox.showerror("Erro", f"Erro de permissão: {e}")
            self.log_error(f"Erro de permissão na conversão: {e}")
        except Exception as e:
            self.progresso_label.config(text="Erro na conversão.")
            messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")
            self.log_error(f"Erro durante conversão: {e}")
        finally:
            # Resetar progresso após um tempo
            self.root.after(3000, lambda: self.barra_progresso.config(value=0))


# Função principal
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
            pass  # Ignorar se não conseguir definir o ícone
        
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
        messagebox.showerror("Erro Crítico", f"Erro ao inicializar aplicação: {e}")
        print(f"Erro crítico: {e}")

if __name__ == "__main__":
    main()
