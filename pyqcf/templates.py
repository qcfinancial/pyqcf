from typing import Dict, Any
from datetime import date

from .pricing import LegTemplate, LegParameters
from . import wrappers as qcw
from .market_data import get_calendars

import sys
if sys.platform in ["win32", "darwin"]:
    import qcfinancial as qcf
else:
    import qc_financial as qcf

# Hate this. There has to be a better way.
# Maybe some sort of dependency injection.
cals = get_calendars(date(2021, 1, 1), is_prod=True)


class Fix6MCLF(LegTemplate):
    def __init__(
        self,
        nombre='Fix6MCLF',
        default={
            LegParameters.LAG_INICIO: 2,
            LegParameters.BUS_ADJ_RULE: qcf.BusyAdjRules.MODFOLLOW,
            LegParameters.PERIODICIDAD_PAGO: qcf.Tenor('6M'),
            LegParameters.LAG_PAGO: 0,
            LegParameters.STUB_PERIOD_PAGO: qcf.StubPeriod.SHORTFRONT,
            LegParameters.CALENDARIO_PAGO: cals['SCL'],
            LegParameters.MONEDA_NOCIONAL: qcf.QCCLF(),
            LegParameters.MONEDA_PAGO: qcf.QCCLP(),
            LegParameters.INDICE_FX: 'UF',
            LegParameters.LAG_FIXING_FX: 0,
            LegParameters.AMORT_ES_FLUJO: True,
            LegParameters.TIPO_TASA: qcw.TypeOfRate.LINACT360,
            LegParameters.ES_BONO: False,
        }
    ):
        LegTemplate.__init__(self, nombre, default)
        self.nombre = nombre
        self.default = default

    def build_leg(self, other: Dict[LegParameters, Any]) -> qcf.Leg:
        """
        Construye la pata fija con los valores de `other` y los valores `default`.

        El Dict `other` debe contener las siguientes llaves:

        - FECHA_CURSE
        - REC_PAY
        - PLAZO
        - TIPO_TASA
        - VALOR_TASA
        - NOCIONAL (en UF)
        """
        cal = self.default[LegParameters.CALENDARIO_PAGO]
        fecha_inicio = cal.shift(
            other[LegParameters.FECHA_CURSE],
            self.default[LegParameters.LAG_INICIO]
        )
        total_months = other[LegParameters.PLAZO].get_months()
        total_months += 12 * other[LegParameters.PLAZO].get_years()
        fecha_final = fecha_inicio.add_months(total_months)

        tasa_cupon = self.default[LegParameters.TIPO_TASA].as_qcf_with_value(
            other[LegParameters.VALOR_TASA]
        )

        return qcf.LegFactory.build_bullet_fixed_rate_leg_2(
            other[LegParameters.REC_PAY],
            fecha_inicio,
            fecha_final,
            self.default[LegParameters.BUS_ADJ_RULE],
            self.default[LegParameters.PERIODICIDAD_PAGO],
            self.default[LegParameters.STUB_PERIOD_PAGO],
            cal,
            self.default[LegParameters.LAG_PAGO],
            other[LegParameters.NOCIONAL],
            self.default[LegParameters.AMORT_ES_FLUJO],
            tasa_cupon,
            self.default[LegParameters.MONEDA_NOCIONAL],
            self.default[LegParameters.ES_BONO],
        )


