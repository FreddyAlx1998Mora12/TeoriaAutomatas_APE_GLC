from .lexer import Lexer, Token, TipoToken
from dataclasses import dataclass
from typing import Union

# AST
@dataclass
class IdNode:     nombre: str
@dataclass
class NotNode:    op: 'Node'
@dataclass
class AndNode:    left: 'Node'; right: 'Node'
@dataclass
class OrNode:     left: 'Node'; right: 'Node'

Node = Union[IdNode, NotNode, AndNode, OrNode]

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def _actual(self) -> Token:
        return self.tokens[self.pos]
    
    def _consumir(self, tipo: TipoToken):
        if self._actual().tipo == tipo:
            t = self._actual()
            self.pos += 1
            return t
        raise ValueError(f"Se esperaba {tipo.name}, se encontró {self._actual().tipo.name}")
    
    def parse(self) -> Node:
        nodo = self._exp()
        if self._actual().tipo != TipoToken.EOF:
            raise ValueError("Tokens sobrantes al final de la expresión")
        return nodo

    # Exp   → Term { | Term }
    def _exp(self) -> Node:
        nodo = self._term()
        while self._actual().tipo == TipoToken.OR:
            self._consumir(TipoToken.OR)
            der = self._term()
            nodo = OrNode(nodo, der)
        return nodo

    # Term  → Factor { & Factor }
    def _term(self) -> Node:
        nodo = self._factor()
        while self._actual().tipo == TipoToken.AND:
            self._consumir(TipoToken.AND)
            der = self._factor()
            nodo = AndNode(nodo, der)
        return nodo

    # Factor→ ~ Factor | ( Exp ) | id
    def _factor(self) -> Node:
        tok = self._actual()
        if tok.tipo == TipoToken.NOT:
            self._consumir(TipoToken.NOT)
            return NotNode(self._factor())
        if tok.tipo == TipoToken.LPAREN:
            self._consumir(TipoToken.LPAREN)
            nodo = self._exp()
            self._consumir(TipoToken.RPAREN)
            return nodo
        if tok.tipo == TipoToken.ID:
            self._consumir(TipoToken.ID)
            return IdNode(tok.valor)
        raise ValueError(f"Token inesperado: {tok.valor} ({tok.tipo.name})")