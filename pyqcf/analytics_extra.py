from dateutil import relativedelta
from typing import Any
import pandas as pd

from qcf_valuation import qcf_wrappers as qcw

from ..models import operations_2 as op


def aux_make_leg_1(raw_leg: dict[str, Any]):
    start_date = qcw.Fecha(fecha=raw_leg["start_date"])
    end_date = qcw.Fecha(fecha=raw_leg["end_date"])
    delta = relativedelta.relativedelta(end_date.as_py_date(), start_date.as_py_date())
    maturity = qcw.Tenor(delta.years, delta.months, delta.days)
    if raw_leg["type_of_amortization"] == 'BULLET':
        notional_or_custom = op.InitialNotional(
            initial_notional=raw_leg["initial_notional"]
        )
    else:
        notional_or_custom = op.CustomNotionalAmort(
            custom_notional_amort=raw_leg["custom_notional_amort"]
        )

    return start_date, end_date, maturity, notional_or_custom


def aux_make_leg_2(raw_leg: dict[str, Any], which: str):
    agnos = raw_leg[which]["agnos"]
    meses = raw_leg[which]["meses"]
    dias = raw_leg[which]["dias"]

    return agnos, dias, meses


def aux_make_mccy(raw_leg: dict[str, Any]) -> op.MultiCurrencyModel:
    return op.MultiCurrencyModel(
        settlement_currency=qcw.Currency(raw_leg["settlement_currency"]),
        fx_rate_index_name=raw_leg["fx_rate_index_name"],
        fx_fixing_lag=raw_leg["fx_fixing_lag"]
    )


def make_fixed_rate_leg_generator(
        raw_leg: dict[str, Any],
) -> op.FixedRateLegGenerator:
    start_date, end_date, maturity, notional_or_custom = aux_make_leg_1(raw_leg)

    agnos, meses, dias = aux_make_leg_2(raw_leg, "periodicity")

    return op.FixedRateLegGenerator(
        rp=qcw.AP.A if raw_leg["rp"] == "A" else qcw.AP.P,
        start_date=start_date,
        end_date=end_date,
        maturity=maturity,
        bus_adj_rule=qcw.BusAdjRules(raw_leg["bus_adj_rule"]),
        periodicity=qcw.Tenor(agnos=agnos, meses=meses, dias=dias),
        stub_period=qcw.StubPeriods(raw_leg["stub_period"]),
        settlement_calendar=raw_leg["settlement_calendar"],
        settlement_lag=raw_leg["settlement_lag"],
        type_of_amortization=raw_leg["type_of_amortization"],
        notional_or_custom=notional_or_custom,
        coupon_rate_value=raw_leg["coupon_rate_value"],
        coupon_rate_type=raw_leg["coupon_rate_type"],
        notional_currency=qcw.Currency(raw_leg["notional_currency"]),
        amort_is_cashflow=raw_leg["amort_is_cashflow"],
        is_bond=False,
    )


def make_fixed_rate_leg(
        raw_leg: dict[str, Any],
) -> op.FixedRateLegModel:
    """
    Construye un objeto de tipo op.FixedRateLegModel.

    Parameters
    ----------
    raw_leg: dict[str, Any]
        Dict con todos los datos necesarios.

    Returns
    -------
    op.FixedRateLegModel
    """

    return op.FixedRateLegModel(
        type_of_leg=op.TypeOfLeg.FIXED_RATE,
        leg_number=raw_leg["leg_number"],
        leg_generator=make_fixed_rate_leg_generator(raw_leg)
    )


def make_fixed_rate_mccy_leg(
        raw_leg: dict[str, Any],
) -> op.FixedRateMultiCurrencyLegModel:
    """
    Construye un objeto de tipo op.FixedRateLegModel a partir de los datos que se obtienen de Analytics.

    Parameters
    ----------
    raw_leg: dict
        Dict con todos los datos necesarios.

    Returns
    -------
    op.FixedRateMultiCurrencyLegModel
    """
    return op.FixedRateMultiCurrencyLegModel(
        type_of_leg=op.TypeOfLeg.FIXED_RATE_MCCY,
        leg_number=raw_leg["leg_number"],
        leg_generator=make_fixed_rate_leg_generator(raw_leg),
        multi_currency=aux_make_mccy(raw_leg),
    )


