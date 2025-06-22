from ps_camp.db.session import engine
from ps_camp.sql_models import user_model, post_model, npc_model

user_model.Base.metadata.create_all(bind=engine)
post_model.Base.metadata.create_all(bind=engine)
npc_model.Base.metadata.create_all(bind=engine)

print("Neon 資料表初始化完成")
