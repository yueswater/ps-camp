import json
import logging
import os
from datetime import UTC, datetime
from uuid import UUID, uuid4

import markdown
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    render_template_string,
    request,
    session,
    url_for,
)
from weasyprint import HTML

from ps_camp.db.session import get_db_session
from ps_camp.repos.bank_sql_repo import BankSQLRepository
from ps_camp.repos.post_sql_repo import PostSQLRepository
from ps_camp.repos.user_sql_repo import UserSQLRepository
from ps_camp.sql_models.bank_model import OwnerType, TransactionType
from ps_camp.sql_models.post_model import Post
from ps_camp.sql_models.user_model import User
from ps_camp.utils.password_hasher import PasswordHasher
from ps_camp.utils.pdf_templates import bank_report_template
from ps_camp.utils.session_helpers import refresh_user_session

load_dotenv()
ADMIN_ID = os.getenv("ADMIN_ID")


def map_role_to_owner_type(role: str) -> OwnerType:
    if role == "admin":
        return OwnerType.admin
    elif role == "party":
        return OwnerType.party
    elif role == "group":
        return OwnerType.group
    else:
        return OwnerType.user


def get_account_by_user(user, bank_repo, db):
    role = user["role"]
    affiliation_name = user["fullname"]

    if role == "member":
        owner_id = user.get("affiliation_id")
        owner_type_str = user.get("affiliation_type")
        if not owner_id or not owner_type_str:
            return None, None
        owner_type = OwnerType(owner_type_str)

        affiliation = (
            db.query(User).filter_by(id=owner_id, role=owner_type.value).first()
        )
        if affiliation:
            affiliation_name = affiliation.fullname
    else:
        owner_id = user["id"]
        owner_type = map_role_to_owner_type(role)

    account = bank_repo.get_account_by_owner(owner_id, owner_type)
    return account, affiliation_name


