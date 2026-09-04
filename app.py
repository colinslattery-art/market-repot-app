import pandas as pd
import requests
import streamlit as st

class MarketDataEngine:
    def __init__(self):
        # CoreLogic Trestle RESO Web API Endpoint
        self.base_url = "https://api-prod.corelogic.com/trestle/odata/Property"
        
        # Check if live keys are present in Streamlit Secrets
        self.client_id = st.secrets.get("TRESTLE_CLIENT_ID", None)
        self.bearer_token = st.secrets.get("TRESTLE_BEARER_TOKEN", None)
        self.is_live = bool(self.bearer_token)
        
        # The rigid master dictionary (Fallback Mode)
        self.local_fallback = {
            "Westlake": {"income": 250000, "price": 1850000, "dom": 38, "inventory": 145},
            "Southlake": {"income": 225000, "price": 1420000, "dom": 35, "inventory": 210},
            "Prosper": {"income": 159000, "price": 825000, "dom": 42, "inventory": 380},
            "Frisco": {"income": 145000, "price": 710000, "dom": 39, "inventory": 620},
            "Plano": {"income": 105000, "price": 540000, "dom": 31, "inventory": 480},
            "McKinney": {"income": 102000, "price": 525000, "dom": 33, "inventory": 510},
            "Richardson": {"income": 95000, "price": 465000, "dom": 32, "inventory": 180},
            "Garland": {"income": 76000, "price": 345000, "dom": 38, "inventory": 310},
            "Fort Worth": {"income": 72000, "price": 345000, "dom": 42, "inventory": 2100},
            "Dallas": {"income": 63000, "price": 435000, "dom": 44, "inventory": 3400},
            "Tyler": {"income": 61000, "price": 315000, "dom": 52, "inventory": 450},
            "Longview": {"income": 56000, "price": 275000, "dom": 58, "inventory": 310},
            "Lindale": {"income": 68000, "price": 325000, "dom": 45, "inventory": 110},
            "Bullard": {"income": 74000, "price": 385000, "dom": 42, "inventory": 85},
            "Canton": {"income": 58000, "price": 295000, "dom": 55, "inventory": 95}
        }

    def validate_market(self, city_name):
        """Validates if the market exists in the data source."""
        city_clean = city_name.title().split(',')[0].strip()
        
        if self.is_live:
            # When live, assume Trestle covers the NTREIS footprint
            return city_clean
        else:
            if city_clean in self.local_fallback:
                return city_clean
            return None

    def get_market_metrics(self, city_name):
        """Fetches market metrics from Trestle, or falls back to local data."""
        city = self.validate_market(city_name)
        if not city:
            raise ValueError(f"Market {city_name} not found in database.")

        if self.is_live:
            return self._fetch_trestle_live_data(city)
        else:
            return self.local_fallback[city]

    def _fetch_trestle_live_data(self, city):
        """OData v4 query to pull active inventory and pricing from RESO API."""
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Accept": "application/json"
        }
        
        # OData filter for active residential listings in the target city
        query_params = {
            "$filter": f"City eq '{city}' and StandardStatus eq 'Active' and PropertyType eq 'Residential'",
            "$select": "ListPrice,DaysOnMarket,City",
            "$top": 500  # Sample size for median calculations
        }
        
        try:
            response = requests.get(self.base_url, headers=headers, params=query_params, timeout=10)
            response.raise_for_status()
            data = response.json().get("value", [])
            
            if not data:
                return self.local_fallback.get(city) # Failsafe
                
            df = pd.DataFrame(data)
            
            return {
                "income": self.local_fallback.get(city, {}).get("income", 85000), # Demographics require a separate census API
                "price": int(df['ListPrice'].median()),
                "dom": int(df['DaysOnMarket'].median()),
                "inventory": len(df) # Representing active subset
            }
        except Exception as e:
            # Failsafe back to local data if the API trips
            return self.local_fallback.get(city)
