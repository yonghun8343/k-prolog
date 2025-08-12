request(45, 1491771679.213,
         [peer(ip(127,0,0,1)),
          method(get),request_uri('/prolog'),path('/prolog'),
          http_version(1_1),host(localhost),port(3037),
          connection('keep_alive'),upgrade_insecure_requests('1'),
          if_modified_since('Wed, 05 Apr 2017 23:24:08 GMT')]).
    

completed(45, 0.0009790000000000076, 0, 304, not_modified).

year_month_daily_visitors(2017, jan, 30018).
year_month_daily_visitors(2017, feb, 32913).
year_month_daily_visitors(2017, mar, 35871).

year_month_total(Year, Month, Total) :-
        Total := Days*Daily,
        year_month_days(Year, Month, Days),
        year_month_daily_visitors(Year, Month, Daily).

year_month_days(2017, jan, 31).
year_month_days(2017, feb, 28).
year_month_days(2017, mar, 31).