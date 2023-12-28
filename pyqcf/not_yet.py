from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
disable_warnings(InsecureRequestWarning)


class GetFixingForLeg(BaseModel):
    """
    Realiza el fixing del cupón corriente de cualquier tipo de pata.
    """

    market_data: Union[StaticData, MarketData]

    class Config:
        arbitrary_types_allowed = True
        allow_mutation = False

    def fix_icpclp_leg(
            self, process_date: qcf.QCDate, leg: qcf.Leg, index_code: str
    ) -> None:
        """
        Realiza el fixing de una pata de tipo ICPCLP (OIS calculado con un índice).
        Sólo se fixea el cupón corriente, ya que los cupones pasados no intervienen en la valorización.

        Parameters
        ----------
        process_date: date
            Fecha a la que se realiza el fixing.
        leg: Qcf.Leg
            Pata a fixear.
        index_code: str
            Corresponde al código del índice a utilizar (ICPCLP, SOFRINDX ...)

        Returns
        -------
        None (el objeto Qcf.Leg muta y queda con el cupón fixeado).

        """
        for i in range(leg.size()):
            cashflow = leg.get_cashflow_at(i)
            if cashflow.get_start_date() <= process_date <= cashflow.get_end_date():
                cashflow.set_start_date_icp(
                    self.market_data.get_index_value(
                        qcf_date_to_py_date(cashflow.get_start_date()), index_code
                    )
                )
                if process_date == cashflow.get_end_date():
                    cashflow.set_end_date_icp(
                        self.market_data.get_index_value(
                            qcf_date_to_py_date(cashflow.get_end_date()), index_code
                        )
                    )
                return

    def fix_icpclf_leg(self, process_date: qcf.QCDate, leg: qcf.Leg) -> None:
        """
        Realiza el fixing de una pata ICPCLF.
        Sólo se fixea el cupón corriente ya que los cupones pasados no intervienen en la valorización.

        Parameters
        ----------
        process_date: Qcf.QCDate
            Fecha a la que se realiza el fixing.
        leg: Qcf.Leg
            Pata a fixear.

        Returns
        -------
        None (el objeto Qcf.Leg muta y queda con el cupón fixeado).
        """

        for i in range(leg.size()):
            cashflow = leg.get_cashflow_at(i)
            if cashflow.get_start_date() <= process_date < cashflow.get_end_date():
                cashflow.set_start_date_icp(
                    self.market_data.get_index_value(
                        qcf_date_to_py_date(cashflow.get_start_date()), "ICPCLP"
                    )
                )
                cashflow.set_start_date_uf(
                    self.market_data.get_index_value(
                        qcf_date_to_py_date(cashflow.get_start_date()), "UF"
                    )
                )

                if process_date == cashflow.get_end_date():
                    cashflow.set_end_date_icp(
                        self.market_data.get_index_value(
                            qcf_date_to_py_date(cashflow.get_end_date()), "ICPCLP"
                        )
                    )
                    cashflow.set_end_date_uf(
                        self.market_data.get_index_value(
                            qcf_date_to_py_date(cashflow.get_end_date()), "UF"
                        )
                    )

                return

    def fix_ibor_leg(self, process_date: qcf.QCDate, leg: qcf.Leg) -> None:
        """
        Realiza el fixing de una pata Ibor.
        Sólo se fixea el cupón corriente ya que los cupones pasados no intervienen en la valorización.

        Parameters
        ----------
        process_date: Qcf.QCDate
            Fecha a la que se realiza el fixing.
        leg: Qcf.Leg
            Pata a fixear.

        Returns
        -------
        None: el objeto Qcf.Leg muta y queda con el cupón fixeado.
        """
        for i in range(leg.size()):
            cashflow = leg.get_cashflow_at(i)
            fecha_fixing = cashflow.get_fixing_dates()[0]
            code = leg.get_cashflow_at(0).get_interest_rate_index().get_code()
            code = config.interest_rate_index_aliases.get(code, code)
            # print(code)
            if fecha_fixing <= process_date:
                cashflow.set_rate_value(
                    self.market_data.get_index_value(
                        qcf_date_to_py_date(fecha_fixing), code
                    )
                )

    def fix_compounded_overnight_rate_leg(
            self, process_date: qcf.QCDate, leg: qcf.Leg
    ) -> float:
        """
        Realiza el fixing de una pata con flujos CompoundedOvernightRate.
        Sólo se *fixea* el cupón corriente, ya que los cupones pasados no intervienen en la valorización.

        Parameters
        ----------
        process_date: qcf.QCDate
            Fecha a la que se realiza el fixing.

        leg: qcf.Leg
            Pata a fixear.

        Returns
        -------
        None: el objeto Qcf.Leg muta y queda con el cupón fixeado.
        """
        code = leg.get_cashflow_at(0).get_interest_rate_index_code()
        code = config.interest_rate_index_aliases.get(code, code)
        for i in range(leg.size()):
            cashflow = leg.get_cashflow_at(i)
            fecha_inicial = cashflow.get_start_date()
            fecha_final = cashflow.get_end_date()
            # print(code)
            if fecha_inicial <= process_date <= fecha_final:
                return cashflow.accrued_fixing(
                    process_date, self.market_data.historic_index_values[code][1]
                )


