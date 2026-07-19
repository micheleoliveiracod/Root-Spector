"""Nós do grafo LangGraph -- implementam Ishikawa (6 categorias) seguido de
5 Porquês, ambos em conversa com o operador (human-in-the-loop). Ver
specs/design.md para o fluxo completo.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from langchain_core.messages import HumanMessage, RemoveMessage, SystemMessage
from langgraph.types import interrupt
from pydantic import BaseModel

from root_cause_agent.config import DB_PATH, get_llm
from root_cause_agent.models import (
    CategoriaAnalise,
    CategoriaDescartada,
    Classification,
    Diagnostico,
    MetricaSensor,
    NaoConformidade,
    PorQue,
    RespostaIshikawa,
    RiskPrediction,
)
from root_cause_agent.state import CATEGORIAS_ISHIKAWA_ORDEM, AgentState
from root_cause_agent.tools import TOOLS, validar_resposta_operador

PARAMETROS_BIOSENSOR = ["temperature", "ph", "dissolved_oxygen", "pressure", "agitator_speed"]


class FalhaLLMError(Exception):
    """Levantada quando get_llm() falha mesmo depois de esgotar toda a
    cadeia de fallback configurada (Gemini -> Anthropic -> OpenAI). A API
    (backend/main.py) traduz isso em HTTP 503 -- ver specs/design.md §
    Tratamento de falha na chamada ao LLM."""


def _invocar_ou_falhar(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        raise FalhaLLMError(str(exc)) from exc


def _resumo_nc(nc: NaoConformidade) -> str:
    fora_da_faixa = ", ".join(nc.parametros_fora_da_faixa) or "nenhum"
    metricas = "; ".join(
        f"{p}: média {m.media:.1f}{m.unidade} (min {m.minimo:.1f}, max {m.maximo:.1f})"
        for p, m in nc.sensor_metrics.items()
    )
    return (
        f"Lote {nc.batch_id}, classificação {nc.classification.value} "
        f"(compliance_score={nc.compliance_score}, risk_prediction={nc.risk_prediction.value}). "
        f"Parâmetro(s) fora da faixa: {fora_da_faixa}. Métricas: {metricas}."
    )


def _limpar_mensagens(state: AgentState) -> list:
    return [RemoveMessage(id=m.id) for m in state["messages"]]


def _fase_atual(state: AgentState) -> str:
    return "ishikawa" if state["categoria_principal"] is None else "porques"


def _progresso_pergunta(state: AgentState) -> dict:
    """Info de progresso mostrada ao operador junto da pergunta -- em qual
    das 6 categorias do Ishikawa ou qual dos 5 Porquês ele está."""
    fase = _fase_atual(state)
    if fase == "ishikawa":
        categoria = state["categoria_atual"]
        indice = CATEGORIAS_ISHIKAWA_ORDEM.index(categoria) + 1
        return {
            "fase": fase,
            "categoria": categoria,
            "indice": indice,
            "total": len(CATEGORIAS_ISHIKAWA_ORDEM),
        }
    return {"fase": fase, "indice": state["numero_porque"], "total": 5}


def calcular_sensor_metrics(
    leituras: list, regras: dict
) -> tuple[dict[str, MetricaSensor], list[str]]:
    """Média/mínimo/máximo por parâmetro de biosensor e quais estão fora da
    faixa aceitável (config/regras_bioprocesso.yaml) -- reusado por
    preparar_contexto e por GET /api/lotes (backend/main.py), que mostra o
    histórico de parâmetros ao operador antes/durante a investigação. Um
    parâmetro é considerado fora da faixa se o mínimo OU o máximo das
    leituras ultrapassa aceitavel_min/aceitavel_max -- não a média."""
    sensor_metrics: dict[str, MetricaSensor] = {}
    parametros_fora_da_faixa: list[str] = []
    for param in PARAMETROS_BIOSENSOR:
        valores = [r[param] for r in leituras]
        faixa = regras["parametros_biosensor"][param]
        minimo, maximo = min(valores), max(valores)
        dentro = faixa["aceitavel_min"] <= minimo and maximo <= faixa["aceitavel_max"]
        sensor_metrics[param] = MetricaSensor(
            parametro=param,
            media=sum(valores) / len(valores),
            minimo=minimo,
            maximo=maximo,
            unidade=faixa["unidade"],
            dentro_da_faixa=dentro,
        )
        if not dentro:
            parametros_fora_da_faixa.append(param)
    return sensor_metrics, parametros_fora_da_faixa


# --------------------------------------------------------------- workflow --

def preparar_contexto(state: AgentState) -> dict:
    """Determinístico: SELECT em batches/sensor_readings, calcula
    sensor_metrics e parametros_fora_da_faixa comparando contra
    config/regras_bioprocesso.yaml, monta a NaoConformidade."""
    from root_cause_agent.config import carregar_regras_setor

    regras = carregar_regras_setor()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        batch = conn.execute(
            "SELECT id, upload_date, status, compliance_score, risk_prediction "
            "FROM batches WHERE id = ?",
            (state["batch_id"],),
        ).fetchone()
        if batch is None:
            raise ValueError(f"Lote {state['batch_id']} não encontrado.")
        leituras = conn.execute(
            "SELECT temperature, ph, dissolved_oxygen, pressure, agitator_speed "
            "FROM sensor_readings WHERE batch_id = ?",
            (state["batch_id"],),
        ).fetchall()
    finally:
        conn.close()

    thresholds = regras["classification_thresholds"]
    score = batch["compliance_score"]
    if score >= thresholds["acceptable_min"]:
        classification = Classification.ACCEPTABLE
    elif score >= thresholds["warning_min"]:
        classification = Classification.WARNING
    else:
        classification = Classification.CRITICAL

    sensor_metrics, parametros_fora_da_faixa = calcular_sensor_metrics(leituras, regras)

    nc_input = NaoConformidade(
        batch_id=batch["id"],
        upload_date=batch["upload_date"],
        compliance_score=score,
        classification=classification,
        risk_prediction=RiskPrediction(batch["risk_prediction"]),
        sensor_metrics=sensor_metrics,
        parametros_fora_da_faixa=parametros_fora_da_faixa,
    )

    return {
        "nc_input": nc_input,
        "regras_setor": regras,
        "categoria_atual": CATEGORIAS_ISHIKAWA_ORDEM[0],
        "respostas_ishikawa": {},
        "categoria_principal": None,
        "categorias_descartadas": [],
        "cadeia_porques": [],
        "numero_porque": 1,
        "pergunta_atual": None,
        "tentativas_pergunta_atual": [],
        "diagnostico": None,
        "ciclos_anteriores": state.get("ciclos_anteriores", []),
        "messages": _limpar_mensagens(state) if state.get("messages") else [],
    }


# ----------------------------------------------------------- nós agênticos --

def _formular_pergunta(state: AgentState, instrucao_sistema: str, contexto_humano: str) -> dict:
    """Compartilhado por formular_pergunta_ishikawa/formular_porque: na
    primeira chamada (sem mensagens pendentes) o LLM tem a ferramenta
    disponível; se ele optar por não chamá-la, ou na segunda chamada (após
    o resultado da ferramenta), a pergunta final vem no conteúdo da
    resposta -- no máximo 1 consulta à ferramenta por pergunta, porque só
    a primeira chamada tem a tool vinculada."""
    primeira_chamada = not state["messages"]
    if primeira_chamada:
        mensagens_novas = [
            SystemMessage(content=instrucao_sistema),
            HumanMessage(content=contexto_humano),
        ]
        llm_chamada = get_llm().bind_tools(TOOLS)
        entrada = mensagens_novas
    else:
        mensagens_novas = []
        llm_chamada = get_llm()
        entrada = state["messages"]

    resposta = _invocar_ou_falhar(llm_chamada.invoke, entrada)
    atualizacao: dict = {"messages": mensagens_novas + [resposta]}
    if not getattr(resposta, "tool_calls", None):
        # .text (não .content): alguns modelos (ex. gemini-2.5-flash) devolvem
        # content como lista de blocos estruturados, não string simples --
        # .text normaliza os dois formatos.
        atualizacao["pergunta_atual"] = resposta.text
    return atualizacao


def formular_pergunta_ishikawa(state: AgentState) -> dict:
    categoria = state["categoria_atual"]
    pergunta_modelo = next(
        c["pergunta_modelo"]
        for c in state["regras_setor"]["categorias_ishikawa"]
        if c["categoria"] == categoria
    )
    instrucao = (
        "Você conduz uma investigação de causa raiz de não-conformidade de "
        "bioprocesso usando o diagrama de Ishikawa (6M). Formule UMA pergunta "
        f"de contexto para a categoria '{categoria}', adaptando (sem repetir "
        f"literalmente) esta pergunta-modelo: \"{pergunta_modelo}\". A pergunta "
        "deve buscar contexto da categoria, não perguntar diretamente sobre o "
        "parâmetro fora da faixa. Use a ferramenta disponível no máximo uma "
        "vez, só se precisar de dado histórico de biosensor para contextualizar."
    )
    return _formular_pergunta(state, instrucao, _resumo_nc(state["nc_input"]))


def orquestrar_analise(state: AgentState) -> dict:
    """Papel de 'orquestrador', implementado como nó (não agente separado --
    ver specs/design.md § Decisão de simplicidade)."""

    class _Analise(BaseModel):
        categoria_principal: CategoriaAnalise
        categorias_descartadas: list[CategoriaDescartada]

    respostas_texto = "\n".join(
        f"- {cat}: {state['respostas_ishikawa'][cat].resposta}" for cat in CATEGORIAS_ISHIKAWA_ORDEM
    )
    instrucao = (
        "Analise as 6 respostas do mapeamento Ishikawa (Método, Máquina, "
        "Material, Mão de obra, Meio ambiente, Medição) desta investigação de "
        "não-conformidade de bioprocesso. Identifique a categoria mais "
        "provável de conter a causa raiz (com justificativa) e registre as "
        "demais categorias como descartadas (com o motivo), verificando "
        "inconsistências entre as respostas."
    )
    contexto = _resumo_nc(state["nc_input"]) + "\n\nRespostas:\n" + respostas_texto
    resultado = _invocar_ou_falhar(
        get_llm().with_structured_output(_Analise).invoke,
        [SystemMessage(content=instrucao), HumanMessage(content=contexto)],
    )
    return {
        "categoria_principal": resultado.categoria_principal,
        "categorias_descartadas": resultado.categorias_descartadas,
    }


def formular_porque(state: AgentState) -> dict:
    numero = state["numero_porque"]
    if numero == 1:
        ancora = (
            f"Categoria identificada como mais provável: {state['categoria_principal'].categoria}. "
            f"Justificativa: {state['categoria_principal'].justificativa}"
        )
    else:
        ancora = f"Resposta anterior: {state['cadeia_porques'][-1].resposta}"
    instrucao = (
        "Você conduz o método dos 5 Porquês, aprofundando a causa raiz de uma "
        f"não-conformidade de bioprocesso. Esta é a pergunta nº {numero} de 5. "
        "Formule UMA pergunta 'por quê' que aprofunde a partir da âncora "
        "abaixo. Use a ferramenta disponível no máximo uma vez, só se "
        "precisar de mais evidência de biosensor."
    )
    contexto = _resumo_nc(state["nc_input"]) + "\n" + ancora
    return _formular_pergunta(state, instrucao, contexto)


def gerar_causa_raiz(state: AgentState) -> dict:
    """Papel de 'relatório', também implementado como nó."""

    class _CausaRaiz(BaseModel):
        causa_raiz: str
        narrativa: str

    porques_texto = "\n".join(
        f"{p.numero}. {p.pergunta} -> {p.resposta}" for p in state["cadeia_porques"]
    )
    instrucao = (
        "Sintetize a causa raiz sistêmica desta investigação de "
        "não-conformidade de bioprocesso, a partir da categoria Ishikawa "
        "principal e da cadeia completa dos 5 Porquês. Produza uma causa raiz "
        "objetiva e uma narrativa curta explicando o raciocínio."
    )
    contexto = (
        _resumo_nc(state["nc_input"])
        + f"\nCategoria principal: {state['categoria_principal'].categoria} "
        f"({state['categoria_principal'].justificativa})\nCadeia de 5 Porquês:\n{porques_texto}"
    )
    resultado = _invocar_ou_falhar(
        get_llm().with_structured_output(_CausaRaiz).invoke,
        [SystemMessage(content=instrucao), HumanMessage(content=contexto)],
    )

    diagnostico = Diagnostico(
        nc=state["nc_input"],
        respostas_ishikawa=[state["respostas_ishikawa"][c] for c in CATEGORIAS_ISHIKAWA_ORDEM],
        categoria_principal=state["categoria_principal"],
        categorias_descartadas=state["categorias_descartadas"],
        cadeia_de_porques=state["cadeia_porques"],
        causa_raiz=resultado.causa_raiz,
        narrativa=resultado.narrativa,
        ciclos_anteriores=state["ciclos_anteriores"],
        gerado_em=datetime.now(UTC),
    )
    return {"diagnostico": diagnostico}


# ------------------------------------------------------- human-in-the-loop --

def perguntar_operador(state: AgentState) -> dict:
    """Mostra pergunta_atual e pausa via interrupt() -- a API captura a
    resposta e retoma via Command(resume=...). Camada 1 (determinística,
    tools.py::validar_resposta_operador): resposta vazia/evasiva -> chama
    interrupt() de novo com um sinal de erro, sem avançar o grafo e sem
    contar como tentativa (tentativas ilimitadas nesta camada)."""
    pergunta = state["pergunta_atual"]
    nc = state["nc_input"].model_dump(mode="json")
    payload = {"pergunta": pergunta, "nc": nc, **_progresso_pergunta(state)}
    resposta = interrupt(payload)
    while not validar_resposta_operador(resposta):
        payload = {
            "pergunta": pergunta,
            "nc": nc,
            **_progresso_pergunta(state),
            "erro": "Este tipo de resposta não é aceito.",
        }
        resposta = interrupt(payload)
    return {"tentativas_pergunta_atual": state["tentativas_pergunta_atual"] + [resposta]}


def avaliar_informatividade(state: AgentState) -> dict:
    """Camada 2 (agêntica, no máximo 2 tentativas por pergunta): julga se a
    última tentativa de fato informa a pergunta feita. Não informativa e é
    a 1ª tentativa -> não avança nada (perguntar_operador pede de novo, 2ª
    e última chance). Informativa, ou não informativa mas 2ª tentativa
    esgotada -> grava a resposta final e avança a fase."""

    class _Julgamento(BaseModel):
        informativa: bool

    pergunta = state["pergunta_atual"]
    tentativas = state["tentativas_pergunta_atual"]
    ultima = tentativas[-1]

    julgamento = _invocar_ou_falhar(
        get_llm().with_structured_output(_Julgamento).invoke,
        [
            SystemMessage(
                content=(
                    "Julgue se a resposta do operador realmente informa a "
                    "pergunta feita -- não é sobre estar 'certa', é sobre não "
                    "ser vaga, fora do assunto ou contraditória."
                )
            ),
            HumanMessage(content=f"Pergunta: {pergunta}\nResposta: {ultima}"),
        ],
    )

    if not julgamento.informativa and len(tentativas) < 2:
        return {}

    informativa_final = julgamento.informativa
    fase = _fase_atual(state)

    if fase == "ishikawa":
        categoria = state["categoria_atual"]
        entrada = RespostaIshikawa(
            categoria=categoria,
            pergunta=pergunta,
            resposta=ultima,
            tentativas=list(tentativas),
            informativa=informativa_final,
        )
        respostas = {**state["respostas_ishikawa"], categoria: entrada}
        indice = CATEGORIAS_ISHIKAWA_ORDEM.index(categoria)
        ainda_ha_proxima = indice + 1 < len(CATEGORIAS_ISHIKAWA_ORDEM)
        proxima = CATEGORIAS_ISHIKAWA_ORDEM[indice + 1] if ainda_ha_proxima else None
        return {
            "respostas_ishikawa": respostas,
            "categoria_atual": proxima,
            "tentativas_pergunta_atual": [],
            "pergunta_atual": None,
            "messages": _limpar_mensagens(state),
        }

    entrada = PorQue(
        numero=state["numero_porque"],
        pergunta=pergunta,
        resposta=ultima,
        tentativas=list(tentativas),
        informativa=informativa_final,
    )
    return {
        "cadeia_porques": state["cadeia_porques"] + [entrada],
        "numero_porque": state["numero_porque"] + 1,
        "tentativas_pergunta_atual": [],
        "pergunta_atual": None,
        "messages": _limpar_mensagens(state),
    }


# ------------------------------------------------------- roteamento (graph.py) --

def rotear_apos_ferramenta(state: AgentState) -> str:
    """usar_ferramenta é compartilhado pelas duas fases -- volta pro nó que
    chamou, conforme a fase atual."""
    if state["categoria_principal"] is None:
        return "formular_pergunta_ishikawa"
    return "formular_porque"


def rotear_apos_avaliar(state: AgentState) -> str:
    if state["pergunta_atual"] is not None:
        # avaliar_informatividade não avançou (não informativa, 1a tentativa)
        return "perguntar_operador"
    if state["categoria_principal"] is None:
        if state["categoria_atual"] is not None:
            return "formular_pergunta_ishikawa"
        return "orquestrar_analise"
    if state["numero_porque"] <= 5:
        return "formular_porque"
    return "gerar_causa_raiz"
