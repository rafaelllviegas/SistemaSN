"""
Backend de Licenciamento — Calculadora DAS
Hospedagem: Railway  |  Banco: Supabase
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from datetime import datetime, timezone
import os, secrets, string, httpx

app = FastAPI(title="DAS Licenser API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Supabase ──────────────────────────────────────────────────────────
SUPABASE_URL  = os.environ["SUPABASE_URL"]
SUPABASE_KEY  = os.environ["SUPABASE_KEY"]
ADMIN_SECRET  = os.environ["ADMIN_SECRET"]   # senha sua para rotas admin

def get_db() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Helpers ───────────────────────────────────────────────────────────
def gerar_chave() -> str:
    """Gera chave no formato XXXX-XXXX-XXXX-XXXX"""
    chars = string.ascii_uppercase + string.digits
    grupos = ["".join(secrets.choice(chars) for _ in range(4)) for _ in range(4)]
    return "-".join(grupos)

def admin_required(x_admin_secret: str = Header(...)):
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Acesso negado.")

# ── Schemas ───────────────────────────────────────────────────────────
class ValidarRequest(BaseModel):
    chave: str
    machine_id: str

class GerarLicencaRequest(BaseModel):
    nome_cliente: str
    email: str
    max_maquinas: int = 1
    dias_validade: int = 365   # 0 = sem expiração

class RevogarRequest(BaseModel):
    chave: str

class NovaVersaoRequest(BaseModel):
    versao: str
    url_download: str
    notas: str = ""


# ══════════════════════════════════════════════════════════════════════
# ROTAS PÚBLICAS (usadas pelo app desktop)
# ══════════════════════════════════════════════════════════════════════

@app.post("/validar")
def validar_licenca(req: ValidarRequest):
    """
    Chamada pelo app ao abrir. Valida chave + registra máquina.
    Retorna: {"valido": bool, "mensagem": str, "cliente": str}
    """
    db = get_db()

    # Busca a licença
    res = db.table("licencas").select("*").eq("chave", req.chave).execute()
    if not res.data:
        raise HTTPException(400, "Chave de licença inválida.")

    lic = res.data[0]

    # Verifica se está ativa
    if lic["status"] != "ativa":
        raise HTTPException(403, f"Licença {lic['status']}. Contate o suporte.")

    # Verifica expiração
    if lic["expira_em"]:
        expira = datetime.fromisoformat(lic["expira_em"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expira:
            db.table("licencas").update({"status": "expirada"}).eq("chave", req.chave).execute()
            raise HTTPException(403, "Licença expirada. Renove para continuar.")

    # Verifica máquinas registradas
    maquinas = db.table("maquinas").select("*").eq("licenca_id", lic["id"]).execute()
    ids = [m["machine_id"] for m in maquinas.data]

    if req.machine_id not in ids:
        if len(ids) >= lic["max_maquinas"]:
            raise HTTPException(403,
                f"Limite de {lic['max_maquinas']} máquina(s) atingido. "
                "Contate o suporte para adicionar um dispositivo.")
        # Registra nova máquina
        db.table("maquinas").insert({
            "licenca_id": lic["id"],
            "machine_id": req.machine_id,
        }).execute()

    # Atualiza último acesso
    db.table("licencas").update({
        "ultimo_acesso": datetime.now(timezone.utc).isoformat()
    }).eq("chave", req.chave).execute()

    return {
        "valido": True,
        "mensagem": "Licença válida.",
        "cliente": lic["nome_cliente"],
        "expira_em": lic["expira_em"],
    }


@app.get("/versao")
def verificar_versao(versao_atual: str):
    """
    Chamada pelo app para checar se há update disponível.
    Retorna: {"atualizado": bool, "versao": str, "url": str, "notas": str}
    """
    db = get_db()
    res = db.table("versoes").select("*").order("criado_em", desc=True).limit(1).execute()

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
# ROTAS ADMIN (protegidas pelo ADMIN_SECRET no header)
# ══════════════════════════════════════════════════════════════════════

@app.post("/admin/gerar", dependencies=[Depends(admin_required)])
def gerar_licenca(req: GerarLicencaRequest):
    """Gera uma nova chave de licença para um cliente."""
    db = get_db()

    chave = gerar_chave()

    expira_em = None
    if req.dias_validade > 0:
        from datetime import timedelta
        expira_em = (datetime.now(timezone.utc) + timedelta(days=req.dias_validade)).isoformat()

    db.table("licencas").insert({
        "chave":        chave,
        "nome_cliente": req.nome_cliente,
        "email":        req.email,
        "max_maquinas": req.max_maquinas,
        "expira_em":    expira_em,
        "status":       "ativa",
    }).execute()

    return {
        "chave":        chave,
        "nome_cliente": req.nome_cliente,
        "email":        req.email,
        "expira_em":    expira_em,
        "max_maquinas": req.max_maquinas,
    }


@app.post("/admin/revogar", dependencies=[Depends(admin_required)])
def revogar_licenca(req: RevogarRequest):
    """Revoga uma licença imediatamente."""
    db = get_db()
    res = db.table("licencas").update({"status": "revogada"}).eq("chave", req.chave).execute()
    if not res.data:
        raise HTTPException(404, "Chave não encontrada.")
    return {"mensagem": f"Licença {req.chave} revogada com sucesso."}


@app.post("/admin/reativar", dependencies=[Depends(admin_required)])
def reativar_licenca(req: RevogarRequest):
    """Reativa uma licença revogada ou expirada."""
    db = get_db()
    db.table("licencas").update({"status": "ativa"}).eq("chave", req.chave).execute()
    return {"mensagem": f"Licença {req.chave} reativada."}


@app.delete("/admin/maquina", dependencies=[Depends(admin_required)])
def remover_maquina(chave: str, machine_id: str):
    """Remove uma máquina de uma licença (para o cliente trocar de PC)."""
    db = get_db()
    res = db.table("licencas").select("id").eq("chave", chave).execute()
    if not res.data:
        raise HTTPException(404, "Chave não encontrada.")
    lic_id = res.data[0]["id"]
    db.table("maquinas").delete().eq("licenca_id", lic_id).eq("machine_id", machine_id).execute()
    return {"mensagem": "Máquina removida. O cliente pode registrar um novo dispositivo."}


@app.get("/admin/clientes", dependencies=[Depends(admin_required)])
def listar_clientes():
    """Lista todos os clientes e status das licenças."""
    db = get_db()
    res = db.table("licencas").select("*").order("criado_em", desc=True).execute()
    return res.data


@app.post("/admin/versao", dependencies=[Depends(admin_required)])
def publicar_versao(req: NovaVersaoRequest):
    """Publica uma nova versão. Todos os clientes receberão o update."""
    db = get_db()
    db.table("versoes").insert({
        "versao":       req.versao,
        "url_download": req.url_download,
        "notas":        req.notas,
    }).execute()
    return {"mensagem": f"Versão {req.versao} publicada. Clientes receberão update automático."}


@app.get("/")
def health():
    return {"status": "online", "servico": "DAS Licenser API"}