class GetM2MForLeg(BaseModel):
    """
    Permite calcular el mark-to-market de cualquier tipo de pata.
    """

    present_value: qcf.PresentValue
    fwd_rates: qcf.ForwardRates
    get_fixing: GetFixingForLeg
    sd: StaticData
    contrapartes_col_usd: Dict[str, str] = config.contrapartes_col_usd
    ignore_collateral: bool = False
    use_scenario: bool = False

    class Config:
        arbitrary_types_allowed = True

    def __get_discount_curve(
            self,
            leg: OperationLeg,
    ) -> str:
        if not self.ignore_collateral and leg.counterparty in self.contrapartes_col_usd:
            curva = config.crv_desc_col_usd[leg.nominal_currency]
        else:
            curva = config.crv_desc_no_col[leg.nominal_currency]

        return self.sd.get_zero_coupon_curve(curva, self.use_scenario)[1]

    def get_m2m_fwd(
            self,
            process_date: qcf.QCDate,
            leg: OperationLeg,
    ) -> float:
        curva_desc = self.__get_discount_curve(leg)
        return self.present_value.pv(
            process_date,
            leg.qcf_leg,
            curva_desc,
        ) * self.sd.get_index_value(
            qcf_date_to_py_date(process_date),
            config.which_fx_rate_index[leg.nominal_currency.value],
        )

    def get_m2m_fixed_leg(
            self,
            process_date: qcf.QCDate,
            leg: OperationLeg,
    ) -> float:
        crv_desc = self.__get_discount_curve(leg)

        return self.present_value.pv(
            process_date,
            leg.qcf_leg,
            crv_desc,
        ) * self.sd.get_index_value(
            qcf_date_to_py_date(process_date),
            config.which_fx_rate_index[leg.nominal_currency],
        )

    def get_m2m_icpclp_leg(
            self,
            process_date: qcf.QCDate,
            leg: OperationLeg,
    ) -> float:
        """
        Calcula el valor presente o mark to market (mtm, m2m) de una pata de tipo ICPCLP.

        Parameters
        ----------
        process_date: Qcf.QCDate
            Fecha a la que se calcula el m2m.
        leg:
            Pata a valorizar.

        Returns
        -------
        float: m2m de la pata.

        """
        index_code = str(leg.interest_rate_index.value)

        self.get_fixing.fix_icpclp_leg(process_date, leg.qcf_leg, index_code)

        self.fwd_rates.set_rates_icp_clp_leg2(
            process_date,
            self.sd.get_index_value(qcf_date_to_py_date(process_date), index_code),
            leg.qcf_leg,
            self.sd.get_zero_coupon_curve(
                config.crv_proy_irs[index_code],
                self.use_scenario,
            )[1],
        )

        crv_desc = self.__get_discount_curve(leg)

        return self.present_value.pv(
            process_date,
            leg.qcf_leg,
            crv_desc,
        ) * self.sd.get_index_value(
            qcf_date_to_py_date(process_date),
            config.which_fx_rate_index[leg.nominal_currency],
        )

    def get_m2m_icpclf_leg(
            self,
            process_date: qcf.QCDate,
            leg: OperationLeg,
    ) -> float:
        """
        Calcula el valor presente o mark to market (mtm, m2m) de una pata de tipo ICPCLF.

        Parameters
        ----------
        process_date: Qcf.QCDate
            Fecha a la que se calcula el m2m.
        leg:
            Pata a valorizar.
        counterparty:
            Rut de la contraparte asociada a la pata.

        Returns
        -------
        float: m2m de la pata.

        """
        uf = self.sd.get_index_value(qcf_date_to_py_date(process_date), "UF")

        self.get_fixing.fix_icpclf_leg(process_date, leg.qcf_leg)
        self.fwd_rates.set_rates_icp_clf_leg(
            process_date,
            self.sd.get_index_value(qcf_date_to_py_date(process_date), "ICPCLP"),
            self.sd.get_index_value(qcf_date_to_py_date(process_date), "UF"),
            leg.qcf_leg,
            self.sd.get_zero_coupon_curve("CICPCLP", self.use_scenario)[1],
            self.sd.get_zero_coupon_curve("CCLPCOLUSD", self.use_scenario)[1],
            self.sd.get_zero_coupon_curve("CCLFCOLUSD", self.use_scenario)[1],
        )

        crv_desc = self.__get_discount_curve(leg)

        return (
                self.present_value.pv(
                    process_date,
                    leg.qcf_leg,
                    crv_desc,
                )
                * uf
        )

    def get_m2m_sofrindx_leg(
            self,
            process_date: qcf.QCDate,
            leg: OperationLeg,
    ) -> float:
        """
        Calcula el valor presente o mark to market (mtm, m2m) de una pata de tipo SOFRINDX.

        Parameters
        ----------
        process_date: Qcf.QCDate
            Fecha a la que se calcula el m2m.
        leg:
            Pata a valorizar.
        counterparty:
            Rut de la contraparte asociada a la pata.

        Returns
        -------
        float: m2m de la pata.

        """
        return self.get_m2m_icpclp_leg(process_date, leg)

    def get_m2m_ibor_leg(
            self,
            process_date: qcf.QCDate,
            leg: OperationLeg,
    ) -> float:
        """
        Calcula el mark to market (mtm, m2m) de una pata de tipo IBOR (floating rate).

        Parameters
        ----------
        process_date: Qcf.QCDate
            Fecha a la que se calcula el mtm.

        leg: Qcf.Leg
            Pata para la que se calcula el mtm.

        Returns
        -------
        float: valor presente o mtm de la pata.

        """

        # Patas Floating
        indice = leg.qcf_leg.get_cashflow_at(0).get_interest_rate_index().get_code()
        indice = config.interest_rate_index_aliases.get(indice, indice)
        self.get_fixing.fix_ibor_leg(process_date, leg.qcf_leg)
        self.fwd_rates.set_rates_ibor_leg(
            process_date,
            leg.qcf_leg,
            self.sd.get_zero_coupon_curve(
                config.crv_proy_irs[leg.interest_rate_index.value],
                self.use_scenario,
            )[1],
        )

        crv_desc = self.__get_discount_curve(leg)

        return self.present_value.pv(
            process_date, leg.qcf_leg, crv_desc
        ) * self.sd.get_index_value(
            qcf_date_to_py_date(process_date),
            config.which_fx_rate_index[leg.nominal_currency],
        )

    def get_m2m_overnight_index_leg(
            self,
            process_date: qcf.QCDate,
            leg: OperationLeg,
    ) -> float:
        """
        Calcula el mark to market (mtm, m2m) de una pata de tipo CompoundedOvernightRate (OIS).

        Parameters
        ----------
        process_date: Qcf.QCDate
            Fecha a la que se calcula el mtm.
        leg: Qcf.Leg
            Pata para la que se calcula el mtm.

        Returns
        -------
        float: valor presente o mtm de la pata.

        """

        # Patas Floating
        indice = leg.qcf_leg.get_cashflow_at(0).get_interest_rate_index_code()
        #  indice_obj = config.interest_rate_index_aliases.get(indice, indice)
        # accrued_fixing = self.get_fixing.fix_compounded_overnight_rate_leg(process_date, leg.qcf_leg)
        self.fwd_rates.set_rates_compounded_overnight_leg(
            process_date,
            leg.qcf_leg,
            self.sd.get_zero_coupon_curve(
                config.crv_proy_irs[leg.interest_rate_index.value],
                self.use_scenario,
            )[1],
            self.sd.historic_index_values[indice][1],
        )

        crv_desc = self.__get_discount_curve(leg)

        return self.present_value.pv(
            process_date, leg.qcf_leg, crv_desc
        ) * self.sd.get_index_value(
            qcf_date_to_py_date(process_date),
            config.which_fx_rate_index[leg.nominal_currency],
        )

    def __call__(
            self,
            process_date: Union[date, qcf.QCDate],
            leg: OperationLeg,
    ) -> float:
        switcher = {
            TypeOfLeg.FXFWD: self.get_m2m_fwd,
            TypeOfLeg.FIXED_RATE: self.get_m2m_fixed_leg,
            TypeOfLeg.ICPCLP: self.get_m2m_icpclp_leg,
            TypeOfLeg.ICPCLF: self.get_m2m_icpclf_leg,
            TypeOfLeg.SOFRINDX: self.get_m2m_sofrindx_leg,
            TypeOfLeg.FLOATING_RATE: self.get_m2m_ibor_leg,
            TypeOfLeg.SOFRRATE: self.get_m2m_overnight_index_leg,
        }

        if isinstance(process_date, date):
            process_date = qcf.build_qcdate_from_string(process_date.isoformat())

        return switcher[leg.type_of_leg](process_date, leg)


