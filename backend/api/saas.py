"""Cuentas, rutas guardadas y geocoding. Postgres si hay DATABASE_URL; si no, SQLite local."""

from __future__ import annotations

import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

import bcrypt
import httpx
import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, create_engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[1]
JWT_SECRET = os.getenv("JWT_SECRET", "planvial-dev-secret-cambia-en-produccion")
JWT_ALG = "HS256"
JWT_DAYS = 7
NOMINATIM_UA = os.getenv(
    "NOMINATIM_USER_AGENT",
    "PlanVial/1.0 (https://planvial.onrender.com; bastianalonso92@gmail.com)",
)

_raw_saas_url = os.getenv("DATABASE_URL", "").strip()
if _raw_saas_url:
    SAAS_DATABASE_URL = _raw_saas_url.replace("postgres://", "postgresql+psycopg://", 1)
    if SAAS_DATABASE_URL.startswith("postgresql://") and "+psycopg" not in SAAS_DATABASE_URL:
        SAAS_DATABASE_URL = SAAS_DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    SAAS_BACKEND = "postgres"
else:
    saas_path = BACKEND_DIR / "data" / "planvial_saas.db"
    saas_path.parent.mkdir(parents=True, exist_ok=True)
    SAAS_DATABASE_URL = f"sqlite:///{saas_path.as_posix()}"
    SAAS_BACKEND = "sqlite"

connect_args = {}
if SAAS_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False, "timeout": 30}

saas_engine = create_engine(SAAS_DATABASE_URL, echo=False, connect_args=connect_args)
SaasSessionLocal = sessionmaker(bind=saas_engine)
SaasBase = declarative_base()

_last_nominatim_at = 0.0


class User(SaasBase):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    routes = relationship("SavedRoute", back_populates="user", cascade="all, delete-orphan")


class SavedRoute(SaasBase):
    __tablename__ = "saved_routes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ciudad_id = Column(Integer, nullable=False)
    ciudad_nombre = Column(String(100), nullable=False, default="")
    name = Column(String(200), nullable=False)
    origin_nodo_id = Column(Integer, nullable=False)
    origin_lat = Column(Float, nullable=False)
    origin_lon = Column(Float, nullable=False)
    origin_label = Column(String(255), nullable=False, default="")
    dest_nodo_id = Column(Integer, nullable=False)
    dest_lat = Column(Float, nullable=False)
    dest_lon = Column(Float, nullable=False)
    dest_label = Column(String(255), nullable=False, default="")
    distancia_total = Column(Float, nullable=False)
    num_pasos = Column(Integer, nullable=False)
    geometry = Column(JSON, nullable=False)
    share_id = Column(String(32), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="routes")

    __table_args__ = (UniqueConstraint("share_id", name="uq_saved_routes_share"),)


def init_saas_db() -> None:
    SaasBase.metadata.create_all(saas_engine)


init_saas_db()


