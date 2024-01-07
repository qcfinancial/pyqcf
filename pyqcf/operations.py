from pydantic import (
    BaseModel,
    field_validator,
    model_validator,
    Field,
    ConfigDict,
    field_serializer,
    PositiveInt,
)

from strenum import StrEnum
from itertools import cycle
from typing import (
    Union,
    Any,
)
from enum import auto
import re

import qcfinancial as qcf

from . import wrappers as qcw
from . import config


class Rut(BaseModel):
    rut: int = Field(ge=0)
    dv: str

    @field_validator('dv')
    @classmethod
    def validate_dv(cls, value: str) -> str:
        if not re.match(r'^[0-9K]$', value):
            raise ValueError('Field can only contain a single character: a digit 0-9 or the character "K"')
        return value

    @model_validator(mode='after')
    def digito_verificador(self):
        reversed_digits = map(int, reversed(str(self.rut)))
        factors = cycle(range(2, 8))
        s = sum(d * f for d, f in zip(reversed_digits, factors))
        check = (-s) % 11 if (-s) % 11 < 10 else 'K'
        if str(check) != self.dv:
            raise ValueError('The data entered is not a valid Chilean RUT.')
        return self

    def __repr__(self):
        return f"{self.rut}-{self.dv}"

    def __str__(self):
        return f"{self.rut}-{self.dv}"


class InitialNotional(BaseModel):
    initial_notional: float


class CustomNotionalAmort(BaseModel):
    custom_notional_amort: list[tuple[float, float]]

    def as_qcf(self) -> qcf.CustomNotionalAmort:
        cna = qcf.CustomNotionalAmort(len(self.custom_notional_amort))
        for i in range(len(self.custom_notional_amort)):
            cna.set_notional_amort_at(
                i,
                self.custom_notional_amort[i][0],
                self.custom_notional_amort[i][1],
            )
        return cna


class TypeOfAmortization(StrEnum):
    """
    Representa los tipos de amortización en Front Desk.
    """
    BULLET = auto()
    CONSTANT = auto()
    CUSTOM = auto()


class Product(StrEnum):
    """
    Representa los tres tipos de producto swap disponibles en Front Desk.
    """
    SWAP_ICP = auto()
    SWAP_TASA = auto()
    SWAP_MONE = auto()


class SettlementMechanism(StrEnum):
    """
    Representa liquidación por compensación (C) y por entrega física (E).
    """
    C = auto()
    E = auto()


class TypeOfLeg(StrEnum):
    """
    Representa los tipos de patas en Front Desk.
    """
    FIXED_RATE = auto()
    FIXED_RATE_MCCY = auto()
    IBOR = auto()
    IBOR_MCCY = auto()
    OVERNIGHT_INDEX = auto()
    OVERNIGHT_INDEX_MCCY = auto()
    COMPOUNDED_OVERNIGHT_RATE = auto()
    COMPOUNDED_OVERNIGHT_RATE_MCCY = auto()
    ICP_CLF = auto()

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)


class MultiCurrencyModel(BaseModel):
    settlement_currency: qcw.Currency
    fx_rate_index_name: str
    fx_fixing_lag: int = Field(ge=0)


# ----------- Leg Generators -----------------------------------------------

class FixedRateLegGenerator(BaseModel):
    """
    Almacena los parámetros necesarios para dar de alta una pata con flujos de tipo
    `qcfinancial.FixedRateCashflow`.
    """
    rp: qcw.AP
    start_date: qcw.Fecha
    end_date: qcw.Fecha
    maturity: qcw.Tenor
    bus_adj_rule: qcw.BusAdjRules
    periodicity: qcw.Tenor
    stub_period: qcw.StubPeriods
    settlement_calendar: str
    settlement_lag: int = Field(ge=0)
    type_of_amortization: TypeOfAmortization
    notional_or_custom: InitialNotional | CustomNotionalAmort
    amort_is_cashflow: bool = True
    coupon_rate_value: float
    coupon_rate_type: qcw.TypeOfRate
    notional_currency: qcw.Currency
    is_bond: bool = False

    @field_serializer('start_date', 'end_date')
    def serialize_date(self, dt: qcw.Fecha):
        return dt.fecha

    def custom_dump(self, type_of_amortization: TypeOfAmortization):
        result = self.model_dump()
        if type_of_amortization == TypeOfAmortization.BULLET:
            result["initial_notional"] = result.pop("notional_or_custom")["initial_notional"]
        else:
            result["custom_notional_amort"] = result.pop("notional_or_custom")["custom_notional_amort"]
        return result


