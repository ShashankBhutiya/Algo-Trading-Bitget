        -- Create the config table
        CREATE TABLE public.bot_config (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            symbol TEXT NOT NULL DEFAULT 'ETHUSDT',
            product_type TEXT NOT NULL DEFAULT 'SPOT',
            buy_size_usdt NUMERIC NOT NULL DEFAULT 5.0,
            sell_size TEXT NOT NULL DEFAULT 'ALL',
            leverage INTEGER NOT NULL DEFAULT 5,
            enable_trading BOOLEAN NOT NULL DEFAULT true,
            dry_run BOOLEAN NOT NULL DEFAULT false,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
        );

        -- Insert the default row (We only need one row for a single bot)
        INSERT INTO public.bot_config (symbol, buy_size_usdt, sell_size, leverage, enable_trading, dry_run)
        VALUES ('ETHUSDT', 5.0, 'ALL', 5, true, false);

        -- Enable Row Level Security
        ALTER TABLE public.bot_config ENABLE ROW LEVEL SECURITY;

        -- Create policy to allow public read/write (FOR NOW - simpler for MVP)
        -- In production, restrict WRITE to authenticated users only.
        CREATE POLICY "Allow Public Access" ON public.bot_config
        FOR ALL USING (true) WITH CHECK (true);
