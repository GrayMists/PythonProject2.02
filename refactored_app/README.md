# Refactored Streamlit Sales Analysis

This project provides a modular and testable Streamlit application for sales analysis.

## Project structure
```
app/
  main.py
  config.py
  state.py
  services/
    supabase_client.py
    sales_repo.py
  core/
    text_cleaning.py
    data_processing.py
  ui/
    components.py
    charts.py
  pages/
    analysis.py
    ingest.py
  utils/
    constants.py
tests/
  test_compute_actual_sales.py
```

## Setup
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Provide Supabase credentials in `.streamlit/secrets.toml` based on the example file.

## Run the app
```bash
streamlit run app/main.py
```

## Run tests
```bash
pytest
```
