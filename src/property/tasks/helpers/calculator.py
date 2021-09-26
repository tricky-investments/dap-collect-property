def traditionals(data):

    # Initialize KPI store
    kpis = {}

    # Initial Property Costs
    purchase_price = data.pop('purchase_price')
    downpayment = data.pop('downpayment')
    closing_cost = data.pop('closing_cost')

    # Monthly Income
    rent = data.pop('rent')

    # Monthly Expenses
    mortgage = data.pop('mortgage')
    pmi = data.pop('pmi')
    tax = data.pop('tax')
    insurance = data.pop('insurance')
    vacancy = data.pop('vacancy_rate')*rent
    repair = data.pop('repair_rate')*rent
    capex = data.pop('capex_rate')*rent
    management = data.pop('management_rate')*rent
    utilities = 0
    for key in data.keys():
        if key in ['electric', 'water', 'gas']:
            utilities += data.get(key)

    # Calculate monthly income
    monthly_profit = rent
    monthly_expenses = mortgage + pmi + (tax/12) + insurance + repair + capex + utilities + management
    monthly_income = monthly_profit - monthly_expenses
    kpis.update({"monthly_income": monthly_income})

    # Calculate Cash on Cash ROI
    initial_investment = downpayment + closing_cost
    roi = (monthly_income*12)/initial_investment
    kpis.update({"roi": roi})

    # Calculate Cap Rate
    noi = rent - tax - insurance - vacancy - repair - management - utilities
    cap_rate = noi/purchase_price
    kpis.update({"cap_rate": cap_rate})

    # Calculate Estimated Growth Rent Multiplier
    annual_rent = rent*12
    grm = purchase_price/annual_rent
    kpis.update({"grm": grm})

    # Calculate Rent to Purchase Price Ratio
    rpr = rent/purchase_price
    kpis.update({"rpr": rpr})

    return kpis


def traditional_reversed_rent(data):

    # Initialize KPI Store
    kpis = {}

    # Initialize Property Costs
    purchase_price = data.pop('purchase_price')
    downpayment = data.pop('downpayment')
    closing_cost = data.pop('closing_cost')

    # Initialize Monthly Expenses and Rates
    mortgage = data.pop('mortgage')
    vacancy_rate = data.pop('vacancy_rate')
    repair_rate = data.pop('repair_rate')
    capex_rate = data.pop('capex_rate')
    management_rate = data.pop('management_rate')
    utilities = 0
    for key in data.keys():
        if key in ['electric', 'water', 'gas']:
            utilities += data[key]

    # Initialize KPIs
    for key in data.keys():

        target = data[key]
        if target is None:
            continue

        if key == 'monthly_income':

            pre_rent = target + mortgage + utilities
            divisor = 1 - vacancy_rate - repair_rate - management_rate - capex_rate
            min_rent = pre_rent/divisor
            kpis.update({'monthly_income': min_rent})

        elif key == 'roi':

            annual_income = target*(downpayment + closing_cost)
            monthly_income = annual_income/12
            pre_rent = monthly_income + mortgage + utilities
            divisor = 1 - vacancy_rate - repair_rate - management_rate - capex_rate
            min_rent = pre_rent / divisor
            kpis.update({'roi': min_rent})

        elif key == 'cap_rate':

            noi = target*purchase_price
            pre_rent = noi + utilities
            divisor = 1 - vacancy_rate - repair_rate - management_rate - capex_rate
            min_rent = pre_rent/divisor
            kpis.update({'cap_rate': min_rent})

        elif key == 'grm':

            annual_rent = purchase_price/target
            min_rent = annual_rent/12
            kpis.update({'grm': min_rent})

        elif key == 'rpr':

            min_rent = target*purchase_price
            kpis.update({'rpr': min_rent})

    return kpis



