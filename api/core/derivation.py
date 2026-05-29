from .parser import Node, IdNode, NotNode, AndNode, OrNode
from typing import List

class DerivationStep:
    def __init__(self, forma: str, produccion_usada: str = ""):
        self.forma = forma
        self.produccion_usada = produccion_usada

class TreeNode:
    def __init__(self, symbol: str, children: list = None, token: str = None):
        self.symbol = symbol
        self.children = children or []
        self.token = token
    
    def to_dict(self):
        if self.token:
            return {"symbol": self.symbol, "token": self.token, "children": []}
        return {"symbol": self.symbol, "children": [c.to_dict() for c in self.children]}

class DerivationBuilder:
    """Reconstruye derivaciones leftmost/rightmost y árbol de esquematización
       desde el AST, usando la gramática original del enunciado."""
    
    def build(self, ast: Node, tokens: list):
        self.tokens = tokens
        self.token_idx = 0
        
        left = self._leftmost(ast)
        right = self._rightmost(ast)
        tree = self._build_tree(ast)
        
        return {
            "leftmost":  [{"paso": i+1, "forma": s.forma, "produccion": s.produccion_usada} 
                         for i, s in enumerate(left)],
            "rightmost": [{"paso": i+1, "forma": s.forma, "produccion": s.produccion_usada} 
                         for i, s in enumerate(right)],
            "arbol": tree.to_dict(),
            "tokens": [{"tipo": t.tipo.name, "valor": t.valor} for t in tokens if t.tipo.name != "EOF"]
        }

    # ---------- LEFT-MOST ----------
    def _leftmost(self, node: Node) -> List[DerivationStep]:
        pasos: List[DerivationStep] = []
        
        def expandir(n: Node, buffer: list) -> list:
            # buffer es lista de strings (terminales/no-terminales ya expandidos)
            # retorna nueva lista de strings después de expandir n
            nonlocal pasos
            
            if isinstance(n, IdNode):
                # Secuencia: Factor -> id
                # Reemplazamos el primer no-terminal (Factor) por id
                # Pero en leftmost, el buffer ya tiene Exp/Term/Factor según contexto
                return buffer  # se maneja externamente
            
            if isinstance(n, NotNode):
                # Factor -> ~ Factor
                return buffer
            
            if isinstance(n, AndNode):
                # Term -> Term & Factor
                return buffer
            
            if isinstance(n, OrNode):
                # Exp -> Exp | Term
                return buffer
            
            return buffer
        
        # Construcción paso a paso leftmost
        forma = ["Exp"]
        pasos.append(DerivationStep(" ".join(forma), "Inicio"))
        
        # Nivel Exp (Or)
        if isinstance(node, OrNode):
            forma = ["Exp", "|", "Term"]
            pasos.append(DerivationStep(" ".join(forma), "Exp → Exp | Term"))
            
            # Expandir left (Exp) leftmost
            forma = self._expand_node_left(node.left, forma, 0, pasos)
            # Ahora expandir Term derecho
            idx = forma.index("Term")
            forma = self._expand_term(node.right, forma, idx, pasos)
        else:
            # No es Or, Exp -> Term
            forma = ["Term"]
            pasos.append(DerivationStep(" ".join(forma), "Exp → Term"))
            forma = self._expand_term(node, forma, 0, pasos)
        
        return pasos
    
    def _expand_node_left(self, node: Node, forma: list, idx: int, pasos: list) -> list:
        """Expande un nodo que está en posición de Exp (leftmost)."""
        if isinstance(node, OrNode):
            forma = forma[:idx] + ["Exp", "|", "Term"] + forma[idx+1:]
            pasos.append(DerivationStep(" ".join(forma), "Exp → Exp | Term"))
            forma = self._expand_node_left(node.left, forma, idx, pasos)
            t_idx = forma.index("Term", idx)
            forma = self._expand_term(node.right, forma, t_idx, pasos)
            return forma
        
        # Exp -> Term
        forma = forma[:idx] + ["Term"] + forma[idx+1:]
        pasos.append(DerivationStep(" ".join(forma), "Exp → Term"))
        return self._expand_term(node, forma, idx, pasos)
    
    def _expand_term(self, node: Node, forma: list, idx: int, pasos: list) -> list:
        if isinstance(node, AndNode):
            forma = forma[:idx] + ["Term", "&", "Factor"] + forma[idx+1:]
            pasos.append(DerivationStep(" ".join(forma), "Term → Term & Factor"))
            forma = self._expand_term(node.left, forma, idx, pasos)
            f_idx = forma.index("Factor", idx)
            forma = self._expand_factor(node.right, forma, f_idx, pasos)
            return forma
        
        # Term -> Factor
        forma = forma[:idx] + ["Factor"] + forma[idx+1:]
        pasos.append(DerivationStep(" ".join(forma), "Term → Factor"))
        return self._expand_factor(node, forma, idx, pasos)
    
    def _expand_factor(self, node: Node, forma: list, idx: int, pasos: list) -> list:
        if isinstance(node, NotNode):
            forma = forma[:idx] + ["~", "Factor"] + forma[idx+1:]
            pasos.append(DerivationStep(" ".join(forma), "Factor → ~ Factor"))
            return self._expand_factor(node.op, forma, idx+1, pasos)
        
        if isinstance(node, IdNode):
            forma = forma[:idx] + [node.nombre] + forma[idx+1:]
            pasos.append(DerivationStep(" ".join(forma), f"Factor → id ({node.nombre})"))
            return forma
        
        if isinstance(node, OrNode) or isinstance(node, AndNode):
            # ( Exp )
            forma = forma[:idx] + ["(", "Exp", ")"] + forma[idx+1:]
            pasos.append(DerivationStep(" ".join(forma), "Factor → ( Exp )"))
            forma = self._expand_node_left(node, forma, idx+1, pasos)
            return forma
        
        return forma

    # ---------- RIGHT-MOST ----------
    def _rightmost(self, node: Node) -> List[DerivationStep]:
        pasos: List[DerivationStep] = []
        forma = ["Exp"]
        pasos.append(DerivationStep(" ".join(forma), "Inicio"))
        
        if isinstance(node, OrNode):
            forma = ["Exp", "|", "Term"]
            pasos.append(DerivationStep(" ".join(forma), "Exp → Exp | Term"))
            # Rightmost: expandir Term primero, luego Exp
            forma = self._expand_term_right(node.right, forma, forma.index("Term"), pasos)
            forma = self._expand_exp_right(node.left, forma, forma.index("Exp"), pasos)
        else:
            forma = ["Term"]
            pasos.append(DerivationStep(" ".join(forma), "Exp → Term"))
            forma = self._expand_term_right(node, forma, 0, pasos)
        
        return pasos
    
    def _expand_exp_right(self, node: Node, forma: list, idx: int, pasos: list) -> list:
        if isinstance(node, OrNode):
            forma = forma[:idx] + ["Exp", "|", "Term"] + forma[idx+1:]
            pasos.append(DerivationStep(" ".join(forma), "Exp → Exp | Term"))
            forma = self._expand_term_right(node.right, forma, forma.index("Term"), pasos)
            forma = self._expand_exp_right(node.left, forma, forma.index("Exp"), pasos)
            return forma
        
        forma = forma[:idx] + ["Term"] + forma[idx+1:]
        pasos.append(DerivationStep(" ".join(forma), "Exp → Term"))
        return self._expand_term_right(node, forma, idx, pasos)
    
    def _expand_term_right(self, node: Node, forma: list, idx: int, pasos: list) -> list:
        if isinstance(node, AndNode):
            forma = forma[:idx] + ["Term", "&", "Factor"] + forma[idx+1:]
            pasos.append(DerivationStep(" ".join(forma), "Term → Term & Factor"))
            forma = self._expand_factor_right(node.right, forma, forma.index("Factor"), pasos)
            forma = self._expand_term_right(node.left, forma, forma.index("Term"), pasos)
            return forma
        
        forma = forma[:idx] + ["Factor"] + forma[idx+1:]
        pasos.append(DerivationStep(" ".join(forma), "Term → Factor"))
        return self._expand_factor_right(node, forma, idx, pasos)
    
    def _expand_factor_right(self, node: Node, forma: list, idx: int, pasos: list) -> list:
        if isinstance(node, NotNode):
            forma = forma[:idx] + ["~", "Factor"] + forma[idx+1:]
            pasos.append(DerivationStep(" ".join(forma), "Factor → ~ Factor"))
            return self._expand_factor_right(node.op, forma, idx+1, pasos)
        
        if isinstance(node, IdNode):
            forma = forma[:idx] + [node.nombre] + forma[idx+1:]
            pasos.append(DerivationStep(" ".join(forma), f"Factor → id ({node.nombre})"))
            return forma
        
        if isinstance(node, (OrNode, AndNode)):
            forma = forma[:idx] + ["(", "Exp", ")"] + forma[idx+1:]
            pasos.append(DerivationStep(" ".join(forma), "Factor → ( Exp )"))
            forma = self._expand_exp_right(node, forma, forma.index("Exp"), pasos)
            return forma
        
        return forma

    # ---------- ÁRBOL DE ESQUEMATIZACIÓN ----------
    def _build_tree(self, node: Node) -> TreeNode:
        if isinstance(node, IdNode):
            f = TreeNode("Factor", [TreeNode("id", token=node.nombre)])
            t = TreeNode("Term", [f])
            return TreeNode("Exp", [t])
        
        if isinstance(node, NotNode):
            inner = self._build_tree(node.op)
            # inner es un árbol Exp; para Factor necesitamos su Factor raíz
            factor_inner = inner.children[0].children[0]  # Exp->Term->Factor
            f = TreeNode("Factor", [
                TreeNode("~", token="~"),
                factor_inner
            ])
            t = TreeNode("Term", [f])
            return TreeNode("Exp", [t])
        
        if isinstance(node, AndNode):
            left = self._build_tree(node.left)
            right = self._build_tree(node.right)
            # Extraer Factores
            f_left = left.children[0].children[0]
            f_right = right.children[0].children[0]
            t = TreeNode("Term", [
                TreeNode("Term", [f_left]),
                TreeNode("&", token="&"),
                f_right
            ])
            return TreeNode("Exp", [t])
        
        if isinstance(node, OrNode):
            left = self._build_tree(node.left)
            right = self._build_tree(node.right)
            t_left = left.children[0]
            t_right = right.children[0]
            return TreeNode("Exp", [
                TreeNode("Exp", [t_left]),
                TreeNode("|", token="|"),
                t_right
            ])
        
        return TreeNode("Exp")