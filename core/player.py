import os
import random
import time
import threading
import queue
from typing import List, Dict, Any, Optional

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class _PygameThread(threading.Thread):
    """Thread dedicada e singleton para todas as operacoes do pygame.mixer.
    Resolve o problema de thread-safety no Windows."""

    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None or not cls._instance.is_alive():
                inst = cls()
                inst.start()
                # Aguarda inicializacao
                time.sleep(0.3)
                cls._instance = inst
            return cls._instance

    def __init__(self):
        super().__init__(daemon=True, name="pygame-audio-thread")
        self._cmd_queue: queue.Queue = queue.Queue()
        self._result_queue: queue.Queue = queue.Queue()
        self.initialized: bool = False

    def run(self):
        """Loop principal — todas as chamadas pygame rodam aqui."""
        if not PYGAME_AVAILABLE:
            return
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            self.initialized = True
        except Exception as e:
            print(f"[PygameThread] Falha ao inicializar mixer: {e}")
            return

        while True:
            try:
                cmd = self._cmd_queue.get(timeout=0.5)
                if cmd is None:
                    break
                try:
                    result = self._dispatch(cmd)
                    self._result_queue.put({"ok": True, "result": result})
                except Exception as e:
                    self._result_queue.put({"ok": False, "error": str(e)})
            except queue.Empty:
                pass

    def _dispatch(self, cmd: dict):
        action = cmd["action"]
        if action == "play":
            pygame.mixer.music.load(cmd["filepath"])
            pygame.mixer.music.set_volume(cmd.get("volume", 0.8))
            pygame.mixer.music.play(start=cmd.get("start", 0.0))
            return True
        elif action == "pause":
            pygame.mixer.music.pause()
            return True
        elif action == "unpause":
            pygame.mixer.music.unpause()
            return True
        elif action == "stop":
            pygame.mixer.music.stop()
            return True
        elif action == "set_volume":
            pygame.mixer.music.set_volume(cmd["volume"])
            return True
        elif action == "get_busy":
            return pygame.mixer.music.get_busy()
        return None

    def send(self, action: str, **kwargs) -> Any:
        """Envia um comando e espera retorno (timeout 3s)."""
        if not self.initialized:
            return None
        self._cmd_queue.put({"action": action, **kwargs})
        try:
            res = self._result_queue.get(timeout=3.0)
            return res.get("result")
        except queue.Empty:
            print(f"[PygameThread] Timeout na acao: {action}")
            return None


