# Underemployment Beyond Unemployment: Streamlit Dashboard

This application presents the Data Story Telling final project as a Streamlit and Plotly dashboard. It shows how underemployment among Filipino workers differs by education level from 2023 to 2025 (UN SDG 8: Decent Work and Economic Growth, Target 8.5).

## Files
- `app.py`: Streamlit application (title bar, filters, KPI cards, and five charts on one page)
- `Integrated_Underemployment_Dataset__2_.csv`: monthly PSA Labor Force Survey data, 2023 to 2025 (36 months, five education groups plus the national rate, and counts by age and sex)
- `requirements.txt`: Python dependencies (streamlit, plotly, pandas, numpy)
- `README.md`: this file

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The dashboard opens in a browser. Keep the CSV in the same folder as `app.py`, and the app will find it by itself. If it cannot, the page will ask you to upload the file.

## How to use the dashboard
- Use the **Year** buttons to view one year or all years.
- Use the **Education group** buttons to focus on one group. The KPI cards and charts update, and the gap chart then shows that group compared with the national rate.
- Use **From month** and **To month** to limit the months shown, and **Reset** to return to the full view.
- Click a bar in **Rate by Education Group** or **Education Gap by Year** to filter by that group or year.
- Use **Count / Share** on the Age and Sex chart to switch between numbers and percentages.
- Hover over any chart to see exact values.

## What the dashboard shows
- **KPI cards:** national rate, highest group, lowest group, education gap, and highest month
- **Rate by Education Group:** average rate of each group, with a dashed line for the national average
- **Education Gap by Year:** highest group minus lowest group for each year
- **Average Rate by Year:** one line per group, compared with the national line
- **Monthly Rate by Education Group:** month by month rates, with the highest and lowest months marked when no filter is on
- **Age and Sex:** counts of underemployed workers by age group, males on the left and females on the right

## Analytical boundaries
- The dashboard shows differences between education groups and how they changed. It does not explain why underemployment changes, and it does not show that education causes the differences.
- The data covers only three years (36 monthly readings), so the dashboard makes no forecasts and the patterns should not be projected forward.
- Yearly and overall rates are simple averages of the monthly rates. The data has no margins of error, so very small changes, such as 0.02 points between 2024 and 2025, are not treated as meaningful.
- The education gap compares the highest and lowest group, which was No Grade Completed and College in all three years. It does not describe the groups in between.
- The source education categories were combined into five broader groups, and a different grouping could change the results.
- The Age and Sex chart shows counts, not rates. A larger count can come from having more workers in that age group, so it does not show a higher risk.
- The national average is used as a reference line, not as an official target.
- The data has no job type, pay, hours, region, or industry, so the reasons behind the patterns cannot be seen.
- Figures describe groups, not individual workers, and must not be used to screen or rank people.