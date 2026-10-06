import os
import streamlit as st

# Configuração inicial da página Streamlit
st.set_page_config(
    page_title="Media Player Desktop",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core.library import (
    load_library,
    scan_directory,
    import_files,
    update_track_metadata,
    import_uploaded_files,
    open_folder_picker_dialog,
    save_custom_cover,
)
from core.playlist import (
    load_playlists,
    create_playlist,
    delete_playlist,
    rename_playlist,
    add_track_to_playlist,
    remove_track_from_playlist,
)
from core.player import AudioPlayer
from ui.components import (
    load_css,
    render_header,
    render_now_playing_panel,
    render_controls_bar,
)

# Carrega estilização CSS do Windows Media Player
CSS_FILE = os.path.join("assets", "style.css")
load_css(CSS_FILE)

# Inicialização do estado da sessão (st.session_state)
if "player" not in st.session_state:
    st.session_state.player = AudioPlayer()

if "library" not in st.session_state:
    st.session_state.library = load_library()

if "playlists" not in st.session_state:
    st.session_state.playlists = load_playlists()

player: AudioPlayer = st.session_state.player

# Callbacks para controles do player
def play_track(track):
    player.play(track)
    st.rerun()

def pause_audio():
    player.pause()
    st.rerun()

def resume_audio():
    player.resume()
    st.rerun()

def stop_audio():
    player.stop()
    st.rerun()

def prev_audio():
    player.prev_track()
    st.rerun()

def next_audio():
    player.next_track()
    st.rerun()

def seek_audio(pos):
    player.seek(pos)
    st.rerun()

def volume_audio(vol):
    player.set_volume(vol)
    st.rerun()

def toggle_shuffle():
    player.toggle_shuffle()
    st.rerun()

def toggle_repeat():
    player.toggle_repeat()
    st.rerun()

# -----------------------------------------------------------------------------
# MENU LATERAL DE NAVEGAÇÃO
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style='text-align: center; padding: 10px 0;'>
            <h2 style='color: #00e5ff; margin-bottom: 0;'>🎵 Media Player</h2>
            <p style='color: #8ab4f8; font-size: 0.85rem;'>Player de Áudio Desktop</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    menu = st.radio(
        "Navegação",
        ["🎧 Tocando Agora", "📚 Biblioteca de Mídias", "🎵 Playlists", "📁 Importar Áudios"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("### 📊 Status da Biblioteca")
    st.write(f"Total de Faixas: **{len(st.session_state.library)}**")
    st.write(f"Playlists Salvas: **{len(st.session_state.playlists)}**")

    if player.get_current_track():
        st.divider()
        st.markdown("### 🔊 Tocando")
        st.caption(player.get_current_track().get("title", ""))

# Renderiza o cabeçalho principal WMP
render_header()

# -----------------------------------------------------------------------------
# TAB 1: TOCANDO AGORA
# -----------------------------------------------------------------------------
if menu == "🎧 Tocando Agora":
    col_left, col_right = st.columns([1.2, 1.8])

    with col_left:
        current_tr = player.get_current_track()
        render_now_playing_panel(current_tr, is_playing=player.is_playing and not player.is_paused)

        if current_tr:
            with st.popover("🖼️ Alterar Capa desta Música", use_container_width=True):
                st.markdown(f"**Nova Capa para:** `{current_tr.get('title')}`")
                uploaded_cover = st.file_uploader(
                    "Selecione uma imagem de capa:",
                    type=["png", "jpg", "jpeg", "webp"],
                    key="now_playing_cover_uploader",
                )
                if st.button("💾 Salvar Nova Capa", key="save_now_playing_cover", use_container_width=True):
                    if uploaded_cover:
                        save_custom_cover(current_tr["id"], uploaded_cover)
                        st.session_state.library = load_library()
                        # Atualiza a faixa atual na fila
                        for item in player.queue:
                            if item["id"] == current_tr["id"]:
                                item["cover_path"] = os.path.join("storage", "covers", f"cover_{current_tr['id']}.png")
                        st.toast("Capa atualizada com sucesso! 🎨")
                        st.rerun()
                    else:
                        st.warning("Selecione uma imagem primeiro.")

    with col_right:
        st.markdown("<div class='wmp-card'>", unsafe_allow_html=True)
        st.subheader("📋 Fila de Reprodução Atual")

        if not player.queue:
            st.info("A fila de reprodução está vazia. Adicione ou selecione faixas na Biblioteca.")
        else:
            for idx, item in enumerate(player.queue):
                is_active = (idx == player.current_index)
                bg_color = "rgba(0, 180, 255, 0.2)" if is_active else "transparent"
                col_i1, col_i2, col_i3, col_i4 = st.columns([0.5, 4, 2, 1])

                with col_i1:
                    st.markdown(f"<p style='margin-top: 6px;'>{'▶' if is_active else str(idx+1)}</p>", unsafe_allow_html=True)
                with col_i2:
                    st.markdown(f"<p style='margin-top: 6px; font-weight: {'bold' if is_active else 'normal'}; color: {'#00e5ff' if is_active else '#ffffff'};'>{item.get('title')}</p>", unsafe_allow_html=True)
                with col_i3:
                    st.markdown(f"<p style='margin-top: 6px; color: #8ab4f8;'>{item.get('artist')}</p>", unsafe_allow_html=True)
                with col_i4:
                    if st.button("▶ Tocar", key=f"queue_play_{idx}"):
                        player.current_index = idx
                        player.play(item)
                        st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 2: BIBLIOTECA DE MÍDIAS
# -----------------------------------------------------------------------------
elif menu == "📚 Biblioteca de Mídias":
    st.markdown("<div class='wmp-card'>", unsafe_allow_html=True)
    st.subheader("📚 Biblioteca de Músicas")

    search_query = st.text_input("🔍 Buscar por título, artista ou álbum:", "")

    library = st.session_state.library
    filtered_lib = list(library)

    if search_query:
        sq = search_query.lower()
        filtered_lib = [
            t for t in filtered_lib
            if sq in t["title"].lower() or sq in t["artist"].lower() or sq in t["album"].lower()
        ]

    if not filtered_lib:
        st.warning("Nenhuma música encontrada na biblioteca local.")
    else:
        st.markdown(f"**Exibindo {len(filtered_lib)} de {len(library)} faixas**")

        # Botão para reproduzir todas na fila
        if st.button("▶ Reproduzir Toda a Biblioteca na Fila"):
            player.set_queue(filtered_lib, start_index=0)
            player.play(filtered_lib[0])
            st.rerun()

        st.divider()

        # Tabela de Músicas
        for idx, track in enumerate(filtered_lib):
            c_act, c_title, c_artist, c_album, c_dur, c_pl, c_edit = st.columns([1, 3.5, 2.5, 2, 1, 1.5, 1])

            with c_act:
                if st.button("▶ Play", key=f"lib_play_{track['id']}"):
                    player.set_queue(filtered_lib, start_index=idx)
                    player.play(track)
                    st.rerun()

            with c_title:
                st.markdown(f"**{track['title']}**")
            with c_artist:
                st.caption(track['artist'])
            with c_album:
                st.caption(track['album'])
            with c_dur:
                st.caption(track.get('duration_str', '00:00'))

            with c_pl:
                playlists = st.session_state.playlists
                if playlists:
                    pl_dict = {p["id"]: p for p in playlists}
                    selected_pl_id = st.selectbox(
                        "Playlist",
                        options=list(pl_dict.keys()),
                        format_func=lambda pid: pl_dict[pid]["name"],
                        key=f"pl_select_{track['id']}",
                        label_visibility="collapsed",
                    )
                    if st.button("+ Playlist", key=f"add_pl_{track['id']}"):
                        add_track_to_playlist(selected_pl_id, track["id"])
                        st.session_state.playlists = load_playlists()
                        st.toast(f"Adicionado à {pl_dict[selected_pl_id]['name']}!")

            with c_edit:
                with st.popover("✏️ Editar"):
                    st.markdown(f"**Editar Metadados e Capa: {track['title']}**")
                    uploaded_c = st.file_uploader(
                        "🖼️ Alterar Capa:",
                        type=["png", "jpg", "jpeg", "webp"],
                        key=f"edit_cover_{track['id']}",
                    )
                    new_t = st.text_input("Título", value=track["title"], key=f"edit_t_{track['id']}")
                    new_a = st.text_input("Artista", value=track["artist"], key=f"edit_a_{track['id']}")
                    new_al = st.text_input("Álbum", value=track["album"], key=f"edit_al_{track['id']}")
                    new_g = st.text_input("Gênero", value=track["genre"], key=f"edit_g_{track['id']}")
                    new_y = st.text_input("Ano", value=track["year"], key=f"edit_y_{track['id']}")

                    if st.button("Salvar Alterações", key=f"save_edit_{track['id']}"):
                        if uploaded_c:
                            save_custom_cover(track["id"], uploaded_c)
                        update_track_metadata(
                            track["id"],
                            {"title": new_t, "artist": new_a, "album": new_al, "genre": new_g, "year": new_y},
                        )
                        st.session_state.library = load_library()
                        st.toast("Metadados e capa atualizados com sucesso! 🎨")
                        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 3: PLAYLISTS
# -----------------------------------------------------------------------------
elif menu == "🎵 Playlists":
    st.markdown("<div class='wmp-card'>", unsafe_allow_html=True)
    st.subheader("🎵 Gerenciador de Playlists")

    # Criar nova playlist com st.form (atômico e confiável no Streamlit Cloud)
    with st.form("create_playlist_form", clear_on_submit=True):
        c_p1, c_p2 = st.columns([3, 1])
        with c_p1:
            new_pl_name = st.text_input(
                "Nome da Nova Playlist:",
                placeholder="Ex: Minhas Favoritas",
                label_visibility="collapsed",
            )
        with c_p2:
            submitted = st.form_submit_button("➕ Criar Playlist", use_container_width=True)

        if submitted:
            final_name = new_pl_name.strip() if new_pl_name and new_pl_name.strip() else "Nova Playlist"
            created = create_playlist(final_name)
            st.session_state.playlists = load_playlists()
            st.toast(f"Playlist '{created['name']}' criada com sucesso! 🎉")
            st.rerun()

    st.divider()

    playlists = st.session_state.playlists
    if not playlists:
        st.info("Nenhuma playlist cadastrada. Crie uma acima para organizar suas faixas.")
    else:
        pl_dict = {p["id"]: p for p in playlists}
        selected_pl_id = st.selectbox(
            "Selecione a Playlist:",
            options=list(pl_dict.keys()),
            format_func=lambda pid: f"{pl_dict[pid]['name']} ({len(pl_dict[pid]['track_ids'])} faixas)",
        )
        selected_pl = pl_dict[selected_pl_id]

        st.markdown(f"### Playlist: **{selected_pl['name']}** ({len(selected_pl['track_ids'])} músicas)")

        # Mapeia IDs para objetos de faixas da biblioteca
        lib_dict = {t["id"]: t for t in st.session_state.library}
        pl_tracks = [lib_dict[tid] for tid in selected_pl["track_ids"] if tid in lib_dict]

        col_pl_act1, col_pl_act2, col_pl_act3 = st.columns([2, 1, 1])
        with col_pl_act1:
            if st.button("▶ Reproduzir Playlist Inteira"):
                if pl_tracks:
                    player.set_queue(pl_tracks, start_index=0)
                    player.play(pl_tracks[0])
                    st.rerun()
                else:
                    st.warning("Esta playlist está vazia.")

        with col_pl_act2:
            with st.popover("✏️ Renomear"):
                r_name = st.text_input("Novo nome:", value=selected_pl["name"])
                if st.button("Confirmar Renomeação"):
                    rename_playlist(selected_pl["id"], r_name)
                    st.session_state.playlists = load_playlists()
                    st.rerun()

        with col_pl_act3:
            if st.button("🗑 Excluir Playlist"):
                delete_playlist(selected_pl["id"])
                st.session_state.playlists = load_playlists()
                st.rerun()

        st.markdown("#### Faixas da Playlist")
        if not pl_tracks:
            st.caption("Playlist sem faixas. Adicione faixas na aba Biblioteca de Mídias.")
        else:
            for idx, tr in enumerate(pl_tracks):
                col_pt1, col_pt2, col_pt3, col_pt4 = st.columns([0.5, 5, 2, 1])
                with col_pt1:
                    st.write(f"{idx+1}.")
                with col_pt2:
                    st.markdown(f"**{tr['title']}** - <span style='color:#8ab4f8'>{tr['artist']}</span>", unsafe_allow_html=True)
                with col_pt3:
                    st.caption(tr['album'])
                with col_pt4:
                    if st.button("❌ Remover", key=f"rm_pl_{selected_pl['id']}_{tr['id']}"):
                        remove_track_from_playlist(selected_pl["id"], tr["id"])
                        st.session_state.playlists = load_playlists()
                        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 4: IMPORTAR ÁUDIOS
# -----------------------------------------------------------------------------
elif menu == "📁 Importar Áudios":
    st.markdown("<div class='wmp-card'>", unsafe_allow_html=True)
    st.subheader("📁 Importar Músicas MP3")

    tab_upload, tab_folder = st.tabs(["🎵 Selecionar Arquivos MP3 (Explorador)", "📂 Escanear Pasta Inteira"])

    with tab_upload:
        st.markdown("Clique abaixo para abrir o **Explorador de Arquivos do Windows** e selecionar um ou vários arquivos `.mp3` do seu computador:")
        
        uploaded_files = st.file_uploader(
            "Selecione as músicas MP3:",
            type=["mp3"],
            accept_multiple_files=True,
            help="Abre o explorador de arquivos nativo do seu sistema",
        )

        if uploaded_files:
            if st.button(f"📥 Processar e Importar {len(uploaded_files)} Arquivo(s)", use_container_width=True):
                with st.spinner("Importando músicas e extraindo metadados/capas..."):
                    updated_lib = import_uploaded_files(uploaded_files)
                    st.session_state.library = updated_lib
                    st.success(f"Sucesso! {len(uploaded_files)} música(s) adicionada(s) à sua biblioteca.")
                    st.rerun()

    with tab_folder:
        st.markdown("Abra a janela do **Explorador de Arquivos do Windows** para selecionar a pasta com suas músicas:")

        if "selected_folder_path" not in st.session_state:
            st.session_state.selected_folder_path = ""

        c_f1, c_f2 = st.columns([3, 1])
        with c_f1:
            folder_path = st.text_input(
                "Caminho da Pasta:",
                value=st.session_state.selected_folder_path,
                placeholder="Clique no botão ao lado para escolher...",
                key="folder_path_input",
            )
        with c_f2:
            if st.button("📂 Escolher Pasta", use_container_width=True):
                chosen_folder = open_folder_picker_dialog()
                if chosen_folder:
                    st.session_state.selected_folder_path = chosen_folder
                    st.rerun()

        if st.button("🔍 Varrer e Importar Pasta", use_container_width=True):
            target_path = folder_path if folder_path else st.session_state.selected_folder_path
            if target_path and os.path.exists(target_path):
                with st.spinner("Escaneando arquivos MP3 e extraindo metadados ID3..."):
                    scanned_list = scan_directory(target_path)
                    st.session_state.library = scanned_list
                    st.success(f"Varredura concluída! Biblioteca atualizada com {len(scanned_list)} faixas.")
                    st.rerun()
            else:
                st.error("Por favor, selecione uma pasta válida.")

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# BARRA DE CONTROLES INFERIOR FLUTUANTE
# -----------------------------------------------------------------------------
def _on_play():
    if player.is_paused:
        player.resume()
    else:
        if not player.queue and st.session_state.get("library"):
            player.set_queue(st.session_state.library, start_index=0)
        player.play()
    st.rerun()

render_controls_bar(
    player=player,
    on_play=_on_play,
    on_pause=pause_audio,
    on_stop=stop_audio,
    on_prev=prev_audio,
    on_next=next_audio,
    on_seek=seek_audio,
    on_volume=volume_audio,
    on_shuffle=toggle_shuffle,
    on_repeat=toggle_repeat,
)