class AudioPlayer:
    def __init__(self):
        self.queue: List[Dict[str, Any]] = []
        self.original_queue: List[Dict[str, Any]] = []
        self.current_index: int = -1
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.volume: float = 0.8
        self.repeat_mode: str = "off"   # "off" | "all" | "one"
        self.shuffle_mode: bool = False

        # Controle de posicao
        self._play_start_time: float = 0.0
        self._play_start_pos: float = 0.0
        self._paused_at_pos: float = 0.0

        self._thread: Optional[_PygameThread] = (
            _PygameThread.get_instance() if PYGAME_AVAILABLE else None
        )

    # ------------------------------------------------------------------
    # Utilitarios internos
    # ------------------------------------------------------------------

    def _send(self, action: str, **kwargs) -> Any:
        if self._thread and self._thread.initialized:
            return self._thread.send(action, **kwargs)
        return None

    def get_current_track(self) -> Optional[Dict[str, Any]]:
        if 0 <= self.current_index < len(self.queue):
            return self.queue[self.current_index]
        return None

    # ------------------------------------------------------------------
    # Fila
    # ------------------------------------------------------------------

    def set_queue(self, tracks: List[Dict[str, Any]], start_index: int = 0):
        self.original_queue = list(tracks)
        self.queue = list(tracks)
        if self.shuffle_mode:
            random.shuffle(self.queue)
            self.current_index = 0
        else:
            self.current_index = (
                start_index if 0 <= start_index < len(tracks) else 0
            )

    # ------------------------------------------------------------------
    # Controles de reproducao
    # ------------------------------------------------------------------

    def play(self, track: Optional[Dict[str, Any]] = None, start_pos: float = 0.0) -> bool:
        from core.library import resolve_filepath

        if track:
            filepath = resolve_filepath(track.get("filepath", ""))
            track["filepath"] = filepath
            found = False
            for idx, item in enumerate(self.queue):
                item_path = resolve_filepath(item.get("filepath", ""))
                item["filepath"] = item_path
                if item_path == filepath:
                    self.current_index = idx
                    found = True
                    break
            if not found:
                self.queue.insert(0, track)
                self.current_index = 0

        target = self.get_current_track()
        if not target:
            return False

        resolved_path = resolve_filepath(target.get("filepath", ""))
        if not os.path.exists(resolved_path):
            return False

        target["filepath"] = resolved_path

        # Tenta enviar para o Pygame local se o mixer estiver inicializado
        self._send(
            "play",
            filepath=resolved_path,
            volume=self.volume,
            start=start_pos,
        )

        self.is_playing = True
        self.is_paused = False
        self._play_start_time = time.time()
        self._play_start_pos = start_pos
        self._paused_at_pos = start_pos
        return True

    def pause(self):
        """Pausa a reproducao — chama pygame na thread correta."""
        self._paused_at_pos = self.get_position()
        self._send("pause")
        self.is_paused = True

    def resume(self):
        """Retoma a reproducao pausada."""
        self._send("unpause")
        self.is_paused = False
        self._play_start_time = time.time()
        self._play_start_pos = self._paused_at_pos

    def stop(self):
        """Para completamente a reproducao."""
        self._send("stop")
        self.is_playing = False
        self.is_paused = False
        self._play_start_pos = 0.0
        self._paused_at_pos = 0.0

    def seek(self, position_seconds: float):
        """Vai para uma posicao especifica em segundos."""
        track = self.get_current_track()
        if track:
            self.play(track, start_pos=position_seconds)

    def set_volume(self, volume_level: float):
        self.volume = max(0.0, min(1.0, volume_level))
        self._send("set_volume", volume=self.volume)

    # ------------------------------------------------------------------
    # Posicao atual
    # ------------------------------------------------------------------

    def check_auto_next(self) -> bool:
        """Verifica se a musica atual terminou e avanca para a proxima se necessario."""
        if self.is_playing and not self.is_paused:
            track = self.get_current_track()
            if track:
                duration = track.get("duration", 0)
                pos = self.get_position()
                if duration > 0 and pos >= duration:
                    self.next_track()
                    return True
        return False

    def get_position(self) -> float:
        """Retorna a posicao atual de reproducao em segundos."""
        if not self.is_playing:
            return 0.0
        if self.is_paused:
            return self._paused_at_pos
        elapsed = time.time() - self._play_start_time
        return self._play_start_pos + elapsed

    # ------------------------------------------------------------------
    # Navegacao
    # ------------------------------------------------------------------

    def next_track(self) -> Optional[Dict[str, Any]]:
        if not self.queue:
            return None
        if self.repeat_mode == "one":
            track = self.get_current_track()
            if track:
                self.play(track)
            return track
        if self.current_index + 1 < len(self.queue):
            self.current_index += 1
        elif self.repeat_mode == "all":
            self.current_index = 0
        else:
            self.stop()
            return None
        track = self.get_current_track()
        if track:
            self.play(track)
        return track

    def prev_track(self) -> Optional[Dict[str, Any]]:
        if not self.queue:
            return None
        if self.get_position() > 3.0:
            track = self.get_current_track()
            if track:
                self.play(track)
            return track
        if self.current_index - 1 >= 0:
            self.current_index -= 1
        elif self.repeat_mode == "all":
            self.current_index = len(self.queue) - 1
        else:
            self.current_index = 0
        track = self.get_current_track()
        if track:
            self.play(track)
        return track

    # ------------------------------------------------------------------
    # Modos
    # ------------------------------------------------------------------

    def toggle_shuffle(self) -> bool:
        self.shuffle_mode = not self.shuffle_mode
        current = self.get_current_track()
        self.queue = list(self.original_queue)
        if self.shuffle_mode:
            random.shuffle(self.queue)
            if current and current in self.queue:
                self.queue.remove(current)
                self.queue.insert(0, current)
            self.current_index = 0
        else:
            if current and current in self.queue:
                self.current_index = self.queue.index(current)
            else:
                self.current_index = 0
        return self.shuffle_mode

    def toggle_repeat(self) -> str:
        modes = ["off", "all", "one"]
        self.repeat_mode = modes[(modes.index(self.repeat_mode) + 1) % len(modes)]
        return self.repeat_mode
