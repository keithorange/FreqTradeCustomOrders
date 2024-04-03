import json
import os

if __name__ == "__main__":
    # Define the path to your pair list and the output config file
    pair_list_path = 'pair_list.txt'
    output_config_path = 'PAIR_LIST.json'

    # Read the pair list from the text file
    with open(pair_list_path, 'r') as file:
        pairs = [line.strip() for line in file.readlines() if line.strip()]

    # Ensure BTC/USD is always included in the whitelist
    default_pair = "BTC/USD"
    if default_pair not in pairs:
        pairs.append(default_pair)
        
    # Print out the pair list
    print(f"Pair list: {pairs}")

    # Define the base structure of your configuration file
    config = {
        "exchange": {
            "name": "kraken",
            "pair_whitelist": pairs,  # Insert the pair list here
            "pair_blacklist": []
        }
    }

    # Save the configuration to the JSON file
    with open(output_config_path, 'w') as json_file:
        json.dump(config, json_file, indent=4)

    print(f"Config file generated at: {output_config_path}")
