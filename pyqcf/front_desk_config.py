# Se configura parametría asociada a Front Desk.
# TODO: esto debe alimentarse desde Front Desk y no estar en duro.

import sys
from enum import Enum
from typing import Dict, Union

if sys.platform in ["win32", "darwin"]:
    import qcfinancial as qcf
else:
    import qc_financial as qcf

from . import wrappers as qcw

fx_rate_index_names = [
    "USDCLP_RC",
    "1CLP",
    "EURCLP_RC",
    "1EUR",
    "CHFCLP_RC",
    "1CHF",
    "JPYCLP_RC",
    "1JPY",
    "GBPCLP_RC",
    "1GBP",
    "COPCLP_RC",
    "1COP",
    "UF",
    "1CLF",
    "CNYCLP_RC",
    "1CNY",
    "CADCLP_RC",
    "1CAD",
    "USDOBS",
    "USDCLF_RC",
]

synth_fx_rate_index_names = [
    "OBS2_UF0",
    "OBS1_UF0",
    "OBS0_UF0",
]


class FXRateIndex(str, Enum):
    USDCLP_RC = "USDCLP_RC"
    UNO_CLP = "1CLP"
    EURCLP_RC = "EURCLP_RC"
    UNO_EUR = "1EUR"
    CHFCLP_RC = "CHFCLP_RC"
    UNO_CHF = "1CHF"
    JPYCLP_RC = "JPYCLP_RC"
    UNO_JPY = "1JPY"
    GBPCLP_RC = "GBPCLP_RC"
    UNO_GBP = "1GBP"
    COPCLP_RC = "COPCLP_RC"
    UNO_COP = "1COP"
    UF = "UF"
    UNO_CLF = "1CLF"
    CNYCLP_RC = "CNYCLP_RC"
    UNO_CNY = "1CNY"
    CADCLP_RC = "CADCLP_RC"
    UNO_CAD = "1CAD"
    USDOBS = "USDOBS"
    USDCLF_RC = "USDCLF_RC"

    # --- Synthetic FX Rate Indices ---
    OBS2_UF0 = "OBS2_UF0"
    OBS1_UF0 = "OBS1_UF0"
    OBS0_UF0 = "OBS0_UF0"

    def as_qcf(self, calendars: Dict[str, qcf.BusinessCalendar]):
        usd = qcw.Currency("USD").as_qcf()
        clp = qcw.Currency("CLP").as_qcf()
        clf = qcw.Currency("CLF").as_qcf()

        usdclp = qcf.FXRate(usd, clp)
        clfclp = qcf.FXRate(clf, clp)
        usdclf = qcf.FXRate(usd, clf)

        switcher = {
            "USDOBS": qcf.FXRateIndex(
                usdclp,
                "USDOBS",
                qcf.Tenor("1D"),
                qcf.Tenor("1D"),
                calendars["SCL"],
            ),
            "UF": qcf.FXRateIndex(
                clfclp,
                "UF",
                qcf.Tenor("0D"),
                qcf.Tenor("0D"),
                calendars["SCL"],
            ),
            "USDCLP_RC": qcf.FXRateIndex(
                clfclp,
                "USDCLP_RC",
                qcf.Tenor("0D"),
                qcf.Tenor("0D"),
                calendars["SCL"],
            ),
            "USDCLF_RC": qcf.FXRateIndex(
                usdclf,
                "USDCLF_RC",
                qcf.Tenor("0D"),
                qcf.Tenor("0D"),
                calendars["SCL"],
            ),
            "OBS1_UF0": qcf.FXRateIndex(
                usdclf,
                "OBS1_UF0",
                qcf.Tenor("0D"),
                qcf.Tenor("0D"),
                calendars["NY-SCL"],
            ),
            "OBS2_UF0": qcf.FXRateIndex(
                usdclf,
                "OBS2_UF0",
                qcf.Tenor("0D"),
                qcf.Tenor("0D"),
                calendars["NY-SCL"],
            ),
            "OBS0_UF0": qcf.FXRateIndex(
                usdclf,
                "OBS0_UF0",
                qcf.Tenor("0D"),
                qcf.Tenor("0D"),
                calendars["NY-SCL"],
            ),
        }

        return switcher.get(self.value, self.value)


