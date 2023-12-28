from pydantic import BaseModel
from datetime import date
import pandas as pd

from .market_data import FxRateIndexHandler, CurveHandler
import qcfinancial as qcf


class MarketData(BaseModel):
    """
    Almacena los datos de mercado necesarios para el fixing y cálculo de valor presente.

    Parameters
    ----------
    process_date: date
        Fecha a la que se efectuará la valorización.

    calendars: Dict[str, Qcf.BusinessCalendar]
        `Dict` con los distintos calendarios requeridos en la valorización. La `key` del `Dict` corresponde
        al nombre del calendario en Front Desk.

    historic_index_values: Dict[str, pd.DataFrame]
        `Dict` con los valores históricos de los índices de tasa de interés y tipo de cambio.

    fx_rate_index_values: FxRateIndexHandler
        Valores a `process_date` de los índices FX a utilizar en la valorización.

    zero_coupon_curves: CurveHandler
        Valores a `process_date` de las curvas cero cupón a utilizar para valorizar.

    Attributes
    ----------
    Los parámetros anteriores se almacenan en variables del mismo nombre y tipo.
    """

    process_date: date
    calendars: dict[str, qcf.BusinessCalendar]
    historic_index_values: dict[str, tuple[pd.DataFrame, qcf.time_series]]
    fx_rate_index_values: FxRateIndexHandler
    zero_coupon_curves: CurveHandler

    class Config:
        """
        Para `pydantic` establece:

        `arbitrary_types_allowed = True`
        """

        arbitrary_types_allowed = True

    def get_index_value(self, which_date: date, index_code: str) -> float:
        """
        Retorna el valor de un índice de tasa de interés a una fecha dada.
        """
        if index_code in config.synth_fx_rate_index_names:
            return self.__get_synth_index_value(which_date, index_code)
        else:
            try:
                result = self.historic_index_values[index_code][0].loc[
                    which_date.isoformat()
                ]
                result = result.value
            except Exception as e:
                result = 0.0
            return result

    def get_zero_coupon_curve(
            self, curve_code: str, use_scenario: bool = False
    ) -> tuple[pd.DataFrame, qcf.ZeroCouponCurve]:
        """
        Retorna la curva cupón cero dado un cierto código de curva. Si no se encuentra el código de la curva
        se levantará una excepción.

        Parameters
        ----------
        curve_code: str
            Código de la curva en Front Desk.

        use_scenario: bool
            Si es True entonces se usan las curvas del último escenario calculado, si es False se usan las curvas base.

        Returns
        -------
        Tuple[pd.DataFrame, qcf.ZeroCouponCurve]
        """
        if curve_code not in self.zero_coupon_curves.zero_coupon_curves:
            raise ValueError(f"En StaticData no se encuentra la curva {curve_code}.")
        if use_scenario:
            return self.zero_coupon_curves.get_scenario()[curve_code]
        else:
            return self.zero_coupon_curves[curve_code]

    def get_fx_rate_index_value(
            self, fx_rate_index_code: str, use_scenario: bool = False
    ) -> float:
        """
        Retorna el valor a fecha de proceso de un FX Rate Index.

        Parameters
        ----------
        fx_rate_index_code: str
            Código del FX Rate Index cuto valor se quiere obtener.

        use_scenario: bool
            Si True, se debe utilizar el valor registrado en el último escenario aplicado. Si False se debe utilizar
            los valores base.

        Returns
        -------
        float:
            El valor del índice FX solicitado.
        """
        return self.fx_rate_index_values.get_fx_rate_index_value(
            fx_rate_index_code, use_scenario
        )

    def __get_synth_index_value(self, which_date: date, which_index: str) -> float:
        """
        Retorna el valor de un índice sintético a una fecha. Se asume que la fecha se refiere a la fecha de
        settlement en la que se utilizará el índice.

        Args:
            which_date: fecha de medición del índice, se refiere a la fecha de settlement en que se aplicará el índice.
            which_index: código del índice sintético de tipo OBSX_UFY.

        Returns:
            float: el valor del índice a la fecha requerida según su definición.
        """
        private_config = {
            "OBS2_UF0": {
                "calendar": "NY-SCL",
                "index1": "USDOBS",
                "index1_days": -2,
                "index2": "UF",
                "index2_days": 0,
                "composition": lambda val1, val2: val1 / val2,
            },
            "OBS1_UF0": {
                "calendar": "NY-SCL",
                "index1": "USDOBS",
                "index1_days": -1,
                "index2": "UF",
                "index2_days": 0,
                "composition": lambda val1, val2: val1 / val2,
            },
            "OBS0_UF0": {
                "calendar": "NY-SCL",
                "index1": "USDOBS",
                "index1_days": 0,
                "index2": "UF",
                "index2_days": 0,
                "composition": lambda val1, val2: val1 / val2,
            },
        }

        calendar = self.calendars[private_config[which_index]["calendar"]]
        fecha = qcw.Fecha(fecha=which_date.isoformat())

        new_date = qcw.Fecha(
            fecha=calendar.shift(
                fecha.as_qcf(), private_config[which_index]["index1_days"]
            ).iso_code()
        )

        index1 = self.get_index_value(
            new_date.as_py_date(),
            private_config[which_index]["index1"],
        )

        new_date = qcw.Fecha(
            fecha=calendar.shift(
                fecha.as_qcf(), private_config[which_index]["index2_days"]
            ).iso_code()
        )

        index2 = self.get_index_value(
            new_date.as_py_date(),
            private_config[which_index]["index2"],
        )
        if index1 > 0 and index2 > 0:
            return private_config[which_index]["composition"](index1, index2)
        else:
            msg = f"Index {private_config[which_index]['index1']} or {private_config[which_index]['index2']} not found."
            raise ValueError(msg)


