#!/bin/bash

# Create necessary directories if they don't exist
mkdir -p user_data/fq_dbs/dry/
mkdir -p user_data/fq_dbs/live/
mkdir -p user_data/ft_logs/

# List of strategies to run
strategies=(
    "ElliotV8_original_ichiv3" # 5m 1.25 dd-0.14
    "NASOSv7"                  # 5m 2.19 dd-0.37
    "NASOSv4_SMA"              # 5m 2.32 dd-0.27
    # "newstrategy4"             # 5m 1.20 dd-0.15 couldnt run
    # "SMAOG"                    # 5m 0.48 dd-0.11
    # "NotAnotherSMAOffsetStrategyHOv3"  # 5m 0.6 dd-0.13
)

# Corresponding ports for each strategy
ports=(
    1111 # Port for "ElliotV8_original_ichiv3"
    2222 # Port for "NASOSv7"
    3333 # Port for "NASOSv4_SMA"
    # 4444  # Port for "newstrategy4"
    # 5555  # Port for "SMAOG"
    # 6666  # Port for "NotAnotherSMAOffsetStrategyHOv3"
)

# Base configuration file
base_config="user_data/binance_all_pairs_config.json"

# DRY RUN
DRY_RUN=true

for i in "${!strategies[@]}"; do
    strategy=${strategies[$i]}
    port=${ports[$i]}

    # Generate unique DB URL based on strategy name
    if [ "$DRY_RUN" = true ]; then
        db_url="sqlite:///user_data/fq_dbs/dry/trades_${strategy}_dryrun.sqlite"
    else
        db_url="sqlite:///user_data/fq_dbs/live/trades_${strategy}_live.sqlite"
    fi

    # Create a temporary configuration with the hard-coded "listen_port"
    temp_config="temp_config_${strategy}.json"
    jq '.api_server.listen_port='"${port}"'' "${base_config}" >"${temp_config}"

    # Log file for the strategy
    logfile="user_data/ft_logs/log_${strategy}.txt"

    # Command to launch the strategy
    command="source .venv/bin/activate && freqtrade trade --config ${temp_config} --strategy ${strategy} --db-url ${db_url}"

    echo -e "\nLaunching strategy: ${strategy} with API server on port ${port}"
    nohup bash -c "${command}" >"${logfile}" 2>&1 &
    echo -e "Strategy ${strategy} is running. API server: http://127.0.0.1:${port}\nOutput and errors are logged to ${logfile}\n"
done

# Optional: Clean up temporary configuration files
# for strategy in "${strategies[@]}"; do
#     rm "temp_config_${strategy}.json"
# done
