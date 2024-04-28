#!/bin/bash

STRATEGY_NAME=$1

# Navigate to the correct directory where the scripts are located
cd user_data/strategies/

# Run the Python script to generate PAIR_LIST.json
python3 generate_pair_list_config.py

# Navigate back to the freqtrade root directory
cd ../../

# Run freqtrade with the newly generated PAIR_LIST.json
freqtrade trade --strategy $STRATEGY_NAME \
    --config user_data/kraken_live_config.json \
    --config user_data/kraken_EXCHANGE_KEYS.json \
    --config user_data/strategies/PAIR_LIST.json \
    --db-url sqlite:///user_data/fq_dbs/live/${STRATEGY_NAME}_live.sqlite