which_fx_rate_index = {
    "CLP": "1CLP",
    "USD": "USDCLP_RC",
    "EUR": "EURCLP_RC",
    "CHF": "CHFCLP_RC",
    "JPY": "JPYCLP_RC",
    "GBP": "GBPCLP_RC",
    "COP": "COPCLP_RC",
    "CLF": "UF",
    "CNY": "CNYCLP_RC",
    "CAD": "CADCLP_RC",
}


which_calendars = [
    "SCL",
    "LONDON",
    "NEW_YORK",
    "SCL-LONDON",
    "NY-LONDON",
    "NY-LONDON-SCL",
    "NY-SCL",
    "SIFMAUS",
]


calendar_aliases = {
    "NEW YORK": "NEW_YORK",
}

interest_rate_index_names = [
    "US0006M",
    "US0003M",
    "US0012M",
    "US0001M",
    "EURIBOR6M",
    "TAB-90-UF",
    "TAB-180-UF",
    "TAB-360-UF",
    "TAB-30-CLP",
    "TAB-90-CLP",
    "TAB-180-CLP",
    "TAB-360-CLP",
    "ICPCLP",
    "SOFRINDX",
    "SOFRRATE",
    "TERMSOFR6M",
]


interest_rate_index_aliases = {
    "TAB_90_UF": "TAB-90-UF",
    "TAB_180_UF": "TAB-180-UF",
    "TAB_360_UF": "TAB-360-UF",
    "TAB_30_CLP": "TAB-30-CLP",
    "TAB_90_CLP": "TAB-90-CLP",
    "TAB_180_CLP": "TAB-180-CLP",
    "TAB_360_CLP": "TAB-360-CLP",
}

contrapartes_col_usd = {
    "97006000-6": "BCI",
    "97036000-K": "SANTANDER",
    "97023000-9": "ITAU CORPBANCA",
    "97018000-1": "SCOTIABANK",
    "97043000-8": "JP MORGAN",
    "463182828-6": "GOLDMAN",
    "404286240-7": "BBVA NY",
    "453423276-K": "MERRIL LYNCH INT LONDON",
    "99500410-0": "BANCO CONSORCIO",
    "99012000-5": "CIA SEG VIDA CONSORCIO NAC SEG VIDA S.A.",
    "96772490-4": "CONSORCIO CORREDORES DE BOLSA",
    "97032000-8": "BANCO BILBAO VIZCAYA ARGENTARIA CHILE",
    "96579280-5": "CN LIFE COMPAÑIA DE SEGUROS DE VIDA S.A.",
    "97004000-5": "BANCO DE CHILE",
    "97008000-7": "Citibank NA",
    "96519800-8": "BCI CORREDOR DE BOLSA S.A.",
    "414935828-0": "CITIBANK NEW YORK",
}

codigos_curvas_derivados = [
    "CSOFR",
    "CFF",
    "CL3M",
    "CL6M",
    "CCLPCOLUSD",
    "CICPCLP",
    "CCLFCOLUSD",
    "CCLFCOLCLP",
    "CUSDCOLCLP",
    "CTABCLF",
    "CEURIBOR6M",
    "CEURCOLUSD",
    "CEURCOLCLP",
    "CCNYCOLUSD",
    "CCNYCOLCLP",
    # "FWDJPY-__RIESGO__",
]


crv_desc_col_usd = {
    "USD": "CFF",
    "CLP": "CCLPCOLUSD",
    "CLF": "CCLFCOLUSD",
    "EUR": "CEURCOLUSD",
    "CNY": "CCNYCOLUSD",
    "JPY": "FWDJPY-__RIESGO__",
}


