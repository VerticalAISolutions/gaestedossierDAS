#!/bin/bash
streamlit run app.py \
  --server.headless true \
  --server.port ${PORT:-8501} \
  --server.address 0.0.0.0
