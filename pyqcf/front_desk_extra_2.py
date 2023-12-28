from dateutil import relativedelta
from datetime import date
import pandas as pd
import numpy as np

from data_services import data_front_desk as dfd
from qcf_valuation import qcf_wrappers as qcw

from ..models import operations_2 as op


def misma_moneda(legs: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra los encabezados de patas que no son multicurrency.

    Args:
        legs: pd.DataFrame con encabezados de patas

    Returns:
        pd.DataFrame filtrado
    """
    result = legs.loc[
    (legs['codigo_moneda_nominal'] == legs['codigo_moneda_compensacion']) | (
        legs['codigo_moneda_compensacion'].isna()
    )].copy()
    result.reset_index(inplace=True)
    return result


def multi_currency(legs: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra los encabezados de patas multicurrency.
    Args:
        legs: pd.DataFrame con encabezados de patas

    Returns:
        pd.DataFrame filtrado
    """
    result = legs.loc[
    (legs['codigo_moneda_nominal'] != legs['codigo_moneda_compensacion']) & (
        ~legs['codigo_moneda_compensacion'].isna()
    )].copy()
    result.reset_index(inplace=True)
    return result


def get_leg_data(
        process_date: date,
        type_of_leg: op.TypeOfLeg,
        is_prod: bool
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Dada una fecha de proceso y un tipo de pata retorna 3 pd.DataFrame.

    - Encabezados de patas que no son multicurrency
    - Encabezados de patas multicurrency
    - Nominales y amortizaciones

    Args:
        process_date: datetime.date, fecha de proceso
        type_of_leg: op.TypeOfLeg, tipo de pata
        is_prod: bool, indica si se utiliza la BBDD de producción o no

    Returns:
        tuple of pd.DataFrame

    """
    if type_of_leg in [op.TypeOfLeg.FIXED_RATE, op.TypeOfLeg.FIXED_RATE_MCCY]:
        headers, amorts = dfd.get_fixed_rate_legs_for_qcf(process_date, is_prod=is_prod)

    elif type_of_leg in [op.TypeOfLeg.IBOR, op.TypeOfLeg.IBOR_MCCY]:
        headers, amorts = dfd.get_floating_rate_legs_for_qcf(process_date, is_prod=is_prod)

    elif type_of_leg in [op.TypeOfLeg.OVERNIGHT_INDEX, op.TypeOfLeg.OVERNIGHT_INDEX_MCCY]:
        headers_icp, amorts_icp = dfd.get_icp_legs_for_qcf(process_date, is_prod=is_prod)
        headers_icp = headers_icp.loc[headers_icp.codigo_moneda_nominal != 'CLF'].copy()
        headers_sofrindx, amorts_sofrindx = dfd.get_sofrindx_legs_for_qcf(process_date, is_prod=is_prod)
        headers = pd.concat([headers_icp, headers_sofrindx])
        headers.reset_index(inplace=True)
        amorts = pd.concat([amorts_icp, amorts_sofrindx])
        amorts.sort_index(inplace=True)

    elif type_of_leg == op.TypeOfLeg.ICP_CLF:
        headers, amorts = dfd.get_icp_legs_for_qcf(process_date, is_prod=is_prod)
        headers = headers.loc[headers.codigo_moneda_nominal == 'CLF'].copy()
        headers.reset_index(inplace=True)

    elif type_of_leg in [op.TypeOfLeg.COMPOUNDED_OVERNIGHT_RATE, op.TypeOfLeg.COMPOUNDED_OVERNIGHT_RATE_MCCY]:
        headers, amorts = dfd.get_sofrrate_legs_for_qcf(process_date, is_prod=is_prod)

    else:
        raise ValueError("process date or Type of Leg is invalid.")

    same_currency_headers = misma_moneda(headers)
    mccy_headers = multi_currency(headers)

    if type_of_leg in [op.TypeOfLeg.FIXED_RATE, op.TypeOfLeg.FIXED_RATE_MCCY]:
        mccy_headers.loc[np.isnan(mccy_headers["lag_fixing_compensacion"]), 'lag_fixing_compensacion'] = 0
        mccy_headers.codigo_indice_compensacion = mccy_headers.codigo_indice_compensacion.fillna('UF')

    return same_currency_headers, mccy_headers, amorts


def aux_make_leg(row: pd.core.series.Series, amorts: pd.DataFrame):
    start_date = qcw.Fecha(fecha=row.fecha_inicial)
    end_date = qcw.Fecha(fecha=row.fecha_final)
    delta = relativedelta.relativedelta(end_date.as_py_date(), start_date.as_py_date())
    maturity = qcw.Tenor(delta.years, delta.months, delta.days)
    if row.codigo_tipo_amortizacion == 'BULLET':
        notional_or_custom = op.InitialNotional(initial_notional=row.nominal_inicial)
    else:
        notional_or_custom = op.CustomNotionalAmort(
            custom_notional_amort=list(
                amorts.loc[
                    row.numero_operacion,
                    row.numero_pata,
                ][["nominal_vigente", "amortization"]].itertuples(
                    index=False,
                    name=None
                )
            )
        )

    return start_date, end_date, maturity, notional_or_custom


def make_fixed_rate_leg_generator(
        row: pd.core.series.Series,
        amorts: pd.DataFrame
) -> op.FixedRateLegGenerator:
    """
    Retorna un objeto de tipo FixedRateLegGenerator a partir de la data de Front Desk.

    Args:
        row: pd.core.series.Series
            Datos de encabezado. Es una fila de un `DataFrame`.
        amorts:

    Returns:

    """
    start_date, end_date, maturity, notional_or_custom = aux_make_leg(row, amorts)
    return op.FixedRateLegGenerator(
            rp=qcw.AP.A if row.numero_pata == 1 else qcw.AP.P,
            start_date=start_date,
            end_date=end_date,
            maturity=maturity,
            bus_adj_rule=qcw.BusAdjRules(row.codigo_ajuste_fecha_pago),
            periodicity=qcw.build_tenor_from_str(row.periodicidad_pago),
            stub_period=qcw.StubPeriods(row.periodo_irregular_pago),
            settlement_calendar=row.codigo_calendario_pago,
            settlement_lag=row.lag_de_pago,
            type_of_amortization=op.TypeOfAmortization(row.codigo_tipo_amortizacion),
            notional_or_custom=notional_or_custom,
            coupon_rate_value=row.valor_tasa_vigente,
            coupon_rate_type=qcw.TypeOfRate(row.codigo_convencion_tasa_vigente),
            notional_currency=qcw.Currency(row.codigo_moneda_nominal),
            amort_is_cashflow=True,
            is_bond=False,
        )


def make_fixed_rate_leg(
        row: pd.core.series.Series,
        amorts: pd.DataFrame
) -> op.FixedRateLegModel:
    """
    Construye un objeto de tipo op.FixedRateLegModel.

    Parameters
    ----------
    row: pd.core.series.Series
        Fila del DataFrame con los datos de cabecera de las patas fijas.

    amorts: pd.DataFrame
        Contiene el nocional vigente y la amortización para todos los flujos de la pata si esta No es BULLET.

    Returns
    -------
    op.FixedRateLegModel
    """
    return op.FixedRateLegModel(
        type_of_leg=op.TypeOfLeg.FIXED_RATE,
        leg_number=row.numero_pata,
        leg_generator=make_fixed_rate_leg_generator(row, amorts)
    )


def make_fixed_rate_mccy_leg(
        row: pd.core.series.Series,
        amorts: pd.DataFrame
) -> op.FixedRateMultiCurrencyLegModel:
    """
    Construye un objeto de tipo op.FixedRateLegModel a partir de los datos que se obtienen de Front Desk.

    Parameters
    ----------
    row: pd.core.series.Series
        Fila del DataFrame con los datos de cabecera de las patas fijas.

    amorts: pd.DataFrame
        Contiene el nocional vigente y la amortización para todos los flujos de la pata si esta No es BULLET.

    Returns
    -------
    op.FixedRateMultiCurrencyLegModel
    """
    mccy_model = op.MultiCurrencyModel(
        settlement_currency=qcw.Currency(row.codigo_moneda_compensacion),
        fx_rate_index_name=row.codigo_indice_compensacion,
        fx_fixing_lag=row.lag_fixing_compensacion
    )
    return op.FixedRateMultiCurrencyLegModel(
        type_of_leg=op.TypeOfLeg.FIXED_RATE_MCCY,
        leg_number=row.numero_pata,
        leg_generator=make_fixed_rate_leg_generator(row, amorts),
        multi_currency=mccy_model,
    )


def make_ibor_leg_generator(
        row: pd.core.series.Series,
        amorts: pd.DataFrame
) -> op.IborLegGenerator:
    """
    Construye un objeto de tipo op.IborLegGenerator a partir de los datos que se obtienen de Front Desk.

    Parameters
    ----------
    row: pd.core.series.Series
        Fila del DataFrame con los datos de cabecera de las patas Ibor.

    amorts: pd.DataFrame
        Contiene el nocional vigente y la amortización para todos los flujos de la pata si esta No es BULLET.

    Returns
    -------
    op.IborLegGenerator
    """
    start_date, end_date, maturity, notional_or_custom = aux_make_leg(row, amorts)
    return op.IborLegGenerator(
        rp=qcw.AP.A if row.numero_pata == 1 else qcw.AP.P,
        start_date=start_date,
        end_date=end_date,
        maturity=maturity,
        bus_adj_rule=qcw.BusAdjRules(row.codigo_ajuste_fecha_pago),
        settlement_periodicity=qcw.build_tenor_from_str(row.periodicidad_pago),
        settlement_stub_period=qcw.StubPeriods(row.periodo_irregular_pago),
        settlement_calendar=row.codigo_calendario_pago,
        settlement_lag=row.lag_de_pago,
        type_of_amortization=row.codigo_tipo_amortizacion,
        fixing_periodicity=qcw.build_tenor_from_str(row.periodicidad_fixing),
        fixing_stub_period=row.periodo_irregular_fixing,
        fixing_calendar=row.codigo_calendario_fixing,
        fixing_lag=row.lag_de_fixing,
        interest_rate_index_name=row.codigo_tasa_flotante,
        notional_or_custom=notional_or_custom,
        amort_is_cashflow=True,
        notional_currency=qcw.Currency(row.codigo_moneda_nominal),
        spread=row.valor_spread_vigente,
        gearing=1.0,
    )


def make_ibor_leg(
        row: pd.core.series.Series,
        amorts: pd.DataFrame
) -> op.IborLegModel:
    """
    Construye un objeto de tipo op.IborLegModel a partir de los datos que se obtienen de Front Desk.

    Parameters
    ----------
    row: pd.core.series.Series
        Fila del DataFrame con los datos de cabecera de las patas Ibor.

    amorts: pd.DataFrame
        Contiene el nocional vigente y la amortización para todos los flujos de la pata si esta No es BULLET.

    Returns
    -------
    op.IborRateLegModel
    """
    return op.IborLegModel(
        type_of_leg=op.TypeOfLeg.IBOR,
        leg_number=row.numero_pata,
        leg_generator=make_ibor_leg_generator(row, amorts)
    )


def make_ibor_mccy_leg(
        row: pd.core.series.Series,
        amorts: pd.DataFrame
) -> op.IborMultiCurrencyLegModel:
    """
    Construye un objeto de tipo op.IborLegMultiCurrencyModel a partir de los datos que se obtienen de Front Desk.

    Parameters
    ----------
    row: pd.core.series.Series
        Fila del DataFrame con los datos de cabecera de las patas Ibor.

    amorts: pd.DataFrame
        Contiene el nocional vigente y la amortización para todos los flujos de la pata si esta No es BULLET.

    Returns
    -------
    op.IborLegMultiCurrencyModel
    """
    ibor_leg_generator = make_ibor_leg_generator(row, amorts)
    mccy_model = op.MultiCurrencyModel(
        settlement_currency=qcw.Currency(row.codigo_moneda_compensacion),
        fx_rate_index_name=row.codigo_indice_compensacion,
        fx_fixing_lag=row.lag_fixing_compensacion
    )
    return op.IborMultiCurrencyLegModel(
        type_of_leg=op.TypeOfLeg.IBOR_MCCY,
        leg_number=row.numero_pata,
        leg_generator=ibor_leg_generator,
        multi_currency=mccy_model
    )


def make_overnight_index_leg_generator(
        row: pd.core.series.Series,
        amorts: pd.DataFrame,
) -> op.OvernightIndexLegGenerator:
    start_date, end_date, maturity, notional_or_custom = aux_make_leg(row, amorts)
    return op.OvernightIndexLegGenerator(
        rp=qcw.AP.A if row.numero_pata == 1 else qcw.AP.P,
        start_date=start_date,
        end_date=end_date,
        maturity=maturity,
        bus_adj_rule=qcw.BusAdjRules(row.codigo_ajuste_fecha_pago),
        fix_adj_rule=qcw.BusAdjRules.PREV,
        settlement_periodicity=qcw.build_tenor_from_str(row.periodicidad_pago),
        settlement_stub_period=qcw.StubPeriods(row.periodo_irregular_pago),
        settlement_calendar=row.codigo_calendario_pago,
        settlement_lag=row.lag_de_pago,
        fixing_calendar=row.codigo_calendario_pago,
        type_of_amortization=row.codigo_tipo_amortizacion,
        overnight_index_name=row.codigo_tasa_flotante,
        interest_rate=qcw.TypeOfRate(row.codigo_convencion_tasa_vigente),
        notional_or_custom=notional_or_custom,
        amort_is_cashflow=True,
        notional_currency=qcw.Currency(row.codigo_moneda_nominal),
        spread=row.valor_spread_vigente,
        gearing=1.0,
        eq_rate_decimal_places=4 if row.codigo_tasa_flotante in ['ICPCLP', 'ICPCLF'] else 8
    )


def make_overnight_index_leg(
        row: pd.core.series.Series,
        amorts: pd.DataFrame
) -> op.OvernightIndexLegModel:
    """
    Construye un objeto de tipo op.OvernightIndexLegModel a partir de los datos que se obtienen de Front Desk.

    Parameters
    ----------
    row: pd.core.series.Series
        Fila del DataFrame con los datos de cabecera de las patas Ibor.

    amorts: pd.DataFrame
        Contiene el nocional vigente y la amortización para todos los flujos de la pata si esta No es BULLET.

    Returns
    -------
    op.OvernightIndexLegModel
    """
    return op.OvernightIndexLegModel(
        type_of_leg=op.TypeOfLeg.OVERNIGHT_INDEX,
        leg_number=row.numero_pata,
        leg_generator=make_overnight_index_leg_generator(row, amorts)
    )


def make_icpclf_leg_generator(
        row: pd.core.series.Series,
        amorts: pd.DataFrame,
) -> op.IcpClfLegGenerator:
    start_date, end_date, maturity, notional_or_custom = aux_make_leg(row, amorts)
    return op.IcpClfLegGenerator(
        rp=qcw.AP.A if row.numero_pata == 1 else qcw.AP.P,
        start_date=start_date,
        end_date=end_date,
        maturity=maturity,
        bus_adj_rule=qcw.BusAdjRules(row.codigo_ajuste_fecha_pago),
        settlement_periodicity=qcw.build_tenor_from_str(row.periodicidad_pago),
        settlement_stub_period=qcw.StubPeriods(row.periodo_irregular_pago),
        settlement_calendar=row.codigo_calendario_pago,
        settlement_lag=row.lag_de_pago,
        overnight_index_name=row.codigo_tasa_flotante,
        type_of_amortization=row.codigo_tipo_amortizacion,
        notional_or_custom=notional_or_custom,
        amort_is_cashflow=True,
        spread=row.valor_spread_vigente,
        gearing=1.0,
    )


def make_icpclf_leg(
        row: pd.core.series.Series,
        amorts: pd.DataFrame
) -> op.IcpClfLegModel:
    """
    Construye un objeto de tipo op.IcpClfLegModel a partir de los datos que se obtienen de Front Desk.

    Parameters
    ----------
    row: pd.core.series.Series
        Fila del DataFrame con los datos de cabecera de las patas Ibor.

    amorts: pd.DataFrame
        Contiene el nocional vigente y la amortización para todos los flujos de la pata si esta No es BULLET.

    Returns
    -------
    op.OvernightIndexLegModel
    """
    return op.IcpClfLegModel(
        type_of_leg=op.TypeOfLeg.ICP_CLF,
        leg_number=row.numero_pata,
        leg_generator=make_icpclf_leg_generator(row, amorts)
    )


def make_overnight_index_mccy_leg(
        row: pd.core.series.Series,
        amorts: pd.DataFrame
) -> op.OvernightIndexMultiCurrencyLegModel:
    """
    Construye un objeto de tipo op.OvernightIndexLegMultiCurrencyModel a partir de los datos que se obtienen de Front Desk.

    Parameters
    ----------
    row: pd.core.series.Series
        Fila del DataFrame con los datos de cabecera de las patas Ibor.

    amorts: pd.DataFrame
        Contiene el nocional vigente y la amortización para todos los flujos de la pata si esta No es BULLET.

    Returns
    -------
    op.OvernightIndexLegMultiCurrencyModel
    """
    overnight_index_leg_generator = make_overnight_index_leg_generator(row, amorts)
    mccy_model = op.MultiCurrencyModel(
        settlement_currency=qcw.Currency(row.codigo_moneda_compensacion),
        fx_rate_index_name=row.codigo_indice_compensacion,
        fx_fixing_lag=row.lag_fixing_compensacion
    )
    return op.OvernightIndexMultiCurrencyLegModel(
        type_of_leg=op.TypeOfLeg.OVERNIGHT_INDEX_MCCY,
        leg_number=row.numero_pata,
        leg_generator=overnight_index_leg_generator,
        multi_currency=mccy_model
    )


def make_compounded_overnight_rate_leg_generator(
        row: pd.core.series.Series,
        amorts: pd.DataFrame,
):
    if row.codigo_tasa_flotante == "TASA SOFR / LOOKBACK":
        nombre_indice = "SOFRRATE"
    else:
        nombre_indice = row.codigo_tasa_flotante
    start_date, end_date, maturity, notional_or_custom = aux_make_leg(row, amorts)
    return op.CompoundedOvernightRateLegGenerator(
        rp=qcw.AP.A if row.numero_pata == 1 else qcw.AP.P,
        start_date=start_date,
        end_date=end_date,
        maturity=maturity,
        bus_adj_rule=qcw.BusAdjRules(row.codigo_ajuste_fecha_pago),
        settlement_periodicity=qcw.build_tenor_from_str(row.periodicidad_pago),
        settlement_stub_period=qcw.StubPeriods(row.periodo_irregular_pago),
        settlement_calendar=row.codigo_calendario_pago,
        settlement_lag=row.lag_de_pago,
        type_of_amortization=row.codigo_tipo_amortizacion,
        fixing_calendar=row.codigo_calendario_fixing,
        overnight_rate_name=nombre_indice,
        notional_or_custom=notional_or_custom,
        amort_is_cashflow=True,
        notional_currency=qcw.Currency(row.codigo_moneda_nominal),
        spread=row.valor_spread_vigente,
        gearing=1.0,
        interest_rate_type=qcw.TypeOfRate.LINACT360 if row.codigo_convencion_tasa_vigente == "LIN_ACT360" else qcw.TypeOfRate.LIN30360,
        eq_rate_decimal_places=8,
        lookback=row.lookback,
        lockout=0,
    )


def make_compounded_overnight_rate_leg(
        row: pd.core.series.Series,
        amorts: pd.DataFrame
) -> op.CompoundedOvernightRateLegModel:
    """
    Construye un objeto de tipo op.CompoundedOvernightRateModel a partir de los datos que se obtienen de Front Desk.

    Parameters
    ----------
    row: pd.core.series.Series
        Fila del DataFrame con los datos de cabecera de las patas Ibor.

    amorts: pd.DataFrame
        Contiene el nocional vigente y la amortización para todos los flujos de la pata si esta No es BULLET.

    Returns
    -------
    op.CompoundedOvernightRateModel
    """
    return op.CompoundedOvernightRateLegModel(
        type_of_leg=op.TypeOfLeg.COMPOUNDED_OVERNIGHT_RATE,
        leg_number=row.numero_pata,
        leg_generator=make_compounded_overnight_rate_leg_generator(row, amorts)
    )


def make_compounded_overnight_rate_mccy_leg(
        row: pd.core.series.Series,
        amorts: pd.DataFrame
) -> op.CompoundedOvernightRateMultiCurrencyLegModel:
    """
    Construye un objeto de tipo op.CompoundedOvernightRateModel a partir de los datos que se obtienen de Front Desk.

    Parameters
    ----------
    row: pd.core.series.Series
        Fila del DataFrame con los datos de cabecera de las patas Ibor.

    amorts: pd.DataFrame
        Contiene el nocional vigente y la amortización para todos los flujos de la pata si esta No es BULLET.

    Returns
    -------
    op.CompoundedOvernightRateModel
    """
    cor_leg_generator = make_compounded_overnight_rate_leg_generator(row, amorts)
    mccy_model = op.MultiCurrencyModel(
        settlement_currency=qcw.Currency(row.codigo_moneda_compensacion),
        fx_rate_index_name=row.codigo_indice_compensacion,
        fx_fixing_lag=row.lag_fixing_compensacion
    )
    return op.CompoundedOvernightRateMultiCurrencyLegModel(
        type_of_leg=op.TypeOfLeg.COMPOUNDED_OVERNIGHT_RATE_MCCY,
        leg_number=row.numero_pata,
        leg_generator=cor_leg_generator,
        multi_currency=mccy_model,
    )


def make_leg(
        row: pd.core.series.Series,
        amorts: pd.DataFrame,
        type_of_leg: op.TypeOfLeg
) -> op.OperationLeg:
    """
    Retorna un modelo de pata (models/operations) a partir de se encabezado, eventuales amortizaciones y
    tipo de pata.

    Args:
        row: pd.core.series.Series. Encabezado de la pata.
        amorts: pd.DataFrame. Nocionales y amortizaciones
        type_of_leg: op.TypeOfLeg. Tipo de pata

    Returns:
        op.OperationLeg

    """
    match type_of_leg:
        case op.TypeOfLeg.FIXED_RATE:
            return make_fixed_rate_leg(row, amorts)

        case op.TypeOfLeg.FIXED_RATE_MCCY:
            return make_fixed_rate_mccy_leg(row, amorts)

        case op.TypeOfLeg.IBOR:
            return make_ibor_leg(row, amorts)

        case op.TypeOfLeg.IBOR_MCCY:
            return make_ibor_mccy_leg(row, amorts)

        case op.TypeOfLeg.OVERNIGHT_INDEX:
            return make_overnight_index_leg(row, amorts)

        case op.TypeOfLeg.ICP_CLF:
            return make_icpclf_leg(row, amorts)

        case op.TypeOfLeg.OVERNIGHT_INDEX_MCCY:
            return make_overnight_index_mccy_leg(row, amorts)

        case op.TypeOfLeg.COMPOUNDED_OVERNIGHT_RATE:
            return make_compounded_overnight_rate_leg(row, amorts)

        case op.TypeOfLeg.COMPOUNDED_OVERNIGHT_RATE_MCCY:
            return make_compounded_overnight_rate_mccy_leg(row, amorts)
