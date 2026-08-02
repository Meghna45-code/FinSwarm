import os
import json
import logging
import math
import numpy as np
from typing import Dict, Any, Optional

logger = logging.getLogger("finswarm.market_data")

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "reliance_market_cache.json")

def fetch_reliance_baseline_metrics() -> Dict[str, Any]:
    """
    Fetches real-time baseline metrics for Reliance Industries (RELIANCE.NS) via yfinance.
    Falls back to cached JSON if network fails or Yahoo rate-limits.
    """
    try:
        import yfinance as yf
        logger.info("Fetching market data for RELIANCE.NS via yfinance...")
        ticker = yf.Ticker("RELIANCE.NS")
        info = ticker.info
        
        # 120-Day OHLCV History
        hist = ticker.history(period="120d")
        close_prices = hist['Close'].values if not hist.empty else np.array([3000.0] * 120)
        
        # Derived Indicators
        rsi_14 = _calculate_rsi(close_prices, period=14)
        macd, macd_signal = _calculate_macd(close_prices)
        volatility = _calculate_volatility(close_prices)
        
        current_price = round(float(info.get("currentPrice", info.get("regularMarketPrice", close_prices[-1]))), 2)
        market_cap_inr = info.get("marketCap", 20000000000000) # ~₹20 Lakh Crore
        total_debt_inr = info.get("totalDebt", 3000000000000)
        beta = float(info.get("beta", 1.05))
        
        # Calculate WACC for Reliance
        wacc = _calculate_wacc(market_cap_inr, total_debt_inr, beta)
        
        # Calculate DCF Intrinsic Value
        fcf_inr = info.get("freeCashflow", 500000000000)
        shares_outstanding = info.get("sharesOutstanding", 6760000000)
        dcf_value = _calculate_dcf_intrinsic_value(fcf_inr, shares_outstanding, wacc)
        
        metrics = {
            "ticker": "RELIANCE.NS",
            "name": info.get("longName", "Reliance Industries Limited"),
            "sector": info.get("sector", "Energy"),
            "industry": info.get("industry", "Oil & Gas Refining & Marketing"),
            "currency": "INR (₹)",
            "stock_price": current_price,
            "market_cap": f"₹{round(market_cap_inr / 1e12, 2)} Trillion",
            "pe_ratio": round(float(info.get("trailingPE", 26.5)), 2),
            "beta": beta,
            "gross_margin": f"{round(float(info.get('grossMargins', 0.22) * 100), 1)}%",
            "operating_margin": f"{round(float(info.get('operatingMargins', 0.13) * 100), 1)}%",
            "free_cash_flow": f"₹{round(fcf_inr / 1e9, 1)} Billion",
            "total_debt": f"₹{round(total_debt_inr / 1e9, 1)} Billion",
            "cash_and_equivalents": f"₹{round(info.get('totalCash', 1500000000000) / 1e9, 1)} Billion",
            "short_interest": f"{round(float(info.get('shortPercentOfFloat', 0.015) * 100), 2)}%",
            "52_week_high": round(float(info.get("fiftyTwoWeekHigh", 3217.90)), 2),
            "52_week_low": round(float(info.get("fiftyTwoWeekLow", 2220.30)), 2),
            "wacc": wacc,
            "dcf_intrinsic_value": round(dcf_value, 2),
            "rsi_14": round(rsi_14, 2),
            "macd": round(macd, 2),
            "macd_signal": round(macd_signal, 2),
            "annualized_volatility": round(volatility, 4)
        }
        
        # Save to local cache
        with open(CACHE_FILE, "w") as f:
            json.dump(metrics, f, indent=2)
            
        return metrics
        
    except Exception as e:
        logger.warning(f"yfinance fetch failed ({e}). Loading fallback cache.")
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        else:
            return _get_hardcoded_fallback()


def _calculate_wacc(market_cap: float, total_debt: float, beta: float) -> float:
    """Calculates WACC for Reliance using Indian market parameters."""
    risk_free_rate = 0.070  # 10-Yr India Government Bond Yield ~7.0%
    equity_risk_premium = 0.060 # India ERP ~6.0%
    cost_of_debt = 0.075 # Borrowing rate ~7.5%
    tax_rate = 0.25 # Corporate Tax ~25%
    
    cost_of_equity = risk_free_rate + (beta * equity_risk_premium)
    total_cap = market_cap + total_debt
    w_e = market_cap / total_cap if total_cap > 0 else 0.85
    w_d = total_debt / total_cap if total_cap > 0 else 0.15
    
    wacc = (w_e * cost_of_equity) + (w_d * cost_of_debt * (1 - tax_rate))
    return round(float(wacc), 4)


def _calculate_dcf_intrinsic_value(fcf: float, shares: float, wacc: float) -> float:
    """Calculates 2-stage DCF intrinsic stock value per share."""
    if shares <= 0 or wacc <= 0:
        return 3100.00
    
    growth_rate = 0.08  # 8% FCF Growth Rate for Reliance energy/retail expansion
    terminal_growth = 0.03 # 3% Perpetual Terminal Growth
    
    pv_fcf = 0.0
    current_fcf = fcf
    for t in range(1, 6):
        current_fcf *= (1 + growth_rate)
        pv_fcf += current_fcf / ((1 + wacc) ** t)
        
    terminal_value = (current_fcf * (1 + terminal_growth)) / (wacc - terminal_growth) if (wacc > terminal_growth) else current_fcf * 10
    pv_terminal = terminal_value / ((1 + wacc) ** 5)
    
    total_pv = pv_fcf + pv_terminal
    intrinsic_value = total_pv / shares
    return float(intrinsic_value)


def _calculate_rsi(prices: np.ndarray, period: int = 14) -> float:
    if len(prices) < period + 1:
        return 50.0
    deltas = np.diff(prices)
    gains = np.maximum(deltas, 0)
    losses = np.maximum(-deltas, 0)
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _calculate_macd(prices: np.ndarray) -> tuple:
    if len(prices) < 26:
        return 0.0, 0.0
    ema_12 = np.mean(prices[-12:])
    ema_26 = np.mean(prices[-26:])
    macd = ema_12 - ema_26
    macd_signal = macd * 0.8
    return macd, macd_signal


def _calculate_volatility(prices: np.ndarray) -> float:
    if len(prices) < 2:
        return 0.18
    returns = np.diff(np.log(prices))
    return float(np.std(returns) * np.sqrt(252))


def _get_hardcoded_fallback() -> Dict[str, Any]:
    return {
        "ticker": "RELIANCE.NS",
        "name": "Reliance Industries Limited",
        "sector": "Energy",
        "industry": "Oil & Gas Refining & Marketing",
        "currency": "INR (₹)",
        "stock_price": 3050.00,
        "market_cap": "₹20.6 Trillion",
        "pe_ratio": 26.5,
        "beta": 1.05,
        "gross_margin": "22.0%",
        "operating_margin": "13.0%",
        "free_cash_flow": "₹500 Billion",
        "total_debt": "₹3.0 Trillion",
        "cash_and_equivalents": "₹1.5 Trillion",
        "short_interest": "1.5%",
        "52_week_high": 3217.90,
        "52_week_low": 2220.30,
        "wacc": 0.0885,
        "dcf_intrinsic_value": 3280.50,
        "rsi_14": 56.4,
        "macd": 12.5,
        "macd_signal": 10.2,
        "annualized_volatility": 0.185
    }
