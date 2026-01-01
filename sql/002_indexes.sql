-- Source records indexes
CREATE INDEX IF NOT EXISTS idx_source_records_npi ON source_records(npi);
CREATE INDEX IF NOT EXISTS idx_source_records_source ON source_records(source);
CREATE INDEX IF NOT EXISTS idx_source_records_name_last ON source_records(name_last);
CREATE INDEX IF NOT EXISTS idx_source_records_state ON source_records(facility_state);
CREATE INDEX IF NOT EXISTS idx_source_records_last_state ON source_records(name_last, facility_state);

-- Canonical physicians indexes
CREATE INDEX IF NOT EXISTS idx_canonical_npi ON canonical_physicians(npi);
CREATE INDEX IF NOT EXISTS idx_canonical_state ON canonical_physicians(state);
CREATE INDEX IF NOT EXISTS idx_canonical_specialty ON canonical_physicians(specialty);

-- Mapping indexes
CREATE INDEX IF NOT EXISTS idx_mapping_canonical ON source_canonical_mapping(canonical_id);

-- Match pairs indexes
CREATE INDEX IF NOT EXISTS idx_match_pairs_source1 ON match_pairs(source_id_1);
CREATE INDEX IF NOT EXISTS idx_match_pairs_source2 ON match_pairs(source_id_2);
CREATE INDEX IF NOT EXISCREATE INDEX IF NOT EXISCREATE INDEX IF NOT EXISCREATE In);

-- Referrals indexes
CREATE INDEX IF NOT EXISTS idx_referrals_referring ON referrals(referring_physician_id);
CREATE INDEX IF NOT EXISTS idx_referrals_receiving ON referrals(receiving_physician_id);
