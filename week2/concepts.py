from pydantic import BaseModel,field_validator


class UserProfile(BaseModel):
    username:str
    level:int
    is_online:bool=False

    @field_validator("username")
    @classmethod
    def username_must_not_space(cls,value:str)->str:
        if " " in value:
            raise ValueError("Username cannot contain spaces!")
        return value
    @field_validator("level")
    @classmethod
    def level_checker(cls,value:int)->int:
        if not (1<=value<=100):
            raise ValueError("Level must be between 1 and 100")
        return value


player = UserProfile(username="ShadowNinja", level="25")
data=player.model_dump()
print(data)
print(type(data))