# astradb-confluence-chatbot

This is a sample repo for a service that indexes data from confluence into an astradb vector table using vertex ai's embeddings api and provides answers to questions using vertex ai's llm.

It uses langchain and cassio for simplicity.

To run:

    python3 -m venv ./venv


    source venv/bin/activate


    pip3 install -r requirements.txt 


    python3 src/main.py

