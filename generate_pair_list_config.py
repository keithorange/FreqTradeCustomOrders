import json
import os


def make_noise():
    # This is a placeholder for making noise; you can customize it as needed
    print('\a')  # This makes a beep noise in many systems


def fix_pairs(pairs):
    corrected_pairs = []
    changes_made = False
    for pair in pairs:
        base, suffix = pair.rsplit('/', 1)
        if suffix != "USD":
            corrected_pair = base + "/USD"  # Correct the pair ending
            corrected_pairs.append(corrected_pair)
            print(f"Corrected pair: {pair} -> {corrected_pair}")
            changes_made = True
        else:
            corrected_pairs.append(pair)
    return corrected_pairs, changes_made


if __name__ == "__main__":
    # Define the path to your pair list and the output config file
    pair_list_path = 'pair_list.txt'
    output_config_path = 'PAIR_LIST.json'

    # Read the pair list from the text file
    with open(pair_list_path, 'r') as file:
        pairs = [line.strip() for line in file.readlines() if line.strip()]

    # Remove duplicates
    pairs = list(set(pairs))

    # Fix any pairs with incorrect endings
    pairs, changes_made = fix_pairs(pairs)

    # Remove duplicates again after corrections
    pairs = list(set(pairs))

    # Make noise if any changes were made
    if changes_made:
        make_noise()
        print("Incorrect pair endings found and corrected. See log for details.")

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
