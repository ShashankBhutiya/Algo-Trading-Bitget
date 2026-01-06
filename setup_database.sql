-- ==============================================================================
-- SUPABASE SETUP SCRIPT (Idempotent / Safe to Re-run)
-- Run this in the SQL Editor of your Supabase Dashboard.
-- ==============================================================================

-- 1. Create table for Trade Logs
CREATE TABLE IF NOT EXISTS public.trade_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    size TEXT,
    price TEXT,
    type TEXT,       -- 'LIVE' or 'DRY_RUN'
    status TEXT,     -- 'FILLED', 'ERROR', 'SIMULATED'
    info TEXT        -- JSON string or error message
);

-- 2. Create table for Bot Configuration
CREATE TABLE IF NOT EXISTS public.bot_config (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    symbol TEXT DEFAULT 'ETHUSDT',
    product_type TEXT DEFAULT 'SPOT',    -- 'SPOT' or 'USDT-FUTURES'
    buy_size_usdt NUMERIC DEFAULT 5.0,
    sell_size TEXT DEFAULT 'ALL',
    leverage INTEGER DEFAULT 5,
    enable_trading BOOLEAN DEFAULT true,
    dry_run BOOLEAN DEFAULT false
);

-- 2b. Add Notification Columns (Safe Migration)
ALTER TABLE public.bot_config ADD COLUMN IF NOT EXISTS telegram_token TEXT;
ALTER TABLE public.bot_config ADD COLUMN IF NOT EXISTS telegram_chat_id TEXT;
ALTER TABLE public.bot_config ADD COLUMN IF NOT EXISTS telegram_chat_id TEXT;
ALTER TABLE public.bot_config ADD COLUMN IF NOT EXISTS enable_notifications BOOLEAN DEFAULT false;
ALTER TABLE public.bot_config ADD COLUMN IF NOT EXISTS dashboard_password TEXT;

-- 2c. Create table for Balance History (PnL Tracking)
CREATE TABLE IF NOT EXISTS public.balance_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    total_balance NUMERIC NOT NULL,
    pnl_change NUMERIC, -- Daily/Trade PnL if needed
    asset_breakdown JSONB -- Snapshot of holdings
);
ALTER TABLE public.balance_history ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow All Access to Balance History" ON public.balance_history;
CREATE POLICY "Allow All Access to Balance History" ON public.balance_history FOR ALL USING (true) WITH CHECK (true);

-- 3. Enable Row Level Security (RLS)
ALTER TABLE public.trade_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bot_config ENABLE ROW LEVEL SECURITY;

-- 4. Create Policies (Drop first to avoid "already exists" error)
DROP POLICY IF EXISTS "Allow All Access to Trade Logs" ON public.trade_logs;
CREATE POLICY "Allow All Access to Trade Logs" ON public.trade_logs FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow All Access to Bot Config" ON public.bot_config;
CREATE POLICY "Allow All Access to Bot Config" ON public.bot_config FOR ALL USING (true) WITH CHECK (true);

-- 5. Insert Default Config if Empty
INSERT INTO public.bot_config (symbol, product_type, buy_size_usdt, sell_size, leverage, enable_trading, dry_run)
SELECT 'ETHUSDT', 'SPOT', 5.0, 'ALL', 5, true, false
WHERE NOT EXISTS (SELECT 1 FROM public.bot_config);
