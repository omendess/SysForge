import tkinter as tk
import os
import sys
import threading
import time
import math

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def _get_video_path():
    """Resolve o caminho do video_splash.mp4 — funciona em .exe e em dev."""
    candidates = [
        # Frozen (PyInstaller): diretório do .exe
        os.path.join(os.path.dirname(sys.executable), "media", "logo m-labs.mp4") if getattr(sys, "frozen", False) else None,
        # Dev: raiz do projeto (cwd)
        os.path.join(os.getcwd(), "gui", "media", "logo m-labs.mp4"),
        # Relativo ao próprio arquivo .py
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "media", "logo m-labs.mp4"),
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return None


class SplashScreen(tk.Toplevel):
    """
    Tela de carregamento com vídeo MP4 (via OpenCV + Pillow).
    Caso o vídeo não esteja disponível, exibe uma animação de fallback.
    """

    MAX_DURATION_MS = 12000  # Tempo máximo ajustado para o vídeo de 10s tocar inteiro
    FALLBACK_CLOSE_MS = 3500 # Duração do fallback animado

    def __init__(self, master, on_ready_callback):
        """
        Parameters
        ----------
        master : tk.Tk (root oculto)
        on_ready_callback : callable — chamado após a splash fechar para abrir a janela principal
        """
        super().__init__(master)
        self._on_ready = on_ready_callback
        self._video_path = _get_video_path()
        self._cap = None
        self._running = True
        self._after_id = None
        self._frame_count = 0

        # ── Janela sem bordas, centralizada ───────────────────────────────
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        W, H = 800, 450
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - W) // 2
        y = (sh - H) // 2
        self.geometry(f"{W}x{H}+{x}+{y}")
        self.configure(bg="#0F172A")

        self._W = W
        self._H = H

        if self._video_path and CV2_AVAILABLE and PIL_AVAILABLE:
            self._setup_video_mode()
        else:
            self._setup_fallback_mode()

    # ─────────────────────────────────────────────────────────────────────
    #  MODO VÍDEO
    # ─────────────────────────────────────────────────────────────────────
    def _setup_video_mode(self):
        self._cap = cv2.VideoCapture(self._video_path)
        fps = self._cap.get(cv2.CAP_PROP_FPS) or 30
        self._frame_delay_ms = max(16, int(1000 / fps))

        self._lbl = tk.Label(self, bg="#0F172A", bd=0, highlightthickness=0)
        self._lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Timeout de segurança
        self._deadline_id = self.after(self.MAX_DURATION_MS, self._finish)
        self._play_frame()

    def _play_frame(self):
        if not self._running:
            return
        ret, frame = self._cap.read()
        if not ret:
            # Vídeo acabou
            self._finish()
            return

        # Redimensiona mantendo proporção
        fh, fw = frame.shape[:2]
        scale = min(self._W / fw, self._H / fh)
        nw, nh = int(fw * scale), int(fh * scale)
        frame = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_AREA)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        img = Image.fromarray(frame)
        photo = ImageTk.PhotoImage(img)
        self._lbl.configure(image=photo)
        self._lbl._photo_ref = photo   # evita GC

        self._frame_count += 1
        self._after_id = self.after(self._frame_delay_ms, self._play_frame)

    # ─────────────────────────────────────────────────────────────────────
    #  MODO FALLBACK (Canvas animado)
    # ─────────────────────────────────────────────────────────────────────
    def _setup_fallback_mode(self):
        W, H = self._W, self._H

        self._canvas = tk.Canvas(self, width=W, height=H, bg="#0F172A",
                                  highlightthickness=0, bd=0)
        self._canvas.place(x=0, y=0)

        # Texto
        self._canvas.create_text(W // 2, H // 2 - 50,
                                   text="⚒  SysForge",
                                   font=("Segoe UI", 38, "bold"),
                                   fill="#3B82F6")
        self._canvas.create_text(W // 2, H // 2 + 5,
                                   text="Motor de Implantação",
                                   font=("Segoe UI", 14),
                                   fill="#64748B")

        # Barra de progresso animada
        self._prog_bg = self._canvas.create_rectangle(
            W // 2 - 180, H // 2 + 60, W // 2 + 180, H // 2 + 75,
            fill="#1E293B", outline="#334155", width=1
        )
        self._prog_bar = self._canvas.create_rectangle(
            W // 2 - 180, H // 2 + 60, W // 2 - 180, H // 2 + 75,
            fill="#3B82F6", outline=""
        )
        self._prog_val = 0.0
        self._anim_step = 0

        self._deadline_id = self.after(self.FALLBACK_CLOSE_MS, self._finish)
        self._animate_fallback()

    def _animate_fallback(self):
        if not self._running:
            return
        W, H = self._W, self._H
        self._anim_step += 1
        t = self._anim_step / 60.0

        # Progresso suavizado (ease-out)
        self._prog_val = min(1.0, t / (self.FALLBACK_CLOSE_MS / 1000.0))
        x0 = W // 2 - 180
        x1 = x0 + int(360 * self._prog_val)
        self._canvas.coords(self._prog_bar,
                             x0, H // 2 + 60,
                             x1, H // 2 + 75)

        # Pulso de cor
        pulse = int(127 + 127 * math.sin(t * 3))
        r = 59 + (pulse * (80 - 59) // 255)
        g = 130
        b = 246
        color = f"#{min(255,r):02x}{min(255,g):02x}{min(255,b):02x}"
        self._canvas.itemconfig(self._prog_bar, fill=color)

        self._after_id = self.after(16, self._animate_fallback)

    # ─────────────────────────────────────────────────────────────────────
    #  FINALIZAÇÃO
    # ─────────────────────────────────────────────────────────────────────
    def _finish(self):
        if not self._running:
            return
        self._running = False

        # Cancela callbacks pendentes
        if self._after_id:
            self.after_cancel(self._after_id)
        try:
            self.after_cancel(self._deadline_id)
        except Exception:
            pass

        if self._cap:
            self._cap.release()

        self.destroy()
        if self._on_ready:
            self._on_ready()
