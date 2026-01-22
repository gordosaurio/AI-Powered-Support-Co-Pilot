DO $$ 
BEGIN
    CREATE TYPE ticket_category AS ENUM ('Técnico', 'Facturación', 'Comercial', 'Otro');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ 
BEGIN
    CREATE TYPE ticket_sentiment AS ENUM ('Positivo', 'Neutral', 'Negativo');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS public.tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    description TEXT NOT NULL,
    category ticket_category,
    sentiment ticket_sentiment,
    processed BOOLEAN DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_created ON public.tickets (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_processed ON public.tickets (processed) WHERE processed = false;

ALTER TABLE public.tickets ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public insert incoming" ON public.tickets;
DROP POLICY IF EXISTS "Public realtime select" ON public.tickets;
DROP POLICY IF EXISTS "Processor update only" ON public.tickets;

CREATE POLICY "Public insert incoming" ON public.tickets 
    FOR INSERT 
    TO anon 
    WITH CHECK (processed = false AND category IS NULL);

CREATE POLICY "Public realtime select" ON public.tickets 
    FOR SELECT 
    TO anon 
    USING (true);

CREATE POLICY "Processor update only" ON public.tickets 
    FOR UPDATE 
    TO anon 
    USING (processed = false) 
    WITH CHECK (processed = true AND category IS NOT NULL);