class GetPresentValueForLeg(BaseModel):
    """
    Permite calcular el mark-to-market de cualquier tipo de pata.
    """

    present_value: qcf.PresentValue
    fwd_rates: qcf.ForwardRates
    get_fixing: GetFixingForLeg
    market_data: MarketData
    contrapartes_col_usd: Dict[str, str] = config.contrapartes_col_usd
    ignore_collateral: bool = False
    use_ir_scenario: bool = False
    use_fx_scenario: bool = False

    class Config:
        arbitrary_types_allowed = True

    def __get_discount_curve(
            self,
            leg: OperationLeg,
    ) -> str:
        if not self.ignore_collateral and leg.counterparty in self.contrapartes_col_usd:
            curva = config.crv_desc_col_usd[leg.nominal_currency]
        else:
            curva = config.crv_desc_no_col[leg.nominal_currency]

        return self.market_data.get_zero_coupon_curve(curva, self.use_ir_scenario)[1]

    def get_m2m_fwd(
            self,
            process_date: qcf.QCDate,
            leg: OperationLeg,
    ) -> float:
        curva_desc = self.__get_discount_curve(leg)
        return self.present_value.pv(
            process_date,
            leg.qcf_leg,
            curva_desc,
        ) * self.market_data.get_fx_rate_index_value(
            config.which_fx_rate_index[leg.nominal_currency.value],
            self.use_fx_scenario,
        )

    def get_m2m_fixed_leg(
            self,
            process_date: qcf.QCDate,
            leg: OperationLeg,
    ) -> float:
        crv_desc = self.__get_discount_curve(leg)

        return self.present_value.pv(
            process_date,
            leg.qcf_leg,
            crv_desc,
        ) * self.market_data.get_fx_rate_index_value(
            config.which_fx_rate_index[leg.nominal_currency.value],
            self.use_fx_scenario,
        )

    def get_m2m_icpclp_leg(
            self,
            process_date: qcf.QCDate,
            leg: OperationLeg,
    ) -> float:
        """
        Calcula el valor presente o mark to market (mtm, m2m) de una pata de tipo ICPCLP.

        Parameters
        ----------
        process_date: Qcf.QCDate
            Fecha a la que se calcula el m2m.
        leg:
            Pata a valorizar.

        Returns
        -------
        float: m2m de la pata.

        """
        index_code = str(leg.interest_rate_index.value)

        self.get_fixing.fix_icpclp_leg(process_date, leg.qcf_leg, index_code)

        self.fwd_rates.set_rates_icp_clp_leg2(
            process_date,
            self.market_data.get_index_value(
                qcf_date_to_py_date(process_date), index_code
            ),
            leg.qcf_leg,
            self.market_data.get_zero_coupon_curve(
                config.crv_proy_irs[index_code],
                self.use_ir_scenario,
            )[1],
        )

        crv_desc = self.__get_discount_curve(leg)

        return self.present_value.pv(
            process_date,
            leg.qcf_leg,
            crv_desc,
        ) * self.market_data.get_fx_rate_index_value(
            config.which_fx_rate_index[leg.nominal_currency.value],
            self.use_fx_scenario,
        )

    def get_m2m_icpclf_leg(
            self,
            process_date: qcf.QCDate,
            leg: OperationLeg,
    ) -> float:
        """
        Calcula el valor presente o mark to market (mtm, m2m) de una pata de tipo ICPCLF.

        Parameters
        ----------
        process_date: Qcf.QCDate
            Fecha a la que se calcula el m2m.
        leg:
            Pata a valorizar.

        Returns
        -------
        float: m2m de la pata.

        """
        uf = self.market_data.get_index_value(qcf_date_to_py_date(process_date), "UF")

        self.get_fixing.fix_icpclf_leg(process_date, leg.qcf_leg)
        self.fwd_rates.set_rates_icp_clf_leg(
            process_date,
            self.market_data.get_index_value(
                qcf_date_to_py_date(process_date), "ICPCLP"
            ),
            self.market_data.get_index_value(qcf_date_to_py_date(process_date), "UF"),
            leg.qcf_leg,
            self.market_data.get_zero_coupon_curve("CICPCLP", self.use_ir_scenario)[1],
            self.market_data.get_zero_coupon_curve("CCLPCOLUSD", self.use_ir_scenario)[
                1
            ],
            self.market_data.get_zero_coupon_curve("CCLFCOLUSD", self.use_ir_scenario)[
                1
            ],
        )

        crv_desc = self.__get_discount_curve(leg)

        return (
                self.present_value.pv(
                    process_date,
                    leg.qcf_leg,
                    crv_desc,
                )
                * uf
        )

    def get_m2m_sofrindx_leg(
            self,
            process_date: qcf.QCDate,
            leg: OperationLeg,
    ) -> float:
        """
        Calcula el valor presente o mark to market (mtm, m2m) de una pata de tipo SOFRINDX.

        Parameters
        ----------
        process_date: Qcf.QCDate
            Fecha a la que se calcula el m2m.
        leg:
            Pata a valorizar.
        counterparty:
            Rut de la contraparte asociada a la pata.

        Returns
        -------
        float: m2m de la pata.

        """
        return self.get_m2m_icpclp_leg(process_date, leg)

    def get_m2m_ibor_leg(
            self,
            process_date: qcf.QCDate,
            leg: OperationLeg,
    ) -> float:
        """
        Calcula el mark to market (mtm, m2m) de una pata de tipo IBOR (floating rate).

        Parameters
        ----------
        process_date: Qcf.QCDate
            Fecha a la que se calcula el mtm.

        leg: Qcf.Leg
            Pata para la que se calcula el mtm.

        Returns
        -------
        float: valor presente o mtm de la pata.

        """

        # Patas Floating
        indice = leg.qcf_leg.get_cashflow_at(0).get_interest_rate_index().get_code()
        indice = config.interest_rate_index_aliases.get(indice, indice)
        self.get_fixing.fix_ibor_leg(process_date, leg.qcf_leg)
        self.fwd_rates.set_rates_ibor_leg(
            process_date,
            leg.qcf_leg,
            self.market_data.get_zero_coupon_curve(
                config.crv_proy_irs[leg.interest_rate_index.value],
                self.use_ir_scenario,
            )[1],
        )

        crv_desc = self.__get_discount_curve(leg)

        return self.present_value.pv(
            process_date, leg.qcf_leg, crv_desc
        ) * self.market_data.get_fx_rate_index_value(
            config.which_fx_rate_index[leg.nominal_currency.value],
            self.use_fx_scenario,
        )

    def get_m2m_overnight_index_leg(
            self,
            process_date: qcf.QCDate,
            leg: OperationLeg,
    ) -> float:
        """
        Calcula el mark to market (mtm, m2m) de una pata de tipo CompoundedOvernightRate (OIS).

        Parameters
        ----------
        process_date: Qcf.QCDate
            Fecha a la que se calcula el mtm.
        leg: Qcf.Leg
            Pata para la que se calcula el mtm.

        Returns
        -------
        float: valor presente o mtm de la pata.

        """

        # Patas Floating
        indice = leg.qcf_leg.get_cashflow_at(0).get_interest_rate_index_code()
        self.fwd_rates.set_rates_compounded_overnight_leg(
            process_date,
            leg.qcf_leg,
            self.market_data.get_zero_coupon_curve(
                config.crv_proy_irs[leg.interest_rate_index.value],
                self.use_ir_scenario,
            )[1],
            self.market_data.historic_index_values[indice][1],
        )

        crv_desc = self.__get_discount_curve(leg)

        return self.present_value.pv(
            process_date, leg.qcf_leg, crv_desc
        ) * self.market_data.get_fx_rate_index_value(
            config.which_fx_rate_index[leg.nominal_currency.value],
            self.use_fx_scenario,
        )

    def __call__(
            self,
            process_date: Union[date, qcf.QCDate],
            leg: OperationLeg,
    ) -> float:
        switcher = {
            TypeOfLeg.FXFWD: self.get_m2m_fwd,
            TypeOfLeg.FIXED_RATE: self.get_m2m_fixed_leg,
            TypeOfLeg.ICPCLP: self.get_m2m_icpclp_leg,
            TypeOfLeg.ICPCLF: self.get_m2m_icpclf_leg,
            TypeOfLeg.SOFRINDX: self.get_m2m_sofrindx_leg,
            TypeOfLeg.FLOATING_RATE: self.get_m2m_ibor_leg,
            TypeOfLeg.SOFRRATE: self.get_m2m_overnight_index_leg,
        }

        if isinstance(process_date, date):
            process_date = qcf.build_qcdate_from_string(process_date.isoformat())

        return switcher[leg.type_of_leg](process_date, leg)


