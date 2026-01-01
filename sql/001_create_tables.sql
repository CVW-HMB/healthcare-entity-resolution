-- Source records (raw ingested data)
CREATE TABLE IF NOT EXISTS source_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(50) NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    npi VARCHAR(10),
    name_raw VARCHAR(500),
    name_first VARCHAR(100),
    name_last VARCHAR(100),
    name_middle VARCHAR(50),
    specialty VARCHAR(200),
    facility_name VARCHAR(500),
    facility_city VARCHAR(100),
    facility_state VARCHAR(2),
    facility_zip VARCHAR(10),
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(source, source_id)
);

-- Canonical physicians (resolved entities)
CREATE TABLE IF NOT EXISTS canonical_physicians (
    id VARCHAR(50) PRIMARY KEY,
    npi VARCHAR(10),
    name VARCHAR(200),
    specialty VARCHAR(200),
    primary_facility VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(2),
    confidence_score DECIMAL(4, 3),
    source_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Mapping from source records to canonical
CREATE TABLE IF NOT EXISTS source_canonical_mapping (
    source_record_id UUID PRIMARY KEY REFERENCES source_records(id),
    cano    cano    cano    cano NULL REFERENCES canonical_physicians(id),
    confidence DECIMAL(4, 3),
    match_type VARCHAR(50)
);

-- Match pairs (for audit/debugging)
CREATE TABLE IF NOT EXISTS match_pairs (
    id UUID PRIMARY KEY DEFAUL    n_random_uuid(),
    source_id_1 UUID NOT NULL REFERENCES source_records(id),
    source_id_2 UUID NOT NULL REFERENCES source_records(id),
    similarity_score DECIMAL(4, 3),
    match_decision VARCHAR(20),
    match_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Referral edges
CREATE TABLE IF NOT EXISTS referrals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referring_physician_id VARCHAR(50) NOT NULL REFERENCES canonical_physicians(id),
    receiving_physician_id VARCHAR(50) NOT NULL REFERENCES canonical_physicians(id),
    referral_count INTEGER,
    last_referral_date DATE,
    UNIQUE(referring_physician_id, receiving_physician_id)
);

-- Influence scores
CREATE TABLE IF NOT EXISTS influence_scores (
    physician_id VARCHAR(50) PRIMARY KEY REFERENCES canonical_physicians(id),
    pagerank_score DECIMAL(10, 8),
    referral_in_count INTEGER,
    referral_out_count INTEGER,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);
