-- Full-text search across contacts (name/company/email), so the Pipeline/Outreach
-- pages can filter by a single search box instead of scrolling. A generated column
-- keeps the tsvector in sync automatically — no trigger to maintain.
ALTER TABLE recruiters ADD COLUMN IF NOT EXISTS search_vector tsvector
    GENERATED ALWAYS AS (
        setweight(to_tsvector('simple', coalesce(name, '')), 'A') ||
        setweight(to_tsvector('simple', coalesce(company, '')), 'A') ||
        setweight(to_tsvector('simple', coalesce(email, '')), 'B')
    ) STORED;

CREATE INDEX IF NOT EXISTS idx_recruiters_search ON recruiters USING GIN (search_vector);