class Fix6MCLPCLP(LegTemplate):
    def __init__(
        self,
        nombre='Fix6MCLPCLP',
        default={
            LegParameters.LAG_INICIO: 2,
            LegParameters.BUS_ADJ_RULE: qcf.BusyAdjRules.MODFOLLOW,
            LegParameters.PERIODICIDAD_PAGO: qcf.Tenor('6M'),
            LegParameters.LAG_PAGO: 0,
            LegParameters.STUB_PERIOD_PAGO: qcf.StubPeriod.SHORTFRONT,
            LegParameters.CALENDARIO_PAGO: cals['SCL'],
            LegParameters.MONEDA_NOCIONAL: qcf.QCCLP(),
            LegParameters.MONEDA_PAGO: qcf.QCCLP(),
            LegParameters.INDICE_FX: '1CLP',
            LegParameters.LAG_FIXING_FX: 0,
            LegParameters.AMORT_ES_FLUJO: True,
            LegParameters.TIPO_TASA: qcw.TypeOfRate.LINACT360,
            LegParameters.ES_BONO: False,
        }
    ):
        LegTemplate.__init__(self, nombre, default)
        self.nombre = nombre
        self.default = default

    def build_leg(self, other: Dict[LegParameters, Any]) -> qcf.Leg:
        """
        Construye la pata fija con los valores de `other` y los valores `default`.

        El Dict `other` debe contener las siguientes llaves:

        - FECHA_CURSE
        - REC_PAY
        - PLAZO
        - TIPO_TASA
        - VALOR_TASA
        - NOCIONAL (en UF)
        """
        cal = self.default[LegParameters.CALENDARIO_PAGO]
        fecha_inicio = cal.shift(
            other[LegParameters.FECHA_CURSE],
            self.default[LegParameters.LAG_INICIO]
        )
        total_months = other[LegParameters.PLAZO].get_months()
        total_months += 12 * other[LegParameters.PLAZO].get_years()
        fecha_final = fecha_inicio.add_months(total_months)

        tasa_cupon = self.default[LegParameters.TIPO_TASA].as_qcf_with_value(
            other[LegParameters.VALOR_TASA]
        )

        return qcf.LegFactory.build_bullet_fixed_rate_leg_2(
            other[LegParameters.REC_PAY],
            fecha_inicio,
            fecha_final,
            self.default[LegParameters.BUS_ADJ_RULE],
            self.default[LegParameters.PERIODICIDAD_PAGO],
            self.default[LegParameters.STUB_PERIOD_PAGO],
            cal,
            self.default[LegParameters.LAG_PAGO],
            other[LegParameters.NOCIONAL],
            self.default[LegParameters.AMORT_ES_FLUJO],
            tasa_cupon,
            self.default[LegParameters.MONEDA_NOCIONAL],
            self.default[LegParameters.ES_BONO],
        )


class IcpClp6M(LegTemplate):
    def __init__(
        self,
        nombre='IcpClp6M',
        default={
            LegParameters.LAG_INICIO: 2,
            LegParameters.BUS_ADJ_RULE: qcf.BusyAdjRules.MODFOLLOW,
            LegParameters.PERIODICIDAD_PAGO: qcf.Tenor('6M'),
            LegParameters.LAG_PAGO: 0,
            LegParameters.STUB_PERIOD_PAGO: qcf.StubPeriod.SHORTFRONT,
            LegParameters.CALENDARIO_PAGO: cals['SCL'],
            LegParameters.MONEDA_NOCIONAL: qcf.QCCLP(),
            LegParameters.MONEDA_PAGO: qcf.QCCLP(),
            LegParameters.INDICE_FX: '1CLP',
            LegParameters.LAG_FIXING_FX: 0,
            LegParameters.AMORT_ES_FLUJO: True,
            LegParameters.ES_ACT360: True,
            LegParameters.VALOR_SPREAD: 0.0,
            LegParameters.VALOR_GEARING: 1.0,
        }
    ):
        LegTemplate.__init__(self, nombre, default)
        self.nombre = nombre
        self.default = default

    def build_leg(self, other: Dict[LegParameters, Any]) -> qcf.Leg:
        """
        Construye la pata ICPCLP con los valores de `other` y los valores `default`.

        El Dict `other` debe contener las siguientes llaves:

        - FECHA_CURSE
        - REC_PAY
        - PLAZO
        - TIPO_TASA
        - VALOR_TASA
        - NOCIONAL (en UF)
        """
        cal = self.default[LegParameters.CALENDARIO_PAGO]
        fecha_inicio = cal.shift(
            other[LegParameters.FECHA_CURSE],
            self.default[LegParameters.LAG_INICIO]
        )
        total_months = other[LegParameters.PLAZO].get_months()
        total_months += 12 * other[LegParameters.PLAZO].get_years()
        fecha_final = fecha_inicio.add_months(total_months)

        return qcf.LegFactory.build_bullet_icp_clp2_leg(
            other[LegParameters.REC_PAY],
            fecha_inicio,
            fecha_final,
            self.default[LegParameters.BUS_ADJ_RULE],
            self.default[LegParameters.PERIODICIDAD_PAGO],
            self.default[LegParameters.STUB_PERIOD_PAGO],
            cal,
            self.default[LegParameters.LAG_PAGO],
            other[LegParameters.NOCIONAL],
            self.default[LegParameters.AMORT_ES_FLUJO],
            self.default[LegParameters.VALOR_SPREAD],
            self.default[LegParameters.VALOR_GEARING],
            self.default[LegParameters.ES_ACT360],
        )
