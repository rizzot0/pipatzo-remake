# ALTERNATIVAS A PostgreSQL - GUÍA COMPLETA

## ❓ ¿POR QUÉ NO USAR PostgreSQL?

**Ventajas de evitar PostgreSQL para práctica**:
- ❌ Requiere instalación y servidor corriendo
- ❌ Más complejidad inicial
- ❌ Overhead para desarrollo simple
- ✅ Para **práctica y prototipado**: Sobrekill

**Veredicto**: Para aprender y practicar, SQLite es MEJOR.

---

## 🎯 COMPARATIVA DE OPCIONES

| Característica | SQLite | PostgreSQL | MongoDB |
|----------------|--------|-----------|---------|
| **Setup** | ✅ 0 min | ❌ 15 min | ❌ 10 min |
| **Instalación** | ✅ Ninguna | ❌ Requiere servidor | ❌ Requiere servidor |
| **Archivo** | ✅ Local .db | ❌ Servidor | ❌ Servidor |
| **Ideal para** | ✅ Desarrollo | ✅ Producción | ⚠️ NoSQL |
| **Relaciones** | ✅ Sí | ✅ Sí | ⚠️ Débiles |
| **Escalabilidad** | ⚠️ Limitada | ✅ Excelente | ✅ Excelente |
| **Grafo/Routing** | ✅ Perfecto | ✅ Perfecto | ⚠️ Complicado |
| **Prisma support** | ✅ Sí | ✅ Sí | ✅ Sí |
| **SQLAlchemy** | ✅ Sí | ✅ Sí | ⚠️ Mongoengine |

---

## 🚀 RECOMENDACIÓN NIVEL POR NIVEL

### **Si eres PRINCIPIANTE**
→ **SQLite + SQLAlchemy** (Python)
- CERO instalación
- Archivo local (pipatzo.db)
- Perfecto para aprender

### **Si quieres algo MODERNO**
→ **SQLite + Prisma** (Node.js)
- Type-safe (TypeScript)
- Excelente Developer Experience
- Fácil de migrar después

### **Si vas a PRODUCCIÓN**
→ **PostgreSQL + SQLAlchemy** (Python) **ó** Prisma (Node.js)
- Escalabilidad
- Multi-usuario
- Backups robustos

---

## 📋 OPCIÓN 1: SQLITE + SQLAlchemy (RECOMENDADO PARA TI)

**Por qué esta opción**:
- ✅ Mantienes Python/FastAPI
- ✅ CERO instalación
- ✅ SQLAlchemy es tipo-safe y moderno
- ✅ Fácil migrar después a PostgreSQL

### Setup

```bash
# 1. Instalar dependencias
pip install sqlalchemy fastapi uvicorn

# 2. Ejecutar migración (crea pipatzo.db automáticamente)
python migrate_to_sqlite.py --ciudad coquimbo

# 3. Ejecutar backend
python main_sqlite.py

# 4. Acceder a documentación
# http://localhost:8000/docs
```

### Diferencias con PostgreSQL

**PostgreSQL (primer script)**:
```python
# Requería esto:
conn = psycopg2.connect(
    host="localhost",
    database="pipatzo_db",
    user="pipatzo",
    password="pipatzo123"
)
```

**SQLite (nuevo script)**:
```python
# Simplemente:
engine = create_engine("sqlite:///pipatzo.db")
# ✓ Archivo local, sin servidor

# Lo demás es IGUAL (SQLAlchemy maneja todo)
```

### Ventajas Prácticas

```bash
# Compartir proyecto = compartir 1 archivo
git add pipatzo.db  # Todo está en un archivo

# vs PostgreSQL = requiere que tengan BD corriendo
```

### Migrar después a PostgreSQL

Si después necesitas PostgreSQL (para producción):

```python
# Cambiar esta línea:
engine = create_engine("sqlite:///pipatzo.db")

# Por esta (SIN cambiar el resto del código):
engine = create_engine("postgresql://user:pass@localhost/pipatzo_db")

# SQLAlchemy maneja todo automáticamente
```

---

## 💎 OPCIÓN 2: SQLITE + PRISMA (SI CAMBIAS A NODE.JS)

**Para si decides usar TypeScript/Node.js**

### Setup

```bash
# 1. Crear proyecto
npx create-next-app@latest pipatzo --typescript

cd pipatzo

# 2. Instalar Prisma
npm install @prisma/client
npm install -D prisma

# 3. Inicializar Prisma con SQLite
npx prisma init

# 4. Editar .env
DATABASE_URL="file:./dev.db"
```

### Schema Prisma (prisma/schema.prisma)

