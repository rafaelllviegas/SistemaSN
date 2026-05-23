import os
import sys
import customtkinter as ctk
from PIL import Image

# ── Tema ──────────────────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ── Cores ─────────────────────────────────────────────────────────────
COR_BG       = "#F1F5F9"
COR_CARD     = "#FFFFFF"
COR_CARD2    = "#F8FAFC"
COR_PRIMARIA = "#2563EB"
COR_VERDE    = "#059669"
COR_AMARELO  = "#D97706"
COR_ROXO     = "#7C3AED"
COR_TEXTO    = "#1E293B"
COR_SUBTEXTO = "#64748B"
COR_BORDA    = "#E2E8F0"

TRIB_CORES = {
    "IRPJ":   "#3B82F6",
    "CSLL":   "#8B5CF6",
    "COFINS": "#F59E0B",
    "PIS":    "#10B981",
    "CPP":    "#EF4444",
    "ICMS":   "#06B6D4",
    "IPI":    "#F97316",
    "ISS":    "#84CC16",
}

# ── Fontes — altere aqui para mudar todos os textos do sistema ────────
FONTE          = "Segoe UI"   # família da fonte

TAM_HEADER     = 16   # título "Calculadora DAS — Simples Nacional" no cabeçalho azul
TAM_CARD_TITLE = 12   # títulos dos cards "DADOS DE ENTRADA", "RESULTADO POR ANEXO", "SEGREGAÇÃO DOS TRIBUTOS"
TAM_LABEL      = 12   # labels dos campos "FATURAMENTO DO MÊS", "RBT12 — 12 MESES", "ANEXO I (%)", "ANEXO II (%)", "ANEXO III (%)"
TAM_INPUT      = 14   # texto digitado nos 5 campos de entrada
TAM_HINT       = 12   # "Soma dos anexos: 0,00% (precisa ser 100%)" e "✓"
TAM_BTN        = 14   # texto dos botões "▶ Calcular DAS" e "✕ Limpar"
TAM_MINI_LABEL = 12   # título dos cards de totais "DAS TOTAL", "ALÍQUOTA EFETIVA", "FAIXA (RBT12)"
TAM_MINI_VALOR = 22   # valor dos cards de totais  "R$ 0,00", "—" nos três cards de totais
TAM_TAB_HEADER = 13   # cabeçalho das tabelas "Anexo", "Faixa", "Receita", "Alíq. Nominal", "Alíq. Efetiva", "DAS Parcial", "Tributo", "% no DAS", "Valor (R$)"
TAM_TAB_LINHA  = 13   # todas as linhas de dados das duas tabelas
TAM_ALERTA     = 17   # texto da mensagem dentro do popup de aviso

# ── Tamanhos de janela e linhas ───────────────────────────────────────
JANELA_W       = 1200   # largura inicial da janela
JANELA_H       = 900    # altura inicial da janela
ALTURA_INPUT   = 44     # altura dos 5 campos de entrada
ALTURA_BTN     = 40     # altura dos botões Calcular e Limpar
ALTURA_LINHA   = 36     # altura de cada linha nas duas tabelas

