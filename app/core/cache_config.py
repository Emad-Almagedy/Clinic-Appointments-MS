import json
import os
from sqlalchemy import select
from app.models import SystemSetting

SETTINGS_FILE = "data/system_settings_cache.json"

class SettingsCache:
    @staticmethod
    async def refresh(db):
        # fetch the settings from DB and save to JSON
        result = await db.execute(select(SystemSetting))
        settings = result.scalars().all()
        
        # convert list of objects to key value dict
        cache_data = {s.key: s.value for s in settings}
        
        # dump it to the JSON file
        with open(SETTINGS_FILE, "w") as f:
            json.dump(cache_data, f, indent=4)
        print("System settings cahe refreshed from the database")   
    
    @staticmethod
    def get(key: str, default = None):
        # if key doesnt exist return the default that will be passed 
        if not os.path.exists(SETTINGS_FILE):
            return default
        
        # open the file, load the JSON, return the value of the key 
        with open (SETTINGS_FILE, "r") as f:
            data = json.load(f)
            return data.get(key, default)     