def get_saas_session() -> Session:
    session = SaasSessionLocal()
    try:
        yield session
    finally:
        session.close()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def make_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def user_from_token(session: Session, token: str) -> User:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        user_id = int(payload.get("sub", "0"))
    except (jwt.PyJWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Sesión inválida o vencida")
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user


def bearer_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    if not authorization:
        return None
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value:
        return None
    return value


def require_user(
    session: Session = Depends(get_saas_session),
    token: Optional[str] = Depends(bearer_token),
) -> User:
    if not token:
        raise HTTPException(status_code=401, detail="Necesitas iniciar sesión")
    return user_from_token(session, token)


class AuthBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: int
    email: str

    model_config = ConfigDict(from_attributes=True)


class AuthOut(BaseModel):
    token: str
    user: UserOut


class PointIn(BaseModel):
    id: int
    latitud: float
    longitud: float
    label: str = ""


class SaveRouteBody(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    ciudad_id: int
    ciudad_nombre: str = ""
    origen: PointIn
    destino: PointIn
    distancia_total: float
    num_pasos: int
    geometry: List[dict]


class SavedRouteOut(BaseModel):
    id: int
    ciudad_id: int
    ciudad_nombre: str
    name: str
    origin_nodo_id: int
    origin_lat: float
    origin_lon: float
    origin_label: str
    dest_nodo_id: int
    dest_lat: float
    dest_lon: float
    dest_label: str
    distancia_total: float
    num_pasos: int
    geometry: list
    share_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GeocodeHit(BaseModel):
    label: str
    latitud: float
    longitud: float
    nodo: Optional[dict] = None


router = APIRouter()


@router.post("/auth/register", response_model=AuthOut)
def register(body: AuthBody, session: Session = Depends(get_saas_session)):
    email = str(body.email).strip().lower()
    if session.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Ese email ya tiene cuenta")
    user = User(email=email, password_hash=hash_password(body.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return AuthOut(token=make_token(user.id), user=UserOut.model_validate(user))


@router.post("/auth/login", response_model=AuthOut)
def login(body: AuthBody, session: Session = Depends(get_saas_session)):
    email = str(body.email).strip().lower()
    user = session.query(User).filter(User.email == email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    return AuthOut(token=make_token(user.id), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(require_user)):
    return user


@router.get("/rutas", response_model=List[SavedRouteOut])
def list_routes(user: User = Depends(require_user), session: Session = Depends(get_saas_session)):
    rows = (
        session.query(SavedRoute)
        .filter(SavedRoute.user_id == user.id)
        .order_by(SavedRoute.id.desc())
        .all()
    )
    return rows


@router.post("/rutas", response_model=SavedRouteOut)
def save_route(
    body: SaveRouteBody,
    user: User = Depends(require_user),
    session: Session = Depends(get_saas_session),
):
    route = SavedRoute(
        user_id=user.id,
        ciudad_id=body.ciudad_id,
        ciudad_nombre=body.ciudad_nombre or "",
        name=body.name.strip(),
        origin_nodo_id=body.origen.id,
        origin_lat=body.origen.latitud,
        origin_lon=body.origen.longitud,
        origin_label=body.origen.label or f"Nodo #{body.origen.id}",
        dest_nodo_id=body.destino.id,
        dest_lat=body.destino.latitud,
        dest_lon=body.destino.longitud,
        dest_label=body.destino.label or f"Nodo #{body.destino.id}",
        distancia_total=body.distancia_total,
        num_pasos=body.num_pasos,
        geometry=body.geometry,
        share_id=secrets.token_urlsafe(10),
    )
    session.add(route)
    session.commit()
    session.refresh(route)
    return route


@router.get("/rutas/compartidas/{share_id}", response_model=SavedRouteOut)
def public_route(share_id: str, session: Session = Depends(get_saas_session)):
    route = session.query(SavedRoute).filter(SavedRoute.share_id == share_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    return route


@router.get("/rutas/{route_id}", response_model=SavedRouteOut)
def get_route(
    route_id: int,
    user: User = Depends(require_user),
    session: Session = Depends(get_saas_session),
):
    route = (
        session.query(SavedRoute)
        .filter(SavedRoute.id == route_id, SavedRoute.user_id == user.id)
        .first()
    )
    if not route:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    return route


@router.delete("/rutas/{route_id}")
def delete_route(
    route_id: int,
    user: User = Depends(require_user),
    session: Session = Depends(get_saas_session),
):
    route = (
        session.query(SavedRoute)
        .filter(SavedRoute.id == route_id, SavedRoute.user_id == user.id)
        .first()
    )
    if not route:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    session.delete(route)
    session.commit()
    return {"ok": True}


def _throttle_nominatim() -> None:
    global _last_nominatim_at
    wait = 1.05 - (time.time() - _last_nominatim_at)
    if wait > 0:
        time.sleep(wait)
    _last_nominatim_at = time.time()


@router.get("/geocodificar", response_model=List[GeocodeHit])
def geocode(
    q: str = Query(..., min_length=3, max_length=200),
    ciudad_id: Optional[int] = None,
    min_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lat: Optional[float] = None,
    max_lon: Optional[float] = None,
):
    params = {
        "q": q.strip(),
        "format": "jsonv2",
        "limit": 5,
        "addressdetails": 0,
        "countrycodes": "cl",
    }
    if None not in (min_lat, min_lon, max_lat, max_lon):
        params["viewbox"] = f"{min_lon},{max_lat},{max_lon},{min_lat}"
        params["bounded"] = 1

    _throttle_nominatim()
    try:
        response = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params=params,
            headers={"User-Agent": NOMINATIM_UA},
            timeout=12.0,
        )
        response.raise_for_status()
        rows = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Geocoding no disponible: {exc}") from exc

    hits: List[GeocodeHit] = []
    for row in rows:
        try:
            hits.append(
                GeocodeHit(
                    label=row.get("display_name") or q,
                    latitud=float(row["lat"]),
                    longitud=float(row["lon"]),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return hits