class GetRegulatoryCashflowForLeg(BaseModel):
    """
    Calcula los flujos regulatorios de cualquier tipo de pata.
    """

    get_fixing: GetFixingForLeg
    sd: Union[StaticData, MarketData]

    class Config:
        arbitrary_types_allowed = True
        allow_mutation = False

    @staticmethod
    def __zero_cashflow(process_date: qcf.QCDate, leg: OperationLeg):
        return [
            (
                leg.deal_number,
                leg.a_p.value,
                leg.type_of_leg.value,
                leg.nominal_currency.value,
                process_date.description(False),
                0.0,
                0.0,
            )
        ]

    def __generic_overnight_index(
            self,
            process_date: qcf.QCDate,
            leg: OperationLeg,
            overnight_index_code: str,
    ) -> List[Tuple[str, str, str, str, str, float, float]]:
        """
        Retorna los flujos obligacionistas de una pata cualquiera de tipo OvernightIndex.

        Parameters
        ----------
        process_date: qcf.QCDate
            Fecha a la que se realiza el cálculo. Sólo se consideran los flujos con end date posterior a `process_date`.

        leg: OperationLeg

        overnight_index_code: str
            Código del índice overnight a utilizar.

        Returns
        -------
        List[Tuple[str, str, str, str, str, float, float]]. Los campos corresponden a:

        - Número de operación
        - Activo o pasivo
        - Tipo de pata
        - Moneda del nocional
        - Fecha del flujo
        - Monto de interés
        - Monto de amortización
        """
        result = leg.get_current_cashflow_and_index(process_date)
        if result is not None:
            cashflow, index = result
        else:
            return GetRegulatoryCashflowForLeg.__zero_cashflow(process_date, leg)

        py_date = qcf_date_to_py_date(process_date)
        result = [
            (
                leg.deal_number,
                leg.a_p.value,
                leg.type_of_leg.value,
                leg.nominal_currency.value,
                leg.qcf_leg.get_cashflow_at(i).get_end_date().description(False),
                amount_to_clp(
                    leg.qcf_leg.get_cashflow_at(i).interest(),
                    leg.nominal_currency,
                    py_date,
                    self.sd,
                ),
                0.0,
            )
            for i in range(index, leg.qcf_leg.size())
        ]

        py_date_1 = py_date + timedelta(days=1)
        self.get_fixing.fix_icpclp_leg(process_date, leg.qcf_leg, overnight_index_code)
        result.insert(
            0,
            (
                leg.deal_number,
                leg.a_p.value,
                leg.type_of_leg.value,
                leg.nominal_currency.value,
                py_date_1.isoformat(),
                amount_to_clp(
                    cashflow.accrued_interest(
                        process_date,
                        self.sd.historic_index_values[overnight_index_code][1],
                    ),
                    leg.nominal_currency,
                    py_date,
                    self.sd,
                ),
                amount_to_clp(
                    cashflow.get_nominal(),
                    leg.nominal_currency,
                    py_date,
                    self.sd,
                ),
            ),
        )

        return result

    def case_fixed_leg(self, process_date: qcf.QCDate, leg: OperationLeg):
        """ """
        result = leg.get_current_cashflow_and_index(process_date)
        if result is not None:
            cashflow, index = result[0], result[1]
        else:
            return GetRegulatoryCashflowForLeg.__zero_cashflow(process_date, leg)

        qcf_leg = leg.qcf_leg

        py_date = qcf_date_to_py_date(process_date)

        return [
            (
                leg.deal_number,
                leg.a_p.value,
                leg.type_of_leg.value,
                leg.nominal_currency.value,
                qcf_leg.get_cashflow_at(i).get_settlement_date().description(False),
                amount_to_clp(
                    qcf_leg.get_cashflow_at(i).interest(),
                    leg.nominal_currency,
                    py_date,
                    self.sd,
                ),
                amount_to_clp(
                    qcf_leg.get_cashflow_at(i).amortization(),
                    leg.nominal_currency,
                    py_date,
                    self.sd,
                ),
            )
            for i in range(index, leg.qcf_leg.size())
        ]

    def case_fwd_leg(self, process_date: qcf.QCDate, leg: OperationLeg):
        """ """

        result = leg.get_current_cashflow(process_date)
        if result is not None:
            cashflow = result
        else:
            return GetRegulatoryCashflowForLeg.__zero_cashflow(process_date, leg)

        py_date = qcf_date_to_py_date(process_date)

        return [
            (
                leg.deal_number,
                leg.a_p.value,
                leg.type_of_leg.value,
                leg.nominal_currency.value,
                cashflow.date().description(False),
                0.0,
                amount_to_clp(
                    cashflow.amount(),
                    leg.nominal_currency,
                    py_date,
                    self.sd,
                ),
            )
        ]

    def case_icp_clp_leg(self, process_date: qcf.QCDate, leg: OperationLeg):
        """
        Retorna los flujos obligacionistas de una pata IcpClp.
        """
        return self.__generic_overnight_index(
            process_date,
            leg,
            "ICPCLP",
        )

    def case_icp_clf_leg(self, process_date: qcf.QCDate, leg: OperationLeg):
        """ """
        self.get_fixing.fix_icpclf_leg(process_date, leg.qcf_leg)
        result = leg.get_current_cashflow_and_index(process_date)
        if result is not None:
            cashflow, index = result[0], result[1]
        else:
            return GetRegulatoryCashflowForLeg.__zero_cashflow(process_date, leg)

        py_date = qcf_date_to_py_date(process_date)

        pydate = qcf_date_to_py_date(process_date)
        icp = self.sd.get_index_value(pydate, "ICPCLP")
        uf = self.sd.get_index_value(pydate, "UF")
        return [
            (
                leg.deal_number,
                leg.a_p.value,
                leg.type_of_leg.value,
                leg.nominal_currency.value,
                process_date.description(False),
                amount_to_clp(
                    cashflow.accrued_interest(process_date, icp, uf),
                    leg.nominal_currency,
                    py_date,
                    self.sd,
                ),
                amount_to_clp(
                    cashflow.get_nominal(),
                    leg.nominal_currency,
                    py_date,
                    self.sd,
                ),
            )
        ]

    def case_sofrindx_leg(self, process_date: qcf.QCDate, leg: OperationLeg):
        """
        Retorna los flujos obligacionistas de una pata SOFRINDX.
        """
        return self.__generic_overnight_index(
            process_date,
            leg,
            "SOFRINDX",
        )

    def case_ibor_leg(self, process_date: qcf.QCDate, leg: OperationLeg):
        """ """
        result = leg.get_current_cashflow_and_index(process_date)
        if result is not None:
            cashflow, indice = result
        else:
            return GetRegulatoryCashflowForLeg.__zero_cashflow(process_date, leg)

        py_date = qcf_date_to_py_date(process_date)
        result = [
            (
                leg.deal_number,
                leg.a_p.value,
                leg.type_of_leg.value,
                leg.nominal_currency.value,
                leg.qcf_leg.get_cashflow_at(i).get_end_date().description(False),
                leg.qcf_leg.get_cashflow_at(i).interest(),
                0.0,
            )
            for i in range(indice + 1, leg.qcf_leg.size())
        ]

        code = cashflow.get_interest_rate_index().get_code()
        code = config.interest_rate_index_aliases.get(code, code)

        self.get_fixing.fix_ibor_leg(process_date, leg.qcf_leg)
        current_cashflow = leg.get_current_cashflow(process_date)
        result.insert(
            0,
            (
                leg.deal_number,
                leg.a_p.value,
                leg.type_of_leg.value,
                leg.nominal_currency.value,
                current_cashflow.get_end_date().description(False),
                amount_to_clp(
                    cashflow.interest(self.sd.historic_index_values[code][1]),
                    leg.nominal_currency,
                    py_date,
                    self.sd,
                ),
                amount_to_clp(
                    cashflow.get_nominal(),
                    leg.nominal_currency,
                    py_date,
                    self.sd,
                ),
            ),
        )

        return result

    def case_sofrrate_leg(self, process_date: qcf.QCDate, leg: OperationLeg):
        """ """
        result = leg.get_current_cashflow_and_index(process_date)
        if result is not None:
            cashflow, indice = result
        else:
            return GetRegulatoryCashflowForLeg.__zero_cashflow(process_date, leg)

        py_date = qcf_date_to_py_date(process_date)
        result = [
            (
                leg.deal_number,
                leg.a_p.value,
                leg.type_of_leg.value,
                leg.nominal_currency.value,
                leg.qcf_leg.get_cashflow_at(i).get_end_date().description(False),
                leg.qcf_leg.get_cashflow_at(i).interest(),
                0.0,
            )
            for i in range(indice + 1, leg.qcf_leg.size())
        ]

        code = "SOFRRATE"
        code = config.interest_rate_index_aliases.get(code, code)

        self.get_fixing.fix_compounded_overnight_rate_leg(process_date, leg.qcf_leg)

        current_cashflow = leg.get_current_cashflow(process_date)
        result.insert(
            0,
            (
                leg.deal_number,
                leg.a_p.value,
                leg.type_of_leg.value,
                leg.nominal_currency.value,
                current_cashflow.get_end_date().description(False),
                amount_to_clp(
                    cashflow.accrued_interest(
                        process_date, self.sd.historic_index_values[code][1]
                    ),
                    leg.nominal_currency,
                    py_date,
                    self.sd,
                ),
                amount_to_clp(
                    cashflow.get_nominal(),
                    leg.nominal_currency,
                    py_date,
                    self.sd,
                ),
            ),
        )

        return result

    def __call__(self, process_date: Union[qcf.QCDate, date], leg: OperationLeg):
        if isinstance(process_date, date):
            process_date = qcf.build_qcdate_from_string(process_date.isoformat())

        switcher = {
            TypeOfLeg.FXFWD: self.case_fwd_leg,
            TypeOfLeg.FIXED_RATE: self.case_fixed_leg,
            TypeOfLeg.ICPCLP: self.case_icp_clp_leg,
            TypeOfLeg.ICPCLF: self.case_icp_clf_leg,
            TypeOfLeg.FLOATING_RATE: self.case_ibor_leg,
            TypeOfLeg.SOFRINDX: self.case_sofrindx_leg,
            TypeOfLeg.SOFRRATE: self.case_sofrrate_leg,
        }

        return switcher[leg.type_of_leg](process_date, leg)


