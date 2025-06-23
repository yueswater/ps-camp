import logging

from ps_camp.db import engine
from ps_camp.sql_models import Base

Base.metadata.create_all(engine)

logging.info("Neon 資料表初始化完成")
