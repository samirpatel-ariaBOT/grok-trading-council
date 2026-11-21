from decimal import Decimal
from services.core import decimal_value as n, ds


def metrics(net_episodes, equity_curve):
    """Caller must supply after-cost completed episodes and cashflow-adjusted equity."""
    episodes = [n(x) for x in net_episodes]
    equity = [n(x, positive=True) for x in equity_curve]
    if not episodes or not equity:
        return {
            "status": "NOT_MEASURED",
            "profit_factor": None,
            "expectancy": None,
            "maximum_drawdown_fraction": None,
            "activation": False,
        }
    gains = sum((x for x in episodes if x > 0), Decimal(0))
    losses = -sum((x for x in episodes if x < 0), Decimal(0))
    peak = equity[0]
    dd = Decimal(0)
    for point in equity:
        peak = max(peak, point)
        dd = max(dd, (peak - point) / peak)
    return {
        "status": "DESCRIPTIVE_ONLY",
        "episodes": len(episodes),
        "expectancy": ds(sum(episodes, Decimal(0)) / len(episodes)),
        "profit_factor": ds(gains / losses) if losses else None,
        "profit_factor_note": "UNDEFINED_NO_LOSSES"
        if not losses
        else "after-cost gains / absolute after-cost losses",
        "maximum_drawdown_fraction": ds(dd),
        "activation": False,
        "inference": "No statistical or profitability conclusion from these summaries.",
    }
