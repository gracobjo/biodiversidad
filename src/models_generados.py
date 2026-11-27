from typing import Optional
import datetime
import decimal

from sqlalchemy import BigInteger, CHAR, DECIMAL, ForeignKeyConstraint, Index, Integer, JSON, String, TIMESTAMP, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class Organizaciones(Base):
    __tablename__ = 'organizaciones'

    organization_key: Mapped[str] = mapped_column(CHAR(36, 'utf8mb4_unicode_ci'), primary_key=True)
    title: Mapped[str] = mapped_column(String(500, 'utf8mb4_unicode_ci'), nullable=False)
    country: Mapped[Optional[str]] = mapped_column(CHAR(2, 'utf8mb4_unicode_ci'))
    city: Mapped[Optional[str]] = mapped_column(String(150, 'utf8mb4_unicode_ci'))
    latitude: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 7))
    longitude: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 7))
    homepage: Mapped[Optional[str]] = mapped_column(String(500, 'utf8mb4_unicode_ci'))
    raw_json: Mapped[Optional[object]] = mapped_column(JSON)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    datasets: Mapped[list['Datasets']] = relationship('Datasets', back_populates='organizaciones')
    ocurrencias: Mapped[list['Ocurrencias']] = relationship('Ocurrencias', back_populates='organizaciones')


class Taxones(Base):
    __tablename__ = 'taxones'

    taxon_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    scientific_name: Mapped[str] = mapped_column(String(255, 'utf8mb4_unicode_ci'), nullable=False)
    canonical_name: Mapped[Optional[str]] = mapped_column(String(255, 'utf8mb4_unicode_ci'))
    taxon_rank: Mapped[Optional[str]] = mapped_column(String(50, 'utf8mb4_unicode_ci'))
    taxonomic_status: Mapped[Optional[str]] = mapped_column(String(50, 'utf8mb4_unicode_ci'))
    kingdom: Mapped[Optional[str]] = mapped_column(String(100, 'utf8mb4_unicode_ci'))
    phylum: Mapped[Optional[str]] = mapped_column(String(100, 'utf8mb4_unicode_ci'))
    class_name: Mapped[Optional[str]] = mapped_column(String(100, 'utf8mb4_unicode_ci'))
    order_name: Mapped[Optional[str]] = mapped_column(String(100, 'utf8mb4_unicode_ci'))
    family: Mapped[Optional[str]] = mapped_column(String(100, 'utf8mb4_unicode_ci'))
    genus: Mapped[Optional[str]] = mapped_column(String(100, 'utf8mb4_unicode_ci'))
    species: Mapped[Optional[str]] = mapped_column(String(150, 'utf8mb4_unicode_ci'))
    raw_json: Mapped[Optional[object]] = mapped_column(JSON)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    ocurrencias: Mapped[list['Ocurrencias']] = relationship('Ocurrencias', back_populates='taxones')


class Datasets(Base):
    __tablename__ = 'datasets'
    __table_args__ = (
        ForeignKeyConstraint(['organization_key'], ['organizaciones.organization_key'], ondelete='SET NULL', onupdate='CASCADE', name='fk_dataset_org'),
        Index('fk_dataset_org', 'organization_key')
    )

    dataset_key: Mapped[str] = mapped_column(CHAR(36, 'utf8mb4_unicode_ci'), primary_key=True)
    title: Mapped[str] = mapped_column(String(500, 'utf8mb4_unicode_ci'), nullable=False)
    organization_key: Mapped[Optional[str]] = mapped_column(CHAR(36, 'utf8mb4_unicode_ci'))
    dataset_type: Mapped[Optional[str]] = mapped_column(String(50, 'utf8mb4_unicode_ci'))
    license: Mapped[Optional[str]] = mapped_column(String(255, 'utf8mb4_unicode_ci'))
    doi: Mapped[Optional[str]] = mapped_column(String(150, 'utf8mb4_unicode_ci'))
    raw_json: Mapped[Optional[object]] = mapped_column(JSON)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    organizaciones: Mapped[Optional['Organizaciones']] = relationship('Organizaciones', back_populates='datasets')
    ocurrencias: Mapped[list['Ocurrencias']] = relationship('Ocurrencias', back_populates='datasets')