def create_app():
    app = Flask(__name__)
    app.secret_key = "2025ntupscamp"

    @app.route("/")
    @refresh_user_session
    def home():
        if session.get("user"):
            with get_db_session() as db:
                bank_repo = BankSQLRepository(db)

                user = session["user"]
                account, _ = get_account_by_user(user, bank_repo, db)
                if account:
                    session["user"]["coins"] = account.balance
                else:
                    session["user"]["coins"] = 0  # 或保留預設
                    flash("找不到對應的銀行帳戶，請聯繫主辦方", "warning")

        return render_template("index.html")

    @app.route("/ping")
    def ping():
        return "pong", 200

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.route("/bank")
    def bank():
        if not session.get("user"):
            return redirect(url_for("login"))

        with get_db_session() as db:
            bank_repo = BankSQLRepository(db)
            user = session["user"]

            account, affiliation_name = get_account_by_user(user, bank_repo, db)
            if not account:
                return "找不到您的銀行帳戶，請聯繫主辦方", 404

            transactions = bank_repo.get_transactions(account.id)
            return render_template(
                "bank.html",
                account=account,
                transactions=transactions,
                affiliation_name=affiliation_name,
            )

    @app.route("/bank/export")
    def export_bank_report():
        user = session.get("user")
        if not user:
            return redirect(url_for("login"))

        with get_db_session() as db:
            try:
                bank_repo = BankSQLRepository(db)
                user_repo = UserSQLRepository(db)

                account = bank_repo.get_account_by_owner(
                    user["id"], map_role_to_owner_type(user["role"])
                )
                transactions = bank_repo.get_transactions(account.id)

                related_account_ids: set[str] = set()
                for tx in transactions:
                    related_account_ids.update([tx.from_account_id, tx.to_account_id])

                related_accounts = bank_repo.get_accounts_by_ids(
                    list(related_account_ids)
                )
                account_map = {acc.id: acc for acc in related_accounts}

                owner_ids = [acc.owner_id for acc in related_accounts]
                owners = user_repo.get_users_by_ids(owner_ids)
                owner_map = {u.id: u.fullname for u in owners}

                account_to_fullname = {
                    acc_id: owner_map.get(acc.owner_id, "未知使用者")
                    for acc_id, acc in account_map.items()
                }

                html = render_template_string(
                    bank_report_template,
                    account=account,
                    transactions=transactions,
                    account_to_fullname=account_to_fullname,
                )
                pdf = HTML(string=html).write_pdf()

                filename = f"bank_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                resp = make_response(pdf)
                resp.headers["Content-Type"] = "application/pdf"
                resp.headers["Content-Disposition"] = f"inline; filename={filename}"
                return resp
            except Exception as e:
                flash(f"輸出明細發生錯誤：{e}")

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

        with get_db_session() as db:
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
                    transaction_type=TransactionType.transfer,
                )
            except ValueError as e:
                return jsonify(success=False, message=str(e)), 400

            return jsonify(success=True, new_balance=from_account.balance)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        with get_db_session() as db:
            repo = UserSQLRepository(db)
            hasher = PasswordHasher()
            if request.method == "POST":
                data = request.form
                role = data["role"]

                affiliation_id = data.get("affiliation_id")
                affiliation_type = data.get("affiliation_type")

                if role == "member":
                    if not affiliation_id or not affiliation_type:
                        flash("請選擇所屬政黨或利益團體")
                        return redirect(url_for("register"))

                new_user = User(
                    id=str(uuid4()),
                    username=data["username"],
                    fullname=data["fullname"],
                    hashed_password=hasher.hash_password(data["password"]),
                    role=data["role"],
                    coins=10000,
                    affiliation_id=affiliation_id if role == "member" else None,
                    affiliation_type=affiliation_type if role == "member" else None,
                )

                repo.add(new_user)

                bank_repo = BankSQLRepository(db)

                if role != "member":
                    owner_type = map_role_to_owner_type(data["role"])
                    bank_repo.create_account(
                        owner_id=new_user.id,
                        owner_type=owner_type,
                        initial_balance=new_user.coins,
                    )

                return redirect(url_for("login"))

            # TODO: list all role == "party" or role == "group"
            all_users = repo.get_all()
            parties = [p for p in all_users if p.role == "party"]
            interest_groups = [g for g in all_users if g.role == "group"]

            return render_template(
                "register.html", parties=parties, interest_groups=interest_groups
            )

    @app.route("/login", methods=["GET", "POST"])
    def login():
        with get_db_session() as db:
            repo = UserSQLRepository(db)
            hasher = PasswordHasher()
            if request.method == "POST":
                username = request.form["username"]
                password = request.form["password"]
                user = repo.get_by_username(username)

                if user and hasher.verify_password(password, user.hashed_password):
                    affiliation_name = None
                    if (
                        user.role == "member"
                        and user.affiliation_id
                        and user.affiliation_type
                    ):
                        affiliation = repo.get_by_id(user.affiliation_id)
                        if affiliation:
                            affiliation_name = affiliation.fullname

                    session["user"] = {
                        "id": str(user.id),
                        "fullname": user.fullname,
                        "coins": user.coins,
                        "role": user.role,
                        "affiliation_id": (
                            str(user.affiliation_id) if user.affiliation_id else None
                        ),
                        "affiliation_type": (
                            str(user.affiliation_type.value)
                            if user.affiliation_type
                            else None
                        ),
                        "affiliation_name": affiliation_name,
                    }
                    return redirect(url_for("home"))
                else:
                    return render_template("login.html", error=True)
            return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("home"))

    @app.route("/profile", methods=["GET", "POST"])
    def profile():
        with get_db_session() as db:
            user_repo = UserSQLRepository(db)
            hasher = PasswordHasher()

            user = session.get("user")
            user_obj = user_repo.get_by_id(UUID(user["id"]))

            if request.method == "POST":
                old_password = request.form["old_password"]
                new_password = request.form["new_password"]
                confirm_password = request.form["confirm_password"]

                if not hasher.verify_password(old_password, user_obj.hashed_password):
                    flash("舊密碼錯誤")
                    return redirect(url_for("profile"))

                if new_password != confirm_password:
                    flash("新密碼與確認不一致")
                    return redirect(url_for("profile"))

                user_obj.hashed_password = hasher.hash_password(new_password)
                db.commit()

                session.clear()
                return redirect(url_for("login"))

            return render_template("profile.html")

    @app.route("/posts")
    @refresh_user_session
    def posts():
        with get_db_session() as db:
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
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, "static", "data", "npcs.json")

        with open(json_path, encoding="utf-8") as f:
            npcs = json.load(f)

        page = int(request.args.get("page", 1))
        per_page = 9
        start = (page - 1) * per_page
        end = start + per_page
        total_pages = (len(npcs) + per_page - 1) // per_page

        return render_template(
            "npc_gallery.html", npcs=npcs[start:end], page=page, total_pages=total_pages
        )

    @app.route("/distribute", methods=["GET", "POST"])
    def distribute_money():
        role = session.get("user", {}).get("role")
        if role != "admin":
            flash("只有管理員可以發錢！", "danger")
            return redirect("/")

        with get_db_session() as db:
            user_repo = UserSQLRepository(db)
            bank_repo = BankSQLRepository(db)

            admin_id = UUID(session["user"]["id"])
            admin_account = bank_repo.get_account_by_owner(admin_id, OwnerType.admin)

            if not admin_account:
                flash("找不到管理員銀行帳戶", "danger")
                return redirect("/")

            if request.method == "POST":
                try:
                    amount = int(request.form["amount"])
                    if amount <= 0:
                        raise ValueError("金額必須為正整數")

                    users = (
                        db.query(user_repo.model)
                        .filter(user_repo.model.role != "admin")
                        .all()
                    )
                    count = 0

                    for user in users:
                        if user.id == admin_id:
                            continue
                        user_account = bank_repo.get_account_by_owner(
                            user.id, map_role_to_owner_type(user.role)
                        )
                        if not user_account:
                            continue

                        logging.debug("發錢中...")
                        bank_repo.create_transaction(
                            from_account=admin_account,
                            to_account=user_account,
                            amount=amount,
                            note="大撒幣",
                            transaction_type=TransactionType.distribute,
                        )
                        count += 1

                    db.commit()
                    flash(
                        f"成功發送 {amount * count} 政治幣給 {count} 位使用者",
                        "success",
                    )
                    return redirect("/")
                except Exception as e:
                    db.rollback()
                    flash(f"發送失敗：{str(e)}", "danger")
                    logging.error(f"發錢失敗：{str(e)}")

            return render_template("distribute.html")

    @app.route("/posts/<string:post_id>", methods=["GET", "POST"])
    def view_post(post_id: str):
        with get_db_session() as db:
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

        with get_db_session() as db:
            repo = PostSQLRepository(db)

            if request.method == "POST":
                data = request.form
                user_id = UUID(session["user"]["id"])
                user_role = session["user"]["role"]
                owner_type = map_role_to_owner_type(user_role)

                post = Post(
                    id=uuid4(),
                    title=data["title"],
                    category=data["category"],
                    content=data["content"],
                    created_at=datetime.now(UTC),
                    created_by=user_id,
                    replies=[],
                    likes=[],
                )

                repo.add(post, owner_id=user_id, owner_type=owner_type)
                return redirect(url_for("posts"))

            return render_template("new_post.html")

    @app.route("/api/posts/<string:post_id>/like", methods=["POST"])
    def like_post(post_id: str):
        if not session.get("user"):
            return jsonify(success=False, message="請先登入"), 401
        with get_db_session() as db:
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
# if __name__ == "__main__":
#     app = create_app()
#     app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
