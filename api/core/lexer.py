from dataclasses import dataclass
from enum import Enum, auto
import re

class TipoToken(Enum):
    ID = auto()
    OR = auto()
    AND = auto()
    NOT = auto()
    LPAREN = auto()
    RPAREN = auto()
    EOF = auto()

@dataclass(frozen=True)
class Token:
    tipo: TipoToken
    valor: str
    pos: int

class Lexer:
    PATRON = re.compile(r'\s*([A-Za-z_][A-Za-z0-9_]*)|(\|)|(&)|(~)|(\()|(\))|.')

    def tokenizar(self, texto: str) -> list[Token]:
        tokens = []
        pos = 0
        while pos < len(texto):
            m = self.PATRON.match(texto, pos)
            if not m or m.end() == pos:
                raise ValueError(f"Carácter inválido en posición {pos}: '{texto[pos]}'")
            
            if m.group(1):      tokens.append(Token(TipoToken.ID,    m.group(1), pos))
            elif m.group(2):    tokens.append(Token(TipoToken.OR,    m.group(2), pos))
            elif m.group(3):    tokens.append(Token(TipoToken.AND,   m.group(3), pos))
            elif m.group(4):    tokens.append(Token(TipoToken.NOT,   m.group(4), pos))
            elif m.group(5):    tokens.append(Token(TipoToken.LPAREN,m.group(5), pos))
            elif m.group(6):    tokens.append(Token(TipoToken.RPAREN,m.group(6), pos))
            else:
                raise ValueError(f"Token inválido: '{m.group(0).strip()}'")
            pos = m.end()
        
        tokens.append(Token(TipoToken.EOF, "", pos))
        return tokens