class IborLegGenerator(BaseModel):
    """
    Almacena los datos necesarios para construir una pata de tipo Ibor.
    """
    rp: qcw.AP
    start_date: qcw.Fecha
    end_date: qcw.Fecha
    maturity: qcw.Tenor
    bus_adj_rule: qcw.BusAdjRules
    settlement_periodicity: qcw.Tenor
    settlement_stub_period: qcw.StubPeriods
    settlement_calendar: str
    settlement_lag: int = Field(ge=0)
    type_of_amortization: TypeOfAmortization
    fixing_periodicity: qcw.Tenor
    fixing_stub_period: qcw.StubPeriods
    fixing_calendar: str
    fixing_lag: int = Field(ge=0)
    interest_rate_index_name: str
    notional_or_custom: InitialNotional | CustomNotionalAmort
    amort_is_cashflow: bool
    notional_currency: qcw.Currency
    spread: float
    gearing: float

    @field_serializer('start_date', 'end_date')
    def serialize_date(self, dt: qcw.Fecha):
        return dt.fecha

    @field_validator('interest_rate_index_name')
    @classmethod
    def replace_spaces(cls, value: str) -> str:
        return value.replace(" ", "-")

    def custom_dump(self, type_of_amortization: TypeOfAmortization):
        result = self.model_dump()
        if type_of_amortization == TypeOfAmortization.BULLET:
            result["initial_notional"] = result.pop("notional_or_custom")["initial_notional"]
        else:
            result["custom_notional_amort"] = result.pop("notional_or_custom")["custom_notional_amort"]
        return result


class OvernightIndexLegGenerator(BaseModel):
    rp: qcw.AP
    start_date: qcw.Fecha
    end_date: qcw.Fecha
    maturity: qcw.Tenor  # NO al constructor de cqf
    bus_adj_rule: qcw.BusAdjRules
    fix_adj_rule: qcw.BusAdjRules
    settlement_periodicity: qcw.Tenor
    settlement_stub_period: qcw.StubPeriods
    settlement_calendar: str
    settlement_lag: int = Field(ge=0)
    fixing_calendar: str
    type_of_amortization: TypeOfAmortization  # NO al constructor de cqf
    overnight_index_name: str
    interest_rate: qcw.TypeOfRate
    eq_rate_decimal_places: PositiveInt
    notional_or_custom: InitialNotional | CustomNotionalAmort
    amort_is_cashflow: bool
    notional_currency: qcw.Currency
    spread: float
    gearing: float

    @field_serializer('start_date', 'end_date')
    def serialize_date(self, dt: qcw.Fecha):
        return dt.fecha

    def custom_dump(self, type_of_amortization: TypeOfAmortization):
        result = self.model_dump()
        if type_of_amortization == TypeOfAmortization.BULLET:
            result["initial_notional"] = result.pop("notional_or_custom")["initial_notional"]
        else:
            result["custom_notional_amort"] = result.pop("notional_or_custom")["custom_notional_amort"]
        return result


