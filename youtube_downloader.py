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


class YouTubeDownloader:
    def __init__(self, root):
        # Configuração principal da janela
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("640x650")
        self.root.configure(bg="#f0f0f0")
        self.root.resizable(True, True)

        # Variáveis
        self.url_var = tk.StringVar()
        self.pasta_destino_var = tk.StringVar()
        self.qualidade_video_var = tk.StringVar()
        self.qualidade_audio_var = tk.StringVar()
        self.formato_audio_var = tk.StringVar(value="mp3")
        self.modo_download_var = tk.StringVar(value="video")
        self.modo_emulacao_var = tk.StringVar(
            value="padrão")  # NOVO: Modo de emulação

        self.processo_ativo = None  # Para controlar o processo ativo
        self.cancelar_download = False  # Flag para cancelamento

        # MODIFICAÇÃO 2: Qualidades puramente técnicas e numéricas
        self.qualidades_video_padrao = [
            "2160p (4K)",
            "1440p (2K)",
            "1080p (Full HD)",
            "720p (HD)",
            "480p (SD)",
            "360p",
            "240p",
            "144p"
        ]

        self.qualidades_audio_padrao = [
            "320kbps",
            "256kbps",
            "192kbps",
            "128kbps",
            "96kbps"
        ]

        # MODIFICAÇÃO 2: Mapeamento técnico de qualidades para filtros de altura
        self.mapeamento_qualidade_video = {
            "2160p (4K)": "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160][ext=mp4]/best[height<=2160]",
            "1440p (2K)": "bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/best[height<=1440][ext=mp4]/best[height<=1440]",
            "1080p (Full HD)": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[height<=1080]",
            "720p (HD)": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]",
            "480p (SD)": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best[height<=480]",
            "360p": "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best[height<=360]",
            "240p": "bestvideo[height<=240][ext=mp4]+bestaudio[ext=m4a]/best[height<=240][ext=mp4]/best[height<=240]",
            "144p": "bestvideo[height<=144][ext=mp4]+bestaudio[ext=m4a]/best[height<=144][ext=mp4]/best[height<=144]"
        }

        self.mapeamento_qualidade_audio = {
            "320kbps": "bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio",
            "256kbps": "bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio",
            "192kbps": "bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio",
            "128kbps": "bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio",
            "96kbps": "bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio"
        }

        # Inicializar valores padrão
        self.qualidade_video_var.set(
            self.qualidades_video_padrao[2])  # 1080p como padrão
        self.qualidade_audio_var.set(
            self.qualidades_audio_padrao[0])  # 320kbps como padrão

        # Verificar dependências
        if not self.verificar_dependencias():
            messagebox.showerror(
                "Erro", "Dependências necessárias não encontradas (yt-dlp.exe ou ffmpeg.exe)")
            return

        # Criar a interface
        self.criar_interface()

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
            return None

    def verificar_dependencias(self):
        """Verifica se as dependências necessárias estão disponíveis"""
        try:
            yt_dlp_path = self.recurso_caminho("yt-dlp.exe")
            ffmpeg_path = self.recurso_caminho("ffmpeg.exe")

            if not yt_dlp_path:
                return False

            if not ffmpeg_path:
                return False

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
        """Cria a interface gráfica do aplicativo"""
        try:
            # Estilo para widgets
            estilo = ttk.Style()
            estilo.configure("TButton", font=("Segoe UI", 10))
            estilo.configure("TLabel", font=(
                "Segoe UI", 10), background="#f0f0f0")
            estilo.configure("Header.TLabel", font=(
                "Segoe UI", 12, "bold"), background="#f0f0f0")
            estilo.configure("TFrame", background="#f0f0f0")
            estilo.configure("TRadiobutton", background="#f0f0f0")

            # Frame principal
            main_frame = ttk.Frame(self.root, padding=20)
            main_frame.pack(fill=tk.BOTH, expand=True)

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

            # MODIFICAÇÃO 1: Seletor de modo de emulação
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

            # Modo de download (vídeo ou áudio)
            modo_frame = ttk.Frame(main_frame)
            modo_frame.pack(fill=tk.X, pady=10)

            ttk.Label(modo_frame, text="Modo de download:").pack(
                side=tk.LEFT, padx=(0, 10))
            ttk.Radiobutton(modo_frame, text="Vídeo", variable=self.modo_download_var,
                            value="video", command=self.alternar_modo).pack(side=tk.LEFT, padx=10)
            ttk.Radiobutton(modo_frame, text="Áudio", variable=self.modo_download_var,
                            value="audio", command=self.alternar_modo).pack(side=tk.LEFT, padx=10)

            # Notebook para abas
            self.notebook = ttk.Notebook(main_frame)
            self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)

            # Aba para download de vídeo
            self.aba_video = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(self.aba_video, text="Download de Vídeo")

            # Aba para download de áudio
            self.aba_audio = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(self.aba_audio, text="Download de Áudio")

            # Configurar abas
            self.configurar_aba_video()
            self.configurar_aba_audio()

            # Frame para pasta de destino
            pasta_frame = ttk.Frame(main_frame)
            pasta_frame.pack(fill=tk.X, pady=10)

            ttk.Label(pasta_frame, text="Pasta de destino:").pack(
                side=tk.LEFT, padx=(0, 10))
            ttk.Entry(pasta_frame, textvariable=self.pasta_destino_var,
                      width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Button(pasta_frame, text="Escolher...", command=self.escolher_pasta).pack(
                side=tk.LEFT, padx=(10, 0))

            # Barra de progresso
            progresso_frame = ttk.Frame(main_frame)
            progresso_frame.pack(fill=tk.X, pady=10)

            self.progresso_label = ttk.Label(progresso_frame, text="Pronto")
            self.progresso_label.pack(fill=tk.X)

            self.barra_progresso = ttk.Progressbar(
                progresso_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
            self.barra_progresso.pack(fill=tk.X, pady=5)

            # Botão de download
            botao_frame = ttk.Frame(main_frame)
            botao_frame.pack(fill=tk.X, pady=10)

            self.botao_cancelar = ttk.Button(
                botao_frame, text="Cancelar", command=self.cancelar_operacao, width=20, state=tk.DISABLED)
            self.botao_cancelar.pack(side=tk.RIGHT, padx=(10, 0))

            self.botao_download = ttk.Button(
                botao_frame, text="Baixar", command=self.iniciar_download, width=20)
            self.botao_download.pack(side=tk.RIGHT)

            # Selecionar aba adequada conforme o modo
            self.alternar_modo()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao criar interface: {e}")

    def configurar_aba_video(self):
        """Configura os widgets da aba de vídeo"""
        try:
            # Qualidade do vídeo
            qualidade_frame = ttk.Frame(self.aba_video)
            qualidade_frame.pack(fill=tk.X, pady=10)

            ttk.Label(qualidade_frame, text="Qualidade do vídeo:").pack(
                side=tk.LEFT, padx=(0, 10))
            self.combo_qualidade_video = ttk.Combobox(qualidade_frame, textvariable=self.qualidade_video_var,
                                                      values=self.qualidades_video_padrao, width=25, state="readonly")
            self.combo_qualidade_video.pack(side=tk.LEFT)
            self.combo_qualidade_video.current(2)  # 1080p como padrão

            # Informações
            info_frame = ttk.Frame(self.aba_video)
            info_frame.pack(fill=tk.X, pady=10)

            info_text = ("Selecione a resolução desejada para o download.\n"
                         "Resoluções maiores oferecem melhor qualidade mas ocupam mais espaço.")

            ttk.Label(info_frame, text=info_text, wraplength=500,
                      justify=tk.LEFT).pack(fill=tk.X)
        except Exception as e:
            messagebox.showerror(
                "Erro", f"Erro ao configurar aba de vídeo: {e}")

    def configurar_aba_audio(self):
        """Configura os widgets da aba de áudio"""
        try:
            # Qualidade do áudio
            qualidade_frame = ttk.Frame(self.aba_audio)
            qualidade_frame.pack(fill=tk.X, pady=10)

            ttk.Label(qualidade_frame, text="Qualidade do áudio:").pack(
                side=tk.LEFT, padx=(0, 10))
            self.combo_qualidade_audio = ttk.Combobox(qualidade_frame, textvariable=self.qualidade_audio_var,
                                                      values=self.qualidades_audio_padrao, width=25, state="readonly")
            self.combo_qualidade_audio.pack(side=tk.LEFT)
            self.combo_qualidade_audio.current(0)

            # Formato do áudio
            formato_frame = ttk.Frame(self.aba_audio)
            formato_frame.pack(fill=tk.X, pady=10)

            ttk.Label(formato_frame, text="Formato de saída:").pack(
                side=tk.LEFT, padx=(0, 10))
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

            ttk.Label(info_frame, text=info_text, wraplength=500,
                      justify=tk.LEFT).pack(fill=tk.X)
        except Exception as e:
            messagebox.showerror(
                "Erro", f"Erro ao configurar aba de áudio: {e}")

    def alternar_modo(self):
        """Alterna entre o modo de download de vídeo e áudio, mostrando apenas abas relevantes"""
        try:
            modo = self.modo_download_var.get()

            # Remover todas as abas
            for i in range(self.notebook.index("end")):
                self.notebook.forget(0)

            if modo == "video":
                # Adicionar apenas aba de vídeo
                self.notebook.add(self.aba_video, text="Download de Vídeo")
                self.notebook.select(self.aba_video)
            else:
                # Adicionar aba de áudio
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
                pasta_anterior = self.pasta_destino_var.get()
                self.pasta_destino_var.set(pasta)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao selecionar pasta: {e}")

    def mostrar_falhas_detalhadas(self, mensagem):
        """Mostra falhas em uma janela com scroll para listas longas"""
        try:
            if len(mensagem) > 1000:  # Se a mensagem for muito longa
                # Criar janela personalizada com scroll
                janela = tk.Toplevel(self.root)
                janela.title("Detalhes das Falhas")
                janela.geometry("600x400")
                janela.configure(bg="#f0f0f0")

                # Frame com scroll
                frame = ttk.Frame(janela)
                frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                # Text widget com scrollbar
                text_widget = tk.Text(
                    frame, wrap=tk.WORD, font=("Segoe UI", 10))
                scrollbar = ttk.Scrollbar(
                    frame, orient=tk.VERTICAL, command=text_widget.yview)
                text_widget.configure(yscrollcommand=scrollbar.set)

                text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

                text_widget.insert(tk.END, mensagem)
                text_widget.config(state=tk.DISABLED)

                # Botão fechar
                ttk.Button(janela, text="Fechar",
                           command=janela.destroy).pack(pady=10)

                # Centralizar janela
                janela.transient(self.root)
                janela.grab_set()
            else:
                # Usar messagebox normal para mensagens curtas
                messagebox.showwarning("Falhas no Download", mensagem)
        except Exception as e:
            # Fallback para messagebox simples
            messagebox.showwarning("Falhas no Download",
                                   mensagem[:500] + "...")

    def cancelar_operacao(self):
        """Cancela a operação em andamento"""
        try:
            self.cancelar_download = True
            if self.processo_ativo:
                self.processo_ativo.terminate()

            self.progresso_label.config(text="Operação cancelada")
            self.barra_progresso["value"] = 0
            self.botao_download.config(state=tk.NORMAL)
            self.botao_cancelar.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao cancelar operação: {e}")

    def iniciar_download(self):
        """Inicia o processo de download em uma thread separada"""
        try:
            url = self.url_var.get().strip()
            if not url:
                messagebox.showerror(
                    "Erro", "Por favor, insira a URL do vídeo YouTube.")
                return

            if not self.validar_url(url):
                if not messagebox.askyesno("Aviso", "A URL não parece ser do YouTube. Deseja continuar mesmo assim?"):
                    return

            # PRESERVAÇÃO: Verificar duplicatas (mantida lógica original)
            eh_duplicata, motivo = self.verificar_duplicatas(url, self.modo_download_var.get(),
                                                             self.qualidade_video_var.get() if self.modo_download_var.get() == "video"
                                                             else self.qualidade_audio_var.get())

            if eh_duplicata:
                resposta = messagebox.askyesnocancel(
                    "Download Duplicado Detectado",
                    f"{motivo}\n\n"
                    f"Modo atual: {self.modo_download_var.get()}\n"
                    f"Qualidade: {self.qualidade_video_var.get() if self.modo_download_var.get() == 'video' else self.qualidade_audio_var.get()}\n\n"
                    f"Deseja continuar mesmo assim?\n\n"
                    f"Sim = Continuar download\n"
                    f"Não = Cancelar\n"
                    f"Cancelar = Voltar"
                )

                if resposta is None or resposta is False:
                    return

                self.tratar_duplicata_confirmada(url, self.modo_download_var.get(),
                                                 self.qualidade_video_var.get() if self.modo_download_var.get() == "video"
                                                 else self.qualidade_audio_var.get())

            pasta_destino = self.pasta_destino_var.get()
            if not os.path.isdir(pasta_destino):
                messagebox.showerror("Erro", "Pasta de destino inválida.")
                return

            # Verificar se a pasta é gravável
            if not os.access(pasta_destino, os.W_OK):
                messagebox.showerror(
                    "Erro", "Sem permissão de escrita na pasta de destino.")
                return

            # Desativar botão durante o download
            self.botao_download.config(state=tk.DISABLED)
            self.progresso_label.config(text="Iniciando download...")
            self.barra_progresso["value"] = 0

            # PRESERVAÇÃO: Iniciar download em uma thread separada
            threading.Thread(target=self.executar_download,
                             daemon=True).start()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao iniciar download: {e}")
            self.botao_download.config(state=tk.NORMAL)

    def executar_download(self):
        """Executa o download com yt-dlp, registrando apenas falhas do YouTube"""
        try:
            # Resetar flag de cancelamento
            self.cancelar_download = False
            self.root.after(
                0, lambda: self.botao_cancelar.config(state=tk.NORMAL))

            import random
            url = self.url_var.get().strip()
            pasta_destino = self.pasta_destino_var.get()
            modo = self.modo_download_var.get()

            yt_dlp_exe = self.recurso_caminho("yt-dlp.exe")
            ffmpeg_exe = self.recurso_caminho("ffmpeg.exe")

            if not yt_dlp_exe or not ffmpeg_exe:
                raise Exception("Dependências não encontradas")

            # Template de saída
            output_template = self.criar_template_saida(pasta_destino, modo,
                                                        self.qualidade_video_var.get() if modo == "video"
                                                        else self.qualidade_audio_var.get())

            # PRESERVAÇÃO: Comando base mantido com CREATE_NO_WINDOW
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

            # MODIFICAÇÃO 3: Medidas de comportamento humano (Anti-Bot)
            comando.extend([
                "--limit-rate", "7M",           # Limitador de taxa
                "--sleep-requests", "1.5",      # Intervalo entre requisições
                "--socket-timeout", "30"        # Timeout de socket
            ])

            # MODIFICAÇÃO 1: Emulação de cliente (Vacina Anti-403)
            modo_emulacao = self.modo_emulacao_var.get()
            if modo_emulacao != "padrão":
                comando.extend([
                    "--extractor-args", f"youtube:player_client={modo_emulacao}"
                ])

            # Adicionar URL no final
            comando.append(url)

            # PRESERVAÇÃO: Lógica de formato mantida
            if modo == "video":
                qualidade = self.qualidade_video_var.get()
                formato = self.mapeamento_qualidade_video.get(
                    qualidade, "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]")
                comando.insert(-1, "-f")
                comando.insert(-1, formato)
            else:
                qualidade = self.qualidade_audio_var.get()
                formato_audio = self.formato_audio_var.get()
                formato = "bestaudio/best"
                comando.insert(-1, "-f")
                comando.insert(-1, formato)
                comando.insert(-1, "--extract-audio")
                comando.insert(-1, "--audio-format")
                comando.insert(-1, formato_audio)
                comando.insert(-1, "--audio-quality")
                comando.insert(-1, "0")

            self.root.after(
                0, lambda: self.progresso_label.config(text="Baixando..."))
            self.root.after(0, lambda: self.barra_progresso.config(value=10))

            # PRESERVAÇÃO: Lista para armazenar falhas do YouTube
            falhas_youtube = []
            titulo_atual = "Desconhecido"

            # Padrões de erro específicos do YouTube
            padroes_erro_youtube = [
                (r'Video is private', 'Vídeo privado'),
                (r'This video is not available', 'Vídeo não disponível'),
                (r'Video unavailable', 'Vídeo indisponível'),
                (r'This video has been removed', 'Vídeo removido'),
                (r'Private video', 'Vídeo privado'),
                (r'Deleted video', 'Vídeo excluído'),
                (r'This video is unavailable', 'Vídeo indisponível'),
                (r'Sign in to confirm your age', 'Restrição de idade'),
                (r'Video blocked', 'Vídeo bloqueado'),
                (r'Copyright', 'Bloqueio por direitos autorais'),
                (r'This video contains content', 'Conteúdo restrito'),
                (r'region', 'Bloqueio regional'),
                (r'country', 'Bloqueio por país'),
                (r'HTTP Error 403', 'Erro 403: Acesso negado'),
                (r'Forbidden', 'Acesso proibido')
            ]

            # PRESERVAÇÃO: subprocess.Popen com CREATE_NO_WINDOW
            self.processo_ativo = subprocess.Popen(
                comando,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            for linha in self.processo_ativo.stdout:
                # PRESERVAÇÃO: Verificar cancelamento
                if self.cancelar_download:
                    self.processo_ativo.terminate()
                    self.root.after(0, lambda: self.progresso_label.config(
                        text="Download cancelado"))
                    self.root.after(
                        0, lambda: self.barra_progresso.config(value=0))
                    return

                if linha.strip():
                    # Capturar título do vídeo
                    if "[youtube]" in linha and "Downloading webpage" in linha:
                        # Extrair título se possível
                        match_titulo = re.search(
                            r'\[youtube\] ([^:]+):', linha)
                        if match_titulo:
                            titulo_atual = match_titulo.group(1).strip()

                    # Verificar se há erro do YouTube na linha
                    for padrao, descricao in padroes_erro_youtube:
                        if re.search(padrao, linha, re.IGNORECASE):
                            falha = {
                                'titulo': titulo_atual,
                                'erro': descricao,
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'linha_original': linha.strip()
                            }
                            falhas_youtube.append(falha)
                            break

                    # Atualizar progresso
                    if "%" in linha and "ETA" in linha:
                        try:
                            match = re.search(r'(\d+(?:\.\d+)?)%', linha)
                            if match:
                                porcentagem = float(match.group(1))
                                self.root.after(
                                    0, lambda p=porcentagem: self.atualizar_progresso(p))
                        except ValueError:
                            pass

            codigo_saida = self.processo_ativo.wait()

            # PRESERVAÇÃO: Resultado final com lógica original
            if codigo_saida == 0:
                if falhas_youtube:
                    self.root.after(0, lambda: self.progresso_label.config(
                        text=f"Concluído com {len(falhas_youtube)} falha(s)"))
                    self.root.after(
                        0, lambda: self.barra_progresso.config(value=100))

                    # Criar mensagem detalhada com todas as falhas
                    mensagem = f"Download concluído com {len(falhas_youtube)} falha(s):\n\n"
                    for i, falha in enumerate(falhas_youtube, 1):
                        mensagem += f"{i}. {falha['titulo']}\n"
                        mensagem += f"   Motivo: {falha['erro']}\n"
                        mensagem += f"   Horário: {falha['timestamp']}\n\n"

                    # Mostrar messagebox com scroll se necessário
                    self.root.after(
                        0, lambda: self.mostrar_falhas_detalhadas(mensagem))
                else:
                    self.root.after(0, lambda: self.progresso_label.config(
                        text="Download concluído com sucesso!"))
                    self.root.after(
                        0, lambda: self.barra_progresso.config(value=100))
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Sucesso", "Download concluído com sucesso!"))
            else:
                self.root.after(0, lambda: self.progresso_label.config(
                    text="Falhas durante o download"))
                if falhas_youtube:
                    mensagem = f"Download finalizado com {len(falhas_youtube)} problema(s):\n\n"
                    for i, falha in enumerate(falhas_youtube, 1):
                        mensagem += f"{i}. {falha['titulo']} - {falha['erro']}\n"
                    self.root.after(0, lambda: messagebox.showwarning(
                        "Problemas Encontrados", mensagem))
                else:
                    self.root.after(0, lambda: messagebox.showwarning(
                        "Aviso", "O download foi concluído com problemas não identificados."))

        except Exception as e:
            self.root.after(0, lambda: self.progresso_label.config(
                text=f"Erro: {str(e)[:50]}..."))
            self.root.after(0, lambda: messagebox.showerror(
                "Erro", f"Ocorreu um erro: {str(e)}"))
        finally:
            self.root.after(
                0, lambda: self.botao_download.config(state=tk.NORMAL))
            self.root.after(
                0, lambda: self.botao_cancelar.config(state=tk.DISABLED))
            if hasattr(self, 'processo_ativo'):
                self.processo_ativo = None

    def criar_template_saida(self, pasta_destino, modo, qualidade):
        """Cria template de saída com diferenciação por qualidade"""
        if modo == "audio":
            formato = self.formato_audio_var.get()
            sufixo = f"_{qualidade.replace(' ', '_')}_{formato}"
        else:
            sufixo = f"_{qualidade.replace(' ', '_')}"

        # Template que inclui qualidade no nome
        template = os.path.join(
            pasta_destino, f"%(title).100s{sufixo}.%(ext)s")
        return template

    def tratar_duplicata_confirmada(self, url, modo, qualidade):
        """Trata download confirmado de duplicata"""
        try:
            pasta_destino = self.pasta_destino_var.get()
            video_id_match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', url)
            if video_id_match:
                video_id = video_id_match.group(1)
                arquivos_existentes = self.verificar_arquivos_existentes(
                    video_id, pasta_destino)

                if arquivos_existentes:
                    mensagem = "ATENÇÃO: Arquivos existentes detectados:\n\n"
                    for arquivo in arquivos_existentes:
                        mensagem += f"• {os.path.basename(arquivo)}\n"
                    mensagem += "\nO novo download terá nome diferenciado pela qualidade."
                    messagebox.showinfo("Arquivos Existentes", mensagem)

            return True
        except Exception:
            return True

    def atualizar_progresso(self, valor):
        """Atualiza a barra de progresso"""
        try:
            self.barra_progresso["value"] = min(valor, 100)
            self.progresso_label.config(text=f"Baixando... {valor:.1f}%")
        except Exception as e:
            print(f"Erro ao atualizar progresso: {e}")

    def verificar_duplicatas(self, url, modo, qualidade):
        """PRESERVAÇÃO: Verifica se o download já foi feito anteriormente (baseado no ID de 11 caracteres)"""
        try:
            pasta_destino = self.pasta_destino_var.get()

            # Extrair ID do vídeo da URL
            video_id = None
            match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', url)
            if match:
                video_id = match.group(1)

            if not video_id:
                return False, "ID do vídeo não identificado"

            # Verificar arquivos existentes na pasta
            arquivos_existentes = self.verificar_arquivos_existentes(
                video_id, pasta_destino)

            if arquivos_existentes:
                detalhes = f"Vídeo {video_id} já existe:\n"
                for arquivo in arquivos_existentes:
                    detalhes += f"• {os.path.basename(arquivo)}\n"
                return True, detalhes

            return False, "Vídeo não encontrado"

        except Exception as e:
            return False, f"Erro na verificação: {e}"

    def verificar_arquivos_existentes(self, video_id, pasta_destino):
        """PRESERVAÇÃO: Verifica se existem arquivos do vídeo na pasta de destino"""
        arquivos_encontrados = []
        try:
            for arquivo in os.listdir(pasta_destino):
                if video_id in arquivo or self.limpar_nome_arquivo(arquivo).find(video_id) != -1:
                    caminho_completo = os.path.join(pasta_destino, arquivo)
                    if os.path.isfile(caminho_completo):
                        arquivos_encontrados.append(caminho_completo)
            return arquivos_encontrados
        except Exception:
            return []

    def limpar_nome_arquivo(self, nome):
        """Remove caracteres especiais do nome do arquivo"""
        return re.sub(r'[<>:"/\\|?*\n\r\t]', '', nome)

    def gerar_nome_unico(self, nome_base, extensao, modo, qualidade, pasta_destino):
        """Gera nome único para arquivo, incluindo qualidade/modo"""
        try:
            # Limpar nome base
            nome_limpo = self.limpar_nome_arquivo(nome_base)

            # Adicionar informações de qualidade/modo
            if modo == "audio":
                formato = self.formato_audio_var.get()
                sufixo = f"_{qualidade.replace(' ', '_')}_{formato}"
            else:
                sufixo = f"_{qualidade.replace(' ', '_')}"

            # Se já existe, adicionar contador
            contador = 1
            nome_final = f"{nome_limpo}{sufixo}.{extensao}"
            caminho_completo = os.path.join(pasta_destino, nome_final)

            while os.path.exists(caminho_completo):
                contador += 1
                nome_final = f"{nome_limpo}{sufixo}_v{contador}.{extensao}"
                caminho_completo = os.path.join(pasta_destino, nome_final)

            return nome_final

        except Exception as e:
            print(f"Erro ao gerar nome único: {e}")
            # Fallback para nome simples
            import time
            timestamp = int(time.time())
            return f"{nome_base}_{timestamp}.{extensao}"

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
        messagebox.showerror(
            "Erro Crítico", f"Erro ao inicializar aplicação: {e}")
        print(f"Erro crítico: {e}")


if __name__ == "__main__":
    main()
