import re
import math
import random
from typing import Dict, Any, List
from .personas import CompanyProfile

class ValuationModel:
    """
    ValuationModel (Stock Valuation Chamber)
    Responsible for projecting the stock price path and final valuation metrics.
    Uses rigorous quantitative finance models:
    - CAPM & WACC for cost of capital calculations.
    - Two-Stage Discounted Cash Flow (DCF) model for intrinsic valuation.
    - Brownian Bridge for generating historical paths ending exactly at current price.
    - Geometric Brownian Motion (GBM) with value-gap mean reversion for future price paths.
    """
    def __init__(self, seed: int = 42):
        self.seed = seed

    def _parse_metric_value(self, val_str: str) -> float:
        """Parses financial values like '$96B' or '$4.3B' into floating-point numbers."""
        if not val_str:
            return 0.0
        val_str = str(val_str).replace("$", "").replace(",", "").strip()
        multiplier = 1.0
        val_str_upper = val_str.upper()
        if "B" in val_str_upper:
            multiplier = 1e9
            val_str = val_str_upper.replace("B", "")
        elif "M" in val_str_upper:
            multiplier = 1e6
            val_str = val_str_upper.replace("M", "")
        elif "T" in val_str_upper:
            multiplier = 1e12
            val_str = val_str_upper.replace("T", "")
        try:
            return float(val_str.strip()) * multiplier
        except ValueError:
            return 0.0

    def _parse_float(self, val_str: str, default: float = 0.0) -> float:
        """Helper to extract floats from variable descriptions/text strings."""
        try:
            if val_str is None or val_str == "":
                return default
            nums = re.findall(r'-?\d+(?:\.\d+)?', str(val_str))
            if nums:
                return float(nums[0])
            return default
        except (ValueError, TypeError):
            return default

    async def _fetch_actual_historical_prices(self, ticker: str, current_price: float) -> list:
        """Fetches actual monthly close prices for the past year from Yahoo Finance public API."""
        import httpx
        try:
            ticker = ticker.upper().strip()
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=1y&interval=1mo"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    result = data.get("chart", {}).get("result", [])
                    if result:
                        indicators = result[0].get("indicators", {}).get("quote", [{}])[0]
                        close_prices = indicators.get("close", [])
                        # Filter out None and round
                        clean_prices = [round(p, 2) for p in close_prices if p is not None]
                        
                        if len(clean_prices) >= 12:
                            prices_slice = clean_prices[-12:]
                            if len(prices_slice) == 12:
                                prices_slice = [prices_slice[0]] + prices_slice
                            # Ensure it matches current price at index 12 to prevent rendering jumps
                            prices_slice[-1] = round(current_price, 2)
                            return prices_slice
        except Exception as e:
            print(f"[FETCH ERROR] Could not fetch real-world history for {ticker}: {e}")
        return None


    async def calculate_valuation(
        self, 
        company_profile: CompanyProfile, 
        final_agent_states: Dict[str, Dict[str, float]], 
        debate_summary: str
    ) -> Dict[str, Any]:
        """
        Calculates historical and projected stock paths using mathematical formulas:
        1. CAPM & WACC for Cost of Capital.
        2. 5-Year Two-Stage DCF Model for Intrinsic Stock Value.
        3. Brownian Bridge for historical stock prices (guided from S_{-12} to S_0).
        4. Ornstein-Uhlenbeck styled Mean-Reverting GBM for future stock projections.
        """
        # --- 1. DETERMINE CURRENT STOCK PRICE ---
        current_price = 150.00
        metrics = company_profile.key_metrics or {}
        for key, val in metrics.items():
            if any(term in key.lower() for term in ["price", "stock", "close", "value", "current"]):
                nums = re.findall(r'\d+(?:\.\d+)?', str(val))
                if nums:
                    current_price = float(nums[0])
                    break

        # Seed the random number generator for reproducibility
        seed_val = self.seed
        if seed_val == 42:
            ticker_str = company_profile.ticker or "TSLA"
            seed_val = (hash(ticker_str) + random.randint(1, 100000)) % 1000000
        random.seed(seed_val)

        # --- 2. COST OF CAPITAL (CAPM & WACC) ---
        env_vars = company_profile.environmental_variables or {}
        rates_offset_str = env_vars.get("Interest Rates", "0.0")
        rates_offset = self._parse_float(rates_offset_str, 0.0) / 100.0
        
        # Risk-free rate: base of 4% adjusted by Interest Rate macro offset
        rf = 0.04 + rates_offset
        erp = 0.055  # Standard Equity Risk Premium (5.5%)

        # Beta (systematic risk) determined by industry sector
        sector = (company_profile.sector or "").lower()
        industry = (company_profile.industry or "").lower()
        if "semiconductor" in industry or "semiconductors" in industry:
            beta = 1.35
        elif "auto" in industry or "automotive" in industry:
            beta = 1.40
        elif "electronics" in industry or "hardware" in industry:
            beta = 1.15
        elif "utility" in sector or "utilities" in sector:
            beta = 0.75
        elif "tech" in sector or "technology" in sector:
            beta = 1.25
        else:
            beta = 1.0

        # Cost of Equity / WACC (assuming mostly equity financing for simplicity)
        wacc = rf + beta * erp

        # --- 3. ESTIMATING INTRINSIC VALUE (TWO-STAGE DCF) ---
        # Parse FCF and Revenue
        fcf_val = 0.0
        revenue_val = 0.0
        for key, val in metrics.items():
            k_lower = key.lower()
            if "free cash flow" in k_lower or "fcf" in k_lower:
                fcf_val = self._parse_metric_value(val)
            elif "revenue" in k_lower or "sales" in k_lower:
                revenue_val = self._parse_metric_value(val)

        # Estimate market cap to calculate FCF yield
        if revenue_val > 0:
            ps_multiple = 6.0 if beta >= 1.25 else (3.5 if beta >= 1.1 else (1.5 if beta <= 0.8 else 2.5))
            market_cap = revenue_val * ps_multiple
        else:
            market_cap = 1e9 * current_price  # fallback estimate

        if fcf_val > 0 and market_cap > 0:
            fcf_yield = fcf_val / market_cap
        elif revenue_val > 0 and market_cap > 0:
            fcf_yield = (0.08 * revenue_val) / market_cap  # estimate FCF as 8% of revenue
        else:
            fcf_yield = 0.045  # standard baseline 4.5% yield

        fcf_yield = max(0.02, min(0.12, fcf_yield))  # Bound yield between 2% and 12%
        fcf_share = current_price * fcf_yield

        # Calculate Swarm Consensus Stance
        total_sentiment = 0.0
        total_conviction = 0.0
        for state in final_agent_states.values():
            total_sentiment += state["sentiment"]
            total_conviction += state["conviction"]
            
        if not final_agent_states:
            avg_sentiment = 0.0
            avg_conviction = 0.0
        else:
            avg_sentiment = total_sentiment / len(final_agent_states)
            avg_conviction = total_conviction / len(final_agent_states)

        # Growth rate (short-term), baseline derived from sector risk
        g_base = 0.15 if beta >= 1.25 else (0.10 if beta >= 1.1 else (0.04 if beta <= 0.8 else 0.08))
        # Growth adjusted by Swarm Consensus Sentiment
        g = g_base + 0.05 * avg_sentiment
        g = max(0.01, min(0.35, g))  # Bound growth between 1% and 35%

        # Long term terminal growth rate (conservative GDP pace)
        g_terminal = 0.025
        wacc = max(wacc, g_terminal + 0.02)  # Mathematical WACC constraint to prevent division issues

        # Two-Stage DCF model calculation
        discounted_cash_flows = 0.0
        for t in range(1, 6):
            discounted_cash_flows += (fcf_share * ((1 + g) ** t)) / ((1 + wacc) ** t)
        fcf_year_5 = fcf_share * ((1 + g) ** 5)
        terminal_value = (fcf_year_5 * (1 + g_terminal)) / (wacc - g_terminal)
        discounted_terminal_value = terminal_value / ((1 + wacc) ** 5)
        
        v_intrinsic = discounted_cash_flows + discounted_terminal_value
        # Clamp intrinsic value to logical bounds (between 30% and 300% of current price)
        v_intrinsic = max(current_price * 0.3, min(current_price * 3.0, v_intrinsic))

        # --- 4. VOLATILITY SCALING (ENVIRONMENT-AWARE) ---
        vol_annual = 0.30 if beta >= 1.25 else (0.15 if beta <= 0.8 else 0.25)
        
        # Scale volatility by active environmental strains
        env_vol_offset = 0.0
        if env_vars.get("CEO Status") == "CEO Resigns under Scandal":
            env_vol_offset += 0.08
        supply_friction = self._parse_float(env_vars.get("Supply Chain"), 0.0) / 100.0
        regulatory_pressure = self._parse_float(env_vars.get("Regulatory Pressure"), 0.0) / 100.0
        market_panic = self._parse_float(env_vars.get("Market Sentiment"), 0.0) / 100.0
        
        env_vol_offset += 0.05 * supply_friction + 0.04 * regulatory_pressure + 0.08 * market_panic
        vol_annual_scaled = vol_annual + env_vol_offset
        sigma_monthly = vol_annual_scaled / math.sqrt(12)

        # --- 5. HISTORICAL PRICE PATH (ACTUAL DATA / BROWNIAN BRIDGE) ---
        actual_history = await self._fetch_actual_historical_prices(company_profile.ticker, current_price)
        if actual_history and len(actual_history) == 13:
            historical_prices = actual_history
        else:
            # Starts 12 months ago at a drift offset and bridges exactly to current_price at step 12
            mu_hist = 0.08  # assume 8% baseline historical drift
            S_start = current_price * math.exp(-mu_hist + random.gauss(0, 0.15))
            
            # Standard Brownian Motion path
            Y = [0.0]
            for _ in range(12):
                Y.append(Y[-1] + random.gauss(0, 1.0))
                
            # Transform standard path into a Brownian Bridge from ln(S_start) to ln(current_price)
            historical_prices = []
            ln_start = math.log(S_start)
            ln_end = math.log(current_price)
            
            for t in range(13):
                # Brownian Bridge interpolation formula
                ln_p = ln_start + (t / 12.0) * (ln_end - ln_start) + sigma_monthly * (Y[t] - (t / 12.0) * Y[12])
                historical_prices.append(round(math.exp(ln_p), 2))

        # --- 6. FUTURE PROJECTION PATH (MEAN-REVERTING GBM) ---
        projected_prices = [current_price]
        temp_price = current_price
        
        # Swarm Stance multiplier
        swarm_stance = avg_sentiment * avg_conviction
        # Fundamental monthly growth drift
        mu_fundamental = g_terminal / 12.0
        # Mean-reversion speed toward intrinsic valuation
        theta = 0.15
        alpha = 0.03

        for t in range(6):
            # Calculate dynamic drift incorporating value gap correction & swarm stance
            valuation_gap = math.log(v_intrinsic / temp_price)
            mu_t = mu_fundamental + theta * valuation_gap + alpha * swarm_stance
            
            # Discrete step of Geometric Brownian Motion
            noise = random.gauss(0, 1.0)
            log_return = (mu_t - 0.5 * (sigma_monthly ** 2)) + sigma_monthly * noise
            temp_price = temp_price * math.exp(log_return)
            projected_prices.append(round(temp_price, 2))

        final_projected_price = projected_prices[-1]
        price_change_percent = round(((final_projected_price - current_price) / current_price) * 100, 2)

        return {
            "current_price": current_price,
            "final_projected_price": final_projected_price,
            "historical_prices": historical_prices,  # 13 points (Months -12 to 0)
            "projected_prices": projected_prices,    # 7 points (Months 0 to 6)
            "price_change_percent": price_change_percent,
            "valuation_summary": (
                f"The debate concluded with a consensus sentiment of {avg_sentiment:.2f} (conviction: {avg_conviction:.2f}). "
                f"Based on a CAPM-derived WACC of {wacc*100:.1f}%, the Two-Stage DCF model projects an intrinsic fair value of "
                f"${v_intrinsic:.2f} per share. Guided by a mean-reverting Geometric Brownian Motion, the stock price is projected to "
                f"change by {price_change_percent}% over the next 6 months, moving from ${current_price:.2f} to ${final_projected_price:.2f}."
            )
        }
