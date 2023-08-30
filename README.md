# openalex-jamming-guidance

First run the notebook **jamming2d.ipynb** to create the data files:

* jammingcentroids2d.pkl
* jammingdfinfo2d.pkl
* jammingdftriple2d.pkl
* source_page_dict.pkl

compress these files with
```
>gzip -k filename.pkl
```
to create the compressed files **filename.pkl.gz** that are loaded into memory for jamming2d.py

To run the streamlit app:

```
>streamlit run jamming2d.py
```