#!/bin/bash
# Run chatbot locally without container

#Activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies if needed
pip install -q -r requirements.txt

# check .env exitsts
if [ ! -f .env ]; then
    echo "No .env file found!"
    cp .env.template .env
    echo "Please edit .env and add your API key"
    exit 1
fi 

# run the app
streamlit run SPEAR_Earth_System_Data_Assistant.py
