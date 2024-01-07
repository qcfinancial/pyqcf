from functools import lru_cache
from datetime import date

from . import analytics_extra as anx
from . import operations as op
from . import wrappers as qcw
from .dependencies import get_db


def get_operations_for_date(process_date: date):
    db = get_db()
    collection_name = f'operations_{process_date}'

    if collection_name not in db.list_collection_names():
        raise ValueError(f"There are no operations for {process_date}.")
    else:
        try:
            op_data = db[collection_name].find({})
        except Exception as e:
            raise RuntimeError(f"Shit happens ... {str(e)}")

    result = []
    for operation in op_data:
        operation["_id"] = str(operation["_id"])
        result.append(operation)
    return result


class DerivativePortfolio:
    def __init__(self, portfolio_date: date):
        self.portfolio_date = portfolio_date
        self.data = get_operations_for_date(portfolio_date)

    @lru_cache
    def get_deal_number(self, deal_number: str) -> op.Operation:
        try:
            raw_op = [x for x in self.data if x["deal_number"] == deal_number][0]
        except Exception as e:
            raise ValueError(f"Cannot find operation {deal_number} for {self.portfolio_date}. {str(e)}")

        counterparty_rut = op.Rut(
            rut=int(raw_op["counterparty_rut"]["rut"]),
            dv=raw_op["counterparty_rut"]["dv"],
        )

        legs = [anx.make_leg(raw_leg) for raw_leg in raw_op["legs"]]

        return op.Operation(
            trade_date=qcw.Fecha(fecha=raw_op["trade_date"]),
            deal_number=raw_op["deal_number"],
            counterparty_name=raw_op["counterparty_name"],
            counterparty_rut=counterparty_rut,
            portfolio=raw_op["portfolio"],
            hedge_accounting=raw_op["hedge_accounting"],
            product=raw_op["product"],
            currency_pair=raw_op["currency_pair"],
            settlement_mechanism=raw_op["settlement_mechanism"],
            legs=legs,
        )

    def get_many_deal_numbers(self, deal_numbers: list[str]) -> dict[str, op.Operation]:
        return {dn: self.get_deal_number(dn) for dn in deal_numbers}

    def get_all_deal_numbers(self) -> dict[str, op.Operation]:
        deal_numbers = [d["deal_number"] for d in self.data ]
        return {dn: self.get_deal_number(dn) for dn in deal_numbers}
