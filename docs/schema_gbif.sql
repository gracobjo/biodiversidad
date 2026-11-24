CREATE DATABASE IF NOT EXISTS gbif_biodiversidad
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE gbif_biodiversidad;

-- 1. Tabla de Taxones (Endpoint: /v1/species/match y /v1/species/{key})
CREATE TABLE IF NOT EXISTS taxones (
    taxon_key INT PRIMARY KEY,
    scientific_name VARCHAR(255) NOT NULL,
    canonical_name VARCHAR(255),
    taxon_rank VARCHAR(50),
    taxonomic_status VARCHAR(50),
    kingdom VARCHAR(100),
    phylum VARCHAR(100),
    class_name VARCHAR(100),
    order_name VARCHAR(100),
    family VARCHAR(100),
    genus VARCHAR(100),
    species VARCHAR(150),
    raw_json JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Tabla de Organizaciones (Endpoint: /v1/organization/{key})
CREATE TABLE IF NOT EXISTS organizaciones (
    organization_key CHAR(36) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    country CHAR(2),
    city VARCHAR(150),
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    homepage VARCHAR(500),
    raw_json JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 3. Tabla de Datasets (Endpoint: /v1/dataset/{key})
CREATE TABLE IF NOT EXISTS datasets (
    dataset_key CHAR(36) PRIMARY KEY,
    organization_key CHAR(36),
    title VARCHAR(500) NOT NULL,
    dataset_type VARCHAR(50),
    license VARCHAR(255),
    doi VARCHAR(150),
    raw_json JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_dataset_org FOREIGN KEY (organization_key)
        REFERENCES organizaciones(organization_key)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 4. Tabla de Ocurrencias (Endpoint: /v1/occurrence/search)
CREATE TABLE IF NOT EXISTS ocurrencias (
    occurrence_key BIGINT PRIMARY KEY,
    taxon_key INT,
    dataset_key CHAR(36),
    organization_key CHAR(36),
    
    -- Taxonomía a nivel de registro (distingue lupus vs familiaris)
    scientific_name VARCHAR(255),
    accepted_scientific_name VARCHAR(255),
    taxon_rank VARCHAR(50),
    specific_epithet VARCHAR(100),
    infraspecific_epithet VARCHAR(100),
    
    -- Espacio y tiempo
    country_code CHAR(2),
    state_province VARCHAR(150),
    comunidad_gadm VARCHAR(150),
    provincia_gadm VARCHAR(150),
    municipio_gadm VARCHAR(150),
    locality TEXT,
    decimal_latitude DECIMAL(10, 7),
    decimal_longitude DECIMAL(10, 7),
    coordinate_uncertainty_m DECIMAL(10, 2),
    event_date VARCHAR(50),
    year INT,
    month INT,
    day INT,
    
    -- Evidencia, estado y trazabilidad
    basis_of_record VARCHAR(80),
    occurrence_status VARCHAR(50),
    vitality VARCHAR(50),
    individual_count INT,
    sex VARCHAR(50),
    life_stage VARCHAR(50),
    recorded_by TEXT,
    identified_by TEXT,
    catalog_number VARCHAR(150),
    institution_code VARCHAR(100),
    license VARCHAR(255),
    gbif_url VARCHAR(255),
    
    -- Registro íntegro en JSON
    raw_json JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_occ_taxon FOREIGN KEY (taxon_key)
        REFERENCES taxones(taxon_key) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_occ_dataset FOREIGN KEY (dataset_key)
        REFERENCES datasets(dataset_key) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_occ_org FOREIGN KEY (organization_key)
        REFERENCES organizaciones(organization_key) ON DELETE SET NULL ON UPDATE CASCADE,
        
    -- Índices para acelerar las consultas exploratorias en el notebook
    INDEX idx_occ_country_year (country_code, year),
    INDEX idx_occ_taxon_rank (taxon_rank, specific_epithet),
    INDEX idx_occ_comunidad (comunidad_gadm),
    INDEX idx_occ_basis (basis_of_record),
    INDEX idx_occ_coords (decimal_latitude, decimal_longitude)
) ENGINE=InnoDB;