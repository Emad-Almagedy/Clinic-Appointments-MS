from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class SystemSettingBase(BaseModel):
    key: str
    value: str
    category: Optional[str] = "General"
    
class SystemSettingCreate(SystemSettingBase):
    pass

class SystemSettingUpdate(BaseModel):
    # we only need to update the value as the system is dependent on the specific name of the system setting
    value: str

class SystemSettingRead(SystemSettingBase):
    model_config = ConfigDict(from_attributes=True)
    id: int    
    key: str
    value: str
    


class SystemSettingsGrouped(BaseModel):
    clinic_information: List[SystemSettingRead] 
    appointment_settings: List[SystemSettingRead] 
    general_settings: List[SystemSettingRead]
            
    