# ── Dados ─────────────────────────────────────────────────────────────
ANEXOS = {
    "Anexo I — Comércio": {
        "faixas": [
            {"n": 1, "lim": 180000,  "al": 0.04,  "ded": 0},
            {"n": 2, "lim": 360000,  "al": 0.073, "ded": 5940},
            {"n": 3, "lim": 720000,  "al": 0.095, "ded": 13860},
            {"n": 4, "lim": 1800000, "al": 0.107, "ded": 22500},
            {"n": 5, "lim": 3600000, "al": 0.143, "ded": 87300},
            {"n": 6, "lim": 4800000, "al": 0.19,  "ded": 378000},
        ],
        "tributos": {
            1: {"IRPJ": 5.50, "CSLL": 3.50, "COFINS": 12.74, "PIS": 2.76, "CPP": 41.50, "ICMS": 34.00},
            2: {"IRPJ": 5.50, "CSLL": 3.50, "COFINS": 12.74, "PIS": 2.76, "CPP": 41.50, "ICMS": 34.00},
            3: {"IRPJ": 5.50, "CSLL": 3.50, "COFINS": 12.74, "PIS": 2.76, "CPP": 42.00, "ICMS": 33.50},
            4: {"IRPJ": 5.50, "CSLL": 3.50, "COFINS": 12.74, "PIS": 2.76, "CPP": 42.00, "ICMS": 33.50},
            5: {"IRPJ": 5.50, "CSLL": 3.50, "COFINS": 12.74, "PIS": 2.76, "CPP": 42.00, "ICMS": 33.50},
            6: {"IRPJ": 13.50, "CSLL": 10.00, "COFINS": 28.27, "PIS": 6.13, "CPP": 42.10},
        },
    },
    "Anexo II — Indústria": {
        "faixas": [
            {"n": 1, "lim": 180000,  "al": 0.045, "ded": 0},
            {"n": 2, "lim": 360000,  "al": 0.078, "ded": 5940},
            {"n": 3, "lim": 720000,  "al": 0.10,  "ded": 13860},
            {"n": 4, "lim": 1800000, "al": 0.112, "ded": 22500},
            {"n": 5, "lim": 3600000, "al": 0.147, "ded": 85500},
            {"n": 6, "lim": 4800000, "al": 0.30,  "ded": 720000},
        ],
        "tributos": {
            1: {"IRPJ": 5.50, "CSLL": 3.50, "COFINS": 11.51, "PIS": 2.49, "CPP": 37.50, "ICMS": 32.00, "IPI": 7.50},
            2: {"IRPJ": 5.50, "CSLL": 3.50, "COFINS": 11.51, "PIS": 2.49, "CPP": 37.50, "ICMS": 32.00, "IPI": 7.50},
            3: {"IRPJ": 5.50, "CSLL": 3.50, "COFINS": 11.51, "PIS": 2.49, "CPP": 37.50, "ICMS": 32.00, "IPI": 7.50},
            4: {"IRPJ": 5.50, "CSLL": 3.50, "COFINS": 11.51, "PIS": 2.49, "CPP": 37.50, "ICMS": 32.00, "IPI": 7.50},
            5: {"IRPJ": 5.50, "CSLL": 3.50, "COFINS": 11.51, "PIS": 2.49, "CPP": 37.50, "ICMS": 32.00, "IPI": 7.50},
            6: {"IRPJ": 8.50, "CSLL": 7.50, "COFINS": 20.96, "PIS": 4.54, "CPP": 23.50, "IPI": 35.00},
        },
    },
    "Anexo III — Serviços": {
        "faixas": [
            {"n": 1, "lim": 180000,  "al": 0.06,  "ded": 0},
            {"n": 2, "lim": 360000,  "al": 0.112, "ded": 9360},
            {"n": 3, "lim": 720000,  "al": 0.135, "ded": 17640},
            {"n": 4, "lim": 1800000, "al": 0.16,  "ded": 35640},
            {"n": 5, "lim": 3600000, "al": 0.21,  "ded": 125640},
            {"n": 6, "lim": 4800000, "al": 0.33,  "ded": 648000},
        ],
        "tributos": {
            1: {"IRPJ": 4.00, "CSLL": 3.50, "COFINS": 12.82, "PIS": 2.78, "CPP": 43.40, "ISS": 33.50},
            2: {"IRPJ": 4.00, "CSLL": 3.50, "COFINS": 14.05, "PIS": 3.05, "CPP": 43.40, "ISS": 32.00},
            3: {"IRPJ": 4.00, "CSLL": 3.50, "COFINS": 13.64, "PIS": 2.96, "CPP": 43.40, "ISS": 32.50},
            4: {"IRPJ": 4.00, "CSLL": 3.50, "COFINS": 13.64, "PIS": 2.96, "CPP": 43.40, "ISS": 32.50},
            5: {"IRPJ": 4.00, "CSLL": 3.50, "COFINS": 12.82, "PIS": 2.78, "CPP": 43.40, "ISS": 33.50},
            6: {"IRPJ": 35.00, "CSLL": 15.00, "COFINS": 16.03, "PIS": 3.47, "CPP": 30.50},
        },
    },
}


