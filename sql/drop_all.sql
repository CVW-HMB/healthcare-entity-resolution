-- Drop all tables in correct order (respects foreign keys)
DROP TABLE IF EXISTS influence_scores CASCADE;
DROP TABLE IF EXISTS referrals CASCADE;
DROP TABLE IF EXISTS match_pairs CASCADE;
DROP TABLE IF EXISTS source_canonical_mapping CASCADE;
DROP TABLE IF EXISTS canonical_physicians CASCADE;
DROP TABLE IF EXISTS source_records CASCADE;
