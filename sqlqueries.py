from states import State

sales_strings = {
    State.pik_today: "Продано {} м²",
    State.pik_yesterday: "Вчера продано {} м²",
    State.moscow_today: "В Московском регионе продано {} м²",
    State.moscow_yesterday: "Вчера в Московском регионе продано {} м²",
    State.regions_today: "В регионах продано {} м²",
    State.regions_yesterday: "Вчера в регионах продано  {} м²",
}

forecast_strings = {
    State.pik_today: "Потенциал {s}м² (подтверждены {ps}м²)",
    State.pik_yesterday: "Вчера потеницал {s}м² (подтверждены {ps}м²)",
    State.moscow_today: "Потенциал Московского региона {s}м² (подтверждены {ps}м²)",
    State.moscow_yesterday: "Вчера потеницал Московского региона {s}м² (подтверждены {ps}м²)",
    State.regions_today: "Потенциал регионов {s}м² (подтверждены {ps}м²)",
    State.regions_yesterday: "Вчера потенциал регионов {s}м² (подтверждены {ps}м²)",
}

sales_requests = {
    State.pik_today: "exec tele_bot_sold null",
    State.pik_yesterday: "exec tele_bot_sold null, -1",
    State.moscow_today: "exec tele_bot_sold 1",
    State.moscow_yesterday: "exec tele_bot_sold 1, -1",
    State.regions_today: "exec tele_bot_sold 0",
    State.regions_yesterday: "exec tele_bot_sold 0, -1",
}

forecast_requests = {
    State.pik_today:
        """declare @today date = cast(getdate() as date)
            select
              sum(Potential.new_areaunderopportunity) as s
            , sum(iif(pic_probabilityName = \'Сделка запланирована и подтверждена\', Potential.new_areaunderopportunity, 0)) as ps
            from Potential
            where DateofQuery = @today
              and EstimatedDateOfDeal = @today""",
    State.pik_yesterday:
        '''
            declare @today date = dateadd(day, -1, cast(getdate() as date))
            select
              sum(Potential.new_areaunderopportunity) as s
            , sum(iif(pic_probabilityName = \'Сделка запланирована и подтверждена\', Potential.new_areaunderopportunity, 0)) as ps
            from Potential
            where DateofQuery = @today
              and EstimatedDateOfDeal = @today
          '''
    ,
    State.moscow_today:
        '''
            declare @today date = cast(getdate() as date)
            select
              sum(Potential.new_areaunderopportunity) as s
            , sum(iif(pic_probabilityName = \'Сделка запланирована и подтверждена\', Potential.new_areaunderopportunity, 0)) as ps
            from Potential
            where DateofQuery = @today
              and EstimatedDateOfDeal = @today
              and super_region = \'Москва и МО\'
          '''
    ,
    State.moscow_yesterday:
        '''
            declare @today date = dateadd(day, -1, cast(getdate() as date))
            select
              sum(Potential.new_areaunderopportunity) as s
            , sum(iif(pic_probabilityName = \'Сделка запланирована и подтверждена\', Potential.new_areaunderopportunity, 0)) as ps
            from Potential
            where DateofQuery = @today
              and EstimatedDateOfDeal = @today
              and super_region = \'Москва и МО\'
          '''
    ,
    State.regions_today:
        '''
            declare @today date = cast(getdate() as date)
            select
              sum(Potential.new_areaunderopportunity) as s
            , sum(iif(pic_probabilityName = \'Сделка запланирована и подтверждена\', Potential.new_areaunderopportunity, 0)) as ps
            from Potential
            where DateofQuery = @today
              and EstimatedDateOfDeal = @today
              and super_region = \'Регионы\'
          '''
    ,
    State.regions_yesterday:
        '''
            declare @today date = dateadd(day, -1, cast(getdate() as date))
            select
              sum(Potential.new_areaunderopportunity) as s
            , sum(iif(pic_probabilityName = \'Сделка запланирована и подтверждена\', Potential.new_areaunderopportunity, 0)) as ps
            from Potential
            where DateofQuery = @today
              and EstimatedDateOfDeal = @today
              and super_region = \'Регионы\'
          '''
    ,
}

sms_requests = {
    State.sms_today:
        '''
          exec plan_fact_sms
          select * from plan_fact_sms_cache
        ''',
    State.sms_yesterday:
        '''
          declare @ts datetime = dateadd(dd, -1, getdate())
          exec plan_fact_sms @ts
          select * from plan_fact_sms_cache
        ''',
    State.sms_holidays:
        '''
          declare @ts datetime = dateadd(dd, -2, getdate())
          exec plan_fact_sms @ts, 2
          select * from plan_fact_sms_cache
        ''',
    State.sms_month:
        '''
          declare @today as date = getdate()
          declare @monthFirst as date = dateadd(month, datediff(month, 0, @today), 0)
          declare @monthCurrent as tinyint = datepart(day, @today)

          exec plan_fact_sms @monthFirst, @monthCurrent
          select * from plan_fact_sms_cache
        '''
}
