from enum import Enum, auto
from strenum import StrEnum
from pydantic import (
    NonNegativeInt,
    BaseModel,
    field_validator,
    ConfigDict
)
from pydantic.dataclasses import dataclass
from datetime import datetime, date
import pandas as pd

import qcfinancial as qcf


class Currency(str, Enum):
    """
    Identifica todas las divisas que se pueden utilizar con `qcfinancial`.
    """
    AUD = "AUD"
    BRL = "BRL"
    CAD = "CAD"
    CHF = "CHF"
    CLF = "CLF"
    CLP = "CLP"
    CNY = "CNY"
    COP = "COP"
    DKK = "DKK"
    EUR = "EUR"
    GBP = "GBP"
    HKD = "HKD"
    JPY = "JPY"
    MXN = "MXN"
    NOK = "NOK"
    PEN = "PEN"
    SEK = "SEK"
    USD = "USD"

    def as_qcf(self):
        """
        Retorna la divisa representada por `self` con el correspondiente objeto `QC_Financial_3`.
        """
        switcher = {
            self.AUD: qcf.QCAUD(),
            self.BRL: qcf.QCBRL(),
            self.CAD: qcf.QCCAD(),
            self.CHF: qcf.QCCHF(),
            self.CLF: qcf.QCCLF(),
            self.CLP: qcf.QCCLP(),
            self.CNY: qcf.QCCNY(),
            self.COP: qcf.QCCOP(),
            self.DKK: qcf.QCDKK(),
            self.EUR: qcf.QCEUR(),
            self.GBP: qcf.QCGBP(),
            self.HKD: qcf.QCHKD(),
            self.JPY: qcf.QCJPY(),
            self.MXN: qcf.QCMXN(),
            self.NOK: qcf.QCNOK(),
            self.PEN: qcf.QCCPEN(),
            self.SEK: qcf.QCSEK(),
            self.USD: qcf.QCUSD(),
        }

        return switcher[self.value]

    def __str__(self):
        return self.as_qcf().get_iso_code()

    def __repr__(self):
        return self.__str__()


class BusAdjRules(str, Enum):
    """
    Representa los distintos algoritmos de ajuste de fecha disponibles en `qcfinancial`.

    Los valores disponibles son:

    - NO: no ajustar las fechas.

    - FOLLOW: si la fecha cae en un feriado, la fecha se desplaza al día hábil siguiente.

    - MOD_FOLLOW: si la fecha cae en feriado se desplaza al día hábil siguiente, excepto que el día hábil siguiente
    esté en el mes siguiente, en ese caso, la fecha se desplaza al día hábil anterior.

    - PREV: si la fecha cae en feriado, la fecha se desplaza al día hábil anterior.

    - MOD_PREV: si la fecha cae en feriado, la fecha se desplaza al día hábil anterior, excepto que el día hábil
    anterior esté en el mes anterior, en ese caso, la fecha se desplaza al día hábil siguiente.
    """

    NO = "NO"
    FOLLOW = "FOLLOW"
    MOD_FOLLOW = "MOD_FOLLOW"
    PREV = "PREV"
    MOD_PREV = "MOD_PREV"

    def as_qcf(self) -> qcf.BusyAdjRules:
        """
        Retorna la regla de ajuste de fecha representada por `self` con el correspondiente objeto `qc_financial`.
        """
        switcher = {
            self.NO: qcf.BusyAdjRules.NO,
            self.FOLLOW: qcf.BusyAdjRules.FOLLOW,
            self.MOD_FOLLOW: qcf.BusyAdjRules.MODFOLLOW,
            self.PREV: qcf.BusyAdjRules.PREVIOUS,
            self.MOD_PREV: qcf.BusyAdjRules.MODPREVIOUS,
        }

        return switcher[self]

    def __str__(self):
        return str(self.value)


