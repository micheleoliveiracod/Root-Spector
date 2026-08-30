"""Regressão: quando avaliar_informatividade (Camada 2, agêntica) julga a
1a tentativa de resposta pouco informativa, o operador precisa ver por quê
na pergunta repetida -- sem isso (bug encontrado testando o agente em
produção, ver nodes.py::perguntar_operador), a mesma pergunta reaparecia
sem nenhum sinal de rejeição, indistinguível de um erro do sistema.
"""

from __future__ import annotations

from langgraph.types import Command

from root_cause_agent.fake_llm import FakeChatModel
from root_cause_agent.graph import build_graph

BATCH_ID = 511


class _FakeJulgamentoControlavel(FakeChatModel):
    """Como FakeChatModel, mas o julgamento de informatividade (schema com
    o campo `informativa`) é controlável: as `n` primeiras chamadas
    julgam não informativa, as seguintes julgam informativa -- simula o
    operador dando uma resposta vaga na 1a tentativa e detalhando na 2a."""

    def __init__(self, tentativas_nao_informativas: int):
        self._restantes = tentativas_nao_informativas
        self._chamadas = 0

    def with_structured_output(self, schema):
        if "informativa" in schema.model_fields:
            self._chamadas += 1
            informativa = self._chamadas > self._restantes

            class _Resultado:
                pass

            resultado = _Resultado()
            resultado.informativa = informativa
            return _InvokerFixo(resultado)
        return super().with_structured_output(schema)


class _InvokerFixo:
    def __init__(self, resultado):
        self._resultado = resultado

    def invoke(self, mensagens):
        return self._resultado


def test_pergunta_repetida_por_camada_2_mostra_o_motivo_ao_operador(monkeypatch, embeddings_fake):
    from root_cause_agent import nodes

    monkeypatch.setattr(
        nodes, "get_llm", lambda: _FakeJulgamentoControlavel(tentativas_nao_informativas=1)
    )

    grafo = build_graph(":memory:")
    config = {"configurable": {"thread_id": str(BATCH_ID)}}

    resultado = grafo.invoke({"batch_id": BATCH_ID}, config=config)
    primeira_pergunta = resultado["__interrupt__"][0].value
    assert primeira_pergunta.get("erro") is None

    # 1a tentativa: Camada 2 julga não informativa (mock acima) -- a
    # mesma pergunta deve voltar, agora com "erro" explicando o motivo.
    resultado = grafo.invoke(Command(resume="tá tudo bem"), config=config)
    pergunta_repetida = resultado["__interrupt__"][0].value
    assert pergunta_repetida["pergunta"] == primeira_pergunta["pergunta"]
    assert pergunta_repetida["categoria"] == primeira_pergunta["categoria"]
    assert pergunta_repetida.get("erro")

    # 2a tentativa: Camada 2 já julga informativa -- avança de categoria,
    # e o aviso da Camada 2 não vaza pra próxima pergunta.
    resultado = grafo.invoke(
        Command(resume="Sim, houve uma mudança de procedimento neste lote."), config=config
    )
    proxima_pergunta = resultado["__interrupt__"][0].value
    assert proxima_pergunta["categoria"] != primeira_pergunta["categoria"]
    assert proxima_pergunta.get("erro") is None
