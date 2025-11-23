-- Initialize TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create indexes for time-series queries
-- (Will be created after tables are created by SQLAlchemy)

-- Create hypertables for time-series data
-- This will be executed after table creation
DO $$
BEGIN
    -- Check if raw_data table exists and convert to hypertable
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'raw_data') THEN
        PERFORM create_hypertable('raw_data', 'timestamp', if_not_exists => TRUE);
    END IF;

    -- Check if metrics table exists and convert to hypertable
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'metrics') THEN
        PERFORM create_hypertable('metrics', 'timestamp', if_not_exists => TRUE);
    END IF;
END$$;

-- Create additional indexes for performance
CREATE INDEX IF NOT EXISTS idx_raw_data_timestamp ON raw_data (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_raw_data_data_type ON raw_data (data_type);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_type ON metrics (metric_type);
CREATE INDEX IF NOT EXISTS idx_insights_timestamp ON insights (timestamp DESC);

-- Enable row-level security (optional, for multi-tenant isolation)
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE data_sources ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE raw_data ENABLE ROW LEVEL SECURITY;
