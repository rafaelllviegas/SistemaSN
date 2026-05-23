"""
Módulo de Licenciamento — Calculadora DAS
"""

import os, sys, platform, hashlib, json, threading, subprocess, tempfile
import customtkinter as ctk
import httpx

# ── Configuração ──────────────────────────────────────────────────────
API_URL      = "https://sistemasn-production.up.railway.app"
VERSAO_ATUAL = "1.1.2"
CHAVE_FILE   = os.path.join(os.path.expanduser("~"), ".das_licenca")

COR_BG      = "#F1F5F9"
COR_CARD    = "#FFFFFF"
COR_TEXTO   = "#1E293B"
COR_SUB     = "#64748B"
COR_AZUL    = "#2563EB"
COR_VERDE   = "#059669"
COR_ERRO    = "#DC2626"


# ── Machine ID ────────────────────────────────────────────────────────
def get_machine_id() -> str:
    raw = f"{platform.node()}-{platform.machine()}-{platform.processor()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


# ── Chave local ───────────────────────────────────────────────────────
def salvar_chave(chave: str):
    with open(CHAVE_FILE, "w") as f:
        json.dump({"chave": chave}, f)

def carregar_chave() -> str | None:
    try:
        with open(CHAVE_FILE) as f:
            return json.load(f).get("chave")
    except Exception:
        return None

def apagar_chave():
    try:
        os.remove(CHAVE_FILE)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════
