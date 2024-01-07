# Portfolio Builders
import pandas as pd

from data_services import data_front_desk as dfd
from . import market_data as qcv
from . import config as config

from typing import List
from datetime import date

from pydantic.dataclasses import dataclass


@dataclass
class GetSwaps:
    """
    Permite construir operaciones swap filtrando por distintos criterios.
    """
    process_date: date
    sd: qcv.StaticData
    is_prod: bool

    def __post_init_post_parse__(self):
        self.all_headers = dfd.get_all_swaps_headers(self.process_date)
        self.fx_rate_ccs = qcv.get_fx_rate_ccs(self.process_date)
        self.fixed_rate_headers = None
        self.fixed_rate_cashflows = None
        self.icp_headers = None
        self.icp_cashflows = None
        self.sofrindx_headers = None
        self.sofrindx_cashflows = None
        self.sofrrate_headers = None
        self.sofrrate_cashflows = None
        self.floating_rate_headers = None
        self.floating_rate_cashflows = None

    def __get_fixed_rate_legs_data(self):
        self.fixed_rate_headers, self.fixed_rate_cashflows = dfd.get_fixed_rate_legs_for_qcf(
            self.process_date,
            is_offline=False,
            is_prod=self.is_prod,
        )

    def __get_icp_legs_data(self):
        self.icp_headers, self.icp_cashflows = dfd.get_icp_legs_for_qcf(
            self.process_date,
            is_offline=False,
            is_prod=self.is_prod,
        )

    def __get_sofrrate_legs_data(self):
        self.sofrrate_headers, self.sofrrate_cashflows = dfd.get_sofrrate_legs_for_qcf(
            self.process_date,
            is_offline=False,
            is_prod=self.is_prod,
        )

    def __get_floating_rate_legs_data(self):
        self.floating_rate_headers, self.floating_rate_cashflows = dfd.get_floating_rate_legs_for_qcf(
            self.process_date,
            is_offline=False,
            is_prod=self.is_prod,
        )

    def __get_sofrindx_legs_data(self):
        self.sofrindx_headers, self.sofrindx_cashflows = dfd.get_sofrindx_legs_for_qcf(
            self.process_date,
            is_offline=False,
            is_prod=self.is_prod,
        )

    def all(self) -> List[qcv.Operation]:
        """
        """
        patas_fijas = None
        patas_icp = None
        patas_sofrindx = None
        patas_ibor = None
        patas_sofrrate = None

        # Construye Patas Fijas
        if self.fixed_rate_headers is None:
            self.__get_fixed_rate_legs_data()

        if len(self.fixed_rate_headers) > 0:
            patas_fijas = qcv.build_qcf_fixed_rate_legs(
                self.fixed_rate_headers,
                self.fixed_rate_cashflows,
                self.sd.calendars,
                self.fx_rate_ccs,
            )

        # Construye Patas ICP
        if self.icp_headers is None:
            self.__get_icp_legs_data()

        if len(self.icp_headers) > 0:
            patas_icp = qcv.build_qcf_icp_legs(
                self.icp_headers,
                self.icp_cashflows,
                self.sd.calendars,
                self.fx_rate_ccs
            )

        # Construye Patas SOFRINDX
        if self.sofrindx_headers is None:
            self.__get_sofrindx_legs_data()

        if len(self.sofrindx_headers) > 0:
            patas_sofrindx = qcv.build_sofrindx_legs(
                self.sofrindx_headers,
                self.sofrindx_cashflows,
                self.sd.calendars,
                self.fx_rate_ccs,
            )

        # Construye Patas SOFRRATE
        if self.sofrrate_headers is None:
            self.__get_sofrrate_legs_data()

        if len(self.sofrrate_headers) > 0:
            patas_sofrrate = qcv.build_sofrrate_legs(
                self.sofrrate_headers,
                self.sofrrate_cashflows,
                self.sd.calendars,
                config.InterestRateIndex,
                self.fx_rate_ccs,
            )

        # Construye Patas Flotantes
        if self.floating_rate_headers is None:
            self.__get_floating_rate_legs_data()

        if len(self.floating_rate_headers) > 0:
            patas_ibor = qcv.build_qcf_ibor_legs(
                self.floating_rate_headers,
                self.floating_rate_cashflows,
                self.sd.calendars,
                config.InterestRateIndex,
                self.fx_rate_ccs,
            )

        # Consolida Cartera y retorna
        return qcv.get_swap_operations(
            self.all_headers,
            patas_fijas,
            patas_icp,
            patas_sofrindx,
            patas_ibor,
            patas_sofrrate,
        )

    def by_deal_number(self, deal_numbers: List[str]) -> List[qcv.Operation]:
        """
        """
        patas_fijas = None
        patas_icp = None
        patas_sofrindx = None
        patas_ibor = None
        patas_sofrrate = None

        # Construye Patas Fijas
        if self.fixed_rate_headers is None:
            self.__get_fixed_rate_legs_data()

        headers = self.fixed_rate_headers[self.fixed_rate_headers.numero_operacion.isin(deal_numbers)]
        if len(headers) > 0:
            patas_fijas = qcv.build_qcf_fixed_rate_legs(
                headers,
                self.fixed_rate_cashflows,
                self.sd.calendars,
                self.fx_rate_ccs,
            )

        # Construye Patas ICP
        if self.icp_headers is None:
            self.__get_icp_legs_data()

        headers = self.icp_headers[self.icp_headers.numero_operacion.isin(deal_numbers)]
        if len(headers) > 0:
            patas_icp = qcv.build_qcf_icp_legs(
                headers,
                self.icp_cashflows,
                self.sd.calendars,
                self.fx_rate_ccs
            )

        # Construye Patas SOFRINDX
        if self.sofrindx_headers is None:
            self.__get_sofrindx_legs_data()

        headers = self.sofrindx_headers[self.sofrindx_headers.numero_operacion.isin(deal_numbers)]
        if len(headers) > 0:
            patas_sofrindx = qcv.build_sofrindx_legs(
                headers,
                self.sofrindx_cashflows,
                self.sd.calendars,
                self.fx_rate_ccs
            )

        # Construye Patas SOFRRATE
        if self.sofrrate_headers is None:
            self.__get_sofrrate_legs_data()

        headers = self.sofrrate_headers[self.sofrrate_headers.numero_operacion.isin(deal_numbers)]
        if len(headers) > 0:
            patas_sofrrate = qcv.build_sofrrate_legs(
                self.sofrrate_headers,
                self.sofrrate_cashflows,
                self.sd.calendars,
                config.InterestRateIndex,
                self.fx_rate_ccs,
            )

        # Construye Patas Flotantes
        if self.floating_rate_headers is None:
            self.__get_floating_rate_legs_data()

        headers = self.floating_rate_headers[self.floating_rate_headers.numero_operacion.isin(deal_numbers)]
        if len(headers) > 0:
            patas_ibor = qcv.build_qcf_ibor_legs(
                headers,
                self.floating_rate_cashflows,
                self.sd.calendars,
                config.InterestRateIndex,
                self.fx_rate_ccs,
            )

        # Consolida Cartera y retorna
        return qcv.get_swap_operations(
            self.all_headers,
            patas_fijas,
            patas_icp,
            patas_sofrindx,
            patas_ibor,
            patas_sofrrate,
        )

    def hedge_accounting(self) -> List[qcv.Operation]:
        headers = self.all_headers[self.all_headers.es_cobertura == 'S']
        deal_numbers = list(headers.numero_operacion.values)
        return self.by_deal_number(deal_numbers)