class StubPeriods(str, Enum):
    """
    Representa los distintos ajustes de período irregular disponibles en `qcfinancial`.
    """

    NO = "NO"
    CORTO_INICIO = "CORTO INICIO"
    CORTO_FINAL = "CORTO FINAL"
    LARGO_INICIO = "LARGO INICIO"
    LARGO_FINAL = "LARGO FINAL"
    LARGO_INICIO_2 = "LARGO INICIO 2"
    LARGO_INICIO_3 = "LARGO INICIO 3"
    LARGO_INICIO_4 = "LARGO INICIO 4"
    LARGO_INICIO_5 = "LARGO INICIO 5"
    LARGO_INICIO_6 = "LARGO INICIO 6"
    LARGO_INICIO_7 = "LARGO INICIO 7"
    LARGO_INICIO_8 = "LARGO INICIO 8"
    LARGO_INICIO_9 = "LARGO INICIO 9"
    LARGO_INICIO_10 = "LARGO INICIO 10"
    LARGO_INICIO_11 = "LARGO INICIO 11"
    LARGO_INICIO_12 = "LARGO INICIO 12"
    LARGO_INICIO_13 = "LARGO INICIO 13"
    LARGO_INICIO_14 = "LARGO INICIO 14"

    def as_qcf(self):
        """
        Retorna la regla de ajuste de período irregular representada por `self` con el correspondiente objeto `QC_Financial_3`.
        """
        switcher = {
            self.NO: qcf.StubPeriod.NO,
            self.CORTO_INICIO: qcf.StubPeriod.SHORTFRONT,
            self.CORTO_FINAL: qcf.StubPeriod.SHORTBACK,
            self.LARGO_INICIO: qcf.StubPeriod.LONGFRONT,
            self.LARGO_FINAL: qcf.StubPeriod.LONGBACK,
            self.LARGO_INICIO_2: qcf.StubPeriod.LONGFRONT2,
            self.LARGO_INICIO_3: qcf.StubPeriod.LONGFRONT3,
            self.LARGO_INICIO_4: qcf.StubPeriod.LONGFRONT4,
            self.LARGO_INICIO_5: qcf.StubPeriod.LONGFRONT5,
            self.LARGO_INICIO_6: qcf.StubPeriod.LONGFRONT6,
            self.LARGO_INICIO_7: qcf.StubPeriod.LONGFRONT7,
            self.LARGO_INICIO_8: qcf.StubPeriod.LONGFRONT8,
            self.LARGO_INICIO_9: qcf.StubPeriod.LONGFRONT9,
            self.LARGO_INICIO_10: qcf.StubPeriod.LONGFRONT10,
            self.LARGO_INICIO_11: qcf.StubPeriod.LONGFRONT11,
            self.LARGO_INICIO_12: qcf.StubPeriod.LONGFRONT12,
            self.LARGO_INICIO_13: qcf.StubPeriod.LONGFRONT13,
            self.LARGO_INICIO_14: qcf.StubPeriod.LONGFRONT14,
        }

        return switcher[self.value]


class YearFraction(StrEnum):
    """
    Identifica las distintas fracciones de año disponibles en `qcfinancial`.
    """

    ACT30 = auto()
    ACT360 = auto()
    ACT365 = auto()
    YF30360 = "30360"
    YF3030 = "3030"

    def as_qcf(self) -> qcf.QCYearFraction:
        """
        Retorna la fracción de año representada por `self` como el correspondiente objeto `QC_Financial_3`.
        """
        switcher = {
            YearFraction.ACT30: qcf.QCAct30,
            YearFraction.ACT360: qcf.QCAct360,
            YearFraction.ACT365: qcf.QCAct365,
            YearFraction.YF30360: qcf.QC30360,
            YearFraction.YF3030: qcf.QC3030,
        }

        return switcher[self]()


class WealthFactor(Enum):
    """
    Identifica los distintos factores de capitalización disponibles en `qcfinancial`.
    """

    COM = auto()
    LIN = auto()
    CON = auto()

    def as_qcf(self) -> qcf.QCWealthFactor:
        """
        Retorna el factor de capitalización representado por `self` como el correspondiente objeto `QC_Financial`.
        """
        switcher = {
            WealthFactor.COM: qcf.QCCompoundWf,
            WealthFactor.LIN: qcf.QCLinearWf,
            WealthFactor.CON: qcf.QCContinousWf,
        }

        return switcher[self]()


