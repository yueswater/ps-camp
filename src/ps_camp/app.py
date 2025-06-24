import json
import logging
import os
from datetime import UTC, datetime, timezone
from uuid import uuid4

import markdown
from dateutil.parser import isoparse
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    current_app,
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
from ps_camp.repos.candidate_sql_repo import CandidateSQLRepository
from ps_camp.repos.post_sql_repo import PostSQLRepository
from ps_camp.repos.referendum_sql_repo import ReferendumSQLRepository
from ps_camp.repos.referendum_vote_sql_repo import ReferendumVoteSQLRepository
from ps_camp.repos.user_sql_repo import UserSQLRepository
from ps_camp.repos.vote_sql_repo import VoteSQLRepository
from ps_camp.sql_models.bank_model import OwnerType, TransactionType
from ps_camp.sql_models.candidate_model import Candidate
from ps_camp.sql_models.post_model import Post
from ps_camp.sql_models.proposal_model import Proposal
from ps_camp.sql_models.user_model import User
from ps_camp.utils.password_hasher import PasswordHasher
from ps_camp.utils.pdf_templates import bank_report_template
from ps_camp.utils.session_helpers import refresh_user_session

load_dotenv()
ADMIN_ID = os.getenv("ADMIN_ID")
VOTE_OPEN_TIME = isoparse(os.getenv("VOTE_OPEN_TIME"))
VOTE_CLOSE_TIME = isoparse(os.getenv("VOTE_CLOSE_TIME"))


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
        current_time = datetime.now(timezone.utc)
        if session.get("user"):
            with get_db_session() as db:
                bank_repo = BankSQLRepository(db)

                user = session["user"]
                account, _ = get_account_by_user(user, bank_repo, db)
                if account:
                    session["user"]["coins"] = account.balance
                else:
                    session["user"]["coins"] = 0  # or keep the presets
                    flash("找不到對應的銀行帳戶，請聯繫主辦方", "warning")

        return render_template(
            "index.html",
            current_time=current_time,
            vote_open_time=VOTE_OPEN_TIME,
            vote_close_time=VOTE_CLOSE_TIME,
        )

    @app.route("/ping")
    def ping():
        return "pong", 200

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.route("/map")
    def map_page():
        return render_template("map.html")

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
                post.preview = markdown.markdown(
                    post.content[:300], extensions=["nl2br"]
                )
            return render_template("posts.html", posts=posts)

    @app.route("/api/posts/<string:post_id>", methods=["GET"])
    def get_post_content(post_id: str):
        try:
            post_uuid = UUID(post_id)
        except ValueError:
            return jsonify(success=False, message="無效貼文 ID"), 400

        with get_db_session() as db:
            repo = PostSQLRepository(db)
            post = repo.get_by_id(post_uuid)
            if not post:
                return jsonify(success=False, message="貼文不存在"), 404

            html_content = markdown.markdown(post.content, extensions=["nl2br"])
            return jsonify(success=True, content=html_content)

    @app.route("/npcs")
    def npcs():
        base_path = os.path.join(current_app.static_folder, "images/NPCs")
        grouped_npcs = {}

        for region in os.listdir(base_path):
            region_path = os.path.join(base_path, region)
            if not os.path.isdir(region_path):
                continue

            npc_list = []
            for filename in os.listdir(region_path):
                # 處理副檔名
                if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                name = os.path.splitext(filename)[0].replace("NPC-", "").strip()
                image_url = f"/static/images/NPCs/{region}/{filename}"

                npc_list.append(
                    {
                        "name": name,
                        "title": "",  # 角色稱號
                        "detail": "",  # 細節描述
                        "image": image_url,
                    }
                )

            grouped_npcs[region] = npc_list

        return render_template("npcs.html", grouped_npcs=grouped_npcs)

    @app.route("/npc/<name>")
    def npc_detail(name):
        npcs_path = os.path.join(app.static_folder, "data", "npcs.json")
        with open(npcs_path, "r", encoding="utf-8") as f:
            npc_data = json.load(f)

        for npc in npc_data:
            if npc["name"] == name:
                return render_template("npc_detail.html", npc=npc)
        return abort(404)

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

    @app.route("/posts/<post_id>", methods=["GET", "POST"])
    def view_post(post_id):
        with get_db_session() as db:
            post = db.query(Post).filter_by(id=post_id).first()
            if not post:
                abort(404)

            # Parse replies JSON
            if isinstance(post.replies, str):
                try:
                    replies = json.loads(post.replies)
                except json.JSONDecodeError:
                    replies = []
            else:
                replies = post.replies or []

            if request.method == "POST":
                user = session.get("user")
                if not user:
                    flash("請先登入以留言", "warning")
                    return redirect(url_for("login"))

                new_reply = {
                    "user_name": user["fullname"],
                    "created_at": datetime.now(UTC).isoformat(),
                    "content": markdown.markdown(request.form["reply"]),
                }
                replies.append(new_reply)
                post.replies = replies
                db.commit()
                flash("留言成功", "success")
                return redirect(url_for("view_post", post_id=post_id))

            post.replies = replies
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

    from uuid import UUID

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

            user_id = str(session["user"]["id"])
            logging.debug("現在 likes:", post.likes)

            if user_id in post.likes:
                post.likes.remove(user_id)
                action = "unlike"
            else:
                post.likes.append(user_id)
                action = "like"

            logging.debug("更新後 likes:", post.likes)
            db.commit()
            logging.debug("commit 完成")

            return jsonify(success=True, action=action, likes=len(post.likes))

    @app.route("/vote", methods=["GET", "POST"])
    def vote():
        if "user" not in session:
            flash("請先登入")
            return redirect(url_for("login"))

        user_id = session["user"]["id"]
        with get_db_session() as db:
            vote_repo = VoteSQLRepository(db)
            ref_repo = ReferendumVoteSQLRepository(db)
            cand_repo = CandidateSQLRepository(db)  # ← 加這行

            if request.method == "POST":
                # Process form submission
                party_id = request.form.get("party")
                if not party_id:
                    flash("請選擇一個政黨才能投票！")
                    return redirect(url_for("vote"))
                referendum_votes = {
                    key.replace("referendum_", ""): value
                    for key, value in request.form.items()
                    if key.startswith("referendum_")
                }

                if vote_repo.has_voted(user_id):
                    flash("你已經投過票囉")
                    return redirect(url_for("vote"))

                vote_repo.add_vote(user_id, party_id)

                for ref_id, choice in referendum_votes.items():
                    ref_repo.add_vote(user_id, ref_id, choice)

                flash("投票成功！")
                return redirect(url_for("home"))

            candidates = cand_repo.get_all()

            ref_repo = ReferendumSQLRepository(db)
            referendums = ref_repo.get_active_referendums()

            if vote_repo.has_voted(user_id):
                flash("你已完成投票")
                return render_template("vote_success.html")

            return render_template(
                "vote.html", parties=candidates, referendums=referendums
            )

    @app.route("/submit", methods=["GET", "POST"])
    @refresh_user_session
    def submit():
        user = session.get("user")
        if not user or user["role"] not in ["party", "group"]:
            abort(403)

        with get_db_session() as db:
            if request.method == "POST":
                data = request.form
                if user["role"] == "party":
                    candidate = Candidate(
                        id=str(uuid4()),
                        party_id=user["id"],
                        name=data["name"],
                        description=data.get("description", ""),
                        created_at=datetime.now(UTC),
                    )
                    db.add(candidate)

                elif user["role"] == "group":
                    proposal = Proposal(
                        id=str(uuid4()),
                        group_id=user["id"],
                        title=data["title"],
                        description=data.get("description", ""),
                        created_at=datetime.now(UTC),
                    )
                    db.add(proposal)

                db.commit()
                flash("提交成功！", "success")
                return redirect(url_for("home"))

        return render_template("submit.html", role=user["role"])

    return app


# TODO: change to guicorn
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
