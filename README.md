# Reprodutor Media Play

Aplicação de reprodução e gerenciamento de músicas desenvolvida em Python com Streamlit.

O sistema permite importar músicas, organizar uma biblioteca, criar playlists, visualizar capas de álbuns e controlar a reprodução de áudio.

## 🔗 URL

Site: https://media-play-desktop-fxudwyu8pcp2zsjafpha6n.streamlit.app/

## 👥 Dupla

- Adan Alexey
- Luiz Nicollas

## 🛠️ Stack

- **Python** — linguagem principal
- **Streamlit** — interface da aplicação
- **Pygame** — reprodução e controle de áudio
- **Mutagen** — leitura e edição de metadados ID3 dos arquivos MP3
- **Pillow** — processamento das capas dos álbuns
- **JSON** — armazenamento local da biblioteca e das playlists
- **Tkinter** — seleção de diretórios e arquivos

## ▶️ Como rodar

### 1. Clone o repositório

```bash
git clone https://github.com/lnicollas/dsai_ap1-Reprodutor-Media-Play.git
cd dsai_ap1-Reprodutor-Media-Play
```

### 2. Crie um ambiente virtual

No Windows:

```bash
python -m venv .venv
```

Ative o ambiente:

```bash
.venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Execute a aplicação

```bash
streamlit run app.py
```

Após a execução, o Streamlit disponibilizará a aplicação no navegador.

## 🤖 Ferramentas

O desenvolvimento foi realizado com auxílio do **Google Antigravity**, utilizado como agente de IA durante a implementação, análise de problemas e evolução do projeto.

Para organizar o desenvolvimento assistido por IA, foi utilizado o **OpenSpec**, framework utilizado para especificação, planejamento e organização das alterações antes da implementação.

O projeto possui o registro dos prompts utilizados em `prompts.md` e as especificações do OpenSpec estão disponíveis na pasta `openspec/`.

## 🧠  IA

A IA utilizada durante o desenvolvimento foi através do agente Google Antigravity.

O modelo foi utilizado como apoio para:

- criação da estrutura inicial do projeto;
- implementação das funcionalidades;
- identificação e correção de erros;
- organização da arquitetura;
- desenvolvimento da interface;
- implementação do sistema de reprodução de áudio;
- gerenciamento da biblioteca e playlists;
- resolução de problemas durante o desenvolvimento.

## 📁 Estrutura principal

```text
├── app.py                  # Aplicação principal
├── core/
│   ├── library.py          # Biblioteca e metadados das músicas
│   ├── player.py           # Reprodução e controles de áudio
│   └── playlist.py         # Gerenciamento de playlists
├── ui/
│   └── components.py       # Componentes da interface
├── assets/
│   └── style.css           # Estilos da aplicação
├── storage/
│   ├── media/              # Arquivos de áudio
│   ├── covers/             # Capas dos álbuns
│   ├── library.json        # Dados da biblioteca
│   └── playlists.json      # Dados das playlists
├── openspec/               # Especificações do projeto
├── prompts.md              # Registro dos prompts utilizados
├── requirements.txt        # Dependências Python
└── packages.txt            # Dependências de sistema
```
