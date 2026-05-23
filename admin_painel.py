import customtkinter as ctk
import httpx
import threading
from datetime import datetime

# ── Configuração ──────────────────────────────────────────────────────
API_URL      = "https://sistemasn-production.up.railway.app"
ADMIN_SECRET = "$$5e9k2h0n$$Abc123"  # ← seu ADMIN_SECRET

# ── Tema ─────────────────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

COR_BG       = "#F1F5F9"
COR_CARD     = "#FFFFFF"
COR_CARD2    = "#F8FAFC"
COR_PRIMARIA = "#2563EB"
COR_VERDE    = "#059669"
COR_VERMELHO = "#DC2626"
COR_AMARELO  = "#D97706"
COR_TEXTO    = "#1E293B"
COR_SUB      = "#64748B"
COR_BORDA    = "#E2E8F0"
COR_HEADER   = "#1E3A5F"


def api(method, endpoint, **kwargs):
    return httpx.request(
        method, f"{API_URL}{endpoint}",
        headers={"x-admin-secret": ADMIN_SECRET},
        timeout=12,
        **kwargs,
    )


class PainelAdmin(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Painel Admin — Calculadora DAS")
        self.geometry("900x700")
        self.configure(fg_color=COR_BG)
        self.resizable(True, True)
        self._build()
        self._carregar_clientes()

    # ── Layout ────────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=COR_HEADER, corner_radius=0, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text="🔑  Painel Admin — Gerenciar Licenças",
            font=ctk.CTkFont("Segoe UI", 15, "bold"),
            text_color="white",
        ).pack(side="left", padx=20, pady=14)

        scroll = ctk.CTkScrollableFrame(self, fg_color=COR_BG)
        scroll.pack(fill="both", expand=True)

        self._card_gerar(scroll)
        self._card_revogar(scroll)
        self._card_clientes(scroll)

    # ── Card: Gerar licença ───────────────────────────────────────────
    def _card_gerar(self, parent):
        body = self._card(parent, "✚  GERAR NOVA LICENÇA", COR_VERDE)
        body.columnconfigure((0, 1, 2, 3), weight=1)

        campos = ["NOME DO CLIENTE", "E-MAIL", "Nº DE MÁQUINAS", "DIAS DE VALIDADE"]
        defaults = ["", "", "1", "365"]
        self.g_entries = []

        for i, (label, default) in enumerate(zip(campos, defaults)):
            ctk.CTkLabel(body, text=label,
                         font=ctk.CTkFont("Segoe UI", 9, "bold"),
                         text_color=COR_SUB).grid(row=0, column=i, padx=8, pady=(10,2), sticky="w")
            e = ctk.CTkEntry(body, font=ctk.CTkFont("Segoe UI", 11),
                             fg_color=COR_CARD2, border_color=COR_BORDA,
                             text_color=COR_TEXTO, corner_radius=10, height=38)
            e.insert(0, default)
            e.grid(row=1, column=i, padx=8, pady=(0,10), sticky="ew")
            self.g_entries.append(e)

        self.lbl_chave = ctk.CTkLabel(body, text="",
                                       font=ctk.CTkFont("Segoe UI", 13, "bold"),
                                       text_color=COR_VERDE)
        self.lbl_chave.grid(row=2, column=0, columnspan=3, padx=8, sticky="w")

        ctk.CTkButton(
            body, text="Gerar Chave", command=self._gerar,
            fg_color=COR_VERDE, hover_color="#047857",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            corner_radius=10, height=38, width=140,
        ).grid(row=2, column=3, padx=8, pady=(0,10), sticky="e")

    # ── Card: Revogar/Reativar ────────────────────────────────────────
    def _card_revogar(self, parent):
        body = self._card(parent, "⚙  GERENCIAR CHAVE", COR_AMARELO)
        body.columnconfigure(0, weight=1)
        body.columnconfigure((1, 2), weight=0)

        ctk.CTkLabel(body, text="CHAVE DE LICENÇA",
                     font=ctk.CTkFont("Segoe UI", 9, "bold"),
                     text_color=COR_SUB).grid(row=0, column=0, padx=8, pady=(10,2), sticky="w")

        self.e_chave_mgmt = ctk.CTkEntry(
            body, placeholder_text="XXXX-XXXX-XXXX-XXXX",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color=COR_CARD2, border_color=COR_BORDA,
            text_color=COR_TEXTO, corner_radius=10, height=38,
        )
        self.e_chave_mgmt.grid(row=1, column=0, padx=8, pady=(0,10), sticky="ew")

        ctk.CTkButton(
            body, text="Revogar", command=self._revogar,
            fg_color=COR_VERMELHO, hover_color="#B91C1C",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            corner_radius=10, height=38, width=120,
        ).grid(row=1, column=1, padx=(0,8), pady=(0,10))

        ctk.CTkButton(
            body, text="Reativar", command=self._reativar,
            fg_color=COR_VERDE, hover_color="#047857",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            corner_radius=10, height=38, width=120,
        ).grid(row=1, column=2, padx=(0,8), pady=(0,10))

        self.lbl_mgmt = ctk.CTkLabel(body, text="",
                                      font=ctk.CTkFont("Segoe UI", 10),
                                      text_color=COR_SUB)
        self.lbl_mgmt.grid(row=2, column=0, columnspan=3, padx=8, pady=(0,8), sticky="w")

    # ── Card: Lista de clientes ───────────────────────────────────────
    def _card_clientes(self, parent):
        body = self._card(parent, "👥  CLIENTES CADASTRADOS", COR_PRIMARIA)

        # Cabeçalho
        hdr = ctk.CTkFrame(body, fg_color=COR_CARD2, corner_radius=10, height=32)
        hdr.pack(fill="x", pady=(0,4))
        hdr.pack_propagate(False)
        inner = ctk.CTkFrame(hdr, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=8)
        for txt, w in [("Cliente", 180), ("E-mail", 200), ("Chave", 160), ("Status", 80), ("Expira", 130), ("Último acesso", 140)]:
            ctk.CTkLabel(inner, text=txt, width=w,
                         font=ctk.CTkFont("Segoe UI", 9, "bold"),
                         text_color=COR_SUB, anchor="w").pack(side="left")

        # Frame das linhas (scrollable)
        self.frame_linhas = ctk.CTkFrame(body, fg_color="transparent")
        self.frame_linhas.pack(fill="both", expand=True)

        # Botão atualizar
        ctk.CTkButton(
            body, text="↻  Atualizar lista", command=self._carregar_clientes,
            fg_color=COR_PRIMARIA, hover_color="#1D4ED8",
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
            corner_radius=8, height=32, width=140,
        ).pack(anchor="e", pady=(8,0))

        self.lbl_status_lista = ctk.CTkLabel(body, text="Carregando...",
                                              font=ctk.CTkFont("Segoe UI", 10),
                                              text_color=COR_SUB)
        self.lbl_status_lista.pack(anchor="w")

    # ── Helpers UI ────────────────────────────────────────────────────
    def _card(self, parent, titulo, cor):
        outer = ctk.CTkFrame(parent, fg_color=COR_CARD, corner_radius=16)
        outer.pack(fill="x", padx=20, pady=(16,0))
        hdr = ctk.CTkFrame(outer, fg_color=cor, corner_radius=12, height=34)
        hdr.pack(fill="x", padx=2, pady=(2,0))
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=titulo,
                     font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color="white").pack(side="left", padx=14)
        body = ctk.CTkFrame(outer, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=(6,12))
        return body

    def _toast(self, label, msg, cor):
        label.configure(text=msg, text_color=cor)
        self.after(4000, lambda: label.configure(text=""))

    # ── Ações ─────────────────────────────────────────────────────────
    def _gerar(self):
        nome  = self.g_entries[0].get().strip()
        email = self.g_entries[1].get().strip()
        maq   = self.g_entries[2].get().strip()
        dias  = self.g_entries[3].get().strip()

        if not nome or not email:
            self._toast(self.lbl_chave, "⚠ Preencha nome e e-mail.", COR_AMARELO)
            return

        self.lbl_chave.configure(text="Gerando...", text_color=COR_SUB)

        def _req():
            try:
                r = api("POST", "/admin/gerar", json={
                    "nome_cliente":  nome,
                    "email":         email,
                    "max_maquinas":  int(maq) if maq.isdigit() else 1,
                    "dias_validade": int(dias) if dias.isdigit() else 365,
                })
                if r.status_code == 200:
                    chave = r.json()["chave"]
                    self.after(0, lambda: self.lbl_chave.configure(
                        text=f"✓  Chave gerada:  {chave}", text_color=COR_VERDE))
                    self.after(0, self._carregar_clientes)
                else:
                    msg = r.json().get("detail", "Erro desconhecido.")
                    self.after(0, lambda: self._toast(self.lbl_chave, f"✗ {msg}", COR_VERMELHO))
            except Exception as e:
                self.after(0, lambda: self._toast(self.lbl_chave, f"✗ Erro: {e}", COR_VERMELHO))

        threading.Thread(target=_req, daemon=True).start()

    def _revogar(self):
        chave = self.e_chave_mgmt.get().strip().upper()
        if len(chave) != 19:
            self._toast(self.lbl_mgmt, "⚠ Chave inválida.", COR_AMARELO); return

        def _req():
            try:
                r = api("POST", "/admin/revogar", json={"chave": chave})
                msg = r.json().get("mensagem") or r.json().get("detail", "Erro.")
                cor = COR_VERDE if r.status_code == 200 else COR_VERMELHO
                self.after(0, lambda: self._toast(self.lbl_mgmt, msg, cor))
                if r.status_code == 200:
                    self.after(0, self._carregar_clientes)
            except Exception as e:
                self.after(0, lambda: self._toast(self.lbl_mgmt, f"Erro: {e}", COR_VERMELHO))

        threading.Thread(target=_req, daemon=True).start()

    def _reativar(self):
        chave = self.e_chave_mgmt.get().strip().upper()
        if len(chave) != 19:
            self._toast(self.lbl_mgmt, "⚠ Chave inválida.", COR_AMARELO); return

        def _req():
            try:
                r = api("POST", "/admin/reativar", json={"chave": chave})
                msg = r.json().get("mensagem") or r.json().get("detail", "Erro.")
                cor = COR_VERDE if r.status_code == 200 else COR_VERMELHO
                self.after(0, lambda: self._toast(self.lbl_mgmt, msg, cor))
                if r.status_code == 200:
                    self.after(0, self._carregar_clientes)
            except Exception as e:
                self.after(0, lambda: self._toast(self.lbl_mgmt, f"Erro: {e}", COR_VERMELHO))

        threading.Thread(target=_req, daemon=True).start()

    def _carregar_clientes(self):
        self.lbl_status_lista.configure(text="Carregando...", text_color=COR_SUB)

        def _req():
            try:
                r = api("GET", "/admin/clientes")
                if r.status_code == 200:
                    clientes = r.json()
                    self.after(0, lambda: self._renderizar_clientes(clientes))
                else:
                    self.after(0, lambda: self.lbl_status_lista.configure(
                        text="Erro ao carregar.", text_color=COR_VERMELHO))
            except Exception as e:
                self.after(0, lambda: self.lbl_status_lista.configure(
                    text=f"Sem conexão: {e}", text_color=COR_VERMELHO))

        threading.Thread(target=_req, daemon=True).start()

    def _renderizar_clientes(self, clientes):
        for w in self.frame_linhas.winfo_children():
            w.destroy()

        STATUS_COR = {"ativa": COR_VERDE, "revogada": COR_VERMELHO, "expirada": COR_AMARELO}

        for i, c in enumerate(clientes):
            cor_bg = COR_CARD if i % 2 == 0 else COR_CARD2
            row = ctk.CTkFrame(self.frame_linhas, fg_color=cor_bg, corner_radius=8, height=30)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=8)

            expira = c.get("expira_em", "—") or "Sem expiração"
            if expira and expira != "Sem expiração":
                try:
                    expira = datetime.fromisoformat(expira.replace("Z","+00:00")).strftime("%d/%m/%Y")
                except Exception:
                    pass

            ultimo = c.get("ultimo_acesso") or "—"
            if ultimo != "—":
                try:
                    ultimo = datetime.fromisoformat(ultimo.replace("Z","+00:00")).strftime("%d/%m/%Y %H:%M")
                except Exception:
                    pass

            status = c.get("status", "—")
            cor_status = STATUS_COR.get(status, COR_SUB)

            dados = [
                (c.get("nome_cliente","—"), 180, COR_TEXTO),
                (c.get("email","—"),        200, COR_SUB),
                (c.get("chave","—"),        160, COR_PRIMARIA),
                (status,                    80,  cor_status),
                (expira,                    130, COR_SUB),
                (ultimo,                    140, COR_SUB),
            ]

            for txt, w, cor in dados:
                ctk.CTkLabel(inner, text=txt, width=w,
                             font=ctk.CTkFont("Segoe UI", 10),
                             text_color=cor, anchor="w").pack(side="left")

        total = len(clientes)
        ativos = sum(1 for c in clientes if c.get("status") == "ativa")
        self.lbl_status_lista.configure(
            text=f"{total} cliente(s) — {ativos} licença(s) ativa(s)",
            text_color=COR_SUB,
        )


if __name__ == "__main__":
    PainelAdmin().mainloop()