# licence_module.py
"""
Módulo de Licenciamento — Calculadora DAS
Inclui: ativação, cadastro, trial, pagamento PIX e update automático.
"""

import os, sys, platform, hashlib, json, threading, subprocess, base64, io
import customtkinter as ctk
from PIL import Image
import httpx

# ── Configuração ──────────────────────────────────────────────────────
API_URL      = "https://calculadora-das-z1hd.onrender.com"
VERSAO_ATUAL = "1.1.16"
CHAVE_FILE   = os.path.join(os.path.expanduser("~"), ".das_licenca")

# ── Cores ─────────────────────────────────────────────────────────────
COR_CARD   = "#FFFFFF"
COR_TEXTO  = "#1E293B"
COR_SUB    = "#64748B"
COR_AZUL   = "#2563EB"
COR_VERDE  = "#059669"
COR_ERRO   = "#DC2626"
COR_FUNDO  = "#F1F5F9"
COR_HEADER = "#1E3A5F"
COR_BORDA  = "#E2E8F0"


# ── Machine ID ────────────────────────────────────────────────────────
def get_machine_id() -> str:
    raw = f"{platform.node()}-{platform.machine()}-{platform.processor()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


# ── Persistência da chave ─────────────────────────────────────────────
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


# ── Helpers UI ────────────────────────────────────────────────────────
def _header(win, texto: str):
    hdr = ctk.CTkFrame(win, fg_color=COR_HEADER, corner_radius=0, height=52)
    hdr.pack(fill="x")
    hdr.pack_propagate(False)
    ctk.CTkLabel(hdr, text=texto,
                 font=ctk.CTkFont("Segoe UI", 14, "bold"),
                 text_color="white").pack(side="left", padx=20, pady=12)
    return hdr

def _base_win(root, titulo, w, h):
    win = ctk.CTkToplevel()
    win.title(titulo)
    win.geometry(f"{w}x{h}")
    win.configure(fg_color=COR_CARD)
    win.resizable(False, False)
    win.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
    win.grab_set()
    win.focus_force()
    return win


