FROM python:3.11-slim

COPY requirements.txt /src/requirements.txt

RUN pip install -r /src/requirements.txt

COPY jamming2d.py /src/jamming2d.py
COPY jammingcentroids2d.pkl.gz /src/jammingcentroids2d.pkl.gz
COPY jammingdfinfo2d.pkl.gz /src/jammingdfinfo2d.pkl.gz
COPY jammingdftriple2d.pkl.gz /src/jammingdftriple2d.pkl.gz
COPY affil_geo_dict.pkl /src/affil_geo_dict.pkl
COPY source_page_dict.pkl /src/source_page_dict.pkl

WORKDIR /src

ENTRYPOINT [ "streamlit", "run", "jamming2d.py" ]