class LicenseManager:

    def __init__(self):
        self.machine_id = get_machine_id()
        self.cliente    = None

    # ── Ponto de entrada ──────────────────────────────────────────────
    def verificar_na_abertura(self, root: ctk.CTk):
        chave_salva = carregar_chave()

        if chave_salva:
            ok, msg, cliente = self._validar_online(chave_salva)
            if ok:
                self.cliente = cliente
                self._verificar_update(root)
                return
            else:
                apagar_chave()
                self._tela_ativacao(root, erro=msg)
        else:
            self._tela_ativacao(root)

    # ── Validação ─────────────────────────────────────────────────────
    def _validar_online(self, chave: str) -> tuple[bool, str, str | None]:
        try:
            r = httpx.post(
                f"{API_URL}/validar",
                json={"chave": chave, "machine_id": self.machine_id},
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                return True, data["mensagem"], data["cliente"]
            else:
                return False, r.json().get("detail", "Erro desconhecido."), None
        except httpx.ConnectError:
            return False, "Sem conexão com o servidor.\nVerifique sua internet.", None
        except Exception as e:
            return False, f"Erro ao validar licença: {e}", None

    # ── Tela de ativação ──────────────────────────────────────────────
    def _tela_ativacao(self, root: ctk.CTk, erro: str = None):
        root.withdraw()

        win = ctk.CTkToplevel()
        win.title("Ativação — Calculadora DAS")
        win.geometry("460x380")
        win.configure(fg_color=COR_CARD)
        win.resizable(False, False)
        win.protocol("WM_DELETE_WINDOW", sys.exit)
        win.grab_set()
        win.focus_force()

        hdr = ctk.CTkFrame(win, fg_color="#1E3A5F", corner_radius=0, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="🔐  Ativação de Licença",
                     font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     text_color="white").pack(side="left", padx=20, pady=12)

        body = ctk.CTkFrame(win, fg_color=COR_CARD)
        body.pack(fill="both", expand=True, padx=32, pady=24)

        ctk.CTkLabel(body, text="Calculadora DAS — Simples Nacional",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=COR_TEXTO).pack(pady=(0, 4))

        ctk.CTkLabel(body, text="Digite sua chave de licença para continuar.",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=COR_SUB).pack(pady=(0, 20))

        entry = ctk.CTkEntry(
            body, placeholder_text="XXXX-XXXX-XXXX-XXXX",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color="#F8FAFC", border_color="#E2E8F0",
            text_color=COR_TEXTO, height=44,
            corner_radius=10, justify="center",
        )
        entry.pack(fill="x", pady=(0, 6))

        lbl_erro = ctk.CTkLabel(body, text=erro or "",
                                font=ctk.CTkFont("Segoe UI", 10),
                                text_color=COR_ERRO, wraplength=380)
        lbl_erro.pack(pady=(0, 16))

        def ativar():
            chave = entry.get().strip().upper()
            if len(chave) != 19:
                lbl_erro.configure(text="Formato inválido. Use: XXXX-XXXX-XXXX-XXXX")
                return
            btn.configure(state="disabled", text="Validando...")
            win.update()

            ok, msg, cliente = self._validar_online(chave)

            if ok:
                salvar_chave(chave)
                self.cliente = cliente
                win.destroy()
                root.deiconify()
                self._verificar_update(root)
            else:
                btn.configure(state="normal", text="Ativar")
                lbl_erro.configure(text=msg)

        btn = ctk.CTkButton(
            body, text="Ativar", command=ativar,
            fg_color=COR_AZUL, hover_color="#1D4ED8",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            corner_radius=10, height=42,
        )
        btn.pack(fill="x")
        entry.bind("<Return>", lambda e: ativar())

        ctk.CTkLabel(body, text="Não tem uma licença? Contate o suporte.",
                     font=ctk.CTkFont("Segoe UI", 9),
                     text_color=COR_SUB).pack(pady=(16, 0))

        win.wait_window()

    # ── Verificar update ──────────────────────────────────────────────
    def _verificar_update(self, root: ctk.CTk):
        def _check():
            try:
                r = httpx.get(f"{API_URL}/versao",
                              params={"versao_atual": VERSAO_ATUAL}, timeout=8)
                if r.status_code != 200:
                    return
                data = r.json()
                if not data["atualizado"]:
                    root.after(0, lambda: self._popup_update(root, data))
            except Exception:
                pass

        threading.Thread(target=_check, daemon=True).start()

    # ── Popup de update ───────────────────────────────────────────────
    def _popup_update(self, root: ctk.CTk, data: dict):
        win = ctk.CTkToplevel(root)
        win.title("Atualização disponível")
        win.geometry("440x300")
        win.configure(fg_color=COR_CARD)
        win.resizable(False, False)
        win.transient(root)
        win.grab_set()

        # Header verde
        hdr = ctk.CTkFrame(win, fg_color=COR_VERDE, corner_radius=0, height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=f"🆕  Nova versão disponível: {data['versao']}",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color="white").pack(side="left", padx=16, pady=12)

        body = ctk.CTkFrame(win, fg_color=COR_CARD)
        body.pack(fill="both", expand=True, padx=28, pady=20)

        ctk.CTkLabel(body,
                     text=f"Versão atual: {VERSAO_ATUAL}   →   Nova versão: {data['versao']}",
                     font=ctk.CTkFont("Segoe UI", 11, "bold"),
                     text_color=COR_TEXTO).pack(pady=(0, 6))

        if data.get("notas"):
            ctk.CTkLabel(body, text=data["notas"],
                         font=ctk.CTkFont("Segoe UI", 10),
                         text_color=COR_SUB, wraplength=370).pack(pady=(0, 12))

        # Barra de progresso (oculta até clicar Sim)
        lbl_prog = ctk.CTkLabel(body, text="",
                                font=ctk.CTkFont("Segoe UI", 10),
                                text_color=COR_SUB)
        lbl_prog.pack()

        barra = ctk.CTkProgressBar(body, width=360, height=12,
                                   corner_radius=6,
                                   fg_color="#E2E8F0",
                                   progress_color=COR_VERDE)
        barra.set(0)

        def iniciar_update():
            btn_sim.configure(state="disabled", text="Baixando...")
            btn_nao.configure(state="disabled")
            barra.pack(pady=(8, 0))
            lbl_prog.configure(text="Preparando atualização...")
            win.update()

            def _download():
                try:
                    url = data["url"]

                    # Descobre tamanho total
                    head = httpx.head(url, follow_redirects=True, timeout=10)
                    total = int(head.headers.get("content-length", 0))

                    # Salva na mesma pasta do executável atual
                    if hasattr(sys, "_MEIPASS"):
                        dest_dir = os.path.dirname(sys.executable)
                    else:
                        dest_dir = os.path.dirname(os.path.abspath(__file__))

                    installer_path = os.path.join(dest_dir, "_update_installer.exe")

                    baixado = 0
                    with httpx.stream("GET", url, follow_redirects=True, timeout=60) as resp:
                        with open(installer_path, "wb") as f:
                            for chunk in resp.iter_bytes(chunk_size=65536):
                                f.write(chunk)
                                baixado += len(chunk)
                                if total > 0:
                                    pct = baixado / total
                                    mb_baixado = baixado / 1_048_576
                                    mb_total   = total   / 1_048_576
                                    root.after(0, lambda p=pct, b=mb_baixado, t=mb_total: (
                                        barra.set(p),
                                        lbl_prog.configure(
                                            text=f"Baixando... {b:.1f} MB de {t:.1f} MB  ({p*100:.0f}%)"
                                        )
                                    ))

                    root.after(0, lambda: lbl_prog.configure(
                        text="✓ Download concluído. Iniciando instalação..."))
                    root.after(0, lambda: barra.set(1))
                    root.after(800, lambda: _instalar(installer_path))

                except Exception as e:
                    root.after(0, lambda: lbl_prog.configure(
                        text=f"✗ Erro: {e}", text_color=COR_ERRO))
                    root.after(0, lambda: btn_sim.configure(
                        state="normal", text="Tentar novamente"))
                    root.after(0, lambda: btn_nao.configure(state="normal"))

            def _instalar(installer_path):
                """
                Executa o instalador Inno Setup com flag /silent.
                O instalador vai: fechar o app atual → substituir o .exe → reabrir.
                """
                try:
                    subprocess.Popen(
                        [installer_path, "/silent", "/closeapplications", "/restartapplications"],
                        creationflags=subprocess.DETACHED_PROCESS
                            if sys.platform == "win32" else 0
                    )
                    root.after(500, root.destroy)
                    root.after(600, sys.exit)
                except Exception as e:
                    root.after(0, lambda: lbl_prog.configure(
                        text=f"✗ Erro ao instalar: {e}", text_color=COR_ERRO))

            threading.Thread(target=_download, daemon=True).start()

        btn_sim = ctk.CTkButton(
            body, text="✓  Sim, atualizar agora",
            command=iniciar_update,
            fg_color=COR_VERDE, hover_color="#047857",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            corner_radius=10, height=42,
        )
        btn_sim.pack(fill="x", pady=(12, 6))

        btn_nao = ctk.CTkButton(
            body, text="Agora não",
            command=win.destroy,
            fg_color="#E2E8F0", hover_color="#CBD5E1",
            text_color=COR_TEXTO,
            font=ctk.CTkFont("Segoe UI", 11),
            corner_radius=10, height=36,
        )
        btn_nao.pack(fill="x")