# Funciones para hacer el fixing de tasa de interés y tipo de cambio de un qcf.Cashflow de cualquier tipo

import qcfinancial as qcf
from qcf_valuation import core as qcv, qcf_wrappers as qcw

index_alias = {
        'INDICE SOFR': 'SOFRINDX',
    }


def fix_overnight_index_cashflow(cashflow: qcf.OvernightIndexCashflow, market_data: qcv.MarketData):
    """
    Realiza el fixing de los índices overnight a fecha inicial y final de un OvernightIndexCashflow.

    Args:
        cashflow (OvernightIndexCashflow)
        market_data (qcv.MarketData): Objeto con la data de mercado necesaria para hacer el fixing

    Returns:
        None: El fixing se realiza inplace.
    """
    fecha1 = qcw.Fecha(fecha=cashflow.get_start_date().iso_code()).as_py_date()
    fecha2 = qcw.Fecha(fecha=cashflow.get_end_date().iso_code()).as_py_date()
    index_name = index_alias.get(cashflow.get_index_code(), cashflow.get_index_code())
    index1 = market_data.get_index_value(fecha1, index_name)
    index2 = market_data.get_index_value(fecha2, index_name)
    cashflow.set_start_date_index(index1)
    cashflow.set_end_date_index(index2)


def fix_overnight_index_mccy_cashflow(cashflow: qcf.OvernightIndexMultiCurrencyCashflow, market_data: qcv.MarketData):
    """
    Realiza el fixing de los índices overnight a fecha inicial y final y el fixing del índice de tipo de cambio
    de un OvernightIndexMultiCurrencyCashflow.

    Args:
        cashflow (OvernightIndexMultiCurrencyCashflow)
        market_data (qcv.MarketData): Objeto con la data de mercado necesaria para hacer el fixing

    Returns:
        None: El fixing se realiza inplace.
    """
    fix_overnight_index_cashflow(cashflow, market_data=market_data)
    fecha = qcw.Fecha(fecha=cashflow.get_fx_rate_index_fixing_date().iso_code()).as_py_date()
    index_name = index_alias.get(cashflow.get_fx_rate_index_code(), cashflow.get_fx_rate_index_code())
    index_value = market_data.get_index_value(fecha, index_name)
    cashflow.set_fx_rate_index_value(index_value)


def fix_fixed_rate_mccy_cashflow(cashflow: qcf.FixedRateMultiCurrencyCashflow, market_data: qcv.MarketData):
    """
    Realiza el fixing del índice de tipo de cambio de un FixedRateMultiCurrencyCashflow.

    Args:
        cashflow (FixedRateMultiCurrencyCashflow)
        market_data (qcv.MarketData): Objeto con la data de mercado necesaria para hacer el fixing

    Returns:
        None: El fixing se realiza inplace.
    """
    fecha = qcw.Fecha(fecha=cashflow.get_fx_fixing_date().iso_code()).as_py_date()
    index_name = cashflow.get_fx_rate_index_code()
    index_value = market_data.get_index_value(fecha, index_name)
    cashflow.set_fx_rate_index_value(index_value)


def fix_icp_clf_cashflow(cashflow: qcf.IcpClfCashflow, market_data: qcv.MarketData):
    """
    Realiza el fixing de los índices ICPCLP y de las UF de un IcpClfCashflow.

    Args:
        cashflow (IcpClfCashflow)
        market_data (qcv.MarketData): Objeto con la data de mercado necesaria para hacer el fixing

    Returns:
        None: El fixing se realiza inplace.

    """
    icpclp = "ICPCLP"
    uf = "UF"
    start_date = qcw.Fecha(fecha=cashflow.get_start_date().iso_code()).as_py_date()
    end_date = qcw.Fecha(fecha=cashflow.get_end_date().iso_code()).as_py_date()
    icpclp1 = market_data.get_index_value(start_date, icpclp)
    icpclp2 = market_data.get_index_value(end_date, icpclp)
    uf1 = market_data.get_index_value(start_date, uf)
    uf2 = market_data.get_index_value(end_date, uf)
    cashflow.set_start_date_icp(icpclp1)
    cashflow.set_end_date_icp(icpclp2)
    cashflow.set_start_date_uf(uf1)
    cashflow.set_end_date_uf(uf2)


def fix_compounded_overnight_rate_cashflow(cashflow: qcf.CompoundedOvernightRateCashflow2, market_data: qcv.MarketData):
    """
    Realiza el fixing de las tasas overnight de un CompoundedOvernightRateCashflow2.

    Args:
        cashflow (CompoundedOvernightRateCashflow2)
        market_data (qcv.MarketData): Objeto con la data de mercado necesaria para hacer el fixing

    Returns:
        None: El fixing se realiza inplace.
    """
    index_code = cashflow.get_interest_rate_index_code()
    ir_fixings = market_data.historic_index_values[index_code][1]
    cashflow.set_fixings(ir_fixings)