class IcpClfLegGenerator(BaseModel):
    rp: qcw.AP
    start_date: qcw.Fecha
    end_date: qcw.Fecha
    maturity: qcw.Tenor  # NO al constructor de cqf
    bus_adj_rule: qcw.BusAdjRules
    settlement_periodicity: qcw.Tenor
    settlement_stub_period: qcw.StubPeriods
    settlement_calendar: str
    settlement_lag: int = Field(ge=0)
    type_of_amortization: TypeOfAmortization  # NO al constructor de cqf
    overnight_index_name: str  # NO al constructor de cqf
    notional_or_custom: InitialNotional | CustomNotionalAmort
    amort_is_cashflow: bool
    spread: float
    gearing: float

    @field_serializer('start_date', 'end_date')
    def serialize_date(self, dt: qcw.Fecha):
        return dt.fecha

    def custom_dump(self, type_of_amortization: TypeOfAmortization):
        result = self.model_dump()
        if type_of_amortization == TypeOfAmortization.BULLET:
            result["initial_notional"] = result.pop("notional_or_custom")["initial_notional"]
        else:
            result["custom_notional_amort"] = result.pop("notional_or_custom")["custom_notional_amort"]
        return result


class CompoundedOvernightRateLegGenerator(BaseModel):
    rp: qcw.AP
    start_date: qcw.Fecha
    end_date: qcw.Fecha
    maturity: qcw.Tenor
    bus_adj_rule: qcw.BusAdjRules
    settlement_periodicity: qcw.Tenor
    settlement_stub_period: qcw.StubPeriods
    settlement_calendar: str
    settlement_lag: int = Field(ge=0)
    type_of_amortization: TypeOfAmortization
    fixing_calendar: str
    overnight_rate_name: str
    notional_or_custom: InitialNotional | CustomNotionalAmort
    amort_is_cashflow: bool
    notional_currency: qcw.Currency
    spread: float
    gearing: float
    interest_rate_type: qcw.TypeOfRate
    eq_rate_decimal_places: int = Field(ge=0)
    lookback: int = Field(ge=0)
    lockout: int = Field(ge=0)

    @field_serializer('start_date', 'end_date')
    def serialize_date(self, dt: qcw.Fecha):
        return dt.fecha

    def custom_dump(self, type_of_amortization: TypeOfAmortization):
        result = self.model_dump()
        if type_of_amortization == TypeOfAmortization.BULLET:
            result["initial_notional"] = result.pop("notional_or_custom")["initial_notional"]
        else:
            result["custom_notional_amort"] = result.pop("notional_or_custom")["custom_notional_amort"]
        return result

# ------------- End Leg Generators ------------------------------------------


