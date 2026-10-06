import os
import base64
import streamlit as st
from typing import Optional, Dict, Any, Callable


from core.library import resolve_filepath, resolve_coverpath


def load_css(css_file: str):
    """Carrega o CSS customizado e injeta no Streamlit."""
    if os.path.exists(css_file):
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def image_to_base64(image_path: str) -> str:
    """Converte um arquivo de imagem local para string Base64."""
    resolved = resolve_coverpath(image_path)
    if not resolved or not os.path.exists(resolved):
        return ""
    try:
        with open(resolved, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
            ext = os.path.splitext(resolved)[1].lower().replace(".", "")
            if ext == "jpg":
                ext = "jpeg"
            return f"data:image/{ext};base64,{encoded}"
    except Exception:
        return ""


def render_header():
    """Renderiza a barra de cabecalho no estilo Windows Media Player."""
    st.markdown(
        """
        <div class="wmp-header-banner">
            <div class="wmp-header-title">
                <div class="wmp-header-logo"></div>
                Windows Media Player
            </div>
            <div>
                <span class="wmp-badge">EDITION 2026</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_now_playing_panel(track: Optional[Dict[str, Any]], is_playing: bool = False):
    """Renderiza a area de visualizacao e capa da musica em reproducao."""
    title = "Nenhuma faixa selecionada"
    artist = "Selecione uma musica da biblioteca"
    album = "-"
    genre = "-"
    cover_src = ""

    if track:
        title = track.get("title", "Titulo Desconhecido")
        artist = track.get("artist", "Artista Desconhecido")
        album = track.get("album", "Album Desconhecido")
        genre = track.get("genre", "Genero Desconhecido")
        cover_src = image_to_base64(track.get("cover_path", ""))

    if not cover_src:
        cover_src = image_to_base64(os.path.join("storage", "covers", "default_cover.png"))

    eq_bars = ""
    if is_playing:
        eq_bars = "<div class='wmp-equalizer'>" + "".join(
            f"<div class='wmp-eq-bar'></div>" for _ in range(8)
        ) + "</div>"
    else:
        eq_bars = "<div style='height:35px;'></div>"

    st.markdown(
        f"""
        <div class="wmp-card" style="text-align:center;">
            <div class="wmp-album-frame">
                <img src="{cover_src}" alt="Cover Art" />
            </div>
            {eq_bars}
            <h3 style="margin:5px 0 2px 0; color:#ffffff; font-size:1.25rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{title}</h3>
            <p style="margin:0 0 4px 0; color:#00b4ff; font-weight:600;">{artist}</p>
            <p style="margin:0; color:#8ab4f8; font-size:0.85rem;">Álbum: {album} | Gênero: {genre}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------
# Barra de progresso com auto-refresh (st.fragment run_every=1)
# ----------------------------------------------------------------------

@st.fragment(run_every=1)
def render_progress_bar():
    """Auto-atualiza a barra de progresso a cada 1 segundo."""
    player = st.session_state.get("player")
    if player is None:
        return

    if player.check_auto_next():
        st.rerun()
        return

    current_track = player.get_current_track()
    duration = current_track.get("duration", 0) if current_track else 0
    pos = player.get_position() if player.is_playing else 0.0
    pos = max(0.0, min(pos, duration)) if duration > 0 else 0.0

    mins, secs = int(pos) // 60, int(pos) % 60
    dur_mins, dur_secs = int(duration) // 60, int(duration) % 60
    progress_ratio = (pos / duration) if duration > 0 else 0.0

    col1, col2, col3 = st.columns([1, 10, 1])
    with col1:
        st.markdown(
            f"<p style='text-align:right; color:#00b4ff; font-weight:bold; margin:6px 0; font-size:0.9rem;'>"
            f"{mins:02d}:{secs:02d}</p>",
            unsafe_allow_html=True,
        )
    with col2:
        st.progress(progress_ratio)
    with col3:
        st.markdown(
            f"<p style='text-align:left; color:#8ab4f8; font-weight:bold; margin:6px 0; font-size:0.9rem;'>"
            f"{dur_mins:02d}:{dur_secs:02d}</p>",
            unsafe_allow_html=True,
        )


# ----------------------------------------------------------------------
# Barra de controles (botoes + volume + seek manual + player HTML5 st.audio)
# ----------------------------------------------------------------------

def render_controls_bar(
    player,
    on_play: Callable,
    on_pause: Callable,
    on_stop: Callable,
    on_prev: Callable,
    on_next: Callable,
    on_seek: Callable,
    on_volume: Callable,
    on_shuffle: Callable,
    on_repeat: Callable,
):
    """Renderiza a barra flutuante de transporte e controles com st.audio para o browser."""
    current_track = player.get_current_track()
    duration = current_track.get("duration", 0) if current_track else 0

    st.markdown("<div class='wmp-control-bar'>", unsafe_allow_html=True)

    # --- Player HTML5 de Áudio nativo do Streamlit para o navegador / Community Cloud ---
    if current_track:
        filepath = resolve_filepath(current_track.get("filepath", ""))
        if filepath and os.path.exists(filepath):
            try:
                with open(filepath, "rb") as f:
                    audio_bytes = f.read()
                st.audio(
                    audio_bytes,
                    format="audio/mp3",
                    autoplay=(player.is_playing and not player.is_paused),
                )
            except Exception as e:
                st.audio(
                    filepath,
                    format="audio/mp3",
                    autoplay=(player.is_playing and not player.is_paused),
                )

    # --- Barra de progresso animada ---
    render_progress_bar()

    # --- Seek manual (slider) ---
    pos_val = int(player.get_position()) if player.is_playing else 0
    max_dur = max(1, int(duration))
    pos_val = min(pos_val, max_dur)

    def _on_seek_change():
        new_pos = st.session_state.get("seek_slider", 0)
        if player and (player.is_playing or player.get_current_track()):
            on_seek(new_pos)

    def _on_volume_change():
        new_vol = st.session_state.get("volume_slider", 0.8)
        if player:
            on_volume(new_vol)

    st.session_state["seek_slider"] = pos_val
    st.session_state["volume_slider"] = float(player.volume)

    st.slider(
        "Posicao",
        min_value=0,
        max_value=max_dur,
        value=pos_val,
        label_visibility="collapsed",
        key="seek_slider",
        on_change=_on_seek_change,
    )

    # --- Botoes de controle ---
    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1.3, 1.5, 1, 1.2, 1, 1, 1, 2])

    with c1:
        shuf_label = "🔀 Shuffle ✔" if player.shuffle_mode else "🔀 Shuffle"
        if st.button(shuf_label, use_container_width=True, help="Alternar Shuffle"):
            on_shuffle()

    with c2:
        rep_icons = {"off": "🔁 Repeat: Off", "all": "🔁 Repeat: Tudo", "one": "🔂 Repeat: 1x"}
        if st.button(rep_icons.get(player.repeat_mode, "🔁 Repeat"), use_container_width=True):
            on_repeat()

    with c3:
        if st.button("⏮", use_container_width=True, help="Anterior"):
            on_prev()

    with c4:
        if player.is_playing and not player.is_paused:
            if st.button("⏸ Pausar", use_container_width=True):
                on_pause()
        else:
            if st.button("▶ Play", use_container_width=True):
                on_play()

    with c5:
        if st.button("⏹ Stop", use_container_width=True, help="Parar"):
            on_stop()

    with c6:
        if st.button("⏭", use_container_width=True, help="Proxima"):
            on_next()

    with c7:
        st.markdown(
            "<p style='text-align:center; color:#8ab4f8; margin-top:8px;'>🔊</p>",
            unsafe_allow_html=True,
        )

    with c8:
        st.slider(
            "Volume",
            min_value=0.0,
            max_value=1.0,
            value=float(player.volume),
            step=0.05,
            label_visibility="collapsed",
            key="volume_slider",
            on_change=_on_volume_change,
        )

    st.markdown("</div>", unsafe_allow_html=True)