def build_market_data(
        process_date: date,
        initial_date: date,
        fx_rate_indices: list[str],
        ir_indices: list[str],
        codigos_curvas: List[str],
        source: MarketDataSource,
) -> MarketData:
    """
    Método factoría que retorna una instancia de `MarketData`. Recordar que `MarketData` almacena los datos necesarios
    para efectuar una valorización.

    Parameters
    ----------
    process_date: date
        Fecha a la que se realizará la valorización.

    initial_date: date
        Fecha más antigua utilizada para los valores de los índices de tasa de interés.

    codigos_curvas: List[str]
        Códigos de las curvas a construir.

    is_prod: bool
        Si True se accede a Front Desk producción, Si no, a Front Desk desarrollo.

    source: Source
        Permite elegir cuál de las fuentes disponibles de datos de mercado utilizar.

    fx_rate_indices: (list[str])
        Lista con los nombres de los FX Rate Índices a consultar.

    ir_indices: (list[str]])
        Lista con los nombres de los IR Índices a consultar.

    """
    calendars = source.get_calendars(initial_date, )
    historic_index_values = source.get_index_values(
        initial_date,
        process_date,
        ir_indices,
        fx_rate_indices,
    )
    fx_rate_index_values = {}
    qcf_process_date = qcf.build_qcdate_from_string(process_date.isoformat())

    for code in fx_rate_indices:
        value = historic_index_values[code][1][qcf_process_date]
        fx_rate_index_values[code] = value

    fx_rate_index_handler = FxRateIndexHandler(
        process_date=process_date,
        fx_rate_index_values=fx_rate_index_values,
    )

    curve_handler = CurveHandler(
        process_date=process_date,
        zero_coupon_curves=source.get_zero_coupon_curves(process_date, codigos_curvas),
    )

    return MarketData(
        process_date=process_date,
        calendars=calendars,
        historic_index_values=historic_index_values,
        fx_rate_index_values=fx_rate_index_handler,
        zero_coupon_curves=curve_handler,
    )

