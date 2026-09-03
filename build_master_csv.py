import os
import pandas as pd

def build_master_redfin_database():
    # Mapping attached filenames to clean dataset tags
    file_mapping = {
        'housing_market': 'redfin_housing_market_monthly_all_country_key_metrics_2026_Jan_to_2026_Jul_2.csv',
        'affordability': 'redfin_affordability_monthly_all_country_all_residential_homeowner_2026_Jan_to_2026_Jun_2.csv',
        'buyers_sellers': 'redfin_buyers_and_sellers_monthly_all_country_2026_Jan_to_2026_Jul_2.csv',
        'cash_loan': 'redfin_cash_loan_monthly_all_country_2026_Jan_to_2026_Jun_2.csv',
        'cancellations': 'redfin_contract_cancellations_monthly_all_country_2026_Jan_to_2026_Jul_2.csv',
        'delistings': 'redfin_delistings_relistings_monthly_all_country_2026_Jan_to_2026_Jul_2.csv',
        'existing_home_sales': 'redfin_ehs_monthly_all_country_2026_Jan_to_2026_Jul_2.csv',
        'investors': 'redfin_investors_by_metro_all_country_2026_Q1_to_2026_Q2_2.csv',
        'luxury': 'redfin_luxury_luxury_all_country_key_metrics_2026_Jan_to_2026_Jul_2.csv',
        'migration': 'redfin_migration_od_pairs_all_states_2026_Q1_to_2026_Q1_2.csv'
    }

    cleaned_dfs = []
    print("Starting master database consolidation...")

    for dataset_tag, filename in file_mapping.items():
        # Fallback to check without the trailing '_2' if renamed locally
        if not os.path.exists(filename):
            alt_filename = filename.replace('_2.csv', '.csv')
            if os.path.exists(alt_filename):
                filename = alt_filename
            else:
                print(f"⚠️ Warning: File not found: {filename}. Skipping...")
                continue

        print(f"Processing: {filename}")
        
        # Load CSV (handles tab or comma delimiters)
        try:
            df = pd.read_csv(filename, sep='\t', low_memory=False)
            if len(df.columns) <= 1:
                df = pd.read_csv(filename, sep=',', low_memory=False)
        except Exception:
            df = pd.read_csv(filename, sep=',', low_memory=False)

        # Standardize column headers
        df.columns = (
            df.columns.str.strip()
            .str.lower()
            .str.replace(' ', '_')
            .str.replace('(%)-', 'pct_')
            .str.replace('(%)', 'pct')
            .str.replace('($)', 'usd')
            .str.replace('(ppts)', 'ppts')
            .str.replace('(days)', 'days')
        )

        # Tag record with dataset category
        df['dataset_type'] = dataset_tag
        cleaned_dfs.append(df)

    if cleaned_dfs:
        # Merge all into one Master DataFrame
        master_df = pd.concat(cleaned_dfs, ignore_index=True)

        # Standardize dates
        if 'period_end' in master_df.columns:
            master_df['period_end'] = pd.to_datetime(master_df['period_end'], errors='coerce')
            master_df = master_df.sort_values(by='period_end', ascending=False)

        output_filename = "master_redfin_database.csv"
        master_df.to_csv(output_filename, index=False, encoding='utf-8')
        
        print(f"\n✅ SUCCESS: Created '{output_filename}'")
        print(f"Total Combined Records: {len(master_df):,}")
        print(f"Total Unified Columns: {len(master_df.columns)}")
        return master_df
    else:
        print("❌ Error: No files were loaded.")
        return None

if __name__ == "__main__":
    build_master_redfin_database()