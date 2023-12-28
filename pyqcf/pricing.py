from enum import Enum
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel

import qcfinancial as qcf
from . import wrappers as qcw
from . import front_desk_config as config
from . import market_data as qcv


class LegParameters(Enum):
    # Parámetros para todas las patas
    FECHA_CURSE = 1
    REC_PAY = 2
    FECHA_INICIO = 3
    FECHA_FINAL = 4
    LAG_INICIO = 5
    PLAZO = 6
    NOCIONAL = 7
    BUS_ADJ_RULE = 8
    PERIODICIDAD_PAGO = 9
    LAG_PAGO = 10
    STUB_PERIOD_PAGO = 11
    CALENDARIO_PAGO = 12
    MONEDA_NOCIONAL = qcw.Currency
    MONEDA_PAGO = 13
    INDICE_FX = 14
    LAG_FIXING_FX = 15
    CAPITAL_AMORT = 16
    AMORT_ES_FLUJO = 17

    # Parámetros para patas fijas
    TIPO_TASA = 18
    VALOR_TASA = 19
    ES_BONO = 20

    # Parámetros para patas flotantes (Ibor)
    PERIODICIDAD_FIXING = 21
    LAG_FIXING = 22
    STUB_PERIOD_FIXING = 23
    CALENDARIO_FIXING = 24
    INDICE_TASA = 25
    VALOR_SPREAD = 26  # Sirve también para patas overnight
    VALOR_GEARING = 27

    # Parámetros para patas ICPCLP
    ES_ACT360 = 28


class LegTemplate(ABC):
    def __init__(self, nombre: str, default: Dict[LegParameters, Any]):
        self.nombre = nombre
        self.default = default

    @abstractmethod
    def build_leg(self, other: Dict[LegParameters, Any]) -> qcf.Leg:
        pass


class OperationBuilder(BaseModel):
    leg_templates: List[LegTemplate]

    class Config:
        arbitrary_types_allowed = True

    def mkt_icpclp(
        self,
        deal_number: str,
        counterparty: str,
        data_pata_fija: Dict[LegParameters, Any],
        data_pata_icp: Dict[LegParameters, Any],
    ) -> qcv.Operation:
        """
        Retorna una operación ICPCLP estándar de mercado.
        """
        fixed_rate_template = [
            t for t in self.leg_templates if t.nombre == "Fix6MCLPCLP"
        ][0]
        icpclp_leg_template = [t for t in self.leg_templates if t.nombre == "IcpClp6M"][
            0
        ]

        fixed_rate_leg = fixed_rate_template.build_leg(data_pata_fija)
        icpclp_leg = icpclp_leg_template.build_leg(data_pata_icp)

        leg_fija = qcv.OperationLeg(
            deal_number=deal_number,
            counterparty=counterparty,
            leg_number=1
            if data_pata_fija[LegParameters.REC_PAY] == qcf.RecPay.RECEIVE
            else 2,
            interest_rate_index=config.InterestRateIndex.NOIRINDX,
            type_of_rate=fixed_rate_template.default[LegParameters.TIPO_TASA],
            fx_rate=qcw.FXRate("CLPCLP"),
            nominal_currency=qcw.Currency.CLP,
            a_p=qcw.AP.A
            if data_pata_fija[LegParameters.REC_PAY] == qcf.RecPay.RECEIVE
            else qcw.AP.P,
            type_of_leg=qcv.TypeOfLeg.FIXED_RATE,
            qcf_leg=fixed_rate_leg,
        )

        leg_icpclp = qcv.OperationLeg(
            deal_number=deal_number,
            counterparty=counterparty,
            leg_number=1
            if data_pata_icp[LegParameters.REC_PAY] == qcf.RecPay.RECEIVE
            else 2,
            interest_rate_index=config.InterestRateIndex.ICPCLP,
            type_of_rate=qcw.TypeOfRate.LINACT360,
            fx_rate=qcw.FXRate("CLPCLP"),
            nominal_currency=qcw.Currency.CLP,
            a_p=qcw.AP.A
            if data_pata_icp[LegParameters.REC_PAY] == qcf.RecPay.RECEIVE
            else qcw.AP.P,
            type_of_leg=qcv.TypeOfLeg.ICPCLP,
            qcf_leg=icpclp_leg,
        )

        return qcv.Operation(
            deal_number=deal_number,
            counterparty=counterparty,
            product="SWAP_ICP",
            portfolio="BANCA",
            legs=(
                leg_fija if leg_fija.leg_number == 1 else leg_icpclp,
                leg_fija if leg_fija.leg_number == 2 else leg_icpclp,
            ),
        )

    def mkt_clf_icpclp(
        self,
        deal_number: str,
        counterparty: str,
        data_pata_fija: Dict[LegParameters, Any],
        data_pata_icp: Dict[LegParameters, Any],
    ) -> qcv.Operation:
        """
        Retorna una operación CCS UF Fija vs ICPLP estándar de mercado.
        """
        fixed_rate_template = [t for t in self.leg_templates if t.nombre == "Fix6MCLF"][
            0
        ]
        icpclp_leg_template = [t for t in self.leg_templates if t.nombre == "IcpClp6M"][
            0
        ]

        fixed_rate_leg = fixed_rate_template.build_leg(data_pata_fija)
        icpclp_leg = icpclp_leg_template.build_leg(data_pata_icp)

        leg_fija = qcv.OperationLeg(
            deal_number=deal_number,
            counterparty=counterparty,
            leg_number=1
            if data_pata_fija[LegParameters.REC_PAY] == qcf.RecPay.RECEIVE
            else 2,
            interest_rate_index=config.InterestRateIndex.NOIRINDX,
            type_of_rate=fixed_rate_template.default[LegParameters.TIPO_TASA],
            fx_rate=qcw.FXRate("CLFCLP"),
            nominal_currency=qcw.Currency.CLF,
            a_p=qcw.AP.A
            if data_pata_fija[LegParameters.REC_PAY] == qcf.RecPay.RECEIVE
            else qcw.AP.P,
            type_of_leg=qcv.TypeOfLeg.FIXED_RATE,
            qcf_leg=fixed_rate_leg,
        )

        leg_icpclp = qcv.OperationLeg(
            deal_number=deal_number,
            counterparty=counterparty,
            leg_number=1
            if data_pata_icp[LegParameters.REC_PAY] == qcf.RecPay.RECEIVE
            else 2,
            interest_rate_index=config.InterestRateIndex.ICPCLP,
            type_of_rate=qcw.TypeOfRate.LINACT360,
            fx_rate=qcw.FXRate("CLFCLP"),
            nominal_currency=qcw.Currency.CLP,
            a_p=qcw.AP.A
            if data_pata_icp[LegParameters.REC_PAY] == qcf.RecPay.RECEIVE
            else qcw.AP.P,
            type_of_leg=qcv.TypeOfLeg.ICPCLP,
            qcf_leg=icpclp_leg,
        )

        return qcv.Operation(
            deal_number=deal_number,
            counterparty=counterparty,
            product="SWAP_MONE",
            portfolio="BANCA",
            legs=(
                leg_fija if leg_fija.leg_number == 1 else leg_icpclp,
                leg_fija if leg_fija.leg_number == 2 else leg_icpclp,
            ),
        )
