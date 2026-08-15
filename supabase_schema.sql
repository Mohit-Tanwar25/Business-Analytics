-- =========================================================
-- Supabase / PostgreSQL Database Schema for Business Analysis System
-- =========================================================
-- Run this script in the Supabase SQL Editor (SQL Editor -> New Query -> Run)

-- 1. Create datasets table to store metadata for each uploaded CSV
CREATE TABLE IF NOT EXISTS public.datasets (
    id VARCHAR(12) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    row_count INTEGER DEFAULT 0,
    column_count INTEGER DEFAULT 0,
    content_hash VARCHAR(32),
    is_active BOOLEAN DEFAULT FALSE
);

-- Index for searching and sorting datasets
CREATE INDEX IF NOT EXISTS idx_datasets_name ON public.datasets(name);
CREATE INDEX IF NOT EXISTS idx_datasets_uploaded_at ON public.datasets(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_datasets_is_active ON public.datasets(is_active);

-- 2. Create sales_records table to store parsed CSV rows
CREATE TABLE IF NOT EXISTS public.sales_records (
    record_id BIGSERIAL PRIMARY KEY,
    dataset_id VARCHAR(12) NOT NULL,
    order_id VARCHAR(100),
    order_date DATE,
    ship_date DATE,
    category VARCHAR(100),
    product_name VARCHAR(255),
    region VARCHAR(100),
    sales DOUBLE PRECISION,
    profit DOUBLE PRECISION,
    quantity INTEGER,
    discount DOUBLE PRECISION,
    shipping_cost DOUBLE PRECISION,
    CONSTRAINT fk_sales_dataset
        FOREIGN KEY (dataset_id)
        REFERENCES public.datasets(id)
        ON DELETE CASCADE
);

-- Index for filtering rows by dataset
CREATE INDEX IF NOT EXISTS idx_sales_records_dataset_id ON public.sales_records(dataset_id);
CREATE INDEX IF NOT EXISTS idx_sales_records_order_date ON public.sales_records(order_date);
CREATE INDEX IF NOT EXISTS idx_sales_records_category ON public.sales_records(category);
CREATE INDEX IF NOT EXISTS idx_sales_records_region ON public.sales_records(region);

-- 3. Row Level Security (RLS) - Enable RLS with open access policies
ALTER TABLE public.datasets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sales_records ENABLE ROW LEVEL SECURITY;

-- Allow public/authenticated read and write access for dashboard operations
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'datasets' AND policyname = 'Allow all access to datasets'
    ) THEN
        CREATE POLICY "Allow all access to datasets" ON public.datasets
        FOR ALL USING (true) WITH CHECK (true);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'sales_records' AND policyname = 'Allow all access to sales_records'
    ) THEN
        CREATE POLICY "Allow all access to sales_records" ON public.sales_records
        FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;
