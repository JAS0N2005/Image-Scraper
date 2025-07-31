"""
Input processor for reading and preparing data from the Excel sheet.
"""

import pandas as pd

def process_input_excel(config):
    df = pd.read_excel(config["INPUT_EXCEL"], usecols=["Name", "Type", "Website", "ActivityId"])
    with open(config["DATA_LOG_CSV"], 'w', newline='', encoding='utf-8') as f:
        f.write("Row,ActivityId,Type,Name,Website,Status,Reason\n")
        for idx, row in df.iterrows():
            website = str(row['Website'])
            if not website or not website.startswith("http"):
                f.write(f"{idx+1},{row['ActivityId']},{row['Type']},{row['Name']},{website},Skipped,No website\n")
            elif "facebook.com" in website or "instagram.com" in website:
                f.write(f"{idx+1},{row['ActivityId']},{row['Type']},{row['Name']},{website},Skipped,Social link\n")
            else:
                f.write(f"{idx+1},{row['ActivityId']},{row['Type']},{row['Name']},{website},Pending,\n")