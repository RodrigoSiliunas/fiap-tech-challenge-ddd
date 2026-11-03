"""Mixin das raízes de agregado: registro e coleta de eventos."""

from oficina.domain.shared.events import DomainEvent


class RaizAgregado:
    _events: list[DomainEvent]

    def _registrar(self, evento: DomainEvent) -> None:
        self._events.append(evento)

    def pull_events(self) -> list[DomainEvent]:
        eventos = list(self._events)
        self._events.clear()
        return eventos
