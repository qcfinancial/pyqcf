from . import config as config
from . import market_data as qcv
from datetime import date
from typing import List, Tuple


def get_regulatory_cashflows(
        process_date: date,
        operations: List[qcv.Operation],
        is_prod: bool,
) -> List[Tuple[str, str, str, str, str, float, float]]:
    sd = qcv.build_static_data(
        process_date=process_date,
        initial_date=date(2019, 1, 1),
        codigos_curvas=config.codigos_curvas_derivados,
        is_prod=is_prod,
    )

    get_fixing = qcv.GetFixingForLeg(
        market_data=sd,
    )

    get_reg = qcv.GetRegulatoryCashflowForLeg(
        get_fixing=get_fixing,
        sd=sd,
    )

    result = []
    for op in operations:
        for leg in op.legs:
            result += get_reg(
                process_date=process_date,
                leg=leg
            )

    return result
