from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.veiculo.aggregate import Veiculo
from app.domain.veiculo.placa import Placa


class VeiculoRepository(ABC):
    @abstractmethod
    def save(self, veiculo: Veiculo) -> None: ...

    @abstractmethod
    def get(self, veiculo_id: UUID) -> Veiculo | None: ...

    @abstractmethod
    def get_by_placa(self, placa: Placa) -> Veiculo | None: ...

    @abstractmethod
    def listar(self, cliente_id: UUID | None, limite: int, offset: int) -> tuple[list[Veiculo], int]: ...

    @abstractmethod
    def remove(self, veiculo_id: UUID) -> None: ...

    @abstractmethod
    def existe_por_cliente(self, cliente_id: UUID) -> bool: ...
