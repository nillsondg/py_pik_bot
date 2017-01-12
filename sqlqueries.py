from states import State

sales_strings = {
    State.pik_today_sold: "Продано {} м²",
    State.pik_yesterday_sold: "Вчера продано {} м²",
    State.moscow_today_sold: "В Московском регионе продано {} м²",
    State.moscow_yesterday_sold: "Вчера в Московском регионе продано {} м²",
    State.regions_today_sold: "В регионах продано {} м²",
    State.regions_yesterday_sold: "Вчера в регионах продано  {} м²",
}

forecast_strings = {
    State.pik_today_forecast: "Потенциал {s}м² (подтверждены {ps}м²)",
    State.pik_yesterday_forecast: "Вчера потеницал {s}м² (подтверждены {ps}м²)",
    State.moscow_today_forecast: "Потенциал Московского региона {s}м² (подтверждены {ps}м²)",
    State.moscow_yesterday_forecast: "Вчера потеницал Московского региона {s}м² (подтверждены {ps}м²)",
    State.regions_today_forecast: "Потенциал регионов {s}м² (подтверждены {ps}м²)",
    State.regions_yesterday_forecast: "Вчера потенциал регионов {s}м² (подтверждены {ps}м²)",
}

sales_requests = {
    State.pik_today_sold: "exec tele_bot_sold null",
    State.pik_yesterday_sold: "exec tele_bot_sold null, -1",
    State.moscow_today_sold: "exec tele_bot_sold 1",
    State.moscow_yesterday_sold: "exec tele_bot_sold 1, -1",
    State.regions_today_sold: "exec tele_bot_sold 0",
    State.regions_yesterday_sold: "exec tele_bot_sold 0, -1",
}

forecast_requests = {
    State.pik_today_forecast:
        '''
          declare @today date = cast(getdate() as date)
          select
            sum(pt.new_areaunderopportunity) as s
          , sum(iif(pt.pic_probabilityName = \'Сделка запланирована и подтверждена\', pt.new_areaunderopportunity, 0)) as ps

          from Potential (nolock) as pt

          inner join [sql1205pik\db6].pic_mscrm.dbo.pic_gkExtensionBase as gk
            on gk.pic_name = pt.pic_gkidName

          where pt.DateofQuery = @today
            and pt.EstimatedDateOfDeal = @today
            and gk.pic_mortonId is null
        ''',
    State.pik_yesterday_forecast:
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
    State.moscow_today_forecast:
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
    State.moscow_yesterday_forecast:
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
    State.regions_today_forecast:
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
    State.regions_yesterday_forecast:
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
    State.all_today_sms:
        '''
          exec tgbot_sms_all
          select
            cast(coalesce(c1.text, iif(datepart(hh, getdate()) > 6, null, c2.text), 'Нет продаж') as varchar(max)) as txt
          from tgbot_sms_cache as c1
          inner join tgbot_sms_cache as c2
            on c2.company is null
            and c2.period = 1
          where c1.period = 0
            and c1.company is null
        ''',
    State.pik_today_sms:
        '''
          exec tgbot_sms_pik
          select
            cast(coalesce(c1.text, iif(datepart(hh, getdate()) > 6, null, c2.text), 'Нет продаж') as varchar(max)) as txt
          from tgbot_sms_cache as c1
          inner join tgbot_sms_cache as c2
            on c2.company = c1.company
            and c2.period = 1
          where c1.period = 0
            and c1.company = 0 -- ПИК
        ''',
    State.pik_yesterday_sms:
        '''
          declare @ts datetime = dateadd(dd, -1, getdate())
          exec plan_fact_sms @ts
          select * from plan_fact_sms_cache
        ''',
    # State.pik_holidays_sms:
    #     '''
    #       declare @ts datetime = dateadd(dd, -2, getdate())
    #       exec plan_fact_sms @ts, 2
    #       select * from plan_fact_sms_cache
    #     ''',
    # State.pik_month_sms:
    #     '''
    #       declare @today as date = getdate()
    #       declare @monthFirst as date = dateadd(month, datediff(month, 0, @today), 0)
    #       declare @monthCurrent as tinyint = datepart(day, @today)

    #       exec plan_fact_sms @monthFirst, @monthCurrent
    #       select * from plan_fact_sms_cache
    #     ''',
    State.morton_today_sms:
        '''
          exec tgbot_sms_morton
          select
            cast(coalesce(c1.text, iif(datepart(hh, getdate()) > 6, null, c2.text), 'Нет продаж') as varchar(max)) as txt
          from tgbot_sms_cache as c1
          inner join tgbot_sms_cache as c2
            on c2.company = c1.company
            and c2.period = 1
          where c1.period = 0
            and c1.company = 1 -- Мортон
        '''
}