crv_desc_no_col = {
    "USD": "CUSDCOLCLP",
    "CLP": "CICPCLP",
    "CLF": "CCLFCOLCLP",
    "EUR": "CEURCOLCLP",
    "CNY": "CCNYCOLCLP",
    "JPY": "FWDJPY-__RIESGO__",
}


crv_proy_irs = {
    "US0006M": "CL6M",
    "US0003M": "CL3M",
    "US0012M": "CL6M",
    "EURIBOR6M": "CEURIBOR6M",
    "TAB-360-UF": "CTABCLF",
    "TAB-90-UF": "CTABCLF",
    "ICPCLP": "CICPCLP",
    "SOFRINDX": "CSOFR",
    "SOFRRATE": "CSOFR",
    "TERMSOFR6M": "CSOFR",
}


class InterestRateIndex(str, Enum):
    """
    Representa los índices de tasa de interés disponibles en Front Desk.
    """

    US0001M = "US0001M"
    US0003M = "US0003M"
    US0006M = "US0006M"
    US0012M = "US0012M"
    EURIBOR6M = "EURIBOR6M"
    TAB_90_UF = "TAB-90-UF"
    TAB_180_UF = "TAB-180-UF"
    TAB_360_UF = "TAB-360-UF"
    TAB_30_CLP = "TAB-30-CLP"
    TAB_90_CLP = "TAB-90-CLP"
    TAB_180_CLP = "TAB-180-CLP"
    TAB_360_CLP = "TAB-360-CLP"
    SOFRINDX = "SOFRINDX"
    SOFRRATE = "SOFRRATE"
    ICPCLP = "ICPCLP"
    ICPCLF = "ICPCLF"
    NOIRINDX = ("NOIRINDX",)
    TERMSOFR1M = ("TERMSOFR1M",)
    TERMSOFR3M = ("TERMSOFR3M",)
    TERMSOFR6M = ("TERMSOFR6M",)
    TERMSOFR1Y = "TERMSOFR1Y"

    def as_qcf(
        self, calendars: Dict[str, qcf.BusinessCalendar]
    ) -> Union[qcf.InterestRateIndex, str]:
        """
        Retorna `self` en formato `Qcf.InterestRateIndex`.
        """
        lin_act360 = qcw.TypeOfRate.LINACT360.as_qcf()
        usd = qcw.Currency("USD").as_qcf()
        clp = qcw.Currency("CLP").as_qcf()
        clf = qcw.Currency("CLF").as_qcf()
        eur = qcw.Currency("EUR").as_qcf()

        switcher = {
            "US0001M": qcf.InterestRateIndex(
                "US0001M",
                lin_act360,
                qcf.Tenor("2d"),
                qcf.Tenor("1m"),
                calendars["LONDON"],
                calendars["LONDON"],
                usd,
            ),
            "US0003M": qcf.InterestRateIndex(
                "US0003M",
                lin_act360,
                qcf.Tenor("2d"),
                qcf.Tenor("3m"),
                calendars["LONDON"],
                calendars["LONDON"],
                usd,
            ),
            "US0006M": qcf.InterestRateIndex(
                "US0006M",
                lin_act360,
                qcf.Tenor("2d"),
                qcf.Tenor("6m"),
                calendars["LONDON"],
                calendars["LONDON"],
                usd,
            ),
            "US0012M": qcf.InterestRateIndex(
                "US0012M",
                lin_act360,
                qcf.Tenor("2d"),
                qcf.Tenor("12m"),
                calendars["LONDON"],
                calendars["LONDON"],
                usd,
            ),
            "EURIBOR6M": qcf.InterestRateIndex(
                "EURIBOR6M",
                lin_act360,
                qcf.Tenor("2d"),
                qcf.Tenor("6m"),
                calendars["LONDON"],
                calendars["LONDON"],
                eur,
            ),
            "TAB-90-UF": qcf.InterestRateIndex(
                "TAB-90-UF",
                lin_act360,
                qcf.Tenor("0d"),
                qcf.Tenor("3m"),
                calendars["SCL"],
                calendars["SCL"],
                clf,
            ),
            "TAB-180-UF": qcf.InterestRateIndex(
                "TAB-180-UF",
                lin_act360,
                qcf.Tenor("0d"),
                qcf.Tenor("6m"),
                calendars["SCL"],
                calendars["SCL"],
                clf,
            ),
            "TAB-360-UF": qcf.InterestRateIndex(
                "TAB-360-UF",
                lin_act360,
                qcf.Tenor("0d"),
                qcf.Tenor("12m"),
                calendars["SCL"],
                calendars["SCL"],
                clf,
            ),
            "TAB-30-CLP": qcf.InterestRateIndex(
                "TAB-30-CLP",
                lin_act360,
                qcf.Tenor("0d"),
                qcf.Tenor("1m"),
                calendars["SCL"],
                calendars["SCL"],
                clp,
            ),
            "TAB-90-CLP": qcf.InterestRateIndex(
                "TAB-90-CLP",
                lin_act360,
                qcf.Tenor("0d"),
                qcf.Tenor("3m"),
                calendars["SCL"],
                calendars["SCL"],
                clp,
            ),
            "TAB-180-CLP": qcf.InterestRateIndex(
                "TAB-180-CLP",
                lin_act360,
                qcf.Tenor("0d"),
                qcf.Tenor("6m"),
                calendars["SCL"],
                calendars["SCL"],
                clp,
            ),
            "TAB-360-CLP": qcf.InterestRateIndex(
                "TAB-360-CLP",
                lin_act360,
                qcf.Tenor("0d"),
                qcf.Tenor("1y"),
                calendars["SCL"],
                calendars["SCL"],
                clp,
            ),
            "SOFRRATE": qcf.InterestRateIndex(
                "SOFRRATE",
                lin_act360,
                qcf.Tenor("0d"),
                qcf.Tenor("1d"),
                calendars["SIFMAUS"],
                calendars["SIFMAUS"],
                usd,
            ),
            "SOFRINDX": qcf.InterestRateIndex(
                "SOFRINDX",
                lin_act360,
                qcf.Tenor("0d"),
                qcf.Tenor("1d"),
                calendars["SIFMAUS"],
                calendars["SIFMAUS"],
                usd,
            ),
            "ICPCLP": qcf.InterestRateIndex(
                "ICPCLP",
                lin_act360,
                qcf.Tenor("0d"),
                qcf.Tenor("1d"),
                calendars["SCL"],
                calendars["SCL"],
                clp,
            ),
            "ICPCLF": qcf.InterestRateIndex(
                "ICPCLF",
                lin_act360,
                qcf.Tenor("0d"),
                qcf.Tenor("1d"),
                calendars["SCL"],
                calendars["SCL"],
                clp,
            ),
            "TERMSOFR1M": qcf.InterestRateIndex(
                "TERMSOFR1M",
                lin_act360,
                qcf.Tenor("2d"),
                qcf.Tenor("1m"),
                calendars["NEW_YORK"],
                calendars["NEW_YORK"],
                usd,
            ),
            "TERMSOFR3M": qcf.InterestRateIndex(
                "TERMSOFR3M",
                lin_act360,
                qcf.Tenor("2d"),
                qcf.Tenor("3m"),
                calendars["NEW_YORK"],
                calendars["NEW_YORK"],
                usd,
            ),
            "TERMSOFR6M": qcf.InterestRateIndex(
                "TERMSOFR6M",
                lin_act360,
                qcf.Tenor("2d"),
                qcf.Tenor("6m"),
                calendars["NEW_YORK"],
                calendars["NEW_YORK"],
                usd,
            ),
            "TERMSOFR1Y": qcf.InterestRateIndex(
                "TERMSOFR1Y",
                lin_act360,
                qcf.Tenor("2d"),
                qcf.Tenor("1y"),
                calendars["NEW_YORK"],
                calendars["NEW_YORK"],
                usd,
            ),
        }

        return switcher.get(self.value, self.value)
