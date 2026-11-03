"""Erros de negócio. A API traduz `codigo` em status HTTP."""


class DomainError(Exception):
    def __init__(self, mensagem: str, codigo: str = "regra_negocio") -> None:
        self.mensagem = mensagem
        self.codigo = codigo
        super().__init__(mensagem)
