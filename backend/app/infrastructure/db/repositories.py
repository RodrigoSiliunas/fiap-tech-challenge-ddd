"""Repositórios SQLAlchemy. Traduzem agregados para tabelas e de volta."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import Session, selectinload

from app.domain.cliente.aggregate import Cliente
from app.domain.cliente.documento import Documento, TipoDocumento
from app.domain.cliente.repository import ClienteRepository
from app.domain.exceptions import DomainError
from app.domain.ordem_servico.aggregate import ItemPeca, ItemServico, Orcamento, OrdemDeServico
from app.domain.ordem_servico.repository import OrdemDeServicoRepository
from app.domain.ordem_servico.status import SituacaoOrcamento, StatusOS
from app.domain.peca.aggregate import Peca
from app.domain.peca.repository import PecaRepository
from app.domain.servico.aggregate import Servico
from app.domain.servico.repository import ServicoRepository
from app.domain.shared.events import DomainEvent
from app.domain.shared.value_objects import Dinheiro, Quantidade
from app.domain.veiculo.aggregate import Veiculo
from app.domain.veiculo.placa import PadraoPlaca, Placa
from app.domain.veiculo.repository import VeiculoRepository
from app.infrastructure.db.models import (
    ClienteModel,
    EventoDominioModel,
    ItemPecaModel,
    ItemServicoModel,
    OrcamentoModel,
    OrdemModel,
    PecaModel,
    SequenciaModel,
    ServicoModel,
    UsuarioModel,
    VeiculoModel,
)
from app.infrastructure.serialization import evento_payload


def _utc(valor: datetime) -> datetime:
    if valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor


def _utc_opcional(valor: datetime | None) -> datetime | None:
    if valor is None:
        return None
    return _utc(valor)


def flush(session: Session) -> None:
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise DomainError("Não foi possível persistir o registro (conflito de dados)", "conflito") from exc


def _bloquear(query, session: Session, lock: bool):
    if lock and session.get_bind().dialect.name == "postgresql":
        return query.with_for_update()
    return query


class SqlAlchemyClienteRepository(ClienteRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, cliente: Cliente) -> None:
        model = self.session.get(ClienteModel, str(cliente.id))
        if model is None:
            model = ClienteModel(
                id=str(cliente.id),
                documento=cliente.documento.valor,
                tipo_documento=cliente.documento.tipo.value,
                criado_em=cliente.criado_em,
            )
            self.session.add(model)
        model.nome = cliente.nome
        model.email = cliente.email
        model.telefone = cliente.telefone
        model.atualizado_em = cliente.atualizado_em
        flush(self.session)

    def get(self, cliente_id: UUID) -> Cliente | None:
        model = self.session.get(ClienteModel, str(cliente_id))
        return _cliente(model) if model else None

    def get_by_documento(self, documento: Documento) -> Cliente | None:
        model = self.session.query(ClienteModel).filter(ClienteModel.documento == documento.valor).one_or_none()
        return _cliente(model) if model else None

    def listar(self, limite: int, offset: int) -> tuple[list[Cliente], int]:
        query = self.session.query(ClienteModel)
        total = query.count()
        rows = query.order_by(ClienteModel.nome.asc()).offset(offset).limit(limite).all()
        return [_cliente(row) for row in rows], total

    def remove(self, cliente_id: UUID) -> None:
        model = self.session.get(ClienteModel, str(cliente_id))
        if model is None:
            raise DomainError("Cliente não encontrado", "nao_encontrado")
        self.session.delete(model)
        flush(self.session)


class SqlAlchemyVeiculoRepository(VeiculoRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, veiculo: Veiculo) -> None:
        model = self.session.get(VeiculoModel, str(veiculo.id))
        if model is None:
            model = VeiculoModel(
                id=str(veiculo.id),
                cliente_id=str(veiculo.cliente_id),
                placa=veiculo.placa.valor,
                padrao_placa=veiculo.placa.padrao.value,
                criado_em=veiculo.criado_em,
            )
            self.session.add(model)
        model.marca = veiculo.marca
        model.modelo = veiculo.modelo
        model.ano = veiculo.ano
        model.atualizado_em = veiculo.atualizado_em
        flush(self.session)

    def get(self, veiculo_id: UUID) -> Veiculo | None:
        model = self.session.get(VeiculoModel, str(veiculo_id))
        return _veiculo(model) if model else None

    def get_by_placa(self, placa: Placa) -> Veiculo | None:
        model = self.session.query(VeiculoModel).filter(VeiculoModel.placa == placa.valor).one_or_none()
        return _veiculo(model) if model else None

    def listar(self, cliente_id: UUID | None, limite: int, offset: int) -> tuple[list[Veiculo], int]:
        query = self.session.query(VeiculoModel)
        if cliente_id is not None:
            query = query.filter(VeiculoModel.cliente_id == str(cliente_id))
        total = query.count()
        rows = query.order_by(VeiculoModel.placa.asc()).offset(offset).limit(limite).all()
        return [_veiculo(row) for row in rows], total

    def remove(self, veiculo_id: UUID) -> None:
        model = self.session.get(VeiculoModel, str(veiculo_id))
        if model is None:
            raise DomainError("Veículo não encontrado", "nao_encontrado")
        self.session.delete(model)
        flush(self.session)

    def existe_por_cliente(self, cliente_id: UUID) -> bool:
        return (
            self.session.query(VeiculoModel.id).filter(VeiculoModel.cliente_id == str(cliente_id)).first() is not None
        )


class SqlAlchemyServicoRepository(ServicoRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, servico: Servico) -> None:
        model = self.session.get(ServicoModel, str(servico.id))
        if model is None:
            model = ServicoModel(id=str(servico.id), criado_em=servico.criado_em)
            self.session.add(model)
        model.nome = servico.nome
        model.descricao = servico.descricao
        model.preco_centavos = servico.preco.centavos
        model.atualizado_em = servico.atualizado_em
        flush(self.session)

    def get(self, servico_id: UUID) -> Servico | None:
        model = self.session.get(ServicoModel, str(servico_id))
        return _servico(model) if model else None

    def listar(self, limite: int, offset: int) -> tuple[list[Servico], int]:
        query = self.session.query(ServicoModel)
        total = query.count()
        rows = query.order_by(ServicoModel.nome.asc()).offset(offset).limit(limite).all()
        return [_servico(row) for row in rows], total

    def remove(self, servico_id: UUID) -> None:
        model = self.session.get(ServicoModel, str(servico_id))
        if model is None:
            raise DomainError("Serviço não encontrado", "nao_encontrado")
        self.session.delete(model)
        flush(self.session)


class SqlAlchemyPecaRepository(PecaRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, peca: Peca) -> None:
        model = self.session.get(PecaModel, str(peca.id))
        if model is None:
            model = PecaModel(id=str(peca.id), criado_em=peca.criado_em)
            self.session.add(model)
        model.nome = peca.nome
        model.descricao = peca.descricao
        model.preco_centavos = peca.preco.centavos
        model.quantidade_estoque = peca.quantidade_estoque.valor
        model.atualizado_em = peca.atualizado_em
        flush(self.session)

    def get(self, peca_id: UUID, *, lock: bool = False) -> Peca | None:
        query = self.session.query(PecaModel).filter(PecaModel.id == str(peca_id))
        model = _bloquear(query, self.session, lock).one_or_none()
        return _peca(model) if model else None

    def listar(self, limite: int, offset: int) -> tuple[list[Peca], int]:
        query = self.session.query(PecaModel)
        total = query.count()
        rows = query.order_by(PecaModel.nome.asc()).offset(offset).limit(limite).all()
        return [_peca(row) for row in rows], total

    def remove(self, peca_id: UUID) -> None:
        model = self.session.get(PecaModel, str(peca_id))
        if model is None:
            raise DomainError("Peça não encontrada", "nao_encontrado")
        self.session.delete(model)
        flush(self.session)


class SqlAlchemyOrdemRepository(OrdemDeServicoRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, ordem: OrdemDeServico) -> None:
        model = self.session.get(OrdemModel, str(ordem.id))
        if model is None:
            model = OrdemModel(id=str(ordem.id), numero=ordem.numero, aberta_em=ordem.aberta_em)
            self.session.add(model)
        model.cliente_id = str(ordem.cliente_id)
        model.veiculo_id = str(ordem.veiculo_id)
        model.status = ordem.status.value
        model.observacao = ordem.observacao
        model.diagnostico_iniciado_em = ordem.diagnostico_iniciado_em
        model.orcamento_gerado_em = ordem.orcamento_gerado_em
        model.execucao_iniciada_em = ordem.execucao_iniciada_em
        model.finalizada_em = ordem.finalizada_em
        model.entregue_em = ordem.entregue_em
        self._sync_servicos(model, ordem)
        self._sync_pecas(model, ordem)
        self._sync_orcamento(model, ordem)
        flush(self.session)

    def get(self, ordem_id: UUID, *, lock: bool = False) -> OrdemDeServico | None:
        query = (
            self.session.query(OrdemModel)
            .options(
                selectinload(OrdemModel.itens_servico),
                selectinload(OrdemModel.itens_peca),
                selectinload(OrdemModel.orcamento),
            )
            .filter(OrdemModel.id == str(ordem_id))
        )
        model = _bloquear(query, self.session, lock).one_or_none()
        return _ordem(model) if model else None

    def listar(self, status: StatusOS | None, limite: int, offset: int) -> tuple[list[OrdemDeServico], int]:
        query = self.session.query(OrdemModel).options(
            selectinload(OrdemModel.itens_servico),
            selectinload(OrdemModel.itens_peca),
            selectinload(OrdemModel.orcamento),
        )
        if status is not None:
            query = query.filter(OrdemModel.status == status.value)
        total = query.count()
        rows = query.order_by(OrdemModel.numero.desc()).offset(offset).limit(limite).all()
        return [_ordem(row) for row in rows], total

    def proximo_numero(self) -> int:
        query = self.session.query(SequenciaModel).filter(SequenciaModel.nome == "ordem_servico")
        query = _bloquear(query, self.session, lock=True)
        try:
            sequencia = query.one()
        except NoResultFound as exc:
            raise DomainError("Sequência de ordens de serviço não inicializada", "erro_interno") from exc
        sequencia.valor += 1
        flush(self.session)
        return sequencia.valor

    def existe_nao_encerrada(self, veiculo_id: UUID) -> bool:
        encerradas = [StatusOS.ENTREGUE.value, StatusOS.REJEITADA.value]
        return (
            self.session.query(OrdemModel.id)
            .filter(OrdemModel.veiculo_id == str(veiculo_id), OrdemModel.status.notin_(encerradas))
            .first()
            is not None
        )

    def existe_por_cliente(self, cliente_id: UUID) -> bool:
        return (
            self.session.query(OrdemModel.id).filter(OrdemModel.cliente_id == str(cliente_id)).first() is not None
        )

    def existe_por_veiculo(self, veiculo_id: UUID) -> bool:
        return (
            self.session.query(OrdemModel.id).filter(OrdemModel.veiculo_id == str(veiculo_id)).first() is not None
        )

    def existe_item_servico(self, servico_id: UUID) -> bool:
        return (
            self.session.query(ItemServicoModel.id).filter(ItemServicoModel.servico_id == str(servico_id)).first()
            is not None
        )

    def existe_item_peca(self, peca_id: UUID) -> bool:
        return (
            self.session.query(ItemPecaModel.id).filter(ItemPecaModel.peca_id == str(peca_id)).first() is not None
        )

    def duracoes_execucao_segundos(self) -> list[float]:
        finais = [StatusOS.FINALIZADA.value, StatusOS.ENTREGUE.value]
        rows = (
            self.session.query(OrdemModel)
            .filter(
                OrdemModel.status.in_(finais),
                OrdemModel.execucao_iniciada_em.isnot(None),
                OrdemModel.finalizada_em.isnot(None),
            )
            .all()
        )
        return [(_utc(row.finalizada_em) - _utc(row.execucao_iniciada_em)).total_seconds() for row in rows]

    def _sync_servicos(self, model: OrdemModel, ordem: OrdemDeServico) -> None:
        atuais = {item.id: item for item in model.itens_servico}
        desejados = {str(item.id) for item in ordem.itens_servico}
        for item_model in list(model.itens_servico):
            if item_model.id not in desejados:
                model.itens_servico.remove(item_model)
        for item in ordem.itens_servico:
            existente = atuais.get(str(item.id))
            if existente is None:
                model.itens_servico.append(
                    ItemServicoModel(
                        id=str(item.id),
                        servico_id=str(item.servico_id),
                        descricao=item.descricao,
                        preco_centavos=item.preco.centavos,
                    )
                )
            else:
                existente.descricao = item.descricao
                existente.preco_centavos = item.preco.centavos

    def _sync_pecas(self, model: OrdemModel, ordem: OrdemDeServico) -> None:
        atuais = {item.id: item for item in model.itens_peca}
        desejados = {str(item.id) for item in ordem.itens_peca}
        for item_model in list(model.itens_peca):
            if item_model.id not in desejados:
                model.itens_peca.remove(item_model)
        for item in ordem.itens_peca:
            existente = atuais.get(str(item.id))
            if existente is None:
                model.itens_peca.append(
                    ItemPecaModel(
                        id=str(item.id),
                        peca_id=str(item.peca_id),
                        nome=item.nome,
                        quantidade=item.quantidade.valor,
                        preco_unitario_centavos=item.preco_unitario.centavos,
                    )
                )
            else:
                existente.nome = item.nome
                existente.quantidade = item.quantidade.valor
                existente.preco_unitario_centavos = item.preco_unitario.centavos

    def _sync_orcamento(self, model: OrdemModel, ordem: OrdemDeServico) -> None:
        if ordem.orcamento is None:
            if model.orcamento is not None:
                model.orcamento = None
            return
        origem = ordem.orcamento
        if model.orcamento is None:
            model.orcamento = OrcamentoModel(id=str(origem.id), ordem_id=model.id, gerado_em=origem.gerado_em)
        destino = model.orcamento
        destino.valor_servicos_centavos = origem.valor_servicos.centavos
        destino.valor_pecas_centavos = origem.valor_pecas.centavos
        destino.valor_total_centavos = origem.valor_total.centavos
        destino.situacao = origem.situacao.value
        destino.gerado_em = origem.gerado_em
        destino.decidido_em = origem.decidido_em
        destino.motivo_rejeicao = origem.motivo_rejeicao


class EventoRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def salvar_todos(self, eventos: list[DomainEvent]) -> None:
        for evento in eventos:
            self.session.add(
                EventoDominioModel(
                    nome=evento.nome_evento,
                    agregado_tipo=evento.agregado_tipo,
                    agregado_id=str(evento.agregado_id),
                    ocorrido_em=evento.ocorrido_em,
                    payload=evento_payload(evento),
                )
            )
        if eventos:
            flush(self.session)

    def listar_por_agregado(self, agregado_id: UUID) -> list[dict]:
        rows = (
            self.session.query(EventoDominioModel)
            .filter(EventoDominioModel.agregado_id == str(agregado_id))
            .order_by(EventoDominioModel.id.asc())
            .all()
        )
        return [
            {
                "id": row.id,
                "nome": row.nome,
                "agregado_tipo": row.agregado_tipo,
                "ocorrido_em": _utc(row.ocorrido_em).isoformat(),
                "payload": row.payload,
            }
            for row in rows
        ]


class UsuarioRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_username(self, username: str) -> UsuarioModel | None:
        return self.session.query(UsuarioModel).filter(UsuarioModel.username == username).one_or_none()


def _cliente(model: ClienteModel) -> Cliente:
    return Cliente(
        id=UUID(model.id),
        nome=model.nome,
        documento=Documento(model.documento, TipoDocumento(model.tipo_documento)),
        email=model.email,
        telefone=model.telefone,
        criado_em=_utc(model.criado_em),
        atualizado_em=_utc(model.atualizado_em),
    )


def _veiculo(model: VeiculoModel) -> Veiculo:
    return Veiculo(
        id=UUID(model.id),
        cliente_id=UUID(model.cliente_id),
        placa=Placa(model.placa, PadraoPlaca(model.padrao_placa)),
        marca=model.marca,
        modelo=model.modelo,
        ano=model.ano,
        criado_em=_utc(model.criado_em),
        atualizado_em=_utc(model.atualizado_em),
    )


def _servico(model: ServicoModel) -> Servico:
    return Servico(
        id=UUID(model.id),
        nome=model.nome,
        descricao=model.descricao,
        preco=Dinheiro(model.preco_centavos),
        criado_em=_utc(model.criado_em),
        atualizado_em=_utc(model.atualizado_em),
    )


def _peca(model: PecaModel) -> Peca:
    return Peca(
        id=UUID(model.id),
        nome=model.nome,
        descricao=model.descricao,
        preco=Dinheiro(model.preco_centavos),
        quantidade_estoque=Quantidade(model.quantidade_estoque),
        criado_em=_utc(model.criado_em),
        atualizado_em=_utc(model.atualizado_em),
    )


def _ordem(model: OrdemModel) -> OrdemDeServico:
    return OrdemDeServico(
        id=UUID(model.id),
        numero=model.numero,
        cliente_id=UUID(model.cliente_id),
        veiculo_id=UUID(model.veiculo_id),
        status=StatusOS(model.status),
        aberta_em=_utc(model.aberta_em),
        itens_servico=[
            ItemServico(
                id=UUID(item.id),
                servico_id=UUID(item.servico_id),
                descricao=item.descricao,
                preco=Dinheiro(item.preco_centavos),
            )
            for item in model.itens_servico
        ],
        itens_peca=[
            ItemPeca(
                id=UUID(item.id),
                peca_id=UUID(item.peca_id),
                nome=item.nome,
                quantidade=Quantidade(item.quantidade),
                preco_unitario=Dinheiro(item.preco_unitario_centavos),
            )
            for item in model.itens_peca
        ],
        orcamento=_orcamento(model.orcamento),
        observacao=model.observacao,
        diagnostico_iniciado_em=_utc_opcional(model.diagnostico_iniciado_em),
        orcamento_gerado_em=_utc_opcional(model.orcamento_gerado_em),
        execucao_iniciada_em=_utc_opcional(model.execucao_iniciada_em),
        finalizada_em=_utc_opcional(model.finalizada_em),
        entregue_em=_utc_opcional(model.entregue_em),
    )


def _orcamento(model: OrcamentoModel | None) -> Orcamento | None:
    if model is None:
        return None
    return Orcamento(
        id=UUID(model.id),
        valor_servicos=Dinheiro(model.valor_servicos_centavos),
        valor_pecas=Dinheiro(model.valor_pecas_centavos),
        valor_total=Dinheiro(model.valor_total_centavos),
        situacao=SituacaoOrcamento(model.situacao),
        gerado_em=_utc(model.gerado_em),
        decidido_em=_utc_opcional(model.decidido_em),
        motivo_rejeicao=model.motivo_rejeicao,
    )
