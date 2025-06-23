from ps_camp.db.session import SessionLocal
from ps_camp.sql_models.referendum_model import Referendum


def main():
    db = SessionLocal()

    ref1 = Referendum(
        title="同性婚姻合法化", description="是否支持同性婚姻完全合法化？"
    )
    ref2 = Referendum(
        title="下修投票年齡至 18 歲", description="是否同意將投票年齡下修至 18 歲？"
    )

    db.add_all([ref1, ref2])
    db.commit()
    print("✅ 公投案已新增完畢！")


if __name__ == "__main__":
    main()