```prisma
datasource db {
  provider = "sqlite"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

model Ciudad {
  id    Int     @id @default(autoincrement())
  nombre String  @unique
  nodos   Nodo[]
  edges   Edge[]
}

model Nodo {
  id        Int     @id @default(autoincrement())
  ciudad_id Int
  ciudad    Ciudad  @relation(fields: [ciudad_id], references: [id])
  osmid     String
  latitud   Float
  longitud  Float
  street_count Int?
  highway   String?
  
  edges_origen Edge[] @relation("origen")
  edges_destino Edge[] @relation("destino")
  
  @@unique([ciudad_id, osmid])
  @@index([ciudad_id])
}

model Edge {
  id              Int @id @default(autoincrement())
  ciudad_id       Int
  nodo_origen_id  Int
  nodo_destino_id Int
  k               Int @default(0)
  osmid           String?
  nombre          String?
  distancia       Float
  
  ciudad    Ciudad @relation(fields: [ciudad_id], references: [id])
  nodo_org  Nodo   @relation("origen", fields: [nodo_origen_id], references: [id])
  nodo_dest Nodo   @relation("destino", fields: [nodo_destino_id], references: [id])
  
  @@index([ciudad_id])
}
```

### Ejecutar

```bash
# 1. Crear BD
npx prisma migrate dev --name init

# 2. Migrar datos
# (adaptar script Python a Node.js)

# 3. Backend API Routes (Next.js)
# app/api/rutas/calcular/route.ts

# 4. Frontend + Backend integrados en Next.js
npm run dev
```

**Ventajas de esta opción**:
- ✅ **Type-safe** - TypeScript evita errores
- ✅ **Modern** - Prisma es lo más nuevo
- ✅ **Fast** - Compilación instantánea
- ✅ **DX** - Mejor experiencia de desarrollo
- ✅ **Full-stack** - Todo en JavaScript/TypeScript

**Desventaja**:
- ⚠️ Requiere cambiar toda la arquitectura (Python → Node.js)

---

## 🔄 OPCIÓN 3: MONGODB + MONGOOSE

**Para si prefieres NoSQL**

### ¿Cuándo NO usar?
- ❌ Grafos necesitan relaciones fuertes
- ❌ Aristas con pesos es mejor en SQL
- ⚠️ Dijkstra requiere joins complejos

### Cuándo sí
- ✅ Datos semi-estructurados
- ✅ Escalabilidad horizontal
- ✅ Flexible schemas

**Veredicto**: NO recomendado para este proyecto (necesitas SQL relacional)

---

## 📊 COMPARATIVA FINAL DE ESFUERZO

| Tarea | SQLite | PostgreSQL | Prisma |
|-------|--------|-----------|--------|
| Setup completo | 5 min | 15 min | 10 min |
| Documentación | ✅ Simple | ⚠️ Compleja | ✅ Excelente |
| Debugging | ✅ Fácil | ⚠️ Requiere CLI | ✅ Super fácil |
| Pasar a producción | ✅ Cambiar string | ✅ Cambiar string | ✅ Cambiar dsn |
| Courier/compartir | ✅ 1 archivo | ❌ Requiere dump | ✅ 1 archivo |

---

## ✅ RECOMENDACIÓN FINAL

**👉 SI SÓLO QUIERES APRENDER AHORA:**
```
SQLite + SQLAlchemy + FastAPI + Next.js
↓
Tiempo total setup: 15 minutos
Archivo final: pipatzo.db (enviable por email)
Producción después: cambiar 1 línea de código
```

**👉 SI QUIERES STACK MODERNO DESDE YA:**
```
SQLite + Prisma + Next.js API Routes + React
↓
Tiempo total setup: 20 minutos
Type-safe: Sí
Documentation: Excelente
```

**👉 SI VA A SER PRODUCCIÓN YA:**
```
PostgreSQL + SQLAlchemy + FastAPI (Python)
ó
PostgreSQL + Prisma + Next.js (TypeScript)
↓
Tiempo total setup: 30 minutos
Escalabilidad: Ilimitada
```

---

## 🚀 COMEÇAR AHORA CON SQLITE

### Paso 1: Instalar
```bash
pip install sqlalchemy fastapi uvicorn
```

### Paso 2: Migrar datos
```bash
python migrate_to_sqlite.py --ciudad coquimbo
# ✓ Crea: pipatzo.db automáticamente
```

### Paso 3: Ejecutar backend
```bash
python main_sqlite.py
# ✓ Accede a: http://localhost:8000/docs
```

### Paso 4: Usar desde Next.js
```typescript
// pages/index.tsx
const res = await fetch('http://localhost:8000/api/rutas/calcular', {
  method: 'POST',
  body: JSON.stringify({
    ciudad_id: 1,
    nodo_origen_id: 100,
    nodo_destino_id: 250
  })
})
```

---

## 🎓 CONCLUSIÓN

**SQLite es TU opción perfecta** porque:
1. ✅ CERO instalación
2. ✅ Mantienes Python/FastAPI
3. ✅ Archivo portable (pipatzo.db)
4. ✅ Fácil compartir/colaborar
5. ✅ Muy fácil migrar después a PostgreSQL

**Scripts ya listos para usar**:
- `migrate_to_sqlite.py` - Migración automática
- `main_sqlite.py` - Backend FastAPI ya configurado

**¡Comienza ahora! No requiere nada más que lo que ya tienes instalado.** 🚀