def fix_compounded_overnight_rate_mccy_cashflow(
        cashflow: qcf.CompoundedOvernightRateMultiCurrencyCashflow2,
        market_data: qcv.MarketData
):
    """
    Realiza el fixing de las tasas overnight y del índice de tipo de cambio de un
    CompoundedOvernightRateMultiCurrencyCashflow.

    Args:
        cashflow (CompoundedOvernightRateMultiCurrencyCashflow)
        market_data (qcv.MarketData): Objeto con la data de mercado necesaria para hacer el fixing

    Returns:
        None: El fixing se realiza inplace.

    """
    ir_index_code = cashflow.get_interest_rate_index_code()
    ir_fixings = market_data.historic_index_values[ir_index_code][1]
    cashflow.set_fixings(ir_fixings)
    fx_rate_index = cashflow.get_fx_rate_index_code()
    fx_fixing_date = qcw.Fecha(fecha=cashflow.get_fx_rate_index_fixing_date().iso_code()).as_py_date()
    fx_rate_index_value = market_data.get_index_value(fx_fixing_date, fx_rate_index)
    cashflow.set_fx_rate_index_value(fx_rate_index_value)


def fix_ibor_cashflow(cashflow: qcf.IborMultiCurrencyCashflow, market_data: qcv.MarketData):
    """
    Realiza el fixing de la tasa IBOR y del índice de tipo de cambio de un IborCashflow.

    Args:
        cashflow: (IborCashflow)
        market_data: (qcv.MarketData): Objeto con la data de mercado necesaria para hacer el fixing

    Returns:
        None: El fixing se realiza inplace.

    """
    ir_index_code = cashflow.get_interest_rate_index_code()
    fixing_date = qcw.Fecha(fecha=cashflow.get_fixing_date().iso_code())
    fixing = market_data.get_index_value(fixing_date.as_py_date(), ir_index_code)
    cashflow.set_interest_rate_value(fixing)


def fix_ibor_mccy_cashflow(cashflow: qcf.IborMultiCurrencyCashflow, market_data: qcv.MarketData):
    """
    Realiza el fixing de la tasa IBOR y del índice de tipo de cambio de un IborCashflow.

    Args:
        cashflow: (IborCashflow)
        market_data: (qcv.MarketData): Objeto con la data de mercado necesaria para hacer el fixing

    Returns:
        None: El fixing se realiza inplace.

    """
    fix_ibor_cashflow(cashflow, market_data)
    fx_rate_index = cashflow.get_fx_rate_index_code()
    fx_fixing_date = qcw.Fecha(fecha=cashflow.get_fx_fixing_date().iso_code()).as_py_date()
    fx_rate_index_value = market_data.get_index_value(fx_fixing_date, fx_rate_index)
    cashflow.set_fx_rate_index_value(fx_rate_index_value)


def fix_cashflow(cashflow: qcf.Cashflow, market_data: qcv.MarketData):
    """
    Realiza el fixing de tasa de interés y tipo de cambio cuando corresponde de cualquier tipo de qcf.Cashflow.

    Args:
        cashflow (qcf.Cashflow)
        market_data (qcv.MarketData): Objeto con la data de mercado necesaria para hacer el fixing

    Returns:
        None: El fixing se realiza inplace.

    """
    type_of_cashflow = cashflow.get_type()

    match type_of_cashflow:
        case "FixedRateCashflow":
            return

        case "FixedRateMultiCurrencyCashflow":
            fix_fixed_rate_mccy_cashflow(cashflow, market_data)

        case "IborCashflow":
            fix_ibor_cashflow(cashflow, market_data)

        case "IborMultiCurrencyCashflow":
            fix_ibor_mccy_cashflow(cashflow, market_data)

        case "OvernightIndexCashflow":
            fix_overnight_index_cashflow(cashflow, market_data)

        case "OvernightIndexMultiCurrencyCashflow":
            fix_overnight_index_mccy_cashflow(cashflow, market_data)

        case "IcpClfCashflow":
            fix_icp_clf_cashflow(cashflow, market_data)

        case "CompoundedOvernightRateCashflow2":
            fix_compounded_overnight_rate_cashflow(cashflow, market_data)

        case "CompoundedOvernightRateMultiCurrencyCashflow2":
            fix_compounded_overnight_rate_mccy_cashflow(cashflow, market_data)

        case _:
            raise ValueError(f"Fixing for cashflow {type_of_cashflow} not implemented yet.")
