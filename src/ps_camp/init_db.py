from ps_camp.db import engine
from ps_camp.sql_models import Base
from ps_camp.sql_models.user_model import User
from ps_camp.sql_models.bank_model import BankAccount

Base.metadata.create_all(engine)

print("Neon 資料表初始化完成")
