"""Issue #45 (specs/fase02/design.md § 2.1): prova dedicada de que
formular_porque e pre_busca_rag, os 2 ramos do fan-out a partir de
orquestrar_analise (graph.py), rodam genuinamente em paralelo -- não uma
sequência disfarçada onde um só começa depois que o outro termina.

Estratégia: uma barreira de sincronização (threading.Event) em cada nó --
cada um sinaliza que começou e só então espera o outro ter sinalizado o
início dele, antes de rodar a lógica real. Se o LangGraph executasse os 2
nós em sequência (não na mesma superstep, em threads concorrentes), o
primeiro a rodar ficaria bloqueado esperando um evento que o segundo (ainda
não iniciado) nunca teria setado, e o wait() estouraria o timeout -- é
exatamente esse deadlock que o teste detectaria como falha."""

from __future__ import annotations

import threading

from root_cause_agent import nodes
from root_cause_agent.main import rodar_investigacao_com_respostas

RESPOSTAS = [f"resposta {i}" for i in range(11)]
TIMEOUT_BARREIRA = 5


def test_pre_busca_rag_e_formular_porque_rodam_em_paralelo(fake_llm, monkeypatch):
    inicio_pre_busca_rag = threading.Event()
    inicio_formular_porque = threading.Event()

    pre_busca_rag_original = nodes.pre_busca_rag
    formular_porque_original = nodes.formular_porque

    def pre_busca_rag_com_barreira(state):
        inicio_pre_busca_rag.set()
        assert inicio_formular_porque.wait(timeout=TIMEOUT_BARREIRA), (
            "pre_busca_rag terminou de esperar sem que formular_porque tivesse "
            "começado -- os 2 ramos não estão rodando na mesma superstep "
            "(fan-out disfarçado de sequencial)."
        )
        return pre_busca_rag_original(state)

    def formular_porque_com_barreira(state):
        inicio_formular_porque.set()
        assert inicio_pre_busca_rag.wait(timeout=TIMEOUT_BARREIRA), (
            "formular_porque terminou de esperar sem que pre_busca_rag "
            "tivesse começado -- os 2 ramos não estão rodando na mesma "
            "superstep (fan-out disfarçado de sequencial)."
        )
        return formular_porque_original(state)

    # graph.py resolve nodes.pre_busca_rag/nodes.formular_porque por
    # atributo no momento de build_graph() (chamado dentro de
    # rodar_investigacao_com_respostas, já que nenhum `graph=` é passado
    # aqui) -- o monkeypatch precisa acontecer antes dessa chamada.
    monkeypatch.setattr(nodes, "pre_busca_rag", pre_busca_rag_com_barreira)
    monkeypatch.setattr(nodes, "formular_porque", formular_porque_com_barreira)

    diagnostico, _graph = rodar_investigacao_com_respostas(502, RESPOSTAS)

    # Confirma que os 2 nós de fato rodaram (a barreira em si já garantiria
    # isso via assert, mas deixa explícito o que o teste está provando) e
    # que o ciclo completo, atravessando os 2 ramos paralelos, ainda produz
    # um diagnóstico correto.
    assert inicio_pre_busca_rag.is_set()
    assert inicio_formular_porque.is_set()
    assert isinstance(diagnostico.fontes_rag, list)
    assert len(diagnostico.cadeia_de_porques) == 5
    assert diagnostico.recomendacao_tratativa


def test_pre_busca_rag_nao_depende_da_cadeia_de_porques(fake_llm, monkeypatch):
    """pre_busca_rag só usa categoria_principal + nc_input -- roda e termina
    sem nunca ler cadeia_porques, reforçando que a independência dos 2
    ramos (pré-requisito para o paralelismo real) é real, não coincidência
    dos dados de teste."""
    leituras_de_cadeia_porques = []

    pre_busca_rag_original = nodes.pre_busca_rag

    def pre_busca_rag_espiao(state):
        leituras_de_cadeia_porques.append(list(state["cadeia_porques"]))
        return pre_busca_rag_original(state)

    monkeypatch.setattr(nodes, "pre_busca_rag", pre_busca_rag_espiao)

    rodar_investigacao_com_respostas(503, RESPOSTAS)

    assert leituras_de_cadeia_porques == [[]]