def make_ibor_leg_generator(
        raw_leg: dict[str, Any],
) -> op.IborLegGenerator:
    start_date, end_date, maturity, notional_or_custom = aux_make_leg_1(raw_leg)

    sett_agnos, sett_meses, sett_dias = aux_make_leg_2(raw_leg, "settlement_periodicity")
    fix_agnos, fix_meses, fix_dias = aux_make_leg_2(raw_leg, "fixing_periodicity")

    return op.IborLegGenerator(
        rp=qcw.AP.A if raw_leg["rp"] == "A" else qcw.AP.P,
        start_date=start_date,
        end_date=end_date,
        maturity=maturity,
        bus_adj_rule=qcw.BusAdjRules(raw_leg["bus_adj_rule"]),
        settlement_periodicity=qcw.Tenor(agnos=sett_agnos, meses=sett_meses, dias=sett_dias),
        settlement_stub_period=qcw.StubPeriods(raw_leg["settlement_stub_period"]),
        settlement_calendar=raw_leg["settlement_calendar"],
        settlement_lag=raw_leg["settlement_lag"],
        type_of_amortization=raw_leg["type_of_amortization"],
        fixing_periodicity=qcw.Tenor(agnos=fix_agnos, meses=fix_meses, dias=fix_dias),
        fixing_stub_period=raw_leg["fixing_stub_period"],
        fixing_calendar=raw_leg["fixing_calendar"],
        fixing_lag=raw_leg["fixing_lag"],
        interest_rate_index_name=raw_leg["interest_rate_index_name"],
        notional_or_custom=notional_or_custom,
        amort_is_cashflow=raw_leg["amort_is_cashflow"],
        notional_currency=qcw.Currency(raw_leg["notional_currency"]),
        spread=raw_leg["spread"],
        gearing=1.0,
    )


def make_ibor_leg(
        raw_leg: dict[str, Any],
) -> op.IborLegModel:
    """
    Construye un objeto de tipo op.IborLegModel a partir de los datos que se obtienen de Analytics.

    Parameters
    ----------
    raw_leg: dict[str, Any]
        Dict con todos los datos necesarios.

    Returns
    -------
    op.IborRateLegModel
    """
    return op.IborLegModel(
        type_of_leg=op.TypeOfLeg.IBOR,
        leg_number=raw_leg["leg_number"],
        leg_generator=make_ibor_leg_generator(raw_leg)
    )


def make_ibor_mccy_leg(
        raw_leg: dict[str, Any]
) -> op.IborMultiCurrencyLegModel:
    """
    Construye un objeto de tipo op.IborLegMultiCurrencyModel a partir de los datos que se obtienen de Analytics.

    Parameters
    ----------
    raw_leg: dict[str, Any]
        Dict con todos los datos necesarios.

    Returns
    -------
    op.IborLegMultiCurrencyModel
    """
    return op.IborMultiCurrencyLegModel(
        type_of_leg=op.TypeOfLeg.IBOR_MCCY,
        leg_number=raw_leg["leg_number"],
        leg_generator=make_ibor_leg_generator(raw_leg),
        multi_currency=aux_make_mccy(raw_leg),
    )


def make_overnight_index_leg_generator(
        raw_leg: dict[str, Any]
) -> op.OvernightIndexLegGenerator:
    start_date, end_date, maturity, notional_or_custom = aux_make_leg_1(raw_leg)

    agnos, meses, dias = aux_make_leg_2(raw_leg, "settlement_periodicity")
    return op.OvernightIndexLegGenerator(
        rp=qcw.AP.A if raw_leg["rp"] == "A" else qcw.AP.P,
        start_date=start_date,
        end_date=end_date,
        maturity=maturity,
        bus_adj_rule=qcw.BusAdjRules(raw_leg["bus_adj_rule"]),
        fix_adj_rule=qcw.BusAdjRules(raw_leg["fix_adj_rule"]),
        settlement_periodicity=qcw.Tenor(agnos=agnos, meses=meses, dias=dias),
        settlement_stub_period=qcw.StubPeriods(raw_leg["settlement_stub_period"]),
        settlement_calendar=raw_leg["settlement_calendar"],
        settlement_lag=raw_leg["settlement_lag"],
        fixing_calendar=raw_leg["fixing_calendar"],
        type_of_amortization=raw_leg["type_of_amortization"],
        overnight_index_name=raw_leg["overnight_index_name"],
        interest_rate=qcw.TypeOfRate(raw_leg["interest_rate"]),
        eq_rate_decimal_places=raw_leg["eq_rate_decimal_places"],
        notional_or_custom=notional_or_custom,
        amort_is_cashflow=raw_leg["amort_is_cashflow"],
        notional_currency=qcw.Currency(raw_leg["notional_currency"]),
        spread=raw_leg["spread"],
        gearing=1.0,
    )


