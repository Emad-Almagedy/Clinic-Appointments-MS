from pydantic import BaseModel
from typing import Optional, List

class SystemSettingBase(BaseModel):
    key: str
    value: str
    category: Optional[str] = "General"
    
class SystemSettingCreate(SystemSettingBase):
    pass

class SystemSettingsUpdate(BaseModel):
    # we only need to update the value as the system is dependent on the specific name of the system setting
    value: str

class SystemSettingRead(SystemSettingBase):
    id: int    
    key: str
    value: str
    
    class Config:
        from_attributes = True

class SystemSettingsGrouped(BaseModel):
    clinic_information: List[SystemSettingRead] 
    appointment_settings: List[SystemSettingRead] 
    general_settings: List[SystemSettingRead]
            
    