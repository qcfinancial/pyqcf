# Funciones para el cálculo del vencimiento de cupones de swaps

from pydantic import BaseModel, PositiveInt, ConfigDict

from qcf_valuation import qcf_wrappers as qcw, core as qcv
import qcfinancial as qcf

from . import dto_factory as dto
from . import fixings as fix

from ..models import operations_2 as op


class DealNumber(BaseModel):
    deal_number: str


class SettlingOperation(DealNumber):
    leg_numbers: set[PositiveInt]


def get_settlements(
        process_date: qcw.Fecha,
        settlement_date: qcw.Fecha,
        swaps: dto.OperationDataAnalytics,
        market_data: qcv.MarketData,
) -> tuple[list[SettlingOperation], list[DealNumber]]:
    """
    Retorna los swaps que tienen un cupón que vence entre process_date (excluido) y next_date (incluido).

    Args:
        process_date (qcw.Fecha): Fecha de proceso. Los swaps encontrados vencen después de process_date.
        settlement_date (qcw.Fecha): Fecha máxima de vencimiento.
        swaps: (dto.OperationDataAnalytics): Objeto con la data de la cartera vigente de swaps.
        market_data (qcv.MarketData): Objeto con datos de mercado y los calendarios requeridos para la construcción
        de las patas qcfinancial.

    Returns: tuple[list[SettlingOperation], list[DealNUmber]]

    """
    deal_number_leg = []
    bad_deal_numbers = []
    all_swaps = swaps.get_all_deal_numbers()
    for deal_number, operation in all_swaps.items():
        legs = set()
        try:
            for leg in operation.legs:
                cashflow = leg.get_current_cashflow(process_date, market_data.calendars)
                if cashflow.get_end_date() <= settlement_date.as_qcf():
                    legs.add(leg.leg_number)
        except IndexError as e:
            bad_deal_numbers.append(DealNumber(deal_number=deal_number))
        if len(legs) > 0:
            deal_number_leg.append(SettlingOperation(deal_number=deal_number, leg_numbers=legs))
    return deal_number_leg, bad_deal_numbers


def get_settling_operation(deal_number: DealNumber, settling_operations: list[SettlingOperation]):
    return [sett_op for sett_op in settling_operations if sett_op.deal_number == deal_number]


class SettlementInfoForLeg(BaseModel):
    """
    Modela la información de vencimiento de un cashflow de una pata:
    - Número de pata
    - Recibo o pago
    - Nocional vigente
    - Fecha inicial (fecha inicial del cupón)
    - Fecha final (fecha en que se termina de determinar el flujo de intereses)
    - Fecha de settlement (fecha efectiva de pago del flujo)
    - Tipo de tasa (fija o si es variable el nombre del índice)
    - Moneda del vencimiento
    - Monto del vencimiento
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
    leg_number: PositiveInt
    rec_pay: qcw.AP
    current_notional: float
    start_date: qcf.QCDate
    end_date: qcf.QCDate
    settlement_date: qcf.QCDate
    interest_rate: str
    settlement_currency: qcw.Currency
    settlement_amount: float

    def custom_dump(self):
        return {
            "leg_number": self.leg_number,
            "rec_pay": self.rec_pay,
            "current_notional": self.current_notional,
            "start_date": self.start_date.iso_code(),
            "end_date": self.end_date.iso_code(),
            "settlement_date": self.settlement_date.iso_code(),
            "interest_rate": self.interest_rate,
            "settlement_currency": self.settlement_currency.value,
            "settlement_amount": self.settlement_amount,
        }


class SettlementInfo(BaseModel):
    """
    Modela la información principal sobre el vencimiento de un cupón de swap, esta es:

    - Número de operación
    - Producto
    - Nombre de la contraparte
    - Rut de la contraparte
    - Par de divisas asociado a la operación
    - Mecanismo de entrega

    Luego, por cada una de las patas con vencimiento
    - SettlementInfoForLeg

    Define los métodos __lt__ y __eq__ para ordenar resultados por número de operación y pata.

    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
    deal_number: str
    product: op.Product
    counterparty_name: str
    counterparty_rut: op.Rut
    currency_pair: qcw.FXRate
    settlement_mechanism: op.SettlementMechanism
    legs: list[SettlementInfoForLeg]

    def __lt__(self, other):
        if self.deal_number == other.deal_number:
            return self.leg_number < other.leg_number
        else:
            return self.deal_number.__lt__(other.deal_number)

    def __eq__(self, other):
        return (self.deal_number == other.deal_number) and (
                self.leg_number == other.leg_number)

    def custom_dump(self):
        return {
            "deal_number": self.deal_number,
            "product": self.product.value,
            "counterparty_name": self.counterparty_name,
            "counterparty_rut": str(self.counterparty_rut),
            "currency_pair": self.currency_pair.value,
            "settlement_mechanism": self.settlement_mechanism.value,
            "legs": [leg.custom_dump() for leg in self.legs],
        }