class Ocurrencias(Base):
    __tablename__ = 'ocurrencias'
    __table_args__ = (
        ForeignKeyConstraint(['dataset_key'], ['datasets.dataset_key'], ondelete='SET NULL', onupdate='CASCADE', name='fk_occ_dataset'),
        ForeignKeyConstraint(['organization_key'], ['organizaciones.organization_key'], ondelete='SET NULL', onupdate='CASCADE', name='fk_occ_org'),
        ForeignKeyConstraint(['taxon_key'], ['taxones.taxon_key'], ondelete='SET NULL', onupdate='CASCADE', name='fk_occ_taxon'),
        Index('fk_occ_dataset', 'dataset_key'),
        Index('fk_occ_org', 'organization_key'),
        Index('fk_occ_taxon', 'taxon_key'),
        Index('idx_occ_basis', 'basis_of_record'),
        Index('idx_occ_comunidad', 'comunidad_gadm'),
        Index('idx_occ_coords', 'decimal_latitude', 'decimal_longitude'),
        Index('idx_occ_country_year', 'country_code', 'year'),
        Index('idx_occ_taxon_rank', 'taxon_rank', 'specific_epithet')
    )

    occurrence_key: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    taxon_key: Mapped[Optional[int]] = mapped_column(Integer)
    dataset_key: Mapped[Optional[str]] = mapped_column(CHAR(36, 'utf8mb4_unicode_ci'))
    organization_key: Mapped[Optional[str]] = mapped_column(CHAR(36, 'utf8mb4_unicode_ci'))
    scientific_name: Mapped[Optional[str]] = mapped_column(String(255, 'utf8mb4_unicode_ci'))
    accepted_scientific_name: Mapped[Optional[str]] = mapped_column(String(255, 'utf8mb4_unicode_ci'))
    taxon_rank: Mapped[Optional[str]] = mapped_column(String(50, 'utf8mb4_unicode_ci'))
    specific_epithet: Mapped[Optional[str]] = mapped_column(String(100, 'utf8mb4_unicode_ci'))
    infraspecific_epithet: Mapped[Optional[str]] = mapped_column(String(100, 'utf8mb4_unicode_ci'))
    country_code: Mapped[Optional[str]] = mapped_column(CHAR(2, 'utf8mb4_unicode_ci'))
    state_province: Mapped[Optional[str]] = mapped_column(String(150, 'utf8mb4_unicode_ci'))
    comunidad_gadm: Mapped[Optional[str]] = mapped_column(String(150, 'utf8mb4_unicode_ci'))
    provincia_gadm: Mapped[Optional[str]] = mapped_column(String(150, 'utf8mb4_unicode_ci'))
    municipio_gadm: Mapped[Optional[str]] = mapped_column(String(150, 'utf8mb4_unicode_ci'))
    locality: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_unicode_ci'))
    decimal_latitude: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 7))
    decimal_longitude: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 7))
    coordinate_uncertainty_m: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2))
    event_date: Mapped[Optional[str]] = mapped_column(String(50, 'utf8mb4_unicode_ci'))
    year: Mapped[Optional[int]] = mapped_column(Integer)
    month: Mapped[Optional[int]] = mapped_column(Integer)
    day: Mapped[Optional[int]] = mapped_column(Integer)
    basis_of_record: Mapped[Optional[str]] = mapped_column(String(80, 'utf8mb4_unicode_ci'))
    occurrence_status: Mapped[Optional[str]] = mapped_column(String(50, 'utf8mb4_unicode_ci'))
    vitality: Mapped[Optional[str]] = mapped_column(String(50, 'utf8mb4_unicode_ci'))
    individual_count: Mapped[Optional[int]] = mapped_column(Integer)
    sex: Mapped[Optional[str]] = mapped_column(String(50, 'utf8mb4_unicode_ci'))
    life_stage: Mapped[Optional[str]] = mapped_column(String(50, 'utf8mb4_unicode_ci'))
    recorded_by: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_unicode_ci'))
    identified_by: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_unicode_ci'))
    catalog_number: Mapped[Optional[str]] = mapped_column(String(150, 'utf8mb4_unicode_ci'))
    institution_code: Mapped[Optional[str]] = mapped_column(String(100, 'utf8mb4_unicode_ci'))
    license: Mapped[Optional[str]] = mapped_column(String(255, 'utf8mb4_unicode_ci'))
    gbif_url: Mapped[Optional[str]] = mapped_column(String(255, 'utf8mb4_unicode_ci'))
    raw_json: Mapped[Optional[object]] = mapped_column(JSON)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    datasets: Mapped[Optional['Datasets']] = relationship('Datasets', back_populates='ocurrencias')
    organizaciones: Mapped[Optional['Organizaciones']] = relationship('Organizaciones', back_populates='ocurrencias')
    taxones: Mapped[Optional['Taxones']] = relationship('Taxones', back_populates='ocurrencias')
