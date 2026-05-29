# 🔷 Analizador GLC — Expresiones Booleanas

Aplicación web que analiza expresiones lógicas booleanas mediante una **Gramática Libre de Contexto (GLC)**. Genera derivaciones paso a paso (_leftmost_ y _rightmost_), árbol de esquematización y validación sintáctica con precedencia de operadores.

**Stack:** Flask (Python) + React + Vite.

---

## 📐 Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        USUARIO                               │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────────────┐
│  FRONTEND (Vite + React)          Puerto: 5173 (dev)       │
│  ├─ InputForm.jsx    → Captura expresión                   │
│  ├─ DerivationSteps.jsx → Muestra derivaciones paso a paso │
│  └─ ParseTree.jsx    → Renderiza árbol de esquematización│
└──────────────────────┬──────────────────────────────────────┘
                       │ fetch / axios
                       │ /api/analizar  (POST)
                       │ /api/health    (GET)
┌──────────────────────▼──────────────────────────────────────┐
│  BACKEND (Flask)                  Puerto: 5000               │
│  ├─ lexer.py         → Tokenización (id, |, &, ~, (, ))    │
│  ├─ parser.py        → AST con precedencia (~ > & > |)     │
│  ├─ derivation.py    → Generador leftmost / rightmost      │
│  └─ app.py           → API REST (CORS habilitado)          │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de datos

1. El usuario escribe una expresión (ej: `id | ~ ( id & id )`).
2. **Frontend** envía la cadena al endpoint `/api/analizar`.
3. **Backend** ejecuta:
   - **Lexer**: convierte la cadena en tokens.
   - **Parser** (descendente recursivo): construye el AST respetando precedencia.
   - **DerivationBuilder**: reconstruye las derivaciones leftmost y rightmost desde el AST.
4. **Frontend** recibe JSON y renderiza tokens, derivaciones y árbol.

---

## 🗂️ Estructura del Proyecto

```
boolean-glc/
├── .gitignore
├── backend/
│   ├── app.py                 # Entrypoint Flask (rutas HTTP)
│   ├── requirements.txt       # Dependencias Python
│   └── core/
│       ├── __init__.py
│       ├── lexer.py           # Tokenización con regex
│       ├── parser.py          # Parser descendente recursivo + AST
│       ├── derivation.py      # Leftmost, Rightmost, Árbol de esquematización
│       └── api.py             # (opcional) DTOs / serialización
└── frontend/
    ├── index.html
    ├── package.json
    ├── package-lock.json      # ⬅️ Sí va en Git (determinismo)
    ├── vite.config.js         # Proxy a Flask en desarrollo
    └── src/
        ├── main.jsx           # Punto de entrada React
        ├── App.jsx            # Layout principal
        ├── api.js             # Cliente Axios centralizado
        └── components/
            ├── InputForm.jsx
            ├── DerivationSteps.jsx
            └── ParseTree.jsx
```

---

## 🧮 Gramática Formal Implementada

```
Exp    → Exp | Term | Term          (Nivel 1: OR,  menor precedencia)
Term   → Term & Factor | Factor     (Nivel 2: AND, mayor precedencia)
Factor → ~ Factor | ( Exp ) | id   (Nivel 3: NOT, máxima precedencia)
```

**Precedencia (de mayor a menor):**
1. `~`  (NOT)
2. `&`  (AND)
3. `|`  (OR)

**Asociatividad:** Izquierda para `|` y `&`.

---

## ⚙️ Requisitos Previos

| Software | Versión mínima | Verificar |
|----------|---------------|-----------|
| Python   | 3.10          | `python --version` |
| Node.js  | 18.x          | `node --version` |
| npm      | 9.x           | `npm --version` |

---

## 🚀 Instalación Paso a Paso

### 1. Clonar o crear la estructura

```bash
git clone <url-del-repo> boolean-glc
cd boolean-glc
```

### 2. Backend (Flask)

```bash
# Entrar al directorio
cd backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# macOS / Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

**Contenido de `requirements.txt`:**
```text
flask==3.0.3
flask-cors==4.0.0
```

### 3. Frontend (Vite + React)

```bash
# Desde la raíz del proyecto, entrar a frontend
cd ../frontend

# Instalar dependencias (usa el package-lock.json versionado)
npm install
```

**Contenido clave de `vite.config.js`:**
```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  },
  build: { outDir: 'dist' }
})
```

---

## ▶️ Ejecución en Desarrollo

Necesitas **dos terminales** simultáneas.

### Terminal 1 — Backend

```bash
cd backend
source venv/bin/activate   # Windows: venv\Scripts\activate
python app.py
```

Deberías ver:
```
 * Running on http://127.0.0.1:5000
```

### Terminal 2 — Frontend

```bash
cd frontend
npm run dev
```

Deberías ver:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
```

Abre tu navegador en **http://localhost:5173**.

> 💡 El proxy de Vite redirige automáticamente las llamadas `/api/*` al Flask en `:5000`.

---

## 📡 API Endpoints

| Método | Ruta | Body | Respuesta |
|--------|------|------|-----------|
| `POST` | `/api/analizar` | `{"expresion": "id | ~ (id & id)"}` | Ver abajo |
| `GET`  | `/api/health` | — | `{"status": "ok"}` |

### Respuesta de `/api/analizar` (ejemplo)

```json
{
  "expresion": "id | ~ ( id & id )",
  "valida": true,
  "tokens": [
    {"tipo": "ID", "valor": "id", "pos": 0},
    {"tipo": "OR", "valor": "|", "pos": 3},
    {"tipo": "NOT", "valor": "~", "pos": 5},
    {"tipo": "LPAREN", "valor": "(", "pos": 7},
    {"tipo": "ID", "valor": "id", "pos": 9},
    {"tipo": "AND", "valor": "&", "pos": 12},
    {"tipo": "ID", "valor": "id", "pos": 14},
    {"tipo": "RPAREN", "valor": ")", "pos": 17}
  ],
  "leftmost": [
    {"paso": 1, "forma": "Exp", "produccion": "Inicio"},
    {"paso": 2, "forma": "Exp | Term", "produccion": "Exp → Exp | Term"},
    ...
  ],
  "rightmost": [
    {"paso": 1, "forma": "Exp", "produccion": "Inicio"},
    {"paso": 2, "forma": "Exp | Term", "produccion": "Exp → Exp | Term"},
    ...
  ],
  "arbol": {
    "symbol": "Exp",
    "children": [
      {"symbol": "Exp", "children": [...]},
      {"symbol": "|", "token": "|"},
      {"symbol": "Term", "children": [...]}
    ]
  }
}
```

---

## 🧪 Pruebas Sugeridas

| Expresión | ¿Válida? | Observación |
|-----------|----------|-------------|
| `id \| ~ ( id & id )` | ✅ | Precedencia: `~` agrupa `(id & id)` |
| `A \| B & C` | ✅ | `&` tiene mayor precedencia que `\|` → `(A \| (B & C))` |
| `~ ~ id` | ✅ | NOT anidado |
| `( id \| id ) & id` | ✅ | Paréntesis alteran precedencia |
| `id &` | ❌ | Faltan operandos |
| `id id` | ❌ | Falta operador |
| `\| id` | ❌ | Falta operando izquierdo |

---

**Autor(es):** *Estudiantes de Ingenieria de Ciencias de Computacion UNL - Lisbeth, Jostin, Freddy - 6A - Teoria de Automatas*  