def calculate_settlement(
        process_date: qcw.Fecha,
        operation_and_legs: SettlingOperation,
        swaps: dto.OperationDataAnalytics,
        market_data: qcv.MarketData,
) -> SettlementInfo:
    """
    Calcula el vencimiento de una pata de una operación swap.

    Args:
        process_date (qcw.Fecha): fecha a la que se realiza el cálculo.
        operation_and_legs (SettlingOperation): Número de operación y número de pata.
        swaps (dto.OperationDataAnalytics): Objeto que almacena la data de todos los swaps vigentes.
        market_data (qcv.MarketData): Objeto con los datos de mercado requeridos para los fixings.

    Returns:
        SettlementInfo: Número de operación, número de pata, monto y moneda del vencimiento.

    """
    deal_number = operation_and_legs.deal_number
    legs = []
    operation = swaps.get_deal_number(deal_number)
    for leg_number in operation_and_legs.leg_numbers:
        leg_number -= 1
        cashflow = operation.legs[leg_number].get_current_cashflow(process_date, market_data.calendars)
        fix.fix_cashflow(cashflow, market_data)

        if operation.legs[leg_number].type_of_leg in [op.TypeOfLeg.FIXED_RATE,
                                                      op.TypeOfLeg.FIXED_RATE_MCCY]:
            interest_rate = 'FIXED'
        elif operation.legs[leg_number].type_of_leg in [op.TypeOfLeg.IBOR,
                                                        op.TypeOfLeg.IBOR_MCCY]:
            interest_rate = operation.legs[leg_number].leg_generator.interest_rate_index_name

        elif operation.legs[leg_number].type_of_leg in [op.TypeOfLeg.OVERNIGHT_INDEX,
                                                        op.TypeOfLeg.OVERNIGHT_INDEX_MCCY]:
            interest_rate = operation.legs[leg_number].leg_generator.overnight_index_name

        elif operation.legs[leg_number].type_of_leg in [op.TypeOfLeg.COMPOUNDED_OVERNIGHT_RATE,
                                                        op.TypeOfLeg.COMPOUNDED_OVERNIGHT_RATE_MCCY]:
            interest_rate = operation.legs[leg_number].leg_generator.overnight_rate_name

        else:
            interest_rate = 'ICPCLF'

        legs.append(SettlementInfoForLeg(
            leg_number=leg_number + 1,
            rec_pay=operation.legs[leg_number].leg_generator.rp,
            current_notional=cashflow.get_nominal(),
            start_date=cashflow.get_start_date(),
            end_date=cashflow.get_end_date(),
            settlement_date=cashflow.get_settlement_date(),
            interest_rate=interest_rate,
            settlement_currency=cashflow.settlement_currency().get_iso_code(),
            settlement_amount=cashflow.settlement_amount(),
        ))

    return SettlementInfo(
        deal_number=deal_number,
        product=op.Product(operation.product),
        counterparty_name=operation.counterparty_name,
        counterparty_rut=op.Rut(rut=operation.counterparty_rut.rut, dv=operation.counterparty_rut.dv),
        currency_pair=qcw.FXRate(operation.currency_pair),
        settlement_mechanism=op.SettlementMechanism(operation.settlement_mechanism),
        legs=legs,
    )