def make_overnight_index_leg(
        raw_leg: dict[str, Any]
) -> op.OvernightIndexLegModel:
    """
    Construye un objeto de tipo op.OvernightIndexLegModel a partir de los datos que se obtienen de Analytics.

    Parameters
    ----------
    raw_leg: dict[str, Any]
        Dict con todos los datos necesarios.

    Returns
    -------
    op.OvernightIndexLegModel
    """
    return op.OvernightIndexLegModel(
        type_of_leg=op.TypeOfLeg.OVERNIGHT_INDEX,
        leg_number=raw_leg["leg_number"],
        leg_generator=make_overnight_index_leg_generator(raw_leg),
    )


def make_icpclf_leg_generator(
        raw_leg: dict[str, Any]
) -> op.IcpClfLegGenerator:
    start_date, end_date, maturity, notional_or_custom = aux_make_leg_1(raw_leg)

    agnos, meses, dias = aux_make_leg_2(raw_leg, "settlement_periodicity")
    return op.IcpClfLegGenerator(
        rp=qcw.AP.A if raw_leg["rp"] == "A" else qcw.AP.P,
        start_date=start_date,
        end_date=end_date,
        maturity=maturity,
        bus_adj_rule=qcw.BusAdjRules(raw_leg["bus_adj_rule"]),
        settlement_periodicity=qcw.Tenor(agnos=agnos, meses=meses, dias=dias),
        settlement_stub_period=qcw.StubPeriods(raw_leg["settlement_stub_period"]),
        settlement_calendar=raw_leg["settlement_calendar"],
        settlement_lag=raw_leg["settlement_lag"],
        type_of_amortization=raw_leg["type_of_amortization"],
        overnight_index_name=raw_leg["overnight_index_name"],
        notional_or_custom=notional_or_custom,
        amort_is_cashflow=raw_leg["amort_is_cashflow"],
        spread=raw_leg["spread"],
        gearing=1.0,
    )


def make_icpclf_leg(
        raw_leg: dict[str, Any]
) -> op.IcpClfLegModel:
    """
    Construye un objeto de tipo op.IcpClfLegModel a partir de los datos que se obtienen de Analytics.

    Parameters
    ----------
    raw_leg: dict[str, Any]
        Dict con todos los datos necesarios.

    Returns
    -------
    op.IcpClfLegModel
    """
    return op.IcpClfLegModel(
        type_of_leg=op.TypeOfLeg.ICP_CLF,
        leg_number=raw_leg["leg_number"],
        leg_generator=make_icpclf_leg_generator(raw_leg),
    )


def make_overnight_index_mccy_leg(
        raw_leg: dict[str, Any],
) -> op.OvernightIndexMultiCurrencyLegModel:
    """
    Construye un objeto de tipo op.OvernightIndexLegMultiCurrencyModel a partir de los datos que se obtienen de Front Desk.

    Parameters
    ----------
    raw_leg: dict[str, Any]
        Dict con todos los datos necesarios.

    Returns
    -------
    op.OvernightIndexLegMultiCurrencyModel
    """
    return op.OvernightIndexMultiCurrencyLegModel(
        type_of_leg=op.TypeOfLeg.OVERNIGHT_INDEX_MCCY,
        leg_number=raw_leg["leg_number"],
        leg_generator=make_overnight_index_leg_generator(raw_leg),
        multi_currency=aux_make_mccy(raw_leg),
    )


