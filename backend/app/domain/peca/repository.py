from abc import ABC, abstractmethod
from uuid import UUID

from oficina.domain.peca.aggregate import Peca


class PecaRepository(ABC):
    @abstractmethod
    def save(self, peca: Peca) -> None: ...

    @abstractmethod
    def get(self, peca_id: UUID, *, lock: bool = False) -> Peca | None: ...

    @abstractmethod
    def listar(self, limite: int, offset: int) -> tuple[list[Peca], int]: ...

    @abstractmethod
    def remove(self, peca_id: UUID) -> None: ...
