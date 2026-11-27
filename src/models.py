from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    CHAR,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Taxon(Base):
    __tablename__ = "taxones"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}

    taxon_key: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    scientific_name: Mapped[str] = mapped_column(String(255), nullable=False)
    canonical_name: Mapped[Optional[str]] = mapped_column(String(255))
    taxon_rank: Mapped[Optional[str]] = mapped_column(String(50))
    taxonomic_status: Mapped[Optional[str]] = mapped_column(String(50))
    kingdom: Mapped[Optional[str]] = mapped_column(String(100))
    phylum: Mapped[Optional[str]] = mapped_column(String(100))
    class_name: Mapped[Optional[str]] = mapped_column(String(100))
    order_name: Mapped[Optional[str]] = mapped_column(String(100))
    family: Mapped[Optional[str]] = mapped_column(String(100))
    genus: Mapped[Optional[str]] = mapped_column(String(100))
    species: Mapped[Optional[str]] = mapped_column(String(150))
    raw_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    # Relación 1:N con ocurrencias
    ocurrencias: Mapped[list[Ocurrencia]] = relationship(back_populates="taxon")

    def __repr__(self) -> str:
        return f"<Taxon(taxon_key={self.taxon_key}, scientific_name={self.scientific_name!r})>"


class Organizacion(Base):
    __tablename__ = "organizaciones"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}

    organization_key: Mapped[str] = mapped_column(CHAR(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    country: Mapped[Optional[str]] = mapped_column(CHAR(2))
    city: Mapped[Optional[str]] = mapped_column(String(150))
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    homepage: Mapped[Optional[str]] = mapped_column(String(500))
    raw_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    # Relaciones 1:N
    datasets: Mapped[list[Dataset]] = relationship(back_populates="organizacion")
    ocurrencias: Mapped[list[Ocurrencia]] = relationship(back_populates="organizacion")

    def __repr__(self) -> str:
        return f"<Organizacion(organization_key={self.organization_key!r}, title={self.title[:40]!r})>"


class Dataset(Base):
    __tablename__ = "datasets"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}

    dataset_key: Mapped[str] = mapped_column(CHAR(36), primary_key=True)
    organization_key: Mapped[Optional[str]] = mapped_column(
        CHAR(36),
        ForeignKey("organizaciones.organization_key", name="fk_dataset_org", ondelete="SET NULL", onupdate="CASCADE"),
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    dataset_type: Mapped[Optional[str]] = mapped_column(String(50))
    license: Mapped[Optional[str]] = mapped_column(String(255))
    doi: Mapped[Optional[str]] = mapped_column(String(150))
    raw_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    # Relaciones
    organizacion: Mapped[Optional[Organizacion]] = relationship(back_populates="datasets")
    ocurrencias: Mapped[list[Ocurrencia]] = relationship(back_populates="dataset")

    def __repr__(self) -> str:
        return f"<Dataset(dataset_key={self.dataset_key!r}, title={self.title[:40]!r})>"


class Ocurrencia(Base):
    __tablename__ = "ocurrencias"
    __table_args__ = (
        Index("idx_occ_country_year", "country_code", "year"),
        Index("idx_occ_taxon_rank", "taxon_rank", "specific_epithet"),
        Index("idx_occ_comunidad", "comunidad_gadm"),
        Index("idx_occ_basis", "basis_of_record"),
        Index("idx_occ_coords", "decimal_latitude", "decimal_longitude"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    occurrence_key: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    taxon_key: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("taxones.taxon_key", name="fk_occ_taxon", ondelete="SET NULL", onupdate="CASCADE"),
    )
    dataset_key: Mapped[Optional[str]] = mapped_column(
        CHAR(36),
        ForeignKey("datasets.dataset_key", name="fk_occ_dataset", ondelete="SET NULL", onupdate="CASCADE"),
    )
    organization_key: Mapped[Optional[str]] = mapped_column(
        CHAR(36),
        ForeignKey("organizaciones.organization_key", name="fk_occ_org", ondelete="SET NULL", onupdate="CASCADE"),
    )

    # Taxonomía a nivel de registro
    scientific_name: Mapped[Optional[str]] = mapped_column(String(255))
    accepted_scientific_name: Mapped[Optional[str]] = mapped_column(String(255))
    taxon_rank: Mapped[Optional[str]] = mapped_column(String(50))
    specific_epithet: Mapped[Optional[str]] = mapped_column(String(100))
    infraspecific_epithet: Mapped[Optional[str]] = mapped_column(String(100))

    # Espacio y tiempo
    country_code: Mapped[Optional[str]] = mapped_column(CHAR(2))
    state_province: Mapped[Optional[str]] = mapped_column(String(150))
    comunidad_gadm: Mapped[Optional[str]] = mapped_column(String(150))
    provincia_gadm: Mapped[Optional[str]] = mapped_column(String(150))
    municipio_gadm: Mapped[Optional[str]] = mapped_column(String(150))
    locality: Mapped[Optional[str]] = mapped_column(Text)
    decimal_latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    decimal_longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    coordinate_uncertainty_m: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    event_date: Mapped[Optional[str]] = mapped_column(String(50))
    year: Mapped[Optional[int]] = mapped_column(Integer)
    month: Mapped[Optional[int]] = mapped_column(Integer)
    day: Mapped[Optional[int]] = mapped_column(Integer)

    # Evidencia, estado y trazabilidad
    basis_of_record: Mapped[Optional[str]] = mapped_column(String(80))
    occurrence_status: Mapped[Optional[str]] = mapped_column(String(50))
    vitality: Mapped[Optional[str]] = mapped_column(String(50))
    individual_count: Mapped[Optional[int]] = mapped_column(Integer)
    sex: Mapped[Optional[str]] = mapped_column(String(50))
    life_stage: Mapped[Optional[str]] = mapped_column(String(50))
    recorded_by: Mapped[Optional[str]] = mapped_column(Text)
    identified_by: Mapped[Optional[str]] = mapped_column(Text)
    catalog_number: Mapped[Optional[str]] = mapped_column(String(150))
    institution_code: Mapped[Optional[str]] = mapped_column(String(100))
    license: Mapped[Optional[str]] = mapped_column(String(255))
    gbif_url: Mapped[Optional[str]] = mapped_column(String(255))

    # JSON nativo y auditoría
    raw_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.current_timestamp())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    # Relaciones N:1
    taxon: Mapped[Optional[Taxon]] = relationship(back_populates="ocurrencias")
    dataset: Mapped[Optional[Dataset]] = relationship(back_populates="ocurrencias")
    organizacion: Mapped[Optional[Organizacion]] = relationship(back_populates="ocurrencias")

    # Propiedades de conveniencia sobre raw_json
    @property
    def es_lobo_silvestre(self) -> bool:
        return (self.specific_epithet or "").lower() == "lupus" and (
            self.infraspecific_epithet or ""
        ).lower() != "familiaris"

    @property
    def url_primera_imagen(self) -> Optional[str]:
        if not self.raw_json:
            return None
        media = self.raw_json.get("media") or []
        if isinstance(media, list) and media and isinstance(media[0], dict):
            return media[0].get("identifier")
        return None

    @property
    def habitat_json(self) -> Optional[str]:
        return self.raw_json.get("habitat") if self.raw_json else None

    def __repr__(self) -> str:
        return (
            f"<Ocurrencia(key={self.occurrence_key}, species={self.scientific_name!r}, "
            f"pais={self.country_code!r}, year={self.year})>"
        )