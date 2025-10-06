import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

from backends.base_backend import ATBackend
from backends.serial_backend import SerialBackend
from backends.mock_backend import MockBackend

APP_TITLE = "AT Command Tester"
DEFAULT_BAUD = 115200
EOL = "\n"

class ATTesterApp(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.master.title(APP_TITLE)
        self.master.geometry("1000x680")
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)

        # Backends
        self.serial_backend = SerialBackend()
        self.mock_backend = MockBackend()
        self.backend: ATBackend = self.serial_backend

        self._build_ui()
        self._refresh_ports()

    # ---------- UI ----------
    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)

        # Demo toggle
        self.demo_var = tk.BooleanVar(value=False)
        demo_chk = ttk.Checkbutton(top, text="Modalità DEMO (senza seriale)", variable=self.demo_var, command=self._on_demo_toggle)
        demo_chk.pack(side=tk.LEFT, padx=(0,12))

        ttk.Label(top, text="Porta:").pack(side=tk.LEFT)
        self.port_var = tk.StringVar()
        self.port_cb = ttk.Combobox(top, textvariable=self.port_var, width=22, state="readonly")
        self.port_cb.pack(side=tk.LEFT, padx=(4,8))
        ttk.Button(top, text="Aggiorna porte", command=self._refresh_ports).pack(side=tk.LEFT)

        ttk.Label(top, text="Baud:").pack(side=tk.LEFT, padx=(12,0))
        self.baud_var = tk.IntVar(value=DEFAULT_BAUD)
        self.baud_cb = ttk.Combobox(top, textvariable=self.baud_var, width=10,
                                     values=[9600,19200,38400,57600,115200,230400,460800,921600], state="readonly")
        self.baud_cb.pack(side=tk.LEFT, padx=(4,12))

        self.connect_btn = ttk.Button(top, text="Connetti", command=self._toggle_connect)
        self.connect_btn.pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="Disconnesso")
        ttk.Label(top, textvariable=self.status_var).pack(side=tk.RIGHT)

        # Notebook tabs
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Interattivo
        self.tab_interactive = ttk.Frame(self.nb)
        self.nb.add(self.tab_interactive, text="Interattivo")
        self._build_interactive(self.tab_interactive)

        # Da file
        self.tab_batch = ttk.Frame(self.nb)
        self.nb.add(self.tab_batch, text="Da file")
        self._build_batch(self.tab_batch)

        self.pack(fill=tk.BOTH, expand=True)

    def _build_interactive(self, parent):
        self.txt = tk.Text(
            parent, wrap="word", height=25, undo=False,
            bg="black", fg="white",           # sfondo e testo di default
            insertbackground="white",         # colore del cursore
            highlightthickness=0, bd=0        # bordi “piatti” (facoltativo)
        )

        self.txt.pack(fill=tk.BOTH, expand=True)
        self._init_text_tags(self.txt)

        bottom = ttk.Frame(parent)
        bottom.pack(fill=tk.X, pady=6)
        ttk.Label(bottom, text="Comando:").pack(side=tk.LEFT)
        self.cmd_var = tk.StringVar(value="AT")
        self.entry = ttk.Entry(bottom, textvariable=self.cmd_var)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        self.entry.bind("<Return>", lambda e: self._on_send())
        self.send_btn = ttk.Button(bottom, text="Invia (Enter)", command=self._on_send)
        self.send_btn.pack(side=tk.LEFT)

    def _build_batch(self, parent):
        cfg = ttk.Frame(parent)
        cfg.pack(fill=tk.X)

        self.file_var = tk.StringVar()
        ttk.Label(cfg, text="File comandi:").grid(row=0, column=0, padx=4, pady=8, sticky="w")
        ttk.Entry(cfg, textvariable=self.file_var).grid(row=0, column=1, padx=4, pady=8, sticky="ew")
        ttk.Button(cfg, text="Sfoglia…", command=self._choose_file).grid(row=0, column=2, padx=4, pady=8)

        ttk.Label(cfg, text="Pausa tra comandi (ms):").grid(row=1, column=0, padx=4, pady=4, sticky="w")
        self.delay_var = tk.IntVar(value=250)
        ttk.Spinbox(cfg, from_=0, to=10000, increment=50, textvariable=self.delay_var, width=8).grid(row=1, column=1, sticky="w", padx=4)

        self.stop_flag = threading.Event()
        self.run_btn = ttk.Button(cfg, text="Esegui file", command=self._run_file)
        self.run_btn.grid(row=1, column=2, padx=4)
        cfg.columnconfigure(1, weight=1)

        self.txt_file = tk.Text(
            parent, wrap="word", height=25, undo=False,
            bg="black", fg="white",
            insertbackground="white",
            highlightthickness=0, bd=0
        )

        self.txt_file.pack(fill=tk.BOTH, expand=True, pady=(6,0))
        self._init_text_tags(self.txt_file)

    def _init_text_tags(self, widget):
        widget.tag_configure("time", foreground="#888888", background="#000000")
        widget.tag_configure("input", foreground="#FFFFFF", background="#000000")  # Input: bianco
        widget.tag_configure("output", foreground="#00AA00", background="#000000")                         # Output: verde
        widget.tag_configure("error", foreground="#FF0000", background="#000000", font=(None, 10, "bold")) # ERROR: rosso

    # ---------- Helpers ----------
    def _current_backend(self) -> ATBackend:
        return self.mock_backend if self.demo_var.get() else self.serial_backend

    def _refresh_ports(self):
        be = self._current_backend()
        ports = be.list_ports()
        self.port_cb["values"] = ports
        if ports and not self.port_var.get():
            self.port_var.set(ports[0])

    def _on_demo_toggle(self):
        if self._current_backend().is_connected():
            self._current_backend().disconnect()
        self.status_var.set("Disconnesso")
        self.connect_btn.config(text="Connetti")
        self._refresh_ports()

    def _toggle_connect(self):
        be = self._current_backend()
        if be.is_connected():
            be.disconnect()
            self.status_var.set("Disconnesso")
            self.connect_btn.config(text="Connetti")
            return
        port = self.port_var.get()
        if not port:
            messagebox.showwarning(APP_TITLE, "Seleziona una porta (o DEMO)")
            return
        baud = int(self.baud_var.get() or DEFAULT_BAUD)
        try:
            be.connect(port, baud)
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"Errore connessione: {e}")
            return
        mode = "DEMO" if self.demo_var.get() else f"{port} @ {baud}"
        self.status_var.set(f"Connesso a {mode}")
        self.connect_btn.config(text="Disconnetti")

    def _append(self, widget, text, tag=None):
        widget.configure(state=tk.NORMAL)
        if tag:
            widget.insert("end", text, tag)
        else:
            widget.insert("end", text)
        widget.see("end")

    def _stamp(self):
        from datetime import datetime
        return datetime.now().strftime("[%H:%M:%S]")

    def _log(self, widget, kind, text):
        ts = self._stamp() + "\n"
        self._append(widget, ts, "time")
        if kind == 'input':
            self._append(widget, "> " + text + "\n", "input")
        else:
            tag = "error" if "ERROR" in text else "output"
            self._append(widget, text if text.endswith("\n") else text + "\n", tag)
        # self._append(widget, "\n")

    # ---------- Interattivo ----------
    def _on_send(self):
        cmd = self.cmd_var.get().strip()
        if not cmd:
            return
        be = self._current_backend()
        if not be.is_connected():
            messagebox.showwarning(APP_TITLE, "Connetti prima (o abilita DEMO)")
            return
        self._log(self.txt, 'input', cmd)
        self.send_btn.config(state=tk.DISABLED)
        self.entry.config(state=tk.DISABLED)
        threading.Thread(target=self._send_thread, args=(cmd,), daemon=True).start()

    def _send_thread(self, cmd):
        be = self._current_backend()
        try:
            resp = be.send_and_read(cmd)
        except Exception as e:
            resp = f"ERROR: {e}"
        self.master.after(0, lambda: self._after_send(resp))

    def _after_send(self, resp):
        self._log(self.txt, 'output', resp.strip())
        self.send_btn.config(state=tk.NORMAL)
        self.entry.config(state=tk.NORMAL)
        self.entry.focus_set()

    # ---------- Da file ----------
    def _choose_file(self):
        path = filedialog.askopenfilename(title="Scegli file comandi", filetypes=[("Testo", "*.txt"), ("CSV", "*.csv"), ("Tutti", "*.*")])
        if path:
            self.file_var.set(path)

    def _run_file(self):
        be = self._current_backend()
        if not be.is_connected():
            messagebox.showwarning(APP_TITLE, "Connetti prima (o abilita DEMO)")
            return
        path = self.file_var.get().strip()
        if not path:
            messagebox.showwarning(APP_TITLE, "Seleziona un file di comandi")
            return
        if self.run_btn["text"] == "Interrompi":
            self.stop_flag.set()
            return
        self.stop_flag.clear()
        self.run_btn.config(text="Interrompi")
        threading.Thread(target=self._run_file_thread, daemon=True).start()

    def _parse_file(self, path):
        cmds = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if ',' in line:
                        cmd = line.split(',', 1)[0].strip()
                    else:
                        cmd = line
                    cmds.append(cmd)
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"Errore lettura file: {e}")
        return cmds

    def _run_file_thread(self):
        be = self._current_backend()
        path = self.file_var.get().strip()
        delay_ms = max(0, self.delay_var.get())
        cmds = self._parse_file(path)
        if not cmds:
            self.master.after(0, lambda: self._batch_done("Nessun comando trovato"))
            return
        self.master.after(0, lambda: self._log(self.txt_file, 'output', f"Esecuzione file: {path} ({len(cmds)} comandi)"))
        for i, cmd in enumerate(cmds, 1):
            if self.stop_flag.is_set():
                break
            self.master.after(0, lambda c=cmd: self._log(self.txt_file, 'input', c))
            try:
                resp = be.send_and_read(cmd)
            except Exception as e:
                resp = f"ERROR: {e}"
            self.master.after(0, lambda r=resp: self._log(self.txt_file, 'output', r.strip()))
            time.sleep(delay_ms / 1000.0)
        self.master.after(0, lambda: self._batch_done("Completato" if not self.stop_flag.is_set() else "Interrotto dall'utente"))

    def _batch_done(self, msg):
        self._log(self.txt_file, 'output', msg)
        self.run_btn.config(text="Esegui file")

    def _on_close(self):
        try:
            self.serial_backend.disconnect()
            self.mock_backend.disconnect()
        except Exception:
            pass
        self.master.destroy()


def main():
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    style = ttk.Style(root)
    if 'vista' in style.theme_names():
        style.theme_use('vista')
    elif 'clam' in style.theme_names():
        style.theme_use('clam')
    app = ATTesterApp(root)
    app.mainloop()


if __name__ == "__main__":
    main()
