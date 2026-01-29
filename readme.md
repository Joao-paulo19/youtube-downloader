# YouTube Downloader

Baixa vídeos (até 4K) e áudios (MP3/FLAC/etc) do YouTube. Versão desktop com interface gráfica.

![Screenshot](screenshot.png)

---

## 🎯 Como funciona?

- Baixa vídeos nas **resoluções**: 2160p (4K), 1440p (2K), 1080p, 720p, 480p, 360p, 240p, 144p
- Baixa áudios em **MP3, FLAC, M4A, WAV ou OPUS** com qualidades de 96kbps até 320kbps
- Interface simples: cola o link, escolhe o formato, clica e baixa

---

## 🔥 Erro 403

YouTube mudou as travas de segurança e agora bloqueia downloads com **HTTP Error 403: Forbidden**. 

**Como funciona agora:**
- O programa tem um **seletor de "Modo de Emulação"** que finge ser um cliente diferente (tipo um app de celular ou smart TV)
- Se der erro 403, **simplesmente troca** o modo de emulação pra `android_vr` ou `ios` e tenta de novo
- Opções disponíveis: `padrão`, `android_vr`, `ios`, `android`, `web_safari`

**Por que funciona?** O YouTube trata clientes de celular/TV de forma diferente. Quando você muda o modo, o yt-dlp "se disfarça" e consegue passar pelas travas.

---

## ⚡ Instalação

**Você precisa de TRÊS executáveis na pasta raiz do programa (nome da pasta raiz a seu critério):**

### 1. **yt-dlp.exe**
Baixa aqui: [yt-dlp Releases](https://github.com/yt-dlp/yt-dlp/releases)

### 2. **ffmpeg.exe** 
Baixa aqui: [Gyan.dev FFmpeg](https://www.gyan.dev/ffmpeg/builds/)
- Pega a versão **`ffmpeg-release-full.zip`**
- Descompacta, entra na pasta `bin` e copia o `ffmpeg.exe`

### 3. **deno.exe** (NOVO - motor JavaScript)
Baixa aqui: [Deno Releases](https://github.com/denoland/deno/releases)
- Pega o arquivo `deno-x86_64-pc-windows-msvc.zip`
- Descompacta e copia o `deno.exe`

**Coloque os três na mesma pasta juntamente com o `youtube_downloader.py` e o `youtube_downloader.spec`.**

> ⚠️ **Sem esses três arquivos, o programa não funciona!** Especialmente o Deno, que é usado pra vencer as novas travas do YouTube (SABR e PO Token).

---

## 📦 Gerando o Executável

**Não tem executável pronto pra baixar.** Você precisa compilar primeiro.

1. Baixa os **três arquivos obrigatórios** (`yt-dlp.exe`, `ffmpeg.exe`, `deno.exe`) e coloca na pasta raiz do projeto
2. Abre o CMD na pasta do projeto e roda:
   ```bash
   pyinstaller youtube_downloader.spec
   ```
3. O executável vai aparecer em **`dist/YouTube Downloader/`**
4. A pasta `build/` pode ignorar, é só lixo temporário da compilação
5. O `icon.ico` é opcional, só se quiser personalizar o ícone

---

## 🚀 Como Usar

1. **Cola a URL** do vídeo do YouTube
2. **Escolhe o Modo de Emulação** (deixa no `padrão` primeiro, só muda se der erro)
3. **Seleciona Vídeo ou Áudio**
   - **Vídeo**: Escolhe a resolução (1080p, 4K, etc)
   - **Áudio**: Escolhe a qualidade (320kbps) e o formato (MP3, FLAC, etc)
4. **Escolhe a pasta** onde vai salvar
5. **Clica em "Baixar"**

Pronto. Simples assim.

---

## 🔧 Resolvendo Problemas Comuns

### **Erro 403 (Acesso Negado)**
**Solução:** Troca o **Modo de Emulação** pra `android_vr` ou `ios` e tenta de novo.

### **Vídeo baixou mas tá sem som**
**Causa:** O `ffmpeg.exe` tá zoado ou não tá na pasta.  
**Solução:** Baixa uma versão **completa** do FFmpeg (link acima) e substitui.

### **"Dependências não encontradas"**
**Solução:** Confere se os três arquivos (`yt-dlp.exe`, `ffmpeg.exe`, `deno.exe`) tão na mesma pasta do programa.

### **YouTube mudou as regras de novo?**
Abre o CMD na pasta do programa e roda:
```bash
yt-dlp.exe -U
```
Isso atualiza o yt-dlp pra versão mais nova e resolve 99% dos problemas.

---

## 💡 Dicas Extras

- **Anti-Bot embutido**: O programa já limita a velocidade de download em 7MB/s e espera 1.5s entre requisições pra não parecer um robô.
- **Detecta duplicatas**: Se você já baixou aquele vídeo, o programa avisa antes.

---

## 🛠️ Pra Desenvolvedores

**Requer:**
- Python 3.6+
- PyInstaller (pra compilar)

**Rodar o código:**
```bash
python youtube_downloader.py
```

**Criar executável:**
```bash
pyinstaller youtube_downloader.spec
```

---

## 📧 Contato

**João Paulo**  
GitHub: [@Joao-paulo19](https://github.com/Joao-paulo19)  
LinkedIn: [joao-paul0](https://www.linkedin.com/in/joao-paul0/)  
Email: joaopaulomariaalvarenga@gmail.com

---

**Projeto:** [github.com/Joao-paulo19/youtube-downloader](https://github.com/Joao-paulo19/youtube-downloader)
