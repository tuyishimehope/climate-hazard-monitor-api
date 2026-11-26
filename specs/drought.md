1. Drought = a long period with much less rain than normal.
2. Add the rain of the 30 full days before today.
   Total <= 20 mm -> drought. Any day missing -> unknown. (20 mm uncalibrated)
3. https://api.open-meteo.com/v1/forecast?latitude=-1.7938&longitude=30.1406
   &daily=precipitation_sum&timezone=Africa/Kigali&past_days=30&forecast_days=1
4. WINDOW_DAYS = 30, DROUGHT_MM = 20
   Keep only the 30 days before today. Ignore today.
   Reuse window_days and rain_total from F1. New: classify uses <=.