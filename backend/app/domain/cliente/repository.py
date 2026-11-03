from abc import ABC, abstractmethod
from uuid import UUID

from oficina.domain.cliente.aggregate import Cliente
from oficina.domain.cliente.documento import Documento


class ClienteRepository(ABC):
    @abstractmethod
    def save(self, cliente: Cliente) -> None: ...

    @abstractmethod
    def get(self, cliente_id: UUID) -> Cliente | None: ...

    @abstractmethod
    def get_by_documento(self, documento: Documento) -> Cliente | None: ...

    @abstractmethod
    def listar(self, limite: int, offset: int) -> tuple[list[Cliente], int]: ...

    @abstractmethod
    def remove(self, cliente_id: UUID) -> None: ...