# ── Resource path (funciona no .exe do PyInstaller) ───────────────────
def resource_path(filename: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


# ── Helpers ───────────────────────────────────────────────────────────
def brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_moeda(event):
    e = event.widget
    raw = e.get()
    clean = ""
    comma = False
    for c in raw:
        if c.isdigit():
            clean += c
        elif c == "," and not comma:
            clean += c
            comma = True
    if not clean:
        e.delete(0, "end")
        return
    parts = clean.split(",")
    intpart = f"{int(parts[0]):,}".replace(",", ".") if parts[0] else ""
    decpart = parts[1][:2] if len(parts) > 1 else ""
    result = intpart + ("," + decpart if comma else "")
    e.delete(0, "end")
    e.insert(0, result)


def fmt_pct(event):
    e = event.widget
    raw = e.get()
    clean = ""
    comma = False
    for c in raw:
        if c.isdigit():
            clean += c
        elif c == "," and not comma:
            clean += c
            comma = True
    parts = clean.split(",")
    intpart = parts[0]
    decpart = parts[1][:2] if len(parts) > 1 else ""
    result = intpart + ("," + decpart if comma else "")
    e.delete(0, "end")
    e.insert(0, result)


def parse_moeda(s: str) -> float:
    s = s.strip().replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    return float(s) if s else 0.0


def parse_pct(s: str) -> float:
    s = s.strip().replace(",", ".")
    return float(s) if s else 0.0


def get_faixa(anexo, rbt12):
    for f in ANEXOS[anexo]["faixas"]:
        if rbt12 <= f["lim"]:
            return f
    return ANEXOS[anexo]["faixas"][-1]


def aliq_efetiva(rbt12, al, ded):
    return ((rbt12 * al) - ded) / rbt12


# ── App ───────────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        try:
            self.iconbitmap(resource_path("das.ico"))
        except Exception:
            pass

        self.title("Calculadora DAS — Simples Nacional")
        self.geometry(f"{JANELA_W}x{JANELA_H}")
        self.configure(fg_color=COR_BG)
        self.resizable(True, True)
        self._build()

    # ── Layout ────────────────────────────────────────────────────────
    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="#1E3A5F", corner_radius=0, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        try:
            logo_img = ctk.CTkImage(Image.open(resource_path("das.png")), size=(36, 36))
            ctk.CTkLabel(hdr, image=logo_img, text="").pack(side="left", padx=(14, 0), pady=10)
        except Exception:
            pass

        ctk.CTkLabel(
            hdr,
            text="  Calculadora DAS — Simples Nacional",
            font=ctk.CTkFont(FONTE, TAM_HEADER, "bold"),
            text_color="#F1F5F9",
        ).pack(side="left", padx=(6, 20), pady=14)

        scroll = ctk.CTkScrollableFrame(self, fg_color=COR_BG, scrollbar_button_color=COR_BORDA)
        scroll.pack(fill="both", expand=True)

        self._card_entrada(scroll)

        frame_totais = ctk.CTkFrame(scroll, fg_color="transparent")
        frame_totais.pack(fill="x", padx=20, pady=(0, 16))
        frame_totais.columnconfigure((0, 1, 2), weight=1)

        self.lbl_das   = self._mini_card(frame_totais, "DAS TOTAL",        "R$ 0,00", COR_VERDE,    0)
        self.lbl_aliq  = self._mini_card(frame_totais, "ALÍQUOTA EFETIVA", "—",        COR_PRIMARIA, 1)
        self.lbl_faixa = self._mini_card(frame_totais, "FAIXA (RBT12)",    "—",        COR_AMARELO,  2)

        self._card_resultado(scroll)
        self._card_segregacao(scroll)

    def _card(self, parent, titulo: str, cor_titulo: str):
        outer = ctk.CTkFrame(parent, fg_color=COR_CARD, corner_radius=16)
        outer.pack(fill="x", padx=20, pady=(0, 16))

        hdr = ctk.CTkFrame(outer, fg_color=cor_titulo, corner_radius=12, height=38)
        hdr.pack(fill="x", padx=2, pady=(2, 0))
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text=titulo,
            font=ctk.CTkFont(FONTE, TAM_CARD_TITLE, "bold"),
            text_color="white",
        ).pack(side="left", padx=14)

        body = ctk.CTkFrame(outer, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(10, 16))
        return body

    def _mini_card(self, parent, titulo, valor, cor, col):
        f = ctk.CTkFrame(parent, fg_color=COR_CARD, corner_radius=16)
        f.grid(row=0, column=col, padx=(0 if col == 0 else 8, 0), sticky="ew")
        ctk.CTkLabel(
            f, text=titulo,
            font=ctk.CTkFont(FONTE, TAM_MINI_LABEL, "bold"),
            text_color=COR_SUBTEXTO,
        ).pack(pady=(14, 2))
        lbl = ctk.CTkLabel(
            f, text=valor,
            font=ctk.CTkFont(FONTE, TAM_MINI_VALOR, "bold"),
            text_color=cor,
        )
        lbl.pack(pady=(0, 14))
        return lbl

    def _entry(self, parent, placeholder, row, col, bind_fn):
        e = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            font=ctk.CTkFont(FONTE, TAM_INPUT),
            fg_color=COR_CARD2,
            border_color=COR_BORDA,
            border_width=1,
            text_color=COR_TEXTO,
            placeholder_text_color=COR_SUBTEXTO,
            corner_radius=10,
            height=ALTURA_INPUT,
        )
        e.grid(row=row, column=col, padx=8, pady=(0, 8), sticky="ew")
        e.bind("<KeyRelease>", bind_fn)
        return e

    def _label(self, parent, texto, row, col):
        ctk.CTkLabel(
            parent, text=texto,
            font=ctk.CTkFont(FONTE, TAM_LABEL, "bold"),
            text_color=COR_SUBTEXTO,
        ).grid(row=row, column=col, padx=8, pady=(10, 2), sticky="w")

    # ── Entrada ───────────────────────────────────────────────────────
    def _card_entrada(self, parent):
        body = self._card(parent, "DADOS DE ENTRADA", "#1E3A5F")
        body.columnconfigure((0, 1, 2, 3, 4), weight=1)

        campos = [
            ("FATURAMENTO DO MÊS", "0,00", 0, fmt_moeda),
            ("RBT12 — 12 MESES",   "0,00", 1, fmt_moeda),
            ("ANEXO I (%)",         "0,00", 2, fmt_pct),
            ("ANEXO II (%)",        "0,00", 3, fmt_pct),
            ("ANEXO III (%)",       "0,00", 4, fmt_pct),
        ]

        self.entries = []
        for texto, ph, col, fn in campos:
            self._label(body, texto, 0, col)
            e = self._entry(body, ph, 1, col, fn)
            if col >= 2:
                e.bind("<KeyRelease>", lambda ev, fn=fn: (fn(ev), self._check_pct()), add="+")
            self.entries.append(e)

        self.e_fat, self.e_rbt, self.e_p1, self.e_p2, self.e_p3 = self.entries

        row_hint = ctk.CTkFrame(body, fg_color="transparent")
        row_hint.grid(row=2, column=0, columnspan=5, sticky="ew", pady=(4, 0))

        self.lbl_pct = ctk.CTkLabel(
            row_hint,
            text="Soma dos anexos: 0,00%  (precisa ser 100%)",
            font=ctk.CTkFont(FONTE, TAM_HINT),
            text_color=COR_SUBTEXTO,
        )
        self.lbl_pct.pack(side="left")

        ctk.CTkButton(
            row_hint, text="✕  Limpar",
            command=self._limpar,
            fg_color="#334155", hover_color="#475569",
            font=ctk.CTkFont(FONTE, TAM_BTN, "bold"),
            text_color="white",
            corner_radius=10, height=ALTURA_BTN, width=120,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            row_hint, text="▶  Calcular DAS",
            command=self._calcular,
            fg_color=COR_VERDE, hover_color="#2563EB",
            font=ctk.CTkFont(FONTE, TAM_BTN, "bold"),
            corner_radius=10, height=ALTURA_BTN, width=160,
        ).pack(side="right")

    # ── Resultado por Anexo ───────────────────────────────────────────
    def _card_resultado(self, parent):
        body = self._card(parent, "RESULTADO POR ANEXO", "#1E3A5F")
        colunas  = ["Anexo", "Faixa", "Receita", "Alíq. Nominal", "Alíq. Efetiva", "DAS Parcial"]
        larguras = [260, 90, 170, 140, 140, 160]
        self._cabecalho_tabela(body, colunas, larguras, 0)
        self.rows_res = self._linhas_tabela(body, 3, colunas, larguras, 1)

    # ── Escalonamento ────────────────────────────────────────────────────
    def _card_segregacao(self, parent):
        body = self._card(parent, "ESCALONAMENTO DOS TRIBUTOS", "#5B21B6")
        colunas  = ["Tributo", "Anexo", "% no DAS", "Valor (R$)"]
        larguras = [120, 240, 120, 180]
        self._cabecalho_tabela(body, colunas, larguras, 0)
        self.rows_seg = self._linhas_tabela(body, 10, colunas, larguras, 1)

    def _cabecalho_tabela(self, parent, colunas, larguras, row):
        hdr = ctk.CTkFrame(parent, fg_color=COR_CARD2, corner_radius=10, height=36)
        hdr.grid(row=row, column=0, sticky="ew", pady=(0, 2))
        parent.columnconfigure(0, weight=1)
        hdr.pack_propagate(False)

        row_f = ctk.CTkFrame(hdr, fg_color="transparent")
        row_f.pack(fill="both", expand=True, padx=8)

        for i, (col, w) in enumerate(zip(colunas, larguras)):
            ctk.CTkLabel(
                row_f, text=col, width=w,
                font=ctk.CTkFont(FONTE, TAM_TAB_HEADER, "bold"),
                text_color=COR_SUBTEXTO,
                anchor="w" if i == 0 else "center",
            ).pack(side="left")

    def _linhas_tabela(self, parent, n_rows, colunas, larguras, start_row):
        rows = []
        for i in range(n_rows):
            cor   = COR_CARD if i % 2 == 0 else COR_CARD2
            row_f = ctk.CTkFrame(parent, fg_color=cor, corner_radius=8, height=ALTURA_LINHA)
            row_f.grid(row=start_row + i, column=0, sticky="ew", pady=1)
            row_f.pack_propagate(False)

            inner = ctk.CTkFrame(row_f, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=8)

            cells = []
            for j, (col, w) in enumerate(zip(colunas, larguras)):
                lbl = ctk.CTkLabel(
                    inner, text="", width=w,
                    font=ctk.CTkFont(FONTE, TAM_TAB_LINHA),
                    text_color=COR_TEXTO,
                    anchor="w" if j == 0 else "center",
                )
                lbl.pack(side="left")
                cells.append(lbl)

            rows.append((row_f, cells))
        return rows

    def _set_row(self, rows, idx, valores, visivel=True, cor_texto=None):
        if idx >= len(rows):
            return
        frame, cells = rows[idx]
        for cell, val in zip(cells, valores):
            cell.configure(text=str(val))
            if cor_texto:
                cell.configure(text_color=cor_texto)
        frame.configure(fg_color=COR_CARD if idx % 2 == 0 else COR_CARD2)
        if visivel:
            frame.grid()
        else:
            frame.grid_remove()

    def _limpar_rows(self, rows):
        for frame, cells in rows:
            for c in cells:
                c.configure(text="", text_color=COR_TEXTO)
            frame.grid_remove()

    # ── Lógica ────────────────────────────────────────────────────────
    def _check_pct(self):
        p1   = parse_pct(self.e_p1.get())
        p2   = parse_pct(self.e_p2.get())
        p3   = parse_pct(self.e_p3.get())
        soma = p1 + p2 + p3
        ok   = abs(soma - 100) < 0.01
        soma_fmt = f"{soma:.2f}".replace(".", ",")
        if soma == 0:
            self.lbl_pct.configure(
                text=f"Soma dos anexos: {soma_fmt}%  (precisa ser 100%)",
                text_color=COR_SUBTEXTO,
            )
        elif ok:
            self.lbl_pct.configure(
                text=f"Soma dos anexos: {soma_fmt}%  ✓", text_color=COR_VERDE
            )
        else:
            self.lbl_pct.configure(
                text=f"Soma dos anexos: {soma_fmt}%  (precisa ser 100%)",
                text_color="#EF4444",
            )
        return ok

    def _limpar(self):
        for e in self.entries:
            e.delete(0, "end")
        self._limpar_rows(self.rows_res)
        self._limpar_rows(self.rows_seg)
        self.lbl_das.configure(text="R$ 0,00", text_color=COR_VERDE)
        self.lbl_aliq.configure(text="—",       text_color=COR_PRIMARIA)
        self.lbl_faixa.configure(text="—",      text_color=COR_AMARELO)
        self.lbl_pct.configure(
            text="Soma dos anexos: 0,00%  (precisa ser 100%)",
            text_color=COR_SUBTEXTO,
        )

    def _alerta(self, msg: str):
        win = ctk.CTkToplevel(self)
        win.title("Aviso")
        win.geometry("400x180")
        win.configure(fg_color=COR_CARD)
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()
        ctk.CTkLabel(
            win, text="⚠  Atenção",
            font=ctk.CTkFont(FONTE, 14, "bold"),
            text_color=COR_AMARELO,
        ).pack(pady=(24, 10))
        ctk.CTkLabel(
            win, text=msg,
            font=ctk.CTkFont(FONTE, TAM_ALERTA),
            text_color=COR_TEXTO,
            wraplength=360,
        ).pack(padx=20)
        ctk.CTkButton(
            win, text="OK", command=win.destroy,
            fg_color=COR_PRIMARIA, corner_radius=10,
            width=100, height=34,
        ).pack(pady=20)

    def _calcular(self):
        try:
            fat = parse_moeda(self.e_fat.get())
            rbt = parse_moeda(self.e_rbt.get())
            p1  = parse_pct(self.e_p1.get())
            p2  = parse_pct(self.e_p2.get())
            p3  = parse_pct(self.e_p3.get())
        except ValueError:
            self._alerta("Verifique os valores informados.\nUse vírgula como separador decimal.")
            return

        if fat <= 0:
            self._alerta("Informe o faturamento do mês."); return
        if rbt <= 0:
            self._alerta("Informe o RBT12."); return
        if not self._check_pct():
            self._alerta("A soma dos percentuais deve ser 100%."); return

        config = [
            ("Anexo I — Comércio",   p1),
            ("Anexo II — Indústria", p2),
            ("Anexo III — Serviços", p3),
        ]

        self._limpar_rows(self.rows_res)
        self._limpar_rows(self.rows_seg)

        total_das  = 0.0
        soma_aliq  = 0.0
        faixa_disp = "—"
        res_idx    = 0
        seg_idx    = 0

        for nome, pct in config:
            if pct <= 0:
                continue

            rec = fat * (pct / 100)
            f   = get_faixa(nome, rbt)
            ae  = aliq_efetiva(rbt, f["al"], f["ded"])
            das = rec * ae
            total_das += das
            soma_aliq += ae * (pct / 100)
            faixa_disp = f"{f['n']}ª"

            self._set_row(self.rows_res, res_idx, [
                nome,
                f"{f['n']}ª Faixa",
                brl(rec),
                f"{f['al']*100:.2f}%".replace(".", ","),
                f"{ae*100:.4f}%".replace(".", ","),
                brl(das),
            ], visivel=True)
            res_idx += 1

            tribs = ANEXOS[nome]["tributos"][f["n"]]
            for trib, pct_t in tribs.items():
                cor = TRIB_CORES.get(trib, COR_SUBTEXTO)
                self._set_row(self.rows_seg, seg_idx, [
                    trib,
                    nome.split("—")[1].strip(),
                    f"{pct_t:.2f}%".replace(".", ","),
                    brl(das * (pct_t / 100)),
                ], visivel=True)
                if seg_idx < len(self.rows_seg):
                    _, cells = self.rows_seg[seg_idx]
                    cells[0].configure(text_color=cor)
                seg_idx += 1

        self.lbl_das.configure(text=brl(total_das))
        self.lbl_aliq.configure(text=f"{soma_aliq*100:.4f}%".replace(".", ","))
        self.lbl_faixa.configure(text=faixa_disp + " Faixa")


# ── Execução ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    from licence_module import LicenseManager

    app = App()
    lm  = LicenseManager()
    lm.verificar_na_abertura(app)
    app.mainloop()