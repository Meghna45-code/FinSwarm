import pytest
from backend.app.services.valuation_model import ValuationModel
from backend.app.services.personas import CompanyProfile

def test_parse_metric_value():
    vm = ValuationModel()
    
    # Test typical billions, millions, trillions
    assert vm._parse_metric_value("$96B") == 96e9
    assert vm._parse_metric_value("$4.3B") == 4.3e9
    assert vm._parse_metric_value("$500M") == 500e6
    assert vm._parse_metric_value("$1.2T") == 1.2e12
    
    # Test formatting variations
    assert vm._parse_metric_value("  $4.3 B  ") == 4.3e9
    assert vm._parse_metric_value("4.3") == 4.3
    assert vm._parse_metric_value("") == 0.0
    assert vm._parse_metric_value(None) == 0.0
    assert vm._parse_metric_value("invalid") == 0.0

def test_parse_float():
    vm = ValuationModel()
    
    assert vm._parse_float("Interest rate offset is 2.5%", 0.0) == 2.5
    assert vm._parse_float("-1.5", 0.0) == -1.5
    assert vm._parse_float("", 1.0) == 1.0
    assert vm._parse_float(None, 5.0) == 5.0

def test_calculate_valuation_typical():
    import asyncio
    async def run_test():
        vm = ValuationModel(seed=42)
        
        company = CompanyProfile(
            ticker="TSLA",
            name="Tesla Inc",
            sector="Consumer Cyclical",
            industry="Auto Manufacturers",
            description="Electric vehicle company.",
            key_metrics={"Revenue": "$96B", "Free Cash Flow": "$4.3B", "Stock Price": "$175.00"},
            historical_news=[],
            recent_events=[]
        )
        
        agent_states = {
            "Bullish_Trader": {"sentiment": 0.8, "conviction": 0.9},
            "Bearish_Analyst": {"sentiment": -0.4, "conviction": 0.6}
        }
        
        res = await vm.calculate_valuation(company, agent_states, "Typical debate summary")
        
        assert res["current_price"] == 175.00
        assert len(res["historical_prices"]) == 13
        assert len(res["projected_prices"]) == 7
        assert res["historical_prices"][-1] == 175.00
        assert res["projected_prices"][0] == 175.00
        assert isinstance(res["final_projected_price"], float)
        assert isinstance(res["price_change_percent"], float)
        assert "intrinsic fair value" in res["valuation_summary"]
    asyncio.run(run_test())

def test_calculate_valuation_extreme_scenarios():
    import asyncio
    async def run_test():
        vm = ValuationModel(seed=123)
        
        # Extremely bearish/bullish agent consensus and macro ratesoffset
        company = CompanyProfile(
            ticker="XYZ",
            name="Extreme Corp",
            sector="Technology",
            industry="Semiconductors",
            description="High growth tech company.",
            key_metrics={"Revenue": "$1B", "Free Cash Flow": "$100M", "Stock Price": "$50.00"},
            historical_news=[],
            recent_events=[],
            environmental_variables={"Interest Rates": "5.0", "CEO Status": "CEO Resigns under Scandal"}
        )
        
        # Very bullish agent consensus
        agent_states_bull = {
            "AgentA": {"sentiment": 1.0, "conviction": 1.0},
            "AgentB": {"sentiment": 1.0, "conviction": 1.0}
        }
        
        res_bull = await vm.calculate_valuation(company, agent_states_bull, "Highly bullish consensus")
        
        # Check that prices are clamped to boundary conditions safely (fair value <= 3.0 * current_price)
        assert res_bull["current_price"] == 50.00
        assert res_bull["final_projected_price"] > 0.0
        
        # Very bearish consensus
        agent_states_bear = {
            "AgentA": {"sentiment": -1.0, "conviction": 1.0},
            "AgentB": {"sentiment": -1.0, "conviction": 1.0}
        }
        
        res_bear = await vm.calculate_valuation(company, agent_states_bear, "Highly bearish consensus")
        assert res_bear["final_projected_price"] > 0.0
    asyncio.run(run_test())

def test_calculate_valuation_empty_states():
    import asyncio
    async def run_test():
        vm = ValuationModel(seed=100)
        
        company = CompanyProfile(
            ticker="ABC",
            name="Baseline Corp",
            sector="Financial Services",
            industry="Banks",
            description="",
            key_metrics={"Stock Price": "$100.00"},
            historical_news=[],
            recent_events=[]
        )
        
        # Empty agent states dictionary to test fallback robustness
        res = await vm.calculate_valuation(company, {}, "")
        assert res["current_price"] == 100.00
        assert len(res["historical_prices"]) == 13
        assert len(res["projected_prices"]) == 7
    asyncio.run(run_test())
