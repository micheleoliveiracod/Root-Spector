"""Estado compartilhado do grafo LangGraph (AgentState). Ver specs/design.md."""

from __future__ import annotations

from typing import Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from root_cause_agent.models import (
    CandidatoRAG,
    CategoriaAnalise,
    CategoriaDescartada,
    CicloAnterior,
    Diagnostico,
    NaoConformidade,
    PorQue,
    RespostaIshikawa,
)

# Ordem fixa das 6 categorias do Ishikawa -- sempre perguntadas nesta
# sequência (Fase 1), independentemente do que preparar_contexto encontrou.
CATEGORIAS_ISHIKAWA_ORDEM: list[str] = [
    "Metodo",
    "Maquina",
    "Material",
    "Mao de obra",
    "Meio ambiente",
    "Medicao",
]


class AgentState(TypedDict):
    # identificador estável da investigação -- passado no primeiro invoke()
    # e mantido em todos os ciclos (inclusive depois de "pedir ajuste");
    # nc_input é o snapshot recalculado a cada ciclo por preparar_contexto.
    batch_id: int
    nc_input: NaoConformidade
    regras_setor: dict

    # memória do sub-loop de tool-calling dentro de uma única pergunta
    # (Ishikawa ou "por quê")
    messages: Annotated[list[BaseMessage], add_messages]

    # Fase 1 -- mapeamento Ishikawa
    respostas_ishikawa: dict[str, RespostaIshikawa]
    categoria_atual: str | None

    # saída de orquestrar_analise
    categoria_principal: CategoriaAnalise | None
    categorias_descartadas: list[CategoriaDescartada]

    # Fase 2 -- 5 Porquês
    cadeia_porques: list[PorQue]
    numero_porque: int

    # pergunta formulada (Ishikawa ou "por quê"), ainda não respondida
    pergunta_atual: str | None

    # respostas da pergunta_atual que já passaram na validação determinística
    # (Camada 1 -- não vazias, não uma frase evasiva fixa), aguardando
    # julgamento de informatividade em avaliar_informatividade (Camada 2).
    # Resetado sempre que uma nova pergunta é formulada. Tamanho 1 no caso
    # normal, 2 quando a 1a tentativa foi julgada não informativa.
    tentativas_pergunta_atual: list[str]

    # mensagem exibida ao operador quando avaliar_informatividade (Camada 2)
    # julga a 1a tentativa pouco informativa e pede a mesma pergunta de
    # novo -- sem isso, perguntar_operador reemite a pergunta sem nenhum
    # sinal de rejeição (ver nodes.py::avaliar_informatividade). None fora
    # desse caso; sempre limpo assim que a pergunta avança.
    erro_informatividade: str | None

    # ciclos anteriores preservados quando o operador pede ajuste
    ciclos_anteriores: list[CicloAnterior]

    # Fase 2 -- RAG (specs/fase02/design.md § RAG). pre_busca_rag roda em
    # paralelo com o loop dos 5 Porquês (fan-out a partir de
    # orquestrar_analise), preenchendo candidatos_rag; recomendar_tratativa
    # consome os dois (candidatos_rag + causa_raiz do diagnóstico) depois
    # que ambos os ramos convergem, produzindo recomendacao_tratativa.
    candidatos_rag: list[CandidatoRAG]
    recomendacao_tratativa: str | None

    diagnostico: Diagnostico | None

    # link do relatório JSON (reports/{batch_id}_{ts}.json), gravado por
    # backend/main.py::responder assim que o ciclo chega a diagnostico
    # pronto -- não é responsabilidade do grafo salvar em disco. O PDF não
    # tem link persistido: é gerado sob demanda (root_cause_agent/reports.py
    # ::gerar_pdf), nunca salvo em disco.
    relatorio_json: str | None
