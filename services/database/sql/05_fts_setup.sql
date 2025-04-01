ALTER TABLE operadoras
ADD COLUMN IF NOT EXISTS fts_document tsvector;

CREATE OR REPLACE FUNCTION operadoras_trigger() RETURNS trigger AS $$
begin
  new.fts_document :=
     setweight(to_tsvector('pg_catalog.portuguese', coalesce(new.razao_social,'')), 'A') ||
     setweight(to_tsvector('pg_catalog.portuguese', coalesce(new.nome_fantasia,'')), 'A') ||
     setweight(to_tsvector('pg_catalog.portuguese', coalesce(new.cnpj::text,'')), 'B') || 
     setweight(to_tsvector('pg_catalog.portuguese', coalesce(new.cidade,'')), 'C');
  return new;
end
$$ LANGUAGE plpgsql;

-- Recreate the trigger (or ensure it uses the updated function)
-- DROP TRIGGER IF EXISTS tsvectorupdate ON operadoras; -- Uncomment if needed to replace
CREATE TRIGGER tsvectorupdate
BEFORE INSERT OR UPDATE ON operadoras
FOR EACH ROW EXECUTE FUNCTION operadoras_trigger();

-- Create a GIN index on the new tsvector column for fast searching
CREATE INDEX IF NOT EXISTS idx_operadoras_fts ON operadoras USING GIN (fts_document);

UPDATE operadoras SET fts_document =
     setweight(to_tsvector('pg_catalog.portuguese', coalesce(razao_social,'')), 'A') ||
     setweight(to_tsvector('pg_catalog.portuguese', coalesce(nome_fantasia,'')), 'A') ||
     setweight(to_tsvector('pg_catalog.portuguese', coalesce(cnpj::text,'')), 'B') ||
     setweight(to_tsvector('pg_catalog.portuguese', coalesce(cidade,'')), 'C')
-- WHERE fts_document IS NULL; -- Optional: Only update if not already populated

COMMIT;