import os
import logging
from datetime import datetime
from uuid import uuid4, UUID
from flask import Flask, render_template, request, redirect, url_for, session, abort, jsonify, flash
from dotenv import load_dotenv
from ps_camp.db.session import SessionLocal, get_db
from ps_camp.sql_models import User
from ps_camp.sql_models.post_model import Post
from ps_camp.sql_models.npc_model import NPC
from ps_camp.repos.user_sql_repo import UserSQLRepository
from ps_camp.repos.post_sql_repo import PostSQLRepository
from ps_camp.repos.npc_sql_repo import NPCSQLRepository
from ps_camp.repos.bank_sql_repo import BankSQLRepository
from ps_camp.sql_models.bank_model import OwnerType, TransactionType
from ps_camp.utils.password_hasher import PasswordHasher
from ps_camp.utils.session_helpers import refresh_user_session
import markdown

load_dotenv()

def map_role_to_owner_type(role: str) -> OwnerType:
    if role == "admin":
        return OwnerType.admin
    elif role == "政黨":
        return OwnerType.party
    elif role == "利益團體":
        return OwnerType.group
    else:
        return OwnerType.user

def create_app():
    app = Flask(__name__)
    app.secret_key = "2025ntupscamp"

    @app.route("/")
    @refresh_user_session
    def home():
        if session.get("user"):
            db = SessionLocal()
            bank_repo = BankSQLRepository(db)

            user = session["user"]
            user_id = user["id"]
            role = user["role"]
            owner_type = map_role_to_owner_type(role)

            account = bank_repo.get_account_by_owner(user_id, owner_type)
            if account:
                session["user"]["coins"] = account.balance
                
        return render_template("index.html")

    @app.route("/bank")
    def bank():
        if not session.get("user"):
            return redirect(url_for("login"))

        db = SessionLocal()
        bank_repo = BankSQLRepository(db)

        user = session["user"]
        user_id = user["id"]
        role = user["role"]
        owner_type = map_role_to_owner_type(role)

        account = bank_repo.get_account_by_owner(user_id, owner_type)
        if not account:
            return "找不到您的銀行帳戶，請聯繫主辦方", 404

        transactions = bank_repo.get_transactions(account.id)
        return render_template("bank.html", account=account, transactions=transactions)

    @app.route("/api/bank/transfer", methods=["POST"])
    def bank_transfer():
        if not session.get("user"):
            return jsonify(success=False, message="請先登入"), 401

        data = request.get_json()
        to_account_number = data.get("to_account_number")
        amount = int(data.get("amount", 0))
        note = data.get("note", "")

        if not to_account_number or amount <= 0:
            return jsonify(success=False, message="輸入不完整或金額不正確"), 400

        db = SessionLocal()
        bank_repo = BankSQLRepository(db)

        from_user_id = session["user"]["id"]
        role = session["user"]["role"]
        from_owner_type = map_role_to_owner_type(role)

        from_account = bank_repo.get_account_by_owner(from_user_id, from_owner_type)
        to_account = bank_repo.get_account_by_number(to_account_number)

        if not from_account or not to_account:
            return jsonify(success=False, message="找不到帳戶"), 404

        try:
            bank_repo.create_transaction(
                from_account=from_account,
                to_account=to_account,
                amount=amount,
                note=note,
                transaction_type=TransactionType.transfer
            )
        except ValueError as e:
            return jsonify(success=False, message=str(e)), 400

        return jsonify(success=True, new_balance=from_account.balance)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        db = SessionLocal()
        repo = UserSQLRepository(db)
        hasher = PasswordHasher()
        if request.method == "POST":
            data = request.form

            new_user = User(
                id=str(uuid4()),
                username=data["username"],
                fullname=data["fullname"],
                hashed_password=hasher.hash_password(data["password"]),
                role=data["role"],
                coins=500
            )

            repo.add(new_user)

            bank_repo = BankSQLRepository(db)
            owner_type = map_role_to_owner_type(data["role"])
            bank_repo.create_account(owner_id=new_user.id, owner_type=owner_type, initial_balance=new_user.coins)

            return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        db = SessionLocal()
        repo = UserSQLRepository(db)
        hasher = PasswordHasher()
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            user = repo.get_by_username(username)
            if user and hasher.verify_password(password, user.hashed_password):
                session["user"] = {
                    "id": str(user.id),
                    "fullname": user.fullname,
                    "coins": user.coins,
                    "role": user.role
                }
                return redirect(url_for("home"))
            else:
                return render_template("login.html", error=True)
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("home"))

    @app.route("/posts")
    @refresh_user_session
    def posts():
        db = SessionLocal()
        repo = PostSQLRepository(db)
        category = request.args.get("category", "").strip()
        keyword = request.args.get("search", "").strip()
        if keyword:
            posts = repo.search(keyword)
        elif category:
            posts = repo.filter(category=category)
        else:
            posts = repo.get_all()

        for post in posts:
            preview = post.content[:300]
            post.content = markdown.markdown(preview, extensions=["nl2br"])

        return render_template("posts.html", posts=posts)

    @app.route("/npcs")
    def npcs():
        db = SessionLocal()
        repo = NPCSQLRepository(db)
        all_npcs = repo.get_all()
        return render_template("npcs.html", npcs=all_npcs)
    
    @app.route("/admin/distribute", methods=["GET", "POST"])
    def distribute_money():
        if session.get("user", {}).get("role") != "admin":
            flash("只有管理員可以發錢！", "danger")
            return redirect("/")
        
        db = SessionLocal()
        user_repo = UserSQLRepository(db)
        bank_repo = BankSQLRepository(db)

        admin_id = UUID(os.getenv("ADMIN_ID"))
        admin_account = bank_repo.get_account_by_owner(admin_id, OwnerType.admin)

        if not admin_account:
            flash("找不到管理員銀行帳戶", "danger")
            return redirect("/")

        if request.method == "POST":
            try:
                amount = int(request.form["amount"])
                if amount <= 0:
                    raise ValueError("金額必須為正整數")
                
                users = db.query(user_repo.model).filter(user_repo.model.role != "admin").all()
                count = 0

                for user in users:
                    if user.id == admin_id:
                        continue
                    user_account = bank_repo.get_account_by_owner(user.id, map_role_to_owner_type(user.role))
                    if not user_account:
                        continue

                    logging.debug("發錢中...")
                    bank_repo.create_transaction(
                        from_account=admin_account,
                        to_account=user_account,
                        amount=amount,
                        note="大撒幣",
                        transaction_type=TransactionType.distribute
                    )
                    count += 1
                
                db.commit()
                flash(f"成功發送 {amount * count} 政治幣給 {count} 位使用者", "success")
                return redirect("/")
            except Exception as e:
                db.rollback()
                flash(f"發送失敗：{str(e)}", "danger")
                logging.error(f"發錢失敗：{str(e)}")
            
        return render_template("distribute.html")

    @app.route("/posts/<string:post_id>", methods=["GET", "POST"])
    def view_post(post_id: str):
        db = SessionLocal()
        post_repo = PostSQLRepository(db)
        try:
            post_uuid = UUID(post_id)
        except ValueError:
            abort(404)
        post = post_repo.get_by_id(post_uuid)
        if not post:
            abort(404)

        if request.method == "POST":
            if not session.get("user"):
                return redirect(url_for("login"))
            reply_content = request.form.get("reply", "").strip()
            if reply_content:
                reply_obj = {
                    "id": str(uuid4()),
                    "user_id": session["user"]["id"],
                    "user_name": session["user"]["fullname"],
                    "content": reply_content,
                    "created_at": datetime.utcnow().isoformat(),
                }
                post.replies.append(reply_obj)
                db.commit()
            return redirect(url_for("view_post", post_id=post_id))

        post.content = markdown.markdown(post.content, extensions=["nl2br"])
        for r in post.replies:
            r["content"] = markdown.markdown(r["content"], extensions=["nl2br"])

        return render_template("view_post.html", post=post)

    @app.route("/posts/new", methods=["GET", "POST"])
    def new_post():
        if not session.get("user"):
            return redirect(url_for("login"))

        db = SessionLocal()
        repo = PostSQLRepository(db)

        if request.method == "POST":
            data = request.form
            user_id = UUID(session["user"]["id"])
            user_role = session["user"]["role"]
            owner_type = map_role_to_owner_type(user_role)  # 加上這行！

            post = Post(
                id=uuid4(),
                title=data["title"],
                category=data["category"],
                content=data["content"],
                created_at=datetime.utcnow(),
                created_by=user_id,
                replies=[],
                likes=[],
            )

            repo.add(post, owner_id=user_id, owner_type=owner_type)  # 要傳入 owner_type
            return redirect(url_for("posts"))

        return render_template("new_post.html")


    @app.route("/api/posts/<string:post_id>/like", methods=["POST"])
    def like_post(post_id: str):
        if not session.get("user"):
            return jsonify(success=False, message="請先登入"), 401
        db = SessionLocal()
        repo = PostSQLRepository(db)
        try:
            post_uuid = UUID(post_id)
        except ValueError:
            return jsonify(success=False, message="無效貼文 ID"), 400

        post = repo.get_by_id(post_uuid)
        if not post:
            return jsonify(success=False, message="貼文不存在"), 404

        user_id = session["user"]["id"]
        if user_id in post.likes:
            post.likes.remove(user_id)
        else:
            post.likes.append(user_id)

        db.commit()
        return jsonify(success=True, likes=len(post.likes))

    return app

# TODO: change to guicorn
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
