from ps_camp.db import engine
from ps_camp.sql_models import Base

Base.metadata.create_all(engine)

print("Neon 資料表初始化完成")
