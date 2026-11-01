"""Monta os DTOs de resposta a partir dos agregados."""

from datetime import datetime, timezone

from oficina.application.queries.ordens_servico import DetalheOrdem, ResumoOrdem
from oficina.domain.cliente.aggregate import Cliente
from oficina.domain.ordem_servico.aggregate import Orcamento, OrdemDeServico
from oficina.domain.ordem_servico.status import StatusOS
from oficina.domain.peca.aggregate import Peca
from oficina.domain.servico.aggregate import Servico
from oficina.domain.shared.value_objects import Dinheiro
from oficina.domain.veiculo.aggregate import Veiculo


def instante(valor: datetime | None) -> str | None:
    if valor is None:
        return None
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=timezone.utc)
    return valor.isoformat()


def dinheiro(valor: Dinheiro) -> str:
    return valor.formatado()


def cliente_out(cliente: Cliente) -> dict:
    return {
        "id": cliente.id,
        "nome": cliente.nome,
        "documento": cliente.documento.formatado(),
        "tipo_documento": cliente.documento.tipo.value,
        "email": cliente.email,
        "telefone": cliente.telefone,
        "criado_em": instante(cliente.criado_em),
        "atualizado_em": instante(cliente.atualizado_em),
    }


def veiculo_out(veiculo: Veiculo) -> dict:
    return {
        "id": veiculo.id,
        "cliente_id": veiculo.cliente_id,
        "placa": veiculo.placa.formatada(),
        "padrao_placa": veiculo.placa.padrao.value,
        "marca": veiculo.marca,
        "modelo": veiculo.modelo,
        "ano": veiculo.ano,
        "criado_em": instante(veiculo.criado_em),
        "atualizado_em": instante(veiculo.atualizado_em),
    }


def servico_out(servico: Servico) -> dict:
    return {
        "id": servico.id,
        "nome": servico.nome,
        "descricao": servico.descricao,
        "preco": dinheiro(servico.preco),
        "criado_em": instante(servico.criado_em),
        "atualizado_em": instante(servico.atualizado_em),
    }


def peca_out(peca: Peca, eventos: list[dict] | None = None) -> dict:
    dados = {
        "id": peca.id,
        "nome": peca.nome,
        "descricao": peca.descricao,
        "preco": dinheiro(peca.preco),
        "quantidade_estoque": peca.quantidade_estoque.valor,
        "criado_em": instante(peca.criado_em),
        "atualizado_em": instante(peca.atualizado_em),
    }
    if eventos is not None:
        dados["eventos"] = eventos
    return dados


def _orcamento(orcamento: Orcamento | None) -> dict | None:
    if orcamento is None:
        return None
    return {
        "id": orcamento.id,
        "valor_servicos": dinheiro(orcamento.valor_servicos),
        "valor_pecas": dinheiro(orcamento.valor_pecas),
        "valor_total": dinheiro(orcamento.valor_total),
        "situacao": orcamento.situacao.value,
        "gerado_em": instante(orcamento.gerado_em),
        "decidido_em": instante(orcamento.decidido_em),
        "motivo_rejeicao": orcamento.motivo_rejeicao,
    }


def marcos(ordem: OrdemDeServico) -> list[dict]:
    pares = [
        (StatusOS.RECEBIDA, ordem.aberta_em),
        (StatusOS.EM_DIAGNOSTICO, ordem.diagnostico_iniciado_em),
        (StatusOS.AGUARDANDO_APROVACAO, ordem.orcamento_gerado_em),
        (StatusOS.EM_EXECUCAO, ordem.execucao_iniciada_em),
        (StatusOS.FINALIZADA, ordem.finalizada_em),
        (StatusOS.ENTREGUE, ordem.entregue_em),
    ]
    lista = []
    for status, quando in pares:
        if quando is not None:
            lista.append({"status": status.value, "descricao": status.descricao, "ocorrido_em": instante(quando)})
    if ordem.status == StatusOS.REJEITADA and ordem.orcamento and ordem.orcamento.decidido_em:
        lista.append(
            {
                "status": StatusOS.REJEITADA.value,
                "descricao": StatusOS.REJEITADA.descricao,
                "ocorrido_em": instante(ordem.orcamento.decidido_em),
            }
        )
    return lista


def _ordem_base(detalhe: DetalheOrdem) -> dict:
    ordem = detalhe.ordem
    return {
        "id": ordem.id,
        "numero": ordem.numero,
        "status": ordem.status.value,
        "status_descricao": ordem.status.descricao,
        "observacao": ordem.observacao,
        "cliente": {
            "id": detalhe.cliente.id,
            "nome": detalhe.cliente.nome,
            "documento": detalhe.cliente.documento.formatado(),
            "tipo_documento": detalhe.cliente.documento.tipo.value,
        },
        "veiculo": {
            "id": detalhe.veiculo.id,
            "placa": detalhe.veiculo.placa.formatada(),
            "marca": detalhe.veiculo.marca,
            "modelo": detalhe.veiculo.modelo,
            "ano": detalhe.veiculo.ano,
        },
        "itens_servico": [
            {
                "id": item.id,
                "servico_id": item.servico_id,
                "descricao": item.descricao,
                "preco": dinheiro(item.preco),
            }
            for item in ordem.itens_servico
        ],
        "itens_peca": [
            {
                "id": item.id,
                "peca_id": item.peca_id,
                "nome": item.nome,
                "quantidade": item.quantidade.valor,
                "preco_unitario": dinheiro(item.preco_unitario),
                "subtotal": dinheiro(item.subtotal()),
            }
            for item in ordem.itens_peca
        ],
        "orcamento": _orcamento(ordem.orcamento),
        "marcos": marcos(ordem),
        "aberta_em": instante(ordem.aberta_em),
        "diagnostico_iniciado_em": instante(ordem.diagnostico_iniciado_em),
        "orcamento_gerado_em": instante(ordem.orcamento_gerado_em),
        "execucao_iniciada_em": instante(ordem.execucao_iniciada_em),
        "finalizada_em": instante(ordem.finalizada_em),
        "entregue_em": instante(ordem.entregue_em),
    }


def ordem_out(detalhe: DetalheOrdem) -> dict:
    return _ordem_base(detalhe)


def ordem_detalhe_out(detalhe: DetalheOrdem) -> dict:
    dados = _ordem_base(detalhe)
    dados["eventos"] = detalhe.eventos
    return dados


def resumo_ordem_out(resumo: ResumoOrdem) -> dict:
    ordem = resumo.ordem
    return {
        "id": ordem.id,
        "numero": ordem.numero,
        "status": ordem.status.value,
        "status_descricao": ordem.status.descricao,
        "cliente_id": ordem.cliente_id,
        "cliente_nome": resumo.cliente_nome,
        "veiculo_id": ordem.veiculo_id,
        "placa": resumo.placa,
        "valor_orcamento": dinheiro(ordem.orcamento.valor_total) if ordem.orcamento else None,
        "aberta_em": instante(ordem.aberta_em),
    }


def pagina(itens: list, total: int, limite: int, offset: int) -> dict:
    return {"itens": itens, "total": total, "limite": limite, "offset": offset}
