from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.servico.aggregate import Servico


class ServicoRepository(ABC):
    @abstractmethod
    def save(self, servico: Servico) -> None: ...

    @abstractmethod
    def get(self, servico_id: UUID) -> Servico | None: ...

    @abstractmethod
    def listar(self, limite: int, offset: int) -> tuple[list[Servico], int]: ...

    @abstractmethod
    def remove(self, servico_id: UUID) -> None: ...