class Config:
    arbitrary_types_allowed = True
    allow_mutation = False


Estado = namedtuple(
    "Estado",
    [
        "deal_number",
        "leg_number",
        "capital_vigente",
        "reajuste_fx",
        "interes_devengado",
        "interes_pagado",
        "flujo_capital",
        "saldo",
        "valor_mercado",
        "ajuste_valor_mercado",
        "flujos",
    ],
)


@dataclass(config=Config)
class CalculaEstado:
    """
    Métodos para el cálculo del estado (en el sentido de ALM) de una pata de una operación.

    El estado de una operación corresponde a los siguientes 4 indicadores:

    - capital_vigente: corresponde al nocional no amortizado.
    - interes_devengado: corresponde a los intereses devengados del cupón corriente.
    - interes_pagado: la suma de los flujos de intereses de los cupones ya vencidos.
    - flujo_capital: la suma de los flujos de amortización de los cupones ya vencidos.
    - ajuste_valor_mercado: corresponde a la diferencia entre el valor presente de la operación
    y la suma del capital vigente más los intereses devengados.
    """

    sd: StaticData
    get_mtm: GetM2MForLeg

    def __post_init_post_parse__(self):
        self.icpclp = qcf.time_series()
        data = self.sd.historic_index_values["ICPCLP"][0]
        for t in data.itertuples():
            self.icpclp[qcf.build_qcdate_from_string(t.Index)] = t.value

        self.sofrindx = qcf.time_series()
        data = self.sd.historic_index_values["SOFRINDX"][0]
        for t in data.itertuples():
            self.sofrindx[qcf.build_qcdate_from_string(t.Index)] = t.value

    def __capital_vigente(self, process_date: qcf.QCDate, leg: OperationLeg) -> float:
        """ """
        if isinstance(process_date, date):
            process_date = qcf.build_qcdate_from_string(process_date.isoformat())

        def simple_cashflow():
            return 0

        def other_cashflow():
            start_date = leg.get_min_start_date()
            end_date = leg.get_max_end_date()

            if process_date < start_date:
                return leg.qcf_leg.get_cashflow_at(0).get_nominal()
            elif start_date <= process_date < end_date:
                return leg.get_current_cashflow(process_date).get_nominal()
            else:
                return 0

        switcher = {
            TypeOfLeg.FXFWD: simple_cashflow,
        }

        amount = switcher.get(leg.type_of_leg, other_cashflow)()
        return amount_to_clp(
            amount,
            leg.nominal_currency,
            qcf_date_to_py_date(process_date),
            self.sd,
        )

    def __reajuste_fx(self, process_date: qcf.QCDate, leg: OperationLeg) -> float:
        if leg.type_of_leg == TypeOfLeg.FXFWD:
            return 0.0

        que_indice = {
            qcw.Currency.CLP: "1CLP",
            qcw.Currency.CLF: "UF",
            qcw.Currency.USD: "USDCLP_RC",
            qcw.Currency.EUR: "EURCLP_RC",
        }

        capital_vigente = self.__capital_vigente(process_date, leg)
        if leg.get_min_start_date() > process_date:
            return 0.0
        fecha_inicio = qcf_date_to_py_date(leg.get_min_start_date())
        moneda = leg.nominal_currency

        fx_inicial = self.sd.get_index_value(
            fecha_inicio,
            que_indice[moneda],
        )

        if fx_inicial == 0.0:
            data = dfd.get_fx_rate_index_values(
                fecha_inicio,
                fecha_inicio,
                que_indice[moneda],
            )
            if len(data) > 0:
                fx_inicial = data.iloc[0].value

        if fx_inicial == 0.0:
            msg = f"El índice {que_indice[moneda]} tiene valor 0 al {fecha_inicio}."
            raise ValueError(msg)

        fx_proceso = self.sd.get_index_value(
            qcf_date_to_py_date(process_date),
            que_indice[moneda],
        )

        if fx_proceso > 0:
            return capital_vigente * (1 - fx_inicial / fx_proceso)
        else:
            msg = f"El índice {que_indice[moneda]} tiene valor 0 al {process_date.description(False)}."
            raise ValueError(msg)

    def __interes_devengado(self, process_date: qcf.QCDate, leg: OperationLeg) -> float:
        """ """

        def simple_cashflow() -> float:
            return 0.0

        def fixed_rate_cashflow():
            start_date = leg.get_min_start_date()
            end_date = leg.get_max_end_date()

            if process_date < start_date:
                return 0.0
            elif start_date <= process_date < end_date:
                return leg.get_current_cashflow(process_date).accrued_interest(
                    process_date
                )
            else:
                return 0

        def icpclp_cashflow() -> float:
            if leg.type_of_leg == TypeOfLeg.ICPCLP:
                index_data = self.icpclp
            else:
                index_data = self.sofrindx

            start_date = leg.get_min_start_date()
            end_date = leg.get_max_end_date()

            if process_date < start_date:
                return 0.0

            elif start_date <= process_date < end_date:
                return leg.get_current_cashflow(process_date).accrued_interest(
                    process_date,
                    index_data,
                )

            else:
                return 0.0

        switcher = {
            TypeOfLeg.FXFWD: simple_cashflow,
            TypeOfLeg.FIXED_RATE: fixed_rate_cashflow,
            TypeOfLeg.ICPCLP: icpclp_cashflow,
            TypeOfLeg.SOFRINDX: icpclp_cashflow,
        }

        amount = switcher.get(leg.type_of_leg, simple_cashflow)()
        return amount_to_clp(
            amount,
            leg.nominal_currency,
            qcf_date_to_py_date(process_date),
            self.sd,
        )

    def __interes_pagado(self, process_date: qcf.QCDate, leg: OperationLeg) -> float:
        def simple_cashflow() -> float:
            return 0.0

        def fixed_rate_cashflow():
            start_date = leg.get_min_start_date()
            end_date = leg.get_max_end_date()
            total = 0.0

            if process_date <= start_date:
                return total
            else:
                for i in range(leg.qcf_leg.size()):
                    cashflow = leg.qcf_leg.get_cashflow_at(i)
                    cashflow_end_date = cashflow.get_end_date()
                    if process_date >= cashflow_end_date:
                        total += amount_to_clp(
                            cashflow.interest(),
                            leg.nominal_currency,
                            qcf_date_to_py_date(cashflow_end_date),
                            self.sd,
                        )
                    else:
                        return total

            return total

        def icpclp_cashflow():
            if leg.type_of_leg == TypeOfLeg.ICPCLP:
                index_data = self.icpclp
            else:
                index_data = self.sofrindx

            start_date = leg.get_min_start_date()
            end_date = leg.get_max_end_date()
            total = 0.0

            if process_date <= start_date:
                return total
            else:
                for i in range(leg.qcf_leg.size()):
                    cashflow = leg.qcf_leg.get_cashflow_at(i)
                    cashflow_end_date = cashflow.get_end_date()
                    if process_date >= cashflow_end_date:
                        total += amount_to_clp(
                            cashflow.accrued_interest(cashflow_end_date, index_data),
                            leg.nominal_currency,
                            qcf_date_to_py_date(cashflow_end_date),
                            self.sd,
                        )
                    else:
                        return total

            return total

        switcher = {
            TypeOfLeg.FXFWD: simple_cashflow,
            TypeOfLeg.FIXED_RATE: fixed_rate_cashflow,
            TypeOfLeg.ICPCLP: icpclp_cashflow,
            TypeOfLeg.SOFRINDX: icpclp_cashflow,
        }

        return switcher.get(leg.type_of_leg, simple_cashflow)()

    def __capital_pagado(self, process_date: qcf.QCDate, leg: OperationLeg) -> float:
        if isinstance(process_date, date):
            process_date = qcf.build_qcdate_from_string(process_date.isoformat())

        def simple_cashflow() -> float:
            return 0.0

        def fixed_rate_cashflow():
            start_date = leg.get_min_start_date()
            end_date = leg.get_max_end_date()
            total = 0.0

            if process_date <= start_date:
                return total
            else:
                for i in range(leg.qcf_leg.size()):
                    cashflow = leg.qcf_leg.get_cashflow_at(i)
                    cashflow_end_date = cashflow.get_end_date()
                    if process_date >= cashflow_end_date:
                        total += amount_to_clp(
                            cashflow.get_amortization(),
                            leg.nominal_currency,
                            qcf_date_to_py_date(cashflow_end_date),
                            self.sd,
                        )
                    else:
                        return total

            return total

        def icpclp_cashflow():
            if leg.type_of_leg == TypeOfLeg.ICPCLP:
                index = "ICPCLP"
            else:
                index = "SOFRINDX"

            start_date = leg.get_min_start_date()
            end_date = leg.get_max_end_date()
            total = 0.0

            if process_date <= start_date:
                return total
            else:
                for i in range(leg.qcf_leg.size()):
                    cashflow = leg.qcf_leg.get_cashflow_at(i)
                    cashflow_end_date = cashflow.get_end_date()
                    if process_date >= cashflow_end_date:
                        total += cashflow.get_amortization()
                    else:
                        return total
            return total

        switcher = {
            TypeOfLeg.FXFWD: simple_cashflow,
            TypeOfLeg.FIXED_RATE: fixed_rate_cashflow,
            TypeOfLeg.ICPCLP: icpclp_cashflow,
            TypeOfLeg.SOFRINDX: icpclp_cashflow,
        }

        return switcher.get(leg.type_of_leg, simple_cashflow)()

    def __valor_mercado(self, process_date: qcf.QCDate, leg: OperationLeg) -> float:
        """ """
        return self.get_mtm(process_date, leg)

    def __call__(
            self, process_date: Union[date, qcf.QCDate], leg: OperationLeg
    ) -> Estado:
        if isinstance(process_date, date):
            process_date = qcf.build_qcdate_from_string(process_date.isoformat())

        comp_index_legs = {
            TypeOfLeg.ICPCLP: self.icpclp,
            TypeOfLeg.SOFRINDX: self.sofrindx,
        }
        if leg.type_of_leg in comp_index_legs.keys():
            index_data = comp_index_legs[leg.type_of_leg]
            for i in range(leg.qcf_leg.size()):
                cashflow = leg.qcf_leg.get_cashflow_at(i)
                if process_date >= cashflow.get_start_date():
                    cashflow.set_start_date_icp(index_data[cashflow.get_start_date()])
                    if process_date >= cashflow.get_end_date():
                        cashflow.set_end_date_icp(index_data[cashflow.get_end_date()])
                else:
                    break

        capital_vigente = self.__capital_vigente(process_date, leg)
        reajuste_fx = self.__reajuste_fx(process_date, leg)
        interes_devengado = self.__interes_devengado(process_date, leg)
        interes_pagado = self.__interes_pagado(process_date, leg)
        capital_pagado = self.__capital_pagado(process_date, leg)
        saldo = capital_vigente + interes_devengado
        valor_mercado = self.__valor_mercado(process_date, leg)
        ajuste_valor_mercado = valor_mercado - saldo
        flujos_pagados = interes_pagado + capital_pagado

        return Estado(
            leg.deal_number,
            leg.leg_number,
            capital_vigente,
            reajuste_fx,
            interes_devengado,
            interes_pagado,
            capital_pagado,
            saldo,
            valor_mercado,
            ajuste_valor_mercado,
            flujos_pagados,
        )