@dataclass
class GetForwards:
    process_date: date
    is_prod: bool

    def all(self) -> List[qcv.Operation]:
        data_forwards = dfd.get_forwards_headers(self.process_date, is_offline=False, is_prod=self.is_prod)
        data_forwards = data_forwards.to_dict('records')
        return qcv.build_qcf_forwards(data_forwards)

    def only_ndf(self) -> List[qcv.Operation]:
        data_forwards = dfd.get_forwards_headers(self.process_date, is_offline=False, is_prod=self.is_prod)
        data_forwards = data_forwards[data_forwards.modalidad_pago == 'C'].copy()
        data_forwards = data_forwards.to_dict('records')
        return qcv.build_qcf_forwards(data_forwards)
    
    def only_market_risk(self, dt_date_next) -> List[qcv.Operation]:
        data_forwards = dfd.get_forwards_headers(self.process_date, is_offline=False, is_prod=self.is_prod)
        data_fwd_ndf = data_forwards[data_forwards.modalidad_pago == 'C'].copy()
        data_fwd_ndf = data_fwd_ndf[['fecha_proceso', 'fecha_final']]
        data_fwd_ndf.fecha_final = pd.to_datetime(data_fwd_ndf.fecha_final, format='%Y-%m-%d')

        lt_index = data_fwd_ndf[data_fwd_ndf.fecha_final <= dt_date_next].index
        data_forwards = data_forwards[~ data_forwards.index.isin(lt_index)]
        data_forwards = data_forwards.to_dict('records')
        return qcv.build_qcf_forwards(data_forwards)
