# Formula 1 Data Engineering Pipeline

End-to-end data pipeline using Formula 1 racing data from historical Ergast CSVs (pre-2023) and the Jolpica F1 API (2023+).

## Data Sources

| Source                                                   | Period        | Type                     | Update Frequency  |
| -------------------------------------------------------- | ------------- | ------------------------ | ----------------- |
| [Ergast CSV Mirror](https://github.com/rubenv/ergast-mrd) | 1950–2022    | CSV (historical archive) | One-time download |
| [Jolpica F1 API](https://api.jolpi.ca/ergast/f1)          | 2023–current | JSON (live API)          | After each race   |