class TypeOfRate(str, Enum):
    """
    `Enum` que identifica distintos tipos de tasa (factor de capitalización + fracción de año).

    La clase hereda también de `str` lo que permite construir el objeto con los siguientes `str`:

    - 'LIN_ACT/360'
    - 'LIN_30/360'
    - 'LIN_ACT/365'
    - 'LIN_ACT/30'
    - 'COM_ACT/365'
    - 'COM_ACT/360'
    - 'COM_30/360'
    - 'CON_ACT/365'
    """

    LINACT360 = "LIN_ACT/360"
    LIN30360 = "LIN_30/360"
    LINACT365 = "LIN_ACT/365"
    LINACT30 = "LIN_ACT/30"
    COMACT365 = "COM_ACT/365"
    COMACT360 = "COM_ACT/360"
    COM30360 = "COM_30/360"
    CONACT365 = "CON_ACT/365"

    def as_qcf(self):
        """
        Retorna `self` en formato `Qcf.QCInterestRate`. El valor de la tasa es 0.
        """
        switcher = {
            self.LINACT360: qcf.QCInterestRate(
                0.0,
                YearFraction.ACT360.as_qcf(),
                WealthFactor.LIN.as_qcf(),
            ),
            self.LIN30360: qcf.QCInterestRate(
                0.0,
                YearFraction.YF30360.as_qcf(),
                WealthFactor.LIN.as_qcf(),
            ),
            self.LINACT365: qcf.QCInterestRate(
                0.0,
                YearFraction.ACT365.as_qcf(),
                WealthFactor.LIN.as_qcf(),
            ),
            self.LINACT30: qcf.QCInterestRate(
                0.0,
                YearFraction.ACT30.as_qcf(),
                WealthFactor.LIN.as_qcf(),
            ),
            self.COMACT365: qcf.QCInterestRate(
                0.0,
                YearFraction.ACT365.as_qcf(),
                WealthFactor.COM.as_qcf(),
            ),
            self.COMACT360: qcf.QCInterestRate(
                0.0,
                YearFraction.ACT360.as_qcf(),
                WealthFactor.COM.as_qcf(),
            ),
            self.COM30360: qcf.QCInterestRate(
                0.0,
                YearFraction.YF30360.as_qcf(),
                WealthFactor.COM.as_qcf(),
            ),
            self.CONACT365: qcf.QCInterestRate(
                0.0,
                YearFraction.ACT365.as_qcf(),
                WealthFactor.CON.as_qcf(),
            ),
        }
        return switcher[self.value]

    def as_qcf_with_value(self, rate_value: float):
        """
        Retorna `self` en formato `Qcf.QCInterestRate` con el valor de tasa especificado.

        Parameters:
        -----------
        rate_value: float
            El valor de la tasa

        Returns:
        --------
        `Qcf.QCInterestRate`.
        """
        result = self.as_qcf()
        result.set_value(rate_value)
        return result

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return self.__str__()


class AP(str, Enum):
    """
    Representa un Activo o un Pasivo.
    """

    A = "A"
    P = "P"

    def __str__(self):
        return str(self.value)

    def as_qcf(self):
        if self.value == "A":
            return qcf.RecPay.RECEIVE
        else:
            return qcf.RecPay.PAY


