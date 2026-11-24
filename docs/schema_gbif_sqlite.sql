-- Activar el soporte de claves foráneas en SQLite (imprescindible en cada conexión)
PRAGMA foreign_keys = ON;

-- 1. Tabla de Taxones (Endpoint: /v1/species/match y /v1/species/{key})
CREATE TABLE IF NOT EXISTS taxones (
    taxon_key INTEGER PRIMARY KEY,
    scientific_name TEXT NOT NULL,
    canonical_name TEXT,
    taxon_rank TEXT,
    taxonomic_status TEXT,
    kingdom TEXT,
    phylum TEXT,
    class_name TEXT,
    order_name TEXT,
    family TEXT,
    genus TEXT,
    species TEXT,
    raw_json TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- 2. Tabla de Organizaciones (Endpoint: /v1/organization/{key})
CREATE TABLE IF NOT EXISTS organizaciones (
    organization_key TEXT PRIMARY KEY CHECK (length(organization_key) = 36),
    title TEXT NOT NULL,
    country TEXT CHECK (country IS NULL OR length(country) = 2),
    city TEXT,
    latitude REAL,
    longitude REAL,
    homepage TEXT,
    raw_json TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- 3. Tabla de Datasets (Endpoint: /v1/dataset/{key})
CREATE TABLE IF NOT EXISTS datasets (
    dataset_key TEXT PRIMARY KEY CHECK (length(dataset_key) = 36),
    organization_key TEXT,
    title TEXT NOT NULL,
    dataset_type TEXT,
    license TEXT,
    doi TEXT,
    raw_json TEXT,
    updated_at TEXT DEFAULT (datetime('now')),
    CONSTRAINT fk_dataset_org FOREIGN KEY (organization_key)
        REFERENCES organizaciones(organization_key)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- 4. Tabla de Ocurrencias (Endpoint: /v1/occurrence/search)
CREATE TABLE IF NOT EXISTS ocurrencias (
    occurrence_key INTEGER PRIMARY KEY,
    taxon_key INTEGER,
    dataset_key TEXT,
    organization_key TEXT,
    
    -- Taxonomía a nivel de registro (distingue lupus vs familiaris)
    scientific_name TEXT,
    accepted_scientific_name TEXT,
    taxon_rank TEXT,
    specific_epithet TEXT,
    infraspecific_epithet TEXT,
    
    -- Espacio y tiempo
    country_code TEXT CHECK (country_code IS NULL OR length(country_code) = 2),
    state_province TEXT,
    comunidad_gadm TEXT,
    provincia_gadm TEXT,
    municipio_gadm TEXT,
    locality TEXT,
    decimal_latitude REAL,
    decimal_longitude REAL,
    coordinate_uncertainty_m REAL,
    event_date TEXT,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    
    -- Evidencia, estado y trazabilidad
    basis_of_record TEXT,
    occurrence_status TEXT,
    vitality TEXT,
    individual_count INTEGER,
    sex TEXT,
    life_stage TEXT,
    recorded_by TEXT,
    identified_by TEXT,
    catalog_number TEXT,
    institution_code TEXT,
    license TEXT,
    gbif_url TEXT,
    
    -- Registro íntegro en JSON (SQLite soporta funciones json_extract nativas sobre TEXT)
    raw_json TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    
    CONSTRAINT fk_occ_taxon FOREIGN KEY (taxon_key)
        REFERENCES taxones(taxon_key) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_occ_dataset FOREIGN KEY (dataset_key)
        REFERENCES datasets(dataset_key) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_occ_org FOREIGN KEY (organization_key)
        REFERENCES organizaciones(organization_key) ON DELETE SET NULL ON UPDATE CASCADE
);

-- Índices para acelerar las consultas exploratorias
CREATE INDEX IF NOT EXISTS idx_occ_country_year ON ocurrencias (country_code, year);
CREATE INDEX IF NOT EXISTS idx_occ_taxon_rank ON ocurrencias (taxon_rank, specific_epithet);
CREATE INDEX IF NOT EXISTS idx_occ_comunidad ON ocurrencias (comunidad_gadm);
CREATE INDEX IF NOT EXISTS idx_occ_basis ON ocurrencias (basis_of_record);
CREATE INDEX IF NOT EXISTS idx_occ_coords ON ocurrencias (decimal_latitude, decimal_longitude);