def make_compounded_overnight_rate_leg_generator(
            raw_leg: dict[str, Any],
    ) -> op.CompoundedOvernightRateLegGenerator:
    start_date, end_date, maturity, notional_or_custom = aux_make_leg_1(raw_leg)

    agnos, meses, dias = aux_make_leg_2(raw_leg, "settlement_periodicity")
    return op.CompoundedOvernightRateLegGenerator(
        rp=qcw.AP.A if raw_leg["rp"] == "A" else qcw.AP.P,
        start_date=start_date,
        end_date=end_date,
        maturity=maturity,
        bus_adj_rule=qcw.BusAdjRules(raw_leg["bus_adj_rule"]),
        settlement_periodicity=qcw.Tenor(agnos=agnos, meses=meses, dias=dias),
        settlement_stub_period=qcw.StubPeriods(raw_leg["settlement_stub_period"]),
        settlement_calendar=raw_leg["settlement_calendar"],
        settlement_lag=raw_leg["settlement_lag"],
        type_of_amortization=raw_leg["type_of_amortization"],
        fixing_calendar=raw_leg["fixing_calendar"],
        overnight_rate_name=raw_leg["overnight_rate_name"],
        notional_or_custom=notional_or_custom,
        amort_is_cashflow=raw_leg["amort_is_cashflow"],
        notional_currency=qcw.Currency(raw_leg["notional_currency"]),
        interest_rate_type=raw_leg["interest_rate_type"],
        spread=raw_leg["spread"],
        gearing=1.0,
        eq_rate_decimal_places=8,  # raw_leg["eq_rate_decimal_places
        lookback=raw_leg["lookback"],
        lockout=0,
    )


def make_compounded_overnight_rate_leg(
        raw_leg: dict[str, Any],
) -> op.CompoundedOvernightRateLegModel:
    """
    Construye un objeto de tipo op.CompoundedOvernightRateModel a partir de los datos que se obtienen de Analytics.

    Parameters
    ----------
    raw_leg: dict[str, Any]
        Dict con todos los datos necesarios.

    Returns
    -------
    op.CompoundedOvernightRateModel
    """
    return op.CompoundedOvernightRateLegModel(
        type_of_leg=op.TypeOfLeg.COMPOUNDED_OVERNIGHT_RATE,
        leg_number=raw_leg["leg_number"],
        leg_generator=make_compounded_overnight_rate_leg_generator(raw_leg),
    )


def make_compounded_overnight_rate_mccy_leg(
        raw_leg: dict[str, Any],
) -> op.CompoundedOvernightRateMultiCurrencyLegModel:
    """
    Construye un objeto de tipo op.CompoundedOvernightRateModel a partir de los datos que se obtienen de Analytics.

    Parameters
    ----------
    raw_leg: dict[str, Any]
        Dict con todos los datos necesarios.

    Returns
    -------
    op.CompoundedOvernightRateModel
    """
    return op.CompoundedOvernightRateMultiCurrencyLegModel(
        type_of_leg=op.TypeOfLeg.COMPOUNDED_OVERNIGHT_RATE_MCCY,
        leg_number=raw_leg["leg_number"],
        leg_generator=make_compounded_overnight_rate_leg_generator(raw_leg),
        multi_currency=aux_make_mccy(raw_leg),
    )


def make_leg(
        raw_leg: dict[str, Any],
) -> op.OperationLeg:
    """
    Retorna un modelo de pata (models/operations) a partir de la data que viene de Analytics y su tipo de pata.

    Parameters
    ----------
    raw_leg: dict[str, Any]
        Dict con todos los datos necesarios.

    Returns
    -------
        op.OperationLeg

    """
    type_of_leg = op.TypeOfLeg(raw_leg["type_of_leg"])

    match type_of_leg:
        case op.TypeOfLeg.FIXED_RATE:
            return make_fixed_rate_leg(raw_leg)

        case op.TypeOfLeg.FIXED_RATE_MCCY:
            return make_fixed_rate_mccy_leg(raw_leg)

        case op.TypeOfLeg.IBOR:
            return make_ibor_leg(raw_leg)

        case op.TypeOfLeg.IBOR_MCCY:
            return make_ibor_mccy_leg(raw_leg)

        case op.TypeOfLeg.OVERNIGHT_INDEX:
            return make_overnight_index_leg(raw_leg)

        case op.TypeOfLeg.ICP_CLF:
            return make_icpclf_leg(raw_leg)

        case op.TypeOfLeg.OVERNIGHT_INDEX_MCCY:
            return make_overnight_index_mccy_leg(raw_leg)

        case op.TypeOfLeg.COMPOUNDED_OVERNIGHT_RATE:
            return make_compounded_overnight_rate_leg(raw_leg)

        case op.TypeOfLeg.COMPOUNDED_OVERNIGHT_RATE_MCCY:
            return make_compounded_overnight_rate_mccy_leg(raw_leg)
