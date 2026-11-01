from abc import ABC, abstractmethod
from uuid import UUID

from oficina.domain.ordem_servico.aggregate import OrdemDeServico
from oficina.domain.ordem_servico.status import StatusOS


class OrdemDeServicoRepository(ABC):
    @abstractmethod
    def save(self, ordem: OrdemDeServico) -> None: ...

    @abstractmethod
    def get(self, ordem_id: UUID, *, lock: bool = False) -> OrdemDeServico | None: ...

    @abstractmethod
    def listar(
        self, status: StatusOS | None, limite: int, offset: int
    ) -> tuple[list[OrdemDeServico], int]: ...

    @abstractmethod
    def proximo_numero(self) -> int: ...

    @abstractmethod
    def existe_nao_encerrada(self, veiculo_id: UUID) -> bool: ...

    @abstractmethod
    def existe_por_cliente(self, cliente_id: UUID) -> bool: ...

    @abstractmethod
    def existe_por_veiculo(self, veiculo_id: UUID) -> bool: ...

    @abstractmethod
    def existe_item_servico(self, servico_id: UUID) -> bool: ...

    @abstractmethod
    def existe_item_peca(self, peca_id: UUID) -> bool: ...

    @abstractmethod
    def duracoes_execucao_segundos(self) -> list[float]: ...