class LegModel(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
    type_of_leg: TypeOfLeg
    leg_number: int = Field(ge=0)

    def qcf_leg(self, all_calendars: dict[str, qcf.BusinessCalendar]) -> qcf.Leg:
        # This method is empty because it will be overriden in subclasses.
        pass

    def get_current_cashflow(self, fecha: qcw.Fecha, all_calendars: dict[str, qcf.BusinessCalendar]):
        qcdate = fecha.as_qcf()
        return [c for c in self.qcf_leg(all_calendars).get_cashflows() if c.get_start_date() <= qcdate < c.get_end_date()][0]


class FixedRateLegModel(LegModel):
    leg_generator: FixedRateLegGenerator

    def custom_dump(self):
        return {
            "type_of_leg": self.type_of_leg,
            "leg_number": self.leg_number,
            **self.leg_generator.custom_dump(
                self.leg_generator.type_of_amortization
            ),
        }

    def qcf_leg(self, all_calendars: dict[str, qcf.BusinessCalendar]) -> qcf.Leg:
        leg_gen = self.leg_generator
        parameters = {
            "rec_pay": leg_gen.rp.as_qcf(),
            "start_date": leg_gen.start_date.as_qcf(),
            "end_date": leg_gen.end_date.as_qcf(),
            "bus_adj_rule": leg_gen.bus_adj_rule.as_qcf(),
            "settlement_periodicity": leg_gen.periodicity.as_qcf(),
            "stub_period": leg_gen.stub_period.as_qcf(),
            "settlement_calendar": all_calendars[leg_gen.settlement_calendar],
            "settlement_lag": leg_gen.settlement_lag,
            "amort_is_cashflow": leg_gen.amort_is_cashflow,
            "interest_rate": leg_gen.coupon_rate_type.as_qcf_with_value(leg_gen.coupon_rate_value),
            "notional_currency": leg_gen.notional_currency.as_qcf(),
        }
        if leg_gen.type_of_amortization == 'BULLET':
            parameters["is_bond"] = leg_gen.is_bond
            parameters["initial_notional"] = leg_gen.notional_or_custom.initial_notional
            return qcf.LegFactory.build_bullet_fixed_rate_leg(**parameters)
        else:
            parameters["notional_and_amort"] = leg_gen.notional_or_custom.as_qcf()
            return qcf.LegFactory.build_custom_amort_fixed_rate_leg(**parameters)


class FixedRateMultiCurrencyLegModel(LegModel):
    leg_generator: FixedRateLegGenerator
    multi_currency: MultiCurrencyModel

    def custom_dump(self) -> dict[str, Any]:
        return {
            "type_of_leg": self.type_of_leg,
            "leg_number": self.leg_number,
            **self.leg_generator.custom_dump(
                self.leg_generator.type_of_amortization,
            ),
            **self.multi_currency.model_dump()
        }

    def qcf_leg(self, all_calendars: dict[str, qcf.BusinessCalendar]) -> qcf.Leg:
        leg_gen = self.leg_generator
        parameters = {
            "rec_pay": leg_gen.rp.as_qcf(),
            "start_date": leg_gen.start_date.as_qcf(),
            "end_date": leg_gen.end_date.as_qcf(),
            "bus_adj_rule": leg_gen.bus_adj_rule.as_qcf(),
            "settlement_periodicity": leg_gen.periodicity.as_qcf(),
            "stub_period": leg_gen.stub_period.as_qcf(),
            "settlement_calendar": all_calendars[leg_gen.settlement_calendar],
            "settlement_lag": leg_gen.settlement_lag,
            "amort_is_cashflow": leg_gen.amort_is_cashflow,
            "interest_rate": leg_gen.coupon_rate_type.as_qcf_with_value(leg_gen.coupon_rate_value),
            "notional_currency": leg_gen.notional_currency.as_qcf(),
            "is_bond": leg_gen.is_bond,
            "settlement_currency": self.multi_currency.settlement_currency.as_qcf(),
            "fx_rate_index": config.FXRateIndex(
                self.multi_currency.fx_rate_index_name
            ).as_qcf(calendars=all_calendars),
            "fx_rate_index_fixing_lag": self.multi_currency.fx_fixing_lag,
        }
        if leg_gen.type_of_amortization == 'BULLET':
            parameters["initial_notional"] = leg_gen.notional_or_custom.initial_notional
            return qcf.LegFactory.build_bullet_fixed_rate_mccy_leg(**parameters)
        else:
            parameters["notional_and_amort"] = leg_gen.notional_or_custom.as_qcf()
            return qcf.LegFactory.build_custom_amort_fixed_rate_mccy_leg(**parameters)


class IborLegModel(LegModel):
    leg_generator: IborLegGenerator

    def custom_dump(self) -> dict[str, Any]:
        return {
            "type_of_leg": self.type_of_leg,
            "leg_number": self.leg_number,
            **self.leg_generator.custom_dump(
                self.leg_generator.type_of_amortization,
            ),
        }

    def qcf_leg(self, all_calendars: dict[str, qcf.BusinessCalendar]) -> qcf.Leg:
        leg_gen = self.leg_generator
        parameters = {
            "rec_pay": leg_gen.rp.as_qcf(),
            "start_date": leg_gen.start_date.as_qcf(),
            "end_date": leg_gen.end_date.as_qcf(),
            "bus_adj_rule": leg_gen.bus_adj_rule.as_qcf(),
            "settlement_periodicity": leg_gen.settlement_periodicity.as_qcf(),
            "stub_period": leg_gen.settlement_stub_period.as_qcf(),
            "settlement_calendar": all_calendars[leg_gen.settlement_calendar],
            "settlement_lag": leg_gen.settlement_lag,
            "fixing_periodicity": leg_gen.fixing_periodicity.as_qcf(),
            "fixing_stub_period": leg_gen.fixing_stub_period.as_qcf(),
            "fixing_calendar": all_calendars[leg_gen.fixing_calendar],
            "fixing_lag": leg_gen.fixing_lag,
            "interest_rate_index": config.InterestRateIndex(leg_gen.interest_rate_index_name).as_qcf(
                calendars=all_calendars,
            ),
            "amort_is_cashflow": leg_gen.amort_is_cashflow,
            "notional_currency": leg_gen.notional_currency.as_qcf(),
            "spread": leg_gen.spread,
            "gearing": leg_gen.gearing,
        }
        if leg_gen.type_of_amortization == 'BULLET':
            parameters["initial_notional"] = leg_gen.notional_or_custom.initial_notional
            return qcf.LegFactory.build_bullet_ibor_leg(**parameters)
        else:
            parameters["notional_and_amort"] = leg_gen.notional_or_custom.as_qcf()
            return qcf.LegFactory.build_custom_amort_ibor_leg(**parameters)


class IborMultiCurrencyLegModel(LegModel):
    leg_generator: IborLegGenerator
    multi_currency: MultiCurrencyModel

    def custom_dump(self) -> dict[str, Any]:
        return {
            "type_of_leg": self.type_of_leg,
            "leg_number": self.leg_number,
            **self.leg_generator.custom_dump(TypeOfAmortization.CUSTOM),
            **self.multi_currency.model_dump()
        }

    def qcf_leg(self, all_calendars: dict[str, qcf.BusinessCalendar]) -> qcf.Leg:
        leg_gen = self.leg_generator
        parameters = {
            "rec_pay": leg_gen.rp.as_qcf(),
            "start_date": leg_gen.start_date.as_qcf(),
            "end_date": leg_gen.end_date.as_qcf(),
            "bus_adj_rule": leg_gen.bus_adj_rule.as_qcf(),
            "settlement_periodicity": leg_gen.settlement_periodicity.as_qcf(),
            "stub_period": leg_gen.settlement_stub_period.as_qcf(),
            "settlement_calendar": all_calendars[leg_gen.settlement_calendar],
            "settlement_lag": leg_gen.settlement_lag,
            "fixing_periodicity": leg_gen.fixing_periodicity.as_qcf(),
            "fixing_stub_period": leg_gen.fixing_stub_period.as_qcf(),
            "fixing_calendar": all_calendars[leg_gen.fixing_calendar],
            "fixing_lag": leg_gen.fixing_lag,
            "interest_rate_index": config.InterestRateIndex(leg_gen.interest_rate_index_name).as_qcf(
                calendars=all_calendars,
            ),
            "amort_is_cashflow": leg_gen.amort_is_cashflow,
            "notional_currency": leg_gen.notional_currency.as_qcf(),
            "spread": leg_gen.spread,
            "gearing": leg_gen.gearing,
            "settlement_currency": self.multi_currency.settlement_currency.as_qcf(),
            "fx_rate_index": config.FXRateIndex(self.multi_currency.fx_rate_index_name).as_qcf(
                calendars=all_calendars
            ),
            "fx_rate_index_fixing_lag": self.multi_currency.fx_fixing_lag,
        }
        if leg_gen.type_of_amortization == 'BULLET':
            parameters["initial_notional"] = leg_gen.notional_or_custom.initial_notional
            return qcf.LegFactory.build_bullet_ibor_mccy_leg(**parameters)
        else:
            parameters["notional_and_amort"] = leg_gen.notional_or_custom.as_qcf()
            return qcf.LegFactory.build_custom_amort_ibor_mccy_leg(**parameters)


class OvernightIndexLegModel(LegModel):
    leg_generator: OvernightIndexLegGenerator

    def custom_dump(self):
        return {
            "type_of_leg": self.type_of_leg,
            "leg_number": self.leg_number,
            **self.leg_generator.custom_dump(
                self.leg_generator.type_of_amortization,
            ),
        }

    def qcf_leg(self, all_calendars: dict[str, qcf.BusinessCalendar]) -> qcf.Leg:
        leg_gen = self.leg_generator
        parameters = {
            "rec_pay": leg_gen.rp.as_qcf(),
            "start_date": leg_gen.start_date.as_qcf(),
            "end_date": leg_gen.end_date.as_qcf(),
            "bus_adj_rule": leg_gen.bus_adj_rule.as_qcf(),
            "fix_adj_rule": leg_gen.fix_adj_rule.as_qcf(),
            "settlement_periodicity": leg_gen.settlement_periodicity.as_qcf(),
            "stub_period": leg_gen.settlement_stub_period.as_qcf(),
            "settlement_calendar": all_calendars[leg_gen.settlement_calendar],
            "settlement_lag": leg_gen.settlement_lag,
            "fixing_calendar": all_calendars[leg_gen.fixing_calendar],
            "amort_is_cashflow": leg_gen.amort_is_cashflow,
            "index_name": leg_gen.overnight_index_name,
            "interest_rate": leg_gen.interest_rate.as_qcf_with_value(0.0),
            "notional_currency": leg_gen.notional_currency.as_qcf(),
            "eq_rate_decimal_places": leg_gen.eq_rate_decimal_places,
            "spread": leg_gen.spread,
            "gearing": leg_gen.gearing,
        }
        if leg_gen.type_of_amortization == 'BULLET':
            parameters["initial_notional"] = leg_gen.notional_or_custom.initial_notional
            return qcf.LegFactory.build_bullet_overnight_index_leg(**parameters)
        else:
            parameters["notional_and_amort"] = leg_gen.notional_or_custom.as_qcf()
            return qcf.LegFactory.build_custom_amort_overnight_index_leg(**parameters)


class IcpClfLegModel(LegModel):
    leg_generator: IcpClfLegGenerator

    def custom_dump(self):
        return {
            "type_of_leg": self.type_of_leg,
            "leg_number": self.leg_number,
            **self.leg_generator.custom_dump(
                self.leg_generator.type_of_amortization,
            ),
        }

    def qcf_leg(self, all_calendars: dict[str, qcf.BusinessCalendar]) -> qcf.Leg:
        leg_gen = self.leg_generator
        parameters = {
            "rec_pay": leg_gen.rp.as_qcf(),
            "start_date": leg_gen.start_date.as_qcf(),
            "end_date": leg_gen.end_date.as_qcf(),
            "bus_adj_rule": leg_gen.bus_adj_rule.as_qcf(),
            "settlement_periodicity": leg_gen.settlement_periodicity.as_qcf(),
            "stub_period": leg_gen.settlement_stub_period.as_qcf(),
            "settlement_calendar": all_calendars[leg_gen.settlement_calendar],
            "settlement_lag": leg_gen.settlement_lag,
            "amort_is_cashflow": leg_gen.amort_is_cashflow,
            "spread": leg_gen.spread,
            "gearing": leg_gen.gearing,
        }
        if leg_gen.type_of_amortization == 'BULLET':
            parameters["initial_notional"] = leg_gen.notional_or_custom.initial_notional
            return qcf.LegFactory.build_bullet_icp_clf_leg(**parameters)
        else:
            parameters["notional_and_amort"] = leg_gen.notional_or_custom.as_qcf()
            return qcf.LegFactory.build_custom_amort_icp_clf_leg(**parameters)


class OvernightIndexMultiCurrencyLegModel(LegModel):
    leg_generator: OvernightIndexLegGenerator
    multi_currency: MultiCurrencyModel

    def custom_dump(self) -> dict[str, Any]:
        return {
            "type_of_leg": self.type_of_leg,
            "leg_number": self.leg_number,
            **self.leg_generator.custom_dump(
                self.leg_generator.type_of_amortization,
            ),
            **self.multi_currency.model_dump()
        }

    def qcf_leg(self, all_calendars: dict[str, qcf.BusinessCalendar]) -> qcf.Leg:
        leg_gen = self.leg_generator
        parameters = {
            "rec_pay": leg_gen.rp.as_qcf(),
            "start_date": leg_gen.start_date.as_qcf(),
            "end_date": leg_gen.end_date.as_qcf(),
            "bus_adj_rule": leg_gen.bus_adj_rule.as_qcf(),
            "fix_adj_rule": leg_gen.bus_adj_rule.PREV.as_qcf(),
            "settlement_periodicity": leg_gen.settlement_periodicity.as_qcf(),
            "stub_period": leg_gen.settlement_stub_period.as_qcf(),
            "settlement_calendar": all_calendars[leg_gen.settlement_calendar],
            "settlement_lag": leg_gen.settlement_lag,
            "fixing_calendar": all_calendars[leg_gen.fixing_calendar],
            "amort_is_cashflow": leg_gen.amort_is_cashflow,
            "index_name": leg_gen.overnight_index_name,
            "interest_rate": leg_gen.interest_rate.as_qcf_with_value(0.0),
            "notional_currency": leg_gen.notional_currency.as_qcf(),
            "eq_rate_decimal_places": leg_gen.eq_rate_decimal_places,
            "spread": leg_gen.spread,
            "gearing": leg_gen.gearing,
            "settlement_currency": self.multi_currency.settlement_currency.as_qcf(),
            "fx_rate_index": config.FXRateIndex(
                self.multi_currency.fx_rate_index_name
            ).as_qcf(calendars=all_calendars),
            "fx_rate_index_fixing_lag": self.multi_currency.fx_fixing_lag,
        }
        if leg_gen.type_of_amortization == 'BULLET':
            parameters["initial_notional"] = leg_gen.notional_or_custom.initial_notional
            return qcf.LegFactory.build_bullet_overnight_index_multi_currency_leg(**parameters)
        else:
            parameters["notional_and_amort"] = leg_gen.notional_or_custom.as_qcf()
            return qcf.LegFactory.build_custom_amort_overnight_index_multi_currency_leg(**parameters)


class CompoundedOvernightRateLegModel(LegModel):
    leg_generator: CompoundedOvernightRateLegGenerator

    def custom_dump(self) -> dict[str, Any]:
        return {
            "type_of_leg": self.type_of_leg,
            "leg_number": self.leg_number,
            **self.leg_generator.custom_dump(
                self.leg_generator.type_of_amortization,
            ),
        }

    def qcf_leg(self, all_calendars: dict[str, qcf.BusinessCalendar]) -> qcf.Leg:
        leg_gen = self.leg_generator
        parameters = {
            "rec_pay": leg_gen.rp.as_qcf(),
            "start_date": leg_gen.start_date.as_qcf(),
            "end_date": leg_gen.end_date.as_qcf(),
            "bus_adj_rule": leg_gen.bus_adj_rule.as_qcf(),
            "settlement_periodicity": leg_gen.settlement_periodicity.as_qcf(),
            "settlement_stub_period": leg_gen.settlement_stub_period.as_qcf(),
            "settlement_calendar": all_calendars[leg_gen.settlement_calendar],
            "settlement_lag": leg_gen.settlement_lag,
            "fixing_calendar": all_calendars[leg_gen.fixing_calendar],
            "interest_rate_index": config.InterestRateIndex(leg_gen.overnight_rate_name).as_qcf(
                calendars=all_calendars),
            "cashflow_is_amort": leg_gen.amort_is_cashflow,
            "notional_currency": leg_gen.notional_currency.as_qcf(),
            "spread": leg_gen.spread,
            "gearing": leg_gen.gearing,
            "interest_rate": leg_gen.interest_rate_type.as_qcf(),
            "eq_rate_decimal_places": leg_gen.eq_rate_decimal_places,
            "lookback": leg_gen.lookback,
            "lockout": leg_gen.lockout,
        }
        if leg_gen.type_of_amortization == 'BULLET':
            parameters["initial_notional"] = leg_gen.notional_or_custom.initial_notional
            return qcf.LegFactory.build_bullet_compounded_overnight_rate_leg_2(
                **parameters
            )
        else:
            parameters["notional_and_amort"] = leg_gen.notional_or_custom.as_qcf()
            return qcf.LegFactory.build_custom_amort_compounded_overnight_rate_leg_2(
                **parameters
            )


class CompoundedOvernightRateMultiCurrencyLegModel(LegModel):
    leg_generator: CompoundedOvernightRateLegGenerator
    multi_currency: MultiCurrencyModel

    def custom_dump(self) -> dict[str, Any]:
        return {
            "type_of_leg": self.type_of_leg,
            "leg_number": self.leg_number,
            **self.leg_generator.custom_dump(
                self.leg_generator.type_of_amortization,
            ),
            **self.multi_currency.model_dump()
        }

    def qcf_leg(self, all_calendars: dict[str, qcf.BusinessCalendar]) -> qcf.Leg:
        leg_gen = self.leg_generator
        parameters = {
            "rec_pay": leg_gen.rp.as_qcf(),
            "start_date": leg_gen.start_date.as_qcf(),
            "end_date": leg_gen.end_date.as_qcf(),
            "bus_adj_rule": leg_gen.bus_adj_rule.as_qcf(),
            "settlement_periodicity": leg_gen.settlement_periodicity.as_qcf(),
            "settlement_stub_period": leg_gen.settlement_stub_period.as_qcf(),
            "settlement_calendar": all_calendars[leg_gen.settlement_calendar],
            "settlement_lag": leg_gen.settlement_lag,
            "fixing_calendar": all_calendars[leg_gen.fixing_calendar],
            "interest_rate_index": config.InterestRateIndex(leg_gen.overnight_rate_name).as_qcf(
                calendars=all_calendars),
            "cashflow_is_amort": leg_gen.amort_is_cashflow,
            "notional_currency": leg_gen.notional_currency.as_qcf(),
            "spread": leg_gen.spread,
            "gearing": leg_gen.gearing,
            "interest_rate": leg_gen.interest_rate_type.as_qcf(),
            "eq_rate_decimal_places": leg_gen.eq_rate_decimal_places,
            "lookback": leg_gen.lookback,
            "lockout": leg_gen.lockout,
            "fx_rate_index_fixing_lag": self.multi_currency.fx_fixing_lag,
            "settlement_currency": self.multi_currency.settlement_currency.as_qcf(),
            "fx_rate_index": config.FXRateIndex(
                self.multi_currency.fx_rate_index_name
            ).as_qcf(calendars=all_calendars),
        }
        if leg_gen.type_of_amortization == 'BULLET':
            parameters["initial_notional"] = leg_gen.notional_or_custom.initial_notional
            return qcf.LegFactory.build_bullet_compounded_overnight_rate_mccy_leg_2(
                **parameters
            )
        else:
            parameters["notional_and_amort"] = leg_gen.notional_or_custom.as_qcf()
            return qcf.LegFactory.build_custom_amort_compounded_overnight_rate_multi_currency_leg_2(
                **parameters
            )


OperationLeg = Union[
    FixedRateLegModel,
    FixedRateMultiCurrencyLegModel,
    IborLegModel,
    IborMultiCurrencyLegModel,
    OvernightIndexLegModel,
    IcpClfLegModel,
    OvernightIndexMultiCurrencyLegModel,
    CompoundedOvernightRateLegModel,
    CompoundedOvernightRateMultiCurrencyLegModel,
]


class Operation(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
    trade_date: qcw.Fecha
    deal_number: str
    counterparty_name: str
    counterparty_rut: Rut
    portfolio: str
    hedge_accounting: str
    product: str
    currency_pair: str
    settlement_mechanism: str
    legs: list[OperationLeg]

    @field_serializer('trade_date')
    def serialize_date(self, dt: qcw.Fecha):
        return dt.fecha

    def custom_dump(self):
        return {
            "trade_date": self.trade_date.as_py_date().isoformat(),
            "deal_number": self.deal_number,
            "counterparty_name": self.counterparty_name,
            "counterparty_rut": self.counterparty_rut.model_dump(),
            "portfolio": self.portfolio,
            "hedge_accounting": self.hedge_accounting,
            "product": self.product,
            "currency_pair": self.currency_pair,
            "settlement_mechanism": self.settlement_mechanism,
            "legs": [
                leg.custom_dump() for leg in self.legs
            ]
        }
