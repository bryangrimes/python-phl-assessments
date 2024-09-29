# python-phl-assessments
python version of futurestateanalytics/phl-assessments R solution

Parquet files are included in the repo for now to "just work"

## Running the Streamlit App Locally
`streamlit run app.py`


## Running the Streamlit App in Docker

`docker build -t streamlit-phl-assessment .`

`docker run -p 8501:8501 streamlit-phl-assessment`
