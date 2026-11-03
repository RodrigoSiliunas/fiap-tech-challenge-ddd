"""CRUD administrativo de clientes, veículos, serviços e peças."""

from uuid import UUID

from app.application.support import concluir, exigir, paginar
from app.domain.cliente.aggregate import Cliente
from app.domain.cliente.documento import Documento
from app.domain.exceptions import DomainError
from app.domain.peca.aggregate import Peca
from app.domain.servico.aggregate import Servico
from app.domain.shared.value_objects import Dinheiro, Quantidade
from app.domain.veiculo.aggregate import Veiculo
from app.domain.veiculo.placa import Placa


class CadastrarCliente:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, nome: str, documento: str, email: str | None, telefone: str | None) -> Cliente:
        doc = Documento.criar(documento)
        if self.uow.clientes.get_by_documento(doc) is not None:
            raise DomainError("Já existe cliente com este CPF/CNPJ", "documento_duplicado")
        cliente = Cliente.cadastrar(nome, doc, email, telefone)
        self.uow.clientes.save(cliente)
        concluir(self.uow, cliente)
        return cliente


class AtualizarCliente:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, cliente_id: UUID, nome: str, email: str | None, telefone: str | None) -> Cliente:
        cliente = exigir(self.uow.clientes.get(cliente_id), "Cliente não encontrado")
        cliente.atualizar(nome, email, telefone)
        self.uow.clientes.save(cliente)
        concluir(self.uow, cliente)
        return cliente


class ExcluirCliente:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, cliente_id: UUID) -> None:
        exigir(self.uow.clientes.get(cliente_id), "Cliente não encontrado")
        if self.uow.veiculos.existe_por_cliente(cliente_id) or self.uow.ordens.existe_por_cliente(cliente_id):
            raise DomainError("Cliente possui veículos ou ordens de serviço e não pode ser excluído", "conflito")
        self.uow.clientes.remove(cliente_id)
        self.uow.commit()


class ObterCliente:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, cliente_id: UUID) -> Cliente:
        return exigir(self.uow.clientes.get(cliente_id), "Cliente não encontrado")


class ListarClientes:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, limite: int, offset: int) -> tuple[list[Cliente], int]:
        limite, offset = paginar(limite, offset)
        return self.uow.clientes.listar(limite, offset)


class CadastrarVeiculo:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, cliente_id: UUID, placa: str, marca: str, modelo: str, ano: int) -> Veiculo:
        exigir(self.uow.clientes.get(cliente_id), "Cliente não encontrado")
        placa_vo = Placa.criar(placa)
        if self.uow.veiculos.get_by_placa(placa_vo) is not None:
            raise DomainError("Já existe veículo com esta placa", "placa_duplicada")
        veiculo = Veiculo.registrar(cliente_id, placa_vo, marca, modelo, ano)
        self.uow.veiculos.save(veiculo)
        concluir(self.uow, veiculo)
        return veiculo


class AtualizarVeiculo:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, veiculo_id: UUID, marca: str, modelo: str, ano: int) -> Veiculo:
        veiculo = exigir(self.uow.veiculos.get(veiculo_id), "Veículo não encontrado")
        veiculo.atualizar(marca, modelo, ano)
        self.uow.veiculos.save(veiculo)
        concluir(self.uow, veiculo)
        return veiculo


class ExcluirVeiculo:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, veiculo_id: UUID) -> None:
        exigir(self.uow.veiculos.get(veiculo_id), "Veículo não encontrado")
        if self.uow.ordens.existe_por_veiculo(veiculo_id):
            raise DomainError("Veículo possui ordens de serviço e não pode ser excluído", "conflito")
        self.uow.veiculos.remove(veiculo_id)
        self.uow.commit()


class ObterVeiculo:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, veiculo_id: UUID) -> Veiculo:
        return exigir(self.uow.veiculos.get(veiculo_id), "Veículo não encontrado")


class ListarVeiculos:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, cliente_id: UUID | None, limite: int, offset: int) -> tuple[list[Veiculo], int]:
        limite, offset = paginar(limite, offset)
        return self.uow.veiculos.listar(cliente_id, limite, offset)


class CadastrarServico:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, nome: str, preco: Dinheiro, descricao: str | None) -> Servico:
        servico = Servico.cadastrar(nome, preco, descricao)
        self.uow.servicos.save(servico)
        concluir(self.uow, servico)
        return servico


class AtualizarServico:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, servico_id: UUID, nome: str, preco: Dinheiro, descricao: str | None) -> Servico:
        servico = exigir(self.uow.servicos.get(servico_id), "Serviço não encontrado")
        servico.atualizar(nome, preco, descricao)
        self.uow.servicos.save(servico)
        concluir(self.uow, servico)
        return servico


class ExcluirServico:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, servico_id: UUID) -> None:
        exigir(self.uow.servicos.get(servico_id), "Serviço não encontrado")
        if self.uow.ordens.existe_item_servico(servico_id):
            raise DomainError("Serviço já utilizado em ordem de serviço e não pode ser excluído", "conflito")
        self.uow.servicos.remove(servico_id)
        self.uow.commit()


class ObterServico:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, servico_id: UUID) -> Servico:
        return exigir(self.uow.servicos.get(servico_id), "Serviço não encontrado")


class ListarServicos:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, limite: int, offset: int) -> tuple[list[Servico], int]:
        limite, offset = paginar(limite, offset)
        return self.uow.servicos.listar(limite, offset)


class CadastrarPeca:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, nome: str, preco: Dinheiro, quantidade: int, descricao: str | None) -> Peca:
        peca = Peca.cadastrar(nome, preco, Quantidade(quantidade), descricao)
        self.uow.pecas.save(peca)
        concluir(self.uow, peca)
        return peca


class AtualizarPeca:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, peca_id: UUID, nome: str, preco: Dinheiro, descricao: str | None) -> Peca:
        peca = exigir(self.uow.pecas.get(peca_id), "Peça não encontrada")
        peca.atualizar(nome, preco, descricao)
        self.uow.pecas.save(peca)
        concluir(self.uow, peca)
        return peca


class ExcluirPeca:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, peca_id: UUID) -> None:
        exigir(self.uow.pecas.get(peca_id), "Peça não encontrada")
        if self.uow.ordens.existe_item_peca(peca_id):
            raise DomainError("Peça já utilizada em ordem de serviço e não pode ser excluída", "conflito")
        self.uow.pecas.remove(peca_id)
        self.uow.commit()


class ObterPeca:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, peca_id: UUID) -> tuple[Peca, list[dict]]:
        peca = exigir(self.uow.pecas.get(peca_id), "Peça não encontrada")
        return peca, self.uow.eventos.listar_por_agregado(peca.id)


class ListarPecas:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, limite: int, offset: int) -> tuple[list[Peca], int]:
        limite, offset = paginar(limite, offset)
        return self.uow.pecas.listar(limite, offset)


class RegistrarEntradaEstoque:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, peca_id: UUID, quantidade: int) -> Peca:
        peca = exigir(self.uow.pecas.get(peca_id, lock=True), "Peça não encontrada")
        peca.registrar_entrada(Quantidade.positiva(quantidade))
        self.uow.pecas.save(peca)
        concluir(self.uow, peca)
        return peca


class AjustarEstoque:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, peca_id: UUID, quantidade: int) -> Peca:
        peca = exigir(self.uow.pecas.get(peca_id, lock=True), "Peça não encontrada")
        peca.ajustar_estoque(Quantidade(quantidade))
        self.uow.pecas.save(peca)
        concluir(self.uow, peca)
        return peca
