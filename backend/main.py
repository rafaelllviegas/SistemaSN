# backend/main.py
"""
Backend de Licenciamento — Calculadora DAS
Hospedagem: Railway  |  Banco: Supabase  |  Pagamento: Mercado Pago
"""

from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from datetime import datetime, timezone, timedelta
import os, secrets, string, httpx, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading

app = FastAPI(title="DAS Licenser API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Configuração ──────────────────────────────────────────────────────
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
ADMIN_SECRET = os.environ["ADMIN_SECRET"]
MP_ACCESS_TOKEN = os.environ["MP_ACCESS_TOKEN"]
EMAIL_USER = os.environ["EMAIL_USER"]
EMAIL_PASS = os.environ["EMAIL_PASS"]
API_BASE_URL = os.environ.get(
    "API_BASE_URL", "https://sistemasn-production.up.railway.app"
)

TRIAL_DIAS = 30
VALOR_MENSAL = 4.99
MP_API = "https://api.mercadopago.com"


def get_db() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ── Helpers ───────────────────────────────────────────────────────────
def gerar_chave() -> str:
    chars = string.ascii_uppercase + string.digits
    grupos = ["".join(secrets.choice(chars) for _ in range(4)) for _ in range(4)]
    return "-".join(grupos)


def admin_required(x_admin_secret: str = Header(...)):
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Acesso negado.")


def enviar_email(destinatario: str, chave: str, nome: str = ""):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🔑 Sua chave de acesso — Calculadora DAS"
        msg["From"] = EMAIL_USER
        msg["To"] = destinatario

        corpo = f"""
        <html><body style="font-family: Segoe UI, sans-serif; background:#F1F5F9; padding:32px;">
          <div style="max-width:480px; margin:0 auto; background:#fff; border-radius:16px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,0.08);">
            <div style="background:#1E3A5F; padding:24px 32px;">
              <h2 style="color:white; margin:0;">📊 Calculadora DAS — Simples Nacional</h2>
            </div>
            <div style="padding:32px;">
              <p style="color:#1E293B; font-size:16px;">Olá{(' ' + nome) if nome else ''}! Sua conta foi criada com sucesso.</p>
              <p style="color:#64748B;">Sua chave de acesso é:</p>
              <div style="background:#F1F5F9; border-radius:10px; padding:20px; text-align:center; margin:20px 0;">
                <span style="font-size:24px; font-weight:bold; letter-spacing:4px; color:#2563EB;">{chave}</span>
              </div>
              <p style="color:#64748B; font-size:14px;">Você tem <strong>30 dias gratuitos</strong>. Após esse período, o acesso custa <strong>R$ 4,99/mês</strong>, renovado via PIX.</p>
              <hr style="border:none; border-top:1px solid #E2E8F0; margin:24px 0;">
              <p style="color:#94A3B8; font-size:12px;">Se você não criou esta conta, ignore este email.</p>
            </div>
          </div>
        </body></html>
        """

        msg.attach(MIMEText(corpo, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(EMAIL_USER, EMAIL_PASS)
            servidor.sendmail(EMAIL_USER, destinatario, msg.as_string())

        return True
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False


# ── Schemas ───────────────────────────────────────────────────────────
class CadastroRequest(BaseModel):
    email: str
    nome: str = ""


class ValidarRequest(BaseModel):
    chave: str
    machine_id: str


class GerarPagamentoRequest(BaseModel):
    chave: str
    email: str


class GerarLicencaRequest(BaseModel):
    nome_cliente: str
    email: str
    max_maquinas: int = 1
    dias_validade: int = 365


class RevogarRequest(BaseModel):
    chave: str


class NovaVersaoRequest(BaseModel):
    versao: str
    url_download: str
    notas: str = ""


# ══════════════════════════════════════════════════════════════════════
# ROTAS PÚBLICAS
# ══════════════════════════════════════════════════════════════════════


@app.post("/cadastro")
def cadastro(req: CadastroRequest):
    """
    Novo usuário se cadastra com email.
    Cria licença trial de 30 dias e envia chave por email.
    """
    db = get_db()

    # Verifica se email já existe
    existente = db.table("licencas").select("id").eq("email", req.email).execute()
    if existente.data:
        raise HTTPException(
            400, "Este email já possui uma conta. Use sua chave de acesso."
        )

    chave = gerar_chave()
    nome = req.nome or req.email.split("@")[0]
    expira_em = (datetime.now(timezone.utc) + timedelta(days=TRIAL_DIAS)).isoformat()

    db.table("licencas").insert(
        {
            "chave": chave,
            "nome_cliente": nome,
            "email": req.email,
            "status": "ativa",
            "max_maquinas": 1,
            "expira_em": expira_em,
            "trial_inicio": datetime.now(timezone.utc).isoformat(),
            "plano": "trial",
        }
    ).execute()

    threading.Thread(
        target=enviar_email, args=(req.email, chave, nome), daemon=True
    ).start()
    email_ok = True

    return {
        "mensagem": "Conta criada com sucesso! Verifique seu email.",
        "email_ok": email_ok,
        "trial_dias": TRIAL_DIAS,
    }


@app.post("/validar")
def validar_licenca(req: ValidarRequest):
    """
    Valida chave + registra máquina.
    Retorna 402 se trial expirado (precisa pagar).
    """
    db = get_db()

    res = db.table("licencas").select("*").eq("chave", req.chave).execute()
    if not res.data:
        raise HTTPException(400, "Chave de licença inválida.")

    lic = res.data[0]

    if lic["status"] == "revogada":
        raise HTTPException(403, "Licença revogada. Contate o suporte.")

    # Verifica expiração
    if lic["expira_em"]:
        expira = datetime.fromisoformat(lic["expira_em"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expira:
            # Marca como suspenso se for trial
            if lic["plano"] == "trial":
                db.table("licencas").update({"plano": "suspenso"}).eq(
                    "chave", req.chave
                ).execute()
            raise HTTPException(402, "trial_expirado")

    if lic["plano"] == "suspenso":
        raise HTTPException(402, "trial_expirado")

    # Registra máquina
    maquinas = db.table("maquinas").select("*").eq("licenca_id", lic["id"]).execute()
    ids = [m["machine_id"] for m in maquinas.data]

    if req.machine_id not in ids:
        if len(ids) >= lic["max_maquinas"]:
            raise HTTPException(
                403, f"Limite de {lic['max_maquinas']} máquina(s) atingido."
            )
        db.table("maquinas").insert(
            {
                "licenca_id": lic["id"],
                "machine_id": req.machine_id,
            }
        ).execute()

    db.table("licencas").update(
        {"ultimo_acesso": datetime.now(timezone.utc).isoformat()}
    ).eq("chave", req.chave).execute()

    return {
        "valido": True,
        "mensagem": "Licença válida.",
        "cliente": lic["nome_cliente"],
        "expira_em": lic["expira_em"],
        "plano": lic["plano"],
    }


@app.post("/pagamento/gerar")
def gerar_pagamento(req: GerarPagamentoRequest):
    """
    Gera QR Code PIX via Mercado Pago para renovação mensal.
    """
    db = get_db()

    res = db.table("licencas").select("*").eq("chave", req.chave).execute()
    if not res.data:
        raise HTTPException(400, "Chave inválida.")

    lic = res.data[0]

    # Cria pagamento no Mercado Pago
    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": secrets.token_hex(16),
    }

    payload = {
        "transaction_amount": VALOR_MENSAL,
        "description": "Calculadora DAS — Assinatura Mensal",
        "payment_method_id": "pix",
        "payer": {"email": req.email},
        "notification_url": f"{API_BASE_URL}/pagamento/webhook",
        "metadata": {"licenca_id": str(lic["id"]), "chave": req.chave},
    }

    resp = httpx.post(
        f"{MP_API}/v1/payments", json=payload, headers=headers, timeout=15
    )

    if resp.status_code not in (200, 201):
        raise HTTPException(500, f"Erro Mercado Pago: {resp.text}")

    data = resp.json()
    payment_id = data["id"]
    tx = data["point_of_interaction"]["transaction_data"]

    # Salva pagamento no banco
    db.table("pagamentos").insert(
        {
            "licenca_id": lic["id"],
            "mp_payment_id": payment_id,
            "status": "pending",
            "valor": VALOR_MENSAL,
        }
    ).execute()

    return {
        "payment_id": payment_id,
        "qr_code": tx["qr_code"],  # copia e cola PIX
        "qr_code_base64": tx["qr_code_base64"],  # imagem QR
        "valor": VALOR_MENSAL,
    }


@app.get("/pagamento/status/{payment_id}")
def status_pagamento(payment_id: int):
    """
    Consultado pelo app a cada 5 segundos para saber se foi pago.
    """
    db = get_db()

    pag = db.table("pagamentos").select("*").eq("mp_payment_id", payment_id).execute()
    if not pag.data:
        raise HTTPException(404, "Pagamento não encontrado.")

    return {"status": pag.data[0]["status"]}


@app.post("/pagamento/webhook")
async def webhook_pagamento(request: Request):
    """
    Mercado Pago chama esta rota quando o pagamento é confirmado.
    Ativa/renova a licença automaticamente.
    """
    try:
        body = await request.json()
    except Exception:
        return {"ok": True}

    if body.get("type") != "payment":
        return {"ok": True}

    mp_payment_id = body.get("data", {}).get("id")
    if not mp_payment_id:
        return {"ok": True}

    # Consulta status no MP
    headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
    resp = httpx.get(
        f"{MP_API}/v1/payments/{mp_payment_id}", headers=headers, timeout=10
    )
    if resp.status_code != 200:
        return {"ok": True}

    data = resp.json()
    status = data.get("status")

    if status != "approved":
        return {"ok": True}

    db = get_db()

    # Busca pagamento no banco
    pag = (
        db.table("pagamentos")
        .select("*")
        .eq("mp_payment_id", int(mp_payment_id))
        .execute()
    )
    if not pag.data:
        return {"ok": True}

    pagamento = pag.data[0]

    if pagamento["status"] == "approved":
        return {"ok": True}  # já processado

    # Atualiza pagamento
    db.table("pagamentos").update(
        {
            "status": "approved",
            "pago_em": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("mp_payment_id", int(mp_payment_id)).execute()

    # Renova licença por 30 dias
    lic = db.table("licencas").select("*").eq("id", pagamento["licenca_id"]).execute()
    if not lic.data:
        return {"ok": True}

    licenca = lic.data[0]
    expira_em = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    db.table("licencas").update(
        {
            "status": "ativa",
            "plano": "ativo",
            "expira_em": expira_em,
        }
    ).eq("id", pagamento["licenca_id"]).execute()

    return {"ok": True}


@app.get("/versao")
def verificar_versao(versao_atual: str):
    db = get_db()
    res = (
        db.table("versoes").select("*").order("criado_em", desc=True).limit(1).execute()
    )
    if not res.data:
        return {"atualizado": True, "versao": versao_atual, "url": None, "notas": ""}
    ultima = res.data[0]
    atualizado = ultima["versao"] == versao_atual
    return {
        "atualizado": atualizado,
        "versao": ultima["versao"],
        "url": ultima["url_download"],
        "notas": ultima["notas"],
    }


# ══════════════════════════════════════════════════════════════════════
# ROTAS ADMIN
# ══════════════════════════════════════════════════════════════════════


@app.post("/admin/gerar", dependencies=[Depends(admin_required)])
def gerar_licenca(req: GerarLicencaRequest):
    db = get_db()
    chave = gerar_chave()
    expira_em = None
    if req.dias_validade > 0:
        expira_em = (
            datetime.now(timezone.utc) + timedelta(days=req.dias_validade)
        ).isoformat()

    db.table("licencas").insert(
        {
            "chave": chave,
            "nome_cliente": req.nome_cliente,
            "email": req.email,
            "max_maquinas": req.max_maquinas,
            "expira_em": expira_em,
            "status": "ativa",
            "plano": "ativo",
        }
    ).execute()

    return {
        "chave": chave,
        "nome_cliente": req.nome_cliente,
        "email": req.email,
        "expira_em": expira_em,
    }


@app.post("/admin/revogar", dependencies=[Depends(admin_required)])
def revogar_licenca(req: RevogarRequest):
    db = get_db()
    res = (
        db.table("licencas")
        .update({"status": "revogada"})
        .eq("chave", req.chave)
        .execute()
    )
    if not res.data:
        raise HTTPException(404, "Chave não encontrada.")
    return {"mensagem": f"Licença {req.chave} revogada."}


@app.post("/admin/reativar", dependencies=[Depends(admin_required)])
def reativar_licenca(req: RevogarRequest):
    db = get_db()
    expira_em = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    db.table("licencas").update(
        {"status": "ativa", "plano": "ativo", "expira_em": expira_em}
    ).eq("chave", req.chave).execute()
    return {"mensagem": f"Licença {req.chave} reativada por 30 dias."}


@app.delete("/admin/maquina", dependencies=[Depends(admin_required)])
def remover_maquina(chave: str, machine_id: str):
    db = get_db()
    res = db.table("licencas").select("id").eq("chave", chave).execute()
    if not res.data:
        raise HTTPException(404, "Chave não encontrada.")
    db.table("maquinas").delete().eq("licenca_id", res.data[0]["id"]).eq(
        "machine_id", machine_id
    ).execute()
    return {"mensagem": "Máquina removida."}


@app.get("/admin/clientes", dependencies=[Depends(admin_required)])
def listar_clientes():
    db = get_db()
    res = db.table("licencas").select("*").order("criado_em", desc=True).execute()
    return res.data


@app.post("/admin/versao", dependencies=[Depends(admin_required)])
def publicar_versao(req: NovaVersaoRequest):
    db = get_db()
    db.table("versoes").insert(
        {
            "versao": req.versao,
            "url_download": req.url_download,
            "notas": req.notas,
        }
    ).execute()
    return {"mensagem": f"Versão {req.versao} publicada."}


@app.get("/admin/testar-email", dependencies=[Depends(admin_required)])
def testar_email(destinatario: str):
    ok = enviar_email(destinatario, "XXXX-TEST-TEST-TEST", "Teste")
    return {"ok": ok}

@app.get("/")
def health():
    return {"status": "online", "servico": "DAS Licenser API", "versao": "2.0.0"}