class FXRate(StrEnum):
    """
    Representa los distintos tipos de cambio disponibles en qcfinancial.
    """
    AUDAUD = auto()
    AUDUSD = auto()
    AUDCLP = auto()

    BRLBRL = auto()
    USDBRL = auto()
    BRLCLP = auto()

    CHFCHF = auto()
    USDCHF = auto()
    EURCHF = auto()
    CHFCLP = auto()

    CADCAD = auto()
    USDCAD = auto()
    CADCLP = auto()

    CLPCLP = auto()
    USDCLP = auto()

    CLFCLF = auto()
    USDCLF = auto()
    CLFCLP = auto()

    CNYCNY = auto()
    USDCNY = auto()
    CNYCLP = auto()

    COPCOP = auto()
    USDCOP = auto()
    COPCLP = auto()

    DKKDKK = auto()
    USDDKK = auto()
    DKKCLP = auto()

    EUREUR = auto()
    EURUSD = auto()
    EURCLP = auto()

    GBPGBP = auto()
    GBPUSD = auto()
    GBPCLP = auto()

    HKDHKD = auto()
    USDHKD = auto()
    HKDCLP = auto()

    JPYJPY = auto()
    USDJPY = auto()
    JPYCLP = auto()

    MXNMXN = auto()
    USDMXN = auto()
    MXNCLP = auto()

    NOKNOK = auto()
    USDNOK = auto()
    NOKCLP = auto()

    PENPEN = auto()
    USDPEN = auto()
    PENCLP = auto()

    SEKSEK = auto()
    USDSEK = auto()
    SEKCLP = auto()

    USDUSD = auto()

    def __str__(self):
        return str(self.value)

    @classmethod
    def mkt(cls, fx_rate: str):
        if len(fx_rate) != 6:
            raise ValueError(f"{fx_rate} is not a valid FX Rate")

        values = [str(v) for v in list(cls)]
        if fx_rate in values:
            return fx_rate
        if (flipped := f"{fx_rate[3:]}{fx_rate[0:3]}") in values:
            return flipped

        raise ValueError(f"{fx_rate} is not recognized")


@dataclass
class Tenor:
    agnos: NonNegativeInt
    meses: NonNegativeInt
    dias: NonNegativeInt

    def as_qcf(self):
        return qcf.Tenor(f"{self.agnos}Y{self.meses}M{self.dias}D")

    def __hash__(self):
        return self.dias + self.meses * 30 + self.agnos * 12 * 30

    def __lt__(self, other):
        return self.__hash__() < other.__hash__()


def build_tenor_from_str(tenor: str) -> Tenor:
    ten = qcf.Tenor(tenor)
    return Tenor(
        dias=ten.get_days(),
        meses=ten.get_months(),
        agnos=ten.get_years(),
    )


class Fecha(BaseModel):
    fecha: str | date | qcf.QCDate

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    @field_validator('fecha')
    @classmethod
    def valid_iso_format(cls, v: str | date | qcf.QCDate) -> str | date | qcf.QCDate:
        if isinstance(v, date) or isinstance(v, qcf.QCDate):
            return v
        try:
            qcf.build_qcdate_from_string(v)
        except Exception as e:
            raise ValueError(f"No es un formato iso de fecha válido. {str(e)}")
        return v

    def as_py_date(self):
        if isinstance(self.fecha, str):
            return datetime.strptime(self.fecha, "%Y-%m-%d").date()
        elif isinstance(self.fecha, qcf.QCDate):
            self.fecha = self.fecha.iso_code()
            return self.as_py_date()
        else:
            return self.fecha

    def as_qcf(self):
        if isinstance(self.fecha, str):
            return qcf.build_qcdate_from_string(self.fecha)
        elif isinstance(self.fecha, qcf.QCDate):
            return self.fecha
        else:
            self.fecha = self.fecha.isoformat()
            return self.as_qcf()

    def as_tag(self):
        if isinstance(self.fecha, str):
            return self.fecha.replace("-", "")
        elif isinstance(self.fecha, qcf.QCDate):
            self.fecha = self.fecha.iso_code()
            return self.as_tag()
        else:
            self.fecha = self.fecha.isoformat()
            return self.as_tag()

    def iso_format(self):
        return self.as_py_date().isoformat()

    def __hash__(self):
        return hash(self.fecha)


def qcf_date_to_py_date(qcf_date: qcf.QCDate) -> date:
    """
    Convierte un objeto `Qcf.Date` en un objeto `datetime.date`.
    """
    dd = qcf_date.day()
    mm = qcf_date.month()
    yy = qcf_date.year()

    return date(yy, mm, dd)


def qcf_leg_as_dataframe(pata: qcf.Leg):
    """
    Envuelve los flujos de un objeto qcf.Leg en un pandas.DataFrame.
    """
    tabla = []
    for i in range(0, pata.size()):
        tabla.append(qcf.show(pata.get_cashflow_at(i)))
    c = list(qcf.get_column_names(pata.get_cashflow_at(0).get_type()))
    dff = pd.DataFrame(tabla, columns=c)
    return dff