# ══════════════════════════════════════════════════════════════════════
class LicenseManager:

    def __init__(self):
        self.machine_id = get_machine_id()
        self.cliente    = None
        self._chave     = None

    # ── Ponto de entrada ──────────────────────────────────────────────
    def verificar_na_abertura(self, root: ctk.CTk):
        chave_salva = carregar_chave()

        if chave_salva:
            self._chave = chave_salva
            ok, codigo, cliente = self._validar_online(chave_salva)

            if ok:
                self.cliente = cliente
                self._verificar_update(root)
                return

            elif codigo == 402:
                # Trial expirado — mostra tela de pagamento
                root.withdraw()
                self._tela_pagamento(root, chave_salva)
                return

            else:
                apagar_chave()
                self._tela_ativacao(root, erro=cliente)
        else:
            self._tela_ativacao(root)

    # ── Validação ─────────────────────────────────────────────────────
    def _validar_online(self, chave: str) -> tuple[bool, int, str | None]:
        """Retorna (ok, http_status, cliente_ou_erro)"""
        try:
            r = httpx.post(
                f"{API_URL}/validar",
                json={"chave": chave, "machine_id": self.machine_id},
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                return True, 200, data["cliente"]
            else:
                detail = r.json().get("detail", "Erro desconhecido.")
                return False, r.status_code, detail
        except httpx.ConnectError:
            return False, 0, "Sem conexão com o servidor.\nVerifique sua internet."
        except Exception as e:
            return False, 0, f"Erro: {e}"

    # ══════════════════════════════════════════════════════════════════
    # TELA DE ATIVAÇÃO (com botão Criar conta)
    # ══════════════════════════════════════════════════════════════════
    def _tela_ativacao(self, root: ctk.CTk, erro: str = None):
        root.withdraw()
        win = _base_win(root, "Ativação — Calculadora DAS", 480, 420)

        _header(win, "🔐  Ativação de Licença")

        body = ctk.CTkFrame(win, fg_color=COR_CARD)
        body.pack(fill="both", expand=True, padx=32, pady=24)

        ctk.CTkLabel(body, text="Calculadora DAS — Simples Nacional",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=COR_TEXTO).pack(pady=(0, 4))

        ctk.CTkLabel(body, text="Digite sua chave de licença para continuar.",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=COR_SUB).pack(pady=(0, 16))

        entry = ctk.CTkEntry(
            body, placeholder_text="XXXX-XXXX-XXXX-XXXX",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color="#F8FAFC", border_color=COR_BORDA,
            text_color=COR_TEXTO, height=44,
            corner_radius=10, justify="center",
        )
        entry.pack(fill="x", pady=(0, 6))

        lbl_erro = ctk.CTkLabel(body, text=erro or "",
                                font=ctk.CTkFont("Segoe UI", 10),
                                text_color=COR_ERRO, wraplength=400)
        lbl_erro.pack(pady=(0, 12))

        def ativar():
            chave = entry.get().strip().upper()
            if len(chave) != 19:
                lbl_erro.configure(text="Formato inválido. Use: XXXX-XXXX-XXXX-XXXX")
                return
            btn_ativar.configure(state="disabled", text="Validando...")
            win.update()

            ok, codigo, resultado = self._validar_online(chave)

            if ok:
                salvar_chave(chave)
                self._chave  = chave
                self.cliente = resultado
                win.destroy()
                root.deiconify()
                self._verificar_update(root)

            elif codigo == 402:
                salvar_chave(chave)
                self._chave = chave
                win.destroy()
                self._tela_pagamento(root, chave)

            elif codigo == 403 and "máquina" in (resultado or "").lower():
                btn_ativar.configure(state="normal", text="Ativar")
                self._oferecer_transferencia(win, root, chave, lbl_erro)

            else:
                btn_ativar.configure(state="normal", text="Ativar")
                lbl_erro.configure(text=resultado)

        btn_ativar = ctk.CTkButton(
            body, text="Ativar",
            command=ativar,
            fg_color=COR_AZUL, hover_color="#1D4ED8",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            corner_radius=10, height=42,
        )
        btn_ativar.pack(fill="x", pady=(0, 10))
        entry.bind("<Return>", lambda e: ativar())

        # Separador
        sep = ctk.CTkFrame(body, fg_color=COR_BORDA, height=1)
        sep.pack(fill="x", pady=(4, 14))

        ctk.CTkLabel(body, text="Ainda não tem uma conta?",
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=COR_SUB).pack()

        def abrir_cadastro():
            win.destroy()
            self._tela_cadastro(root)

        ctk.CTkButton(
            body, text="✨  Criar conta grátis — 30 dias sem custo",
            command=abrir_cadastro,
            fg_color=COR_VERDE, hover_color="#047857",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            corner_radius=10, height=40,
        ).pack(fill="x", pady=(8, 0))

        win.wait_window()

    # ══════════════════════════════════════════════════════════════════
    # TELA DE CADASTRO
    # ══════════════════════════════════════════════════════════════════
    def _tela_cadastro(self, root: ctk.CTk):
        win = _base_win(root, "Criar conta — Calculadora DAS", 480, 520)

        _header(win, "✨  Criar conta gratuita")

        body = ctk.CTkFrame(win, fg_color=COR_CARD)
        body.pack(fill="both", expand=True, padx=32, pady=24)

        ctk.CTkButton(
            body, text="← Voltar",
            command=lambda: (win.destroy(), self._tela_ativacao(root)),
            fg_color="#E2E8F0", hover_color="#CBD5E1",
            text_color=COR_TEXTO,
            font=ctk.CTkFont("Segoe UI", 10),
            corner_radius=10, height=32,
        ).pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(body, text="30 dias grátis, sem cartão de crédito",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=COR_VERDE).pack(pady=(0, 6))

        ctk.CTkLabel(body,
                     text="Após o trial, apenas R$ 4,99/mês via PIX.\nSua chave de acesso será enviada para o email.",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=COR_SUB, justify="center").pack(pady=(0, 20))

        # Nome
        ctk.CTkLabel(body, text="NOME (opcional)",
                     font=ctk.CTkFont("Segoe UI", 9, "bold"),
                     text_color=COR_SUB).pack(anchor="w")
        e_nome = ctk.CTkEntry(body, placeholder_text="Seu nome",
                              fg_color="#F8FAFC", border_color=COR_BORDA,
                              text_color=COR_TEXTO, height=40, corner_radius=10)
        e_nome.pack(fill="x", pady=(2, 10))

        # Email
        ctk.CTkLabel(body, text="SEU EMAIL  *",
                     font=ctk.CTkFont("Segoe UI", 9, "bold"),
                     text_color=COR_SUB).pack(anchor="w")
        e_email = ctk.CTkEntry(body, placeholder_text="seu@email.com",
                               fg_color="#F8FAFC", border_color=COR_BORDA,
                               text_color=COR_TEXTO, height=40, corner_radius=10)
        e_email.pack(fill="x", pady=(2, 6))

        lbl_msg = ctk.CTkLabel(body, text="",
                               font=ctk.CTkFont("Segoe UI", 10),
                               text_color=COR_ERRO, wraplength=400)
        lbl_msg.pack(pady=(0, 10))

        def cadastrar():
            email = e_email.get().strip()
            nome  = e_nome.get().strip()

            if "@" not in email or "." not in email:
                lbl_msg.configure(text="Digite um email válido.", text_color=COR_ERRO)
                return

            btn.configure(state="disabled", text="Criando conta...")
            win.update()

            try:
                r = httpx.post(f"{API_URL}/cadastro",
                               json={"email": email, "nome": nome}, timeout=15)

                if r.status_code == 200:
                    lbl_msg.configure(
                        text="✓  Conta criada! Verifique seu email e copie a chave de acesso.",
                        text_color=COR_VERDE)
                    btn.configure(state="disabled", text="Email enviado ✓")
                    # Botão para voltar à ativação
                    ctk.CTkButton(
                        body, text="← Inserir minha chave",
                        command=lambda: (win.destroy(), self._tela_ativacao(root)),
                        fg_color=COR_AZUL, hover_color="#1D4ED8",
                        font=ctk.CTkFont("Segoe UI", 11, "bold"),
                        corner_radius=10, height=38,
                    ).pack(fill="x", pady=(8, 0))

                else:
                    detalhe = r.json().get("detail", "Erro ao criar conta.")
                    lbl_msg.configure(text=detalhe, text_color=COR_ERRO)
                    btn.configure(state="normal", text="Criar conta grátis")

            except Exception as e:
                lbl_msg.configure(text=f"Erro de conexão: {e}", text_color=COR_ERRO)
                btn.configure(state="normal", text="Criar conta grátis")

        btn = ctk.CTkButton(
            body, text="Criar conta grátis",
            command=cadastrar,
            fg_color=COR_VERDE, hover_color="#047857",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            corner_radius=10, height=42,
        )
        btn.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            body, text="← Já tenho uma chave",
            command=lambda: (win.destroy(), self._tela_ativacao(root)),
            fg_color="#E2E8F0", hover_color="#CBD5E1",
            text_color=COR_TEXTO,
            font=ctk.CTkFont("Segoe UI", 10),
            corner_radius=10, height=34,
        ).pack(fill="x")

        win.wait_window()

    # ══════════════════════════════════════════════════════════════════
    # TELA DE PAGAMENTO (QR Code PIX)
    # ══════════════════════════════════════════════════════════════════
    def _tela_pagamento(self, root: ctk.CTk, chave: str):
        win = ctk.CTkToplevel()
        win.title("Renovar acesso — Calculadora DAS")
        win.geometry("500x680")          # ← altura maior como padrão
        win.minsize(480, 500)            # ← tamanho mínimo
        win.configure(fg_color=COR_CARD)
        win.resizable(False, True)       # ← permite redimensionar verticalmente
        def fechar():
            self._polling_ativo = False
            win.destroy()
            sys.exit(0)

        win.protocol("WM_DELETE_WINDOW", fechar)
        win.grab_set()
        win.focus_force()

        _header(win, "💳  Renovar acesso — R$ 4,99/mês")

        # ← Troca CTkFrame por CTkScrollableFrame
        body = ctk.CTkScrollableFrame(win, fg_color=COR_CARD)
        body.pack(fill="both", expand=True, padx=32, pady=24)

        ctk.CTkLabel(body,
                     text="Seu período gratuito encerrou.",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=COR_TEXTO).pack(pady=(0, 4))

        ctk.CTkLabel(body,
                     text="Pague R$ 4,99 via PIX para continuar usando.\nO acesso é liberado automaticamente após o pagamento.",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=COR_SUB, justify="center").pack(pady=(0, 14))

        # Campo email
        ctk.CTkLabel(body, text="SEU EMAIL (para identificar o pagamento)",
                     font=ctk.CTkFont("Segoe UI", 9, "bold"),
                     text_color=COR_SUB).pack(anchor="w")
        e_email = ctk.CTkEntry(body, placeholder_text="seu@email.com",
                               fg_color="#F8FAFC", border_color=COR_BORDA,
                               text_color=COR_TEXTO, height=40, corner_radius=10)
        e_email.pack(fill="x", pady=(2, 10))

        # Frame do QR code (oculto até gerar)
        frame_qr = ctk.CTkFrame(body, fg_color=COR_FUNDO, corner_radius=12)
        lbl_qr_img  = ctk.CTkLabel(frame_qr, text="")
        lbl_pix_key = ctk.CTkEntry(frame_qr, font=ctk.CTkFont("Segoe UI", 9),
                                   fg_color="#F8FAFC", border_color=COR_BORDA,
                                   text_color=COR_SUB, height=32, corner_radius=8,
                                   state="readonly", justify="center")
        lbl_copiado = ctk.CTkLabel(frame_qr, text="",
                                   font=ctk.CTkFont("Segoe UI", 10),
                                   text_color=COR_VERDE)
        lbl_status  = ctk.CTkLabel(body, text="",
                                   font=ctk.CTkFont("Segoe UI", 11),
                                   text_color=COR_SUB)

        lbl_msg = ctk.CTkLabel(body, text="",
                               font=ctk.CTkFont("Segoe UI", 10),
                               text_color=COR_ERRO, wraplength=420)
        lbl_msg.pack()

        self._polling_ativo = False

        def gerar():
            email = e_email.get().strip()
            if "@" not in email:
                lbl_msg.configure(text="Digite um email válido.", text_color=COR_ERRO)
                return

            btn_gerar.configure(state="disabled", text="Gerando QR Code...")
            win.update()

            try:
                r = httpx.post(f"{API_URL}/pagamento/gerar",
                               json={"chave": chave, "email": email}, timeout=20)

                if r.status_code != 200:
                    lbl_msg.configure(text=r.json().get("detail", "Erro ao gerar pagamento."),
                                      text_color=COR_ERRO)
                    btn_gerar.configure(state="normal", text="Gerar QR Code PIX")
                    return

                data       = r.json()
                payment_id = data["payment_id"]
                qr_b64     = data["qr_code_base64"]
                pix_code   = data["qr_code"]

                # Exibe QR code
                img_bytes = base64.b64decode(qr_b64)
                img       = Image.open(io.BytesIO(img_bytes)).resize((220, 220))
                ctk_img   = ctk.CTkImage(img, size=(220, 220))

                frame_qr.pack(fill="x", pady=(8, 0))
                ctk.CTkLabel(frame_qr,
                             text="Escaneie o QR Code ou copie o código PIX:",
                             font=ctk.CTkFont("Segoe UI", 10),
                             text_color=COR_SUB).pack(pady=(12, 6))

                lbl_qr_img.configure(image=ctk_img)
                lbl_qr_img.pack(pady=(0, 8))

                lbl_pix_key.configure(state="normal")
                lbl_pix_key.delete(0, "end")
                lbl_pix_key.insert(0, pix_code)
                lbl_pix_key.configure(state="readonly")
                lbl_pix_key.pack(fill="x", padx=12, pady=(0, 4))

                def copiar_pix():
                    win.clipboard_clear()
                    win.clipboard_append(pix_code)
                    lbl_copiado.configure(text="✓ Código copiado!")
                    win.after(2000, lambda: lbl_copiado.configure(text=""))

                ctk.CTkButton(
                    frame_qr, text="📋  Copiar código PIX",
                    command=copiar_pix,
                    fg_color=COR_AZUL, hover_color="#1D4ED8",
                    font=ctk.CTkFont("Segoe UI", 10, "bold"),
                    corner_radius=8, height=34,
                ).pack(padx=12, pady=(0, 4))

                lbl_copiado.pack(pady=(0, 8))

                lbl_status.pack(pady=(10, 0))
                lbl_status.configure(text="⏳ Aguardando pagamento...")
                btn_gerar.configure(text="QR Code gerado ✓")

                # Inicia polling
                self._polling_ativo = True
                self._iniciar_polling(win, root, payment_id, lbl_status)

            except Exception as e:
                lbl_msg.configure(text=f"Erro: {e}", text_color=COR_ERRO)
                btn_gerar.configure(state="normal", text="Gerar QR Code PIX")

        btn_gerar = ctk.CTkButton(
            body, text="Gerar QR Code PIX",
            command=gerar,
            fg_color=COR_AZUL, hover_color="#1D4ED8",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            corner_radius=10, height=42,
        )
        btn_gerar.pack(fill="x", pady=(8, 0))
        
        # Aviso de fallback
        aviso = ctk.CTkFrame(body, fg_color="#FEF3C7", corner_radius=10)
        aviso.pack(fill="x", pady=(12, 0))

        ctk.CTkLabel(
            aviso,
            text="⚠️  Após realizar o pagamento PIX",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color="#92400E",
        ).pack(pady=(10, 2))

        ctk.CTkLabel(
            aviso,
            text="Feche e abra o programa novamente.\nSeu acesso será liberado automaticamente!",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color="#92400E",
            justify="center",
        ).pack(pady=(0, 10))

        win.wait_window()
        
    def _oferecer_transferencia(self, win_ativacao, root, chave, lbl_erro):
        lbl_erro.configure(text="")
        confirm = ctk.CTkToplevel(win_ativacao)
        confirm.title("Transferir licença")
        confirm.geometry("420x280")
        confirm.configure(fg_color=COR_CARD)
        confirm.resizable(False, False)
        confirm.transient(win_ativacao)
        confirm.grab_set()
        confirm.focus_force()

        body = ctk.CTkFrame(confirm, fg_color=COR_CARD)
        body.pack(fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(body, text="⚠️  Trocar de computador?",
                    font=ctk.CTkFont("Segoe UI", 14, "bold"),
                    text_color=COR_TEXTO).pack(pady=(0, 10))

        ctk.CTkLabel(body,
                    text="Essa chave já está ativada em outro computador.\n"
                        "Vamos enviar um código de confirmação para o\n"
                        "email cadastrado. O acesso no computador\n"
                        "anterior será desativado.",
                    font=ctk.CTkFont("Segoe UI", 11),
                    text_color=COR_SUB, justify="center").pack(pady=(0, 20))

        def confirmar():
            confirm.destroy()
            self._solicitar_codigo_transferencia(win_ativacao, root, chave, lbl_erro)

        ctk.CTkButton(
            body, text="Enviar código de confirmação",
            command=confirmar,
            fg_color=COR_AZUL, hover_color="#1D4ED8",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            corner_radius=10, height=40,
        ).pack(fill="x", pady=(0, 8))

        ctk.CTkButton(
            body, text="Cancelar",
            command=confirm.destroy,
            fg_color="#E2E8F0", hover_color="#CBD5E1",
            text_color=COR_TEXTO,
            font=ctk.CTkFont("Segoe UI", 10),
            corner_radius=10, height=34,
        ).pack(fill="x")

    def _solicitar_codigo_transferencia(self, win_ativacao, root, chave, lbl_erro):
        try:
            r = httpx.post(
                f"{API_URL}/transferir/solicitar",
                json={"chave": chave, "machine_id": self.machine_id},
                timeout=15,
            )
            if r.status_code == 200:
                data = r.json()
                self._tela_confirmar_codigo(win_ativacao, root, chave, data.get("email_mascarado", "seu email"))
            else:
                detail = r.json().get("detail", "Erro ao solicitar transferência.")
                lbl_erro.configure(text=detail)
        except Exception as e:
            lbl_erro.configure(text=f"Erro: {e}")

    def _tela_confirmar_codigo(self, win_ativacao, root, chave, email_mascarado):
        win = _base_win(root, "Confirmar transferência", 420, 340)
        _header(win, "📧  Confirmar transferência")

        body = ctk.CTkFrame(win, fg_color=COR_CARD)
        body.pack(fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(body, text=f"Enviamos um código de 6 dígitos para:\n{email_mascarado}",
                    font=ctk.CTkFont("Segoe UI", 11),
                    text_color=COR_SUB, justify="center").pack(pady=(0, 6))

        ctk.CTkLabel(body, text="O código expira em 15 minutos.",
                    font=ctk.CTkFont("Segoe UI", 9),
                    text_color=COR_SUB).pack(pady=(0, 16))

        entry_codigo = ctk.CTkEntry(
            body, placeholder_text="000000",
            font=ctk.CTkFont("Segoe UI", 20, "bold"),
            fg_color="#F8FAFC", border_color=COR_BORDA,
            text_color=COR_TEXTO, height=48, corner_radius=10,
            justify="center",
        )
        entry_codigo.pack(fill="x", pady=(0, 10))

        lbl_msg = ctk.CTkLabel(body, text="", font=ctk.CTkFont("Segoe UI", 10),
                                text_color=COR_ERRO, wraplength=360)
        lbl_msg.pack(pady=(0, 10))

        def confirmar():
            codigo = entry_codigo.get().strip()
            if len(codigo) != 6 or not codigo.isdigit():
                lbl_msg.configure(text="Digite o código de 6 dígitos.")
                return
            btn.configure(state="disabled", text="Confirmando...")
            win.update()
            try:
                r = httpx.post(
                    f"{API_URL}/transferir/confirmar",
                    json={"chave": chave, "machine_id": self.machine_id, "codigo": codigo},
                    timeout=15,
                )
                if r.status_code == 200:
                    data = r.json()
                    salvar_chave(chave)
                    self._chave  = chave
                    self.cliente = data["cliente"]
                    win.destroy()
                    win_ativacao.destroy()
                    root.deiconify()
                    self._verificar_update(root)
                else:
                    detail = r.json().get("detail", "Código inválido.")
                    lbl_msg.configure(text=detail)
                    btn.configure(state="normal", text="Confirmar")
            except Exception as e:
                lbl_msg.configure(text=f"Erro: {e}")
                btn.configure(state="normal", text="Confirmar")

        btn = ctk.CTkButton(
            body, text="Confirmar", command=confirmar,
            fg_color=COR_AZUL, hover_color="#1D4ED8",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            corner_radius=10, height=42,
        )
        btn.pack(fill="x", pady=(0, 8))

        ctk.CTkButton(
            body, text="Cancelar", command=win.destroy,
            fg_color="#E2E8F0", hover_color="#CBD5E1",
            text_color=COR_TEXTO,
            font=ctk.CTkFont("Segoe UI", 10),
            corner_radius=10, height=34,
        ).pack(fill="x")

        win.wait_window()

    def _iniciar_polling(self, win, root, payment_id: int, lbl_status):
        def _check():
            if not self._polling_ativo:
                return
            try:
                r = httpx.get(f"{API_URL}/pagamento/status/{payment_id}", timeout=5)
                if r.status_code == 200 and r.json().get("status") == "approved":
                    self._polling_ativo = False
                    try:
                        win.after(0, lambda: self._pagamento_confirmado(win, root))
                    except Exception:
                        pass
                    return
            except Exception:
                pass
            try:
                win.after(5000, lambda: threading.Thread(target=_check, daemon=True).start())
            except Exception:
                pass

        threading.Thread(target=_check, daemon=True).start()

    def _pagamento_confirmado(self, win, root):
        try:
            for widget in win.winfo_children():
                widget.destroy()
        except Exception:
            return

        win.configure(fg_color=COR_VERDE)

        body = ctk.CTkFrame(win, fg_color=COR_VERDE)
        body.pack(fill="both", expand=True, padx=40, pady=40)

        ctk.CTkLabel(body, text="✓",
                    font=ctk.CTkFont("Segoe UI", 56, "bold"),
                    text_color="white").pack(pady=(0, 10))

        ctk.CTkLabel(body, text="Pagamento confirmado!",
                    font=ctk.CTkFont("Segoe UI", 18, "bold"),
                    text_color="white").pack()

        ctk.CTkLabel(body, text="Seu acesso foi renovado por 30 dias.",
                    font=ctk.CTkFont("Segoe UI", 12),
                    text_color="white").pack(pady=(6, 0))

        lbl = ctk.CTkLabel(body, text="Abrindo o sistema em 3...",
                        font=ctk.CTkFont("Segoe UI", 11),
                        text_color="white")
        lbl.pack(pady=(16, 0))

        def countdown(n):
            if n <= 0:
                try:
                    win.destroy()
                    root.deiconify()
                    self._verificar_update(root)
                except Exception:
                    pass
                return
            try:
                lbl.configure(text=f"Abrindo o sistema em {n}...")
                win.after(1000, lambda: countdown(n - 1))
            except Exception:
                pass

        win.after(800, lambda: countdown(3))

    # ══════════════════════════════════════════════════════════════════
    # UPDATE AUTOMÁTICO
    # ══════════════════════════════════════════════════════════════════
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

    def _popup_update(self, root: ctk.CTk, data: dict):
        win = ctk.CTkToplevel(root)
        win.title("Atualização disponível")
        win.geometry("440x300")
        win.configure(fg_color=COR_CARD)
        win.resizable(False, False)
        win.transient(root)
        win.grab_set()

        hdr = ctk.CTkFrame(win, fg_color=COR_VERDE, corner_radius=0, height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=f"🆕  Nova versão: {data['versao']}",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color="white").pack(side="left", padx=16, pady=12)

        body = ctk.CTkFrame(win, fg_color=COR_CARD)
        body.pack(fill="both", expand=True, padx=28, pady=20)

        ctk.CTkLabel(body,
                     text=f"Versão atual: {VERSAO_ATUAL}   →   Nova: {data['versao']}",
                     font=ctk.CTkFont("Segoe UI", 11, "bold"),
                     text_color=COR_TEXTO).pack(pady=(0, 6))

        if data.get("notas"):
            ctk.CTkLabel(body, text=data["notas"],
                         font=ctk.CTkFont("Segoe UI", 10),
                         text_color=COR_SUB, wraplength=370).pack(pady=(0, 12))

        lbl_prog = ctk.CTkLabel(body, text="",
                                font=ctk.CTkFont("Segoe UI", 10),
                                text_color=COR_SUB)
        lbl_prog.pack()

        barra = ctk.CTkProgressBar(body, width=360, height=12,
                                   corner_radius=6, fg_color="#E2E8F0",
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
                    url   = data["url"]
                    head  = httpx.head(url, follow_redirects=True, timeout=10)
                    total = int(head.headers.get("content-length", 0))

                    dest_dir = (os.path.dirname(sys.executable)
                                if hasattr(sys, "_MEIPASS")
                                else os.path.dirname(os.path.abspath(__file__)))
                    installer = os.path.join(dest_dir, "_update_installer.exe")

                    baixado = 0
                    with httpx.stream("GET", url, follow_redirects=True, timeout=60) as resp:
                        with open(installer, "wb") as f:
                            for chunk in resp.iter_bytes(chunk_size=65536):
                                f.write(chunk)
                                baixado += len(chunk)
                                if total > 0:
                                    p = baixado / total
                                    b = baixado / 1_048_576
                                    t = total   / 1_048_576
                                    root.after(0, lambda p=p, b=b, t=t: (
                                        barra.set(p),
                                        lbl_prog.configure(
                                            text=f"Baixando... {b:.1f} MB / {t:.1f} MB  ({p*100:.0f}%)")
                                    ))

                    root.after(0, lambda: lbl_prog.configure(text="✓ Download concluído. Instalando..."))
                    root.after(0, lambda: barra.set(1))
                    root.after(800, lambda: _instalar(installer))

                except Exception as e:
                    root.after(0, lambda: lbl_prog.configure(
                        text=f"✗ Erro: {e}", text_color=COR_ERRO))
                    root.after(0, lambda: btn_sim.configure(
                        state="normal", text="Tentar novamente"))
                    root.after(0, lambda: btn_nao.configure(state="normal"))

            def _instalar(path):
                try:
                    subprocess.Popen(
                        [path, "/silent", "/closeapplications", "/restartapplications"],
                        creationflags=subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0
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