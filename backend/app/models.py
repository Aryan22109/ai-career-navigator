from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from .skills_data import ROLES


class Base(DeclarativeBase):
    pass


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    skills: Mapped[list["RoleSkill"]] = relationship(back_populates="role", cascade="all, delete-orphan")


class RoleSkill(Base):
    __tablename__ = "role_skills"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), index=True)
    skill: Mapped[str] = mapped_column(String(80))
    weight: Mapped[int] = mapped_column(Integer)
    role: Mapped[Role] = relationship(back_populates="skills")


class Analysis(Base):
    """Stores only aggregate results. Resume text and personal details are never persisted."""
    __tablename__ = "analyses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_key: Mapped[str] = mapped_column(String(50), index=True)
    score: Mapped[float] = mapped_column(Float)
    matched_count: Mapped[int] = mapped_column(Integer)
    missing_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


def make_session_factory(url: str):
    engine = create_engine(url, pool_pre_ping=True, future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(engine, expire_on_commit=False)


def seed_roles(session_factory):
    with session_factory() as s:
        existing = {r.key: r for r in s.scalars(select(Role))}
        for key, (name, skills) in ROLES.items():
            role = existing.get(key) or Role(key=key, name=name)
            role.name = name
            role.skills = [RoleSkill(skill=sk, weight=w) for sk, w in skills.items()]
            s.add(role)
        s.commit()
