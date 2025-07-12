import json
import logging
import os
import re
from datetime import UTC, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from functools import wraps
from uuid import uuid4

import markdown
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
from ps_camp.repos.post_sql_repo import PostSQLRepository
from ps_camp.repos.referendum_vote_sql_repo import ReferendumVoteSQLRepository
from ps_camp.repos.user_sql_repo import UserSQLRepository
from ps_camp.repos.vote_sql_repo import VoteSQLRepository
from ps_camp.sql_models.bank_model import OwnerType, TransactionType
from ps_camp.sql_models.candidate_model import Candidate
from ps_camp.sql_models.party_document_model import PartyDocument
from ps_camp.sql_models.post_model import Post
from ps_camp.sql_models.proposal_model import Proposal
from ps_camp.sql_models.user_model import User
from ps_camp.utils.get_latest_weather import get_latest_weather_summary
from ps_camp.utils.get_register_close_time import get_register_close_time
from ps_camp.utils.humanize_time_diff import humanize_time_diff, taipei_now
from ps_camp.utils.password_hasher import PasswordHasher
from ps_camp.utils.password_rules import is_strong_password
from ps_camp.utils.pdf_templates import bank_report_template
from ps_camp.utils.convert_md import downgrade_headings
from ps_camp.utils.resolve_owner_name import resolve_owner_name
from ps_camp.utils.session_helpers import refresh_user_session
from ps_camp.utils.voting_config import (
    get_vote_close_time,
    get_vote_open_time,
    get_register_close_time,
    get_upload_close_time,
    get_candidate_deadline,
    get_alliance_deadline,
    get_camp_deadlines,
)
from ps_camp.repos.proposal_sql_repo import ProposalSQLRepository
from ps_camp.utils.google_drive import upload_file_to_drive

load_dotenv()
ADMIN_ID = os.getenv("ADMIN_ID")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ICON_MAP = {
    "晴": "fas fa-sun",
    "多雲": "fas fa-cloud-sun",
    "陰": "fas fa-cloud",
    "雨": "fas fa-cloud-showers-heavy",
    "雷": "fas fa-bolt",
    "雷雨": "fas fa-bolt",
    "雪": "fas fa-snowflake",
}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def restrict_roles(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user = session.get("user")
            if not user or user["role"] not in allowed_roles:
                flash("您沒有權限瀏覽此頁面", "danger")
                return redirect(url_for("home"))
            return f(*args, **kwargs)

        return wrapped

    return decorator


def map_role_to_owner_type(role: str) -> OwnerType:
    role = role.lower()
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

    @app.template_filter("file_exists")
    def file_exists_filter(path):
        full_path = os.path.join(current_app.root_path, path)
        return os.path.exists(full_path)

    @app.context_processor
    def inject_common_time():
        return {
            "current_time": taipei_now(),
            "register_close_time": get_register_close_time(),
            "vote_open_time": get_vote_open_time(),
        }

    @app.context_processor
    def inject_weather():
        try:
            w = get_latest_weather_summary("大安區")
            icon = next(
                (v for k, v in ICON_MAP.items() if k in w["天氣現象"]), "fas fa-smog"
            )
            return {
                "current_weather_icon": icon,
                "current_weather_temp": w["溫度"],
                "current_weather_pop": w["降雨機率"],
            }
        except Exception as e:
            logger.warning(f"[Weather] 無法取得天氣資料：{e}")
            return {
                "current_weather_icon": None,
                "current_weather_temp": None,
                "current_weather_pop": None,
            }

    @app.route("/")
    @refresh_user_session
    def home():
        tz = timezone(timedelta(hours=8))
        current_time = taipei_now()
        vote_open_time = get_vote_open_time().astimezone(tz)
        vote_close_time = get_vote_close_time().astimezone(tz)
        register_close_time = get_register_close_time().astimezone(tz)
        upload_close_time = get_upload_close_time().astimezone(tz)
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

        voted = False
        if "user" in session:
            with get_db_session() as db:
                vote_repo = VoteSQLRepository(db)
                voted = vote_repo.has_voted(session["user"]["id"])

        return render_template(
            "index.html",
            current_time=current_time,
            vote_open_time=vote_open_time,
            vote_close_time=vote_close_time,
            register_close_time=register_close_time,
            upload_close_time=upload_close_time,
            voted=voted,
        )

    @app.route("/ping")
    def ping():
        return "pong", 200

    @app.route("/force500")
    def force_500():
        raise Exception("這是測試用的 500 internal server error")

    @app.errorhandler(500)
    def internal_server_error(e):
        try:
            logging.exception("Internal Server Error 發生了：")
            return render_template("500.html"), 500
        except Exception as inner_e:
            logging.error(f"連 500.html 都渲染失敗：{inner_e}")
            return "伺服器發生嚴重錯誤，請聯絡主辦方。", 500

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
                    acc_id: resolve_owner_name(acc.owner_id, db)
                    for acc_id, acc in account_map.items()
                }

                html = render_template_string(
                    bank_report_template,
                    account=account,
                    transactions=transactions,
                    account_to_fullname=account_to_fullname,
                    generated_at=datetime.now(),
                )
                pdf = HTML(string=html).write_pdf()

                filename = f"bank_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                resp = make_response(pdf)
                resp.headers["Content-Type"] = "application/pdf"
                resp.headers["Content-Disposition"] = f"inline; filename={filename}"
                return resp
            except Exception as e:
                flash(f"輸出明細發生錯誤：{e}")
                logging.debug(f"輸出明細發生錯誤：{e}")
                return redirect(url_for("bank"))

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
        if taipei_now() > get_register_close_time():
            flash("註冊時間已截止", "danger")
            return redirect(url_for("home"))

        with get_db_session() as db:
            repo = UserSQLRepository(db)
            hasher = PasswordHasher()

            # Pre-retrieve lists of all political parties and groups
            all_users = repo.get_all()
            parties = [p for p in all_users if p.role == "party"]
            interest_groups = [g for g in all_users if g.role == "group"]

            if request.method == "POST":
                data = request.form

                username = data["username"].strip()
                fullname = data["fullname"].strip()
                password = data["password"]
                role = data["role"]
                affiliation_id = data.get("affiliation_id")
                affiliation_type = data.get("affiliation_type")

                # Check the account format
                if not re.match(r"^[a-zA-Z0-9_]{4,20}$", username):
                    return render_template(
                        "register.html",
                        parties=parties,
                        interest_groups=interest_groups,
                        error="帳號僅能包含英文、數字與底線，長度 4-20 字",
                    )

                # Check whether the account is duplicated
                if repo.get_by_username(username):
                    return render_template(
                        "register.html",
                        parties=parties,
                        interest_groups=interest_groups,
                        error="此帳號已被使用，請選擇其他帳號！",
                    )

                # Register name is prohibited
                if username.lower() in ["admin", "root"]:
                    return render_template(
                        "register.html",
                        parties=parties,
                        interest_groups=interest_groups,
                        error="禁止註冊管理員帳號",
                    )

                # Password strength check
                if not is_strong_password(password):
                    return render_template(
                        "register.html",
                        parties=parties,
                        interest_groups=interest_groups,
                        error="密碼需至少 8 字，包含大寫、小寫、數字與特殊符號",
                    )

                # If it is a member, check the column
                if role == "member" and (not affiliation_id or not affiliation_type):
                    return render_template(
                        "register.html",
                        parties=parties,
                        interest_groups=interest_groups,
                        error="請選擇所屬政黨或利益團體",
                    )

                # Create a user
                new_user = User(
                    id=str(uuid4()),
                    username=username,
                    fullname=fullname,
                    hashed_password=hasher.hash_password(password),
                    role=role,
                    coins=10000,
                    affiliation_id=affiliation_id if role == "member" else None,
                    affiliation_type=affiliation_type if role == "member" else None,
                )
                repo.add(new_user)

                # Create a bank account (member does not need)
                if role != "member":
                    bank_repo = BankSQLRepository(db)
                    owner_type = map_role_to_owner_type(role)
                    bank_repo.create_account(
                        owner_id=new_user.id,
                        owner_type=owner_type,
                        initial_balance=new_user.coins,
                    )

                return redirect(url_for("login"))

            # GET Request
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
            user_name = user_obj.fullname
            avatar_url = None
            for ext in list(ALLOWED_EXTENSIONS):
                filename = f"{user_name}_avatar.{ext}"
                path = os.path.join("static", "uploads", "avatars", filename)
                if os.path.exists(os.path.join(current_app.root_path, path)):
                    avatar_url = "/" + path
                    break

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

            return render_template("profile.html", avatar_url=avatar_url)

    @app.route("/upload_avatar", methods=["POST"])
    def upload_avatar():
        logging.debug("[DEBUG] avatar upload 被觸發了，method:", request.method)
        # Check if there are any files
        if "avatar" not in request.files:
            flash("未選擇檔案", "error")
            return redirect(url_for("profile"))

        file = request.files["avatar"]

        # The file name is empty
        if file.filename.strip() == "":
            flash("檔案名稱為空", "error")
            return redirect(url_for("profile"))

        # Is it a allowed format
        if file and allowed_file(file.filename):
            # The secondary file name retains the original format
            ext = file.filename.rsplit(".", 1)[1].lower()

            raw_name = session["user"]["fullname"]
            filename = f"{raw_name}_avatar.{ext}"

            folder = os.path.join(current_app.root_path, "static", "uploads", "avatars")
            os.makedirs(folder, exist_ok=True)

            filepath = os.path.join(folder, filename)
            file.save(filepath)

            flash("大頭貼上傳成功", "success")
            return redirect(url_for("profile"))
        else:
            flash("檔案類型不允許，只能上傳 PNG 或 JPG", "error")
            return redirect(url_for("profile"))

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
                post.display_time = humanize_time_diff(post.created_at)
                post.preview = markdown.markdown(
                    downgrade_headings(post.content[:50]),
                    extensions=["nl2br", "fenced_code", "codehilite"],
                )
            return render_template("posts.html", posts=posts)

    from uuid import UUID

    @app.route("/api/posts/<post_id>/preview")
    def get_post_preview(post_id):
        try:
            post_uuid = UUID(post_id)
        except ValueError:
            return jsonify(success=False, message="無效貼文 ID"), 400

        with get_db_session() as db:
            repo = PostSQLRepository(db)
            post = repo.get_by_id(post_uuid)
            if not post:
                return jsonify(success=False, message="找不到貼文"), 404

            short_text = post.content[:100] + "..."
            html = markdown.markdown(
                downgrade_headings(short_text),
                extensions=["nl2br", "fenced_code", "codehilite"],
            )
            return jsonify({"success": True, "preview": html})

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

            html_content = markdown.markdown(
                downgrade_headings(post.content),
                extensions=["nl2br", "fenced_code", "codehilite"],
            )
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
                # Process the sub-file name
                if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                name = os.path.splitext(filename)[0].replace("NPC-", "").strip()
                image_url = f"/static/images/NPCs/{region}/{filename}"

                npc_list.append(
                    {
                        "name": name,
                        "title": "",  # Character title
                        "detail": "",  # Details description
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

            post.rendered_content = markdown.markdown(
                downgrade_headings(post.content),
                extensions=["nl2br", "fenced_code", "codehilite"],
            )

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

        user = session["user"]
        role = user["role"]

        # Classification permission definition
        ADMIN_ONLY_CATEGORIES = ["規則", "公告", "議題", "成立宣言", "白皮書"]
        PARTY_OR_GROUP_ONLY = ["新聞"]

        with get_db_session() as db:
            repo = PostSQLRepository(db)

            if request.method == "POST":
                data = request.form
                user_id = UUID(user["id"])
                owner_type = map_role_to_owner_type(role)
                category = data["category"]

                # Classification permission check
                if category in ADMIN_ONLY_CATEGORIES and role != "admin":
                    flash("您沒有權限發布此分類的貼文")
                    return redirect(url_for("new_post"))

                if category in PARTY_OR_GROUP_ONLY and role not in [
                    "party",
                    "group",
                ]:
                    flash("只有政黨與利益團體能發布新聞")
                    return redirect(url_for("new_post"))

                post = Post(
                    id=uuid4(),
                    title=data["title"],
                    category=category,
                    content=data["content"],
                    created_at=taipei_now(),
                    created_by=user_id,
                    replies=[],
                    likes=[],
                )

                repo.add(post, owner_id=user_id, owner_type=owner_type)
                return redirect(url_for("posts"))

            return render_template("new_post.html", role=role)

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

    @app.route("/api/posts/<string:post_id>/replies", methods=["POST"])
    def add_reply(post_id: str):
        if not session.get("user"):
            return jsonify(success=False, message="請先登入"), 401

        try:
            post_uuid = UUID(post_id)
        except ValueError:
            return jsonify(success=False, message="無效貼文 ID"), 400

        data = request.get_json()
        content = data.get("content", "").strip()
        if not content:
            return jsonify(success=False, message="請輸入內容"), 400

        with get_db_session() as db:
            repo = PostSQLRepository(db)
            post = repo.get_by_id(post_uuid)
            if not post:
                return jsonify(success=False, message="貼文不存在"), 404

            user = session["user"]
            reply = {
                "user": user["fullname"],
                "content": content,
                "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            }

            post.replies.append(reply)
            db.commit()
            return jsonify(success=True, reply=reply, total=len(post.replies))

    @app.route("/api/posts/<string:post_id>/replies", methods=["GET"])
    def get_replies(post_id: str):
        try:
            post_uuid = UUID(post_id)
        except ValueError:
            return jsonify(success=False, message="無效貼文 ID"), 400

        with get_db_session() as db:
            repo = PostSQLRepository(db)
            post = repo.get_by_id(post_uuid)
            if not post:
                return jsonify(success=False, message="找不到貼文"), 404

            return jsonify(success=True, replies=post.replies)

    @app.route("/api/search-users")
    def search_users():
        if not session.get("user"):
            return jsonify([]), 401

        keyword = request.args.get("q", "").strip()
        if not keyword:
            return jsonify([])

        with get_db_session() as db:
            user_repo = UserSQLRepository(db)
            bank_repo = BankSQLRepository(db)

            matched_users = (
                db.query(user_repo.model)
                .filter(user_repo.model.fullname.ilike(f"%{keyword}%"))
                .limit(5)
                .all()
            )

            results = []
            for user in matched_users:
                role_str = str(user.role).lower()
                owner_type = map_role_to_owner_type(role_str)
                account = bank_repo.get_account_by_owner(user.id, owner_type)

                print(
                    f"[DEBUG] 使用者：{user.fullname} ({user.role}) → owner_type: {owner_type.value}"
                )
                print(
                    f"[DEBUG] 帳戶查詢結果：{account.account_number if account else '無帳戶'}"
                )

                if account:
                    results.append(
                        {
                            "fullname": user.fullname,
                            "username": user.username,
                            "account_number": account.account_number,
                        }
                    )

            return jsonify(results)

    @app.route("/api/lookup-user-by-account")
    def lookup_user_by_account():
        if not session.get("user"):
            return jsonify({"error": "unauthorized"}), 401

        account_number = request.args.get("q", "").strip()
        if not account_number:
            return jsonify({"error": "missing query"}), 400

        with get_db_session() as db:
            bank_repo = BankSQLRepository(db)
            account = bank_repo.get_account_by_number(account_number)

            if not account:
                return jsonify({"error": "account not found"}), 404

            user = db.query(User).filter_by(id=account.owner_id).first()
            if not user:
                return jsonify({"error": "user not found"}), 404

            return jsonify(
                {
                    "fullname": user.fullname,
                    "username": user.username,
                    "account_number": account.account_number,
                }
            )

    @app.route("/vote_party", methods=["GET", "POST"])
    @restrict_roles("admin", "member")
    def vote_party():
        if "user" not in session:
            flash("請先登入")
            return redirect(url_for("login"))

        user_id = session["user"]["id"]
        with get_db_session() as db:
            vote_repo = VoteSQLRepository(db)
            user_repo = UserSQLRepository(db)

            # Prevent repeated voting
            if vote_repo.has_voted(user_id):
                flash("您已完成投票")
                return render_template("vote_success.html")

            parties = [u for u in user_repo.get_all() if u.role == "party"]

            if request.method == "POST":
                party_id = request.form.get("party")
                if not party_id:
                    flash("請選擇一個政黨！")
                    return redirect(url_for("vote_party"))

                session["vote_party"] = party_id
                return redirect(url_for("vote_referendum"))

            for party in parties:
                party_name = party.fullname
                extensions = ["png", "jpg", "jpeg"]
                for ext in extensions:
                    filename = f"{party_name}_avatar.{ext}"
                    path = os.path.join("static", "uploads", "avatars", filename)
                    full_path = os.path.join(current_app.root_path, path)
                    if os.path.exists(full_path):
                        party.logo_url = "/" + path
                        break

            return render_template("vote_party.html", parties=parties)

    @app.route("/vote_referendum", methods=["GET", "POST"])
    @restrict_roles("admin", "member")
    def vote_referendum():
        if "user" not in session:
            flash("請先登入")
            return redirect(url_for("login"))

        user_id = session["user"]["id"]
        party_id = session.get("vote_party")

        if not party_id:
            flash("請先投政黨票，才能進入公投投票")
            return redirect(url_for("vote_party"))

        with get_db_session() as db:
            vote_repo = VoteSQLRepository(db)
            ref_repo = ReferendumVoteSQLRepository(db)
            proposal_repo = ProposalSQLRepository(db)
            referendums = proposal_repo.get_all()

            # Prevent repeated voting
            if vote_repo.has_voted(user_id):
                flash("您已完成投票")
                return render_template("vote_success.html")

            if request.method == "POST":
                # Verify that every question has been submitted
                missing = [
                    ref.id
                    for ref in referendums
                    if f"referendum_{ref.id}" not in request.form
                ]
                if missing:
                    flash("請對每一項公投都投票！")
                    return redirect(url_for("vote_referendum"))

                # Save party tickets
                vote_repo.add_vote(user_id, party_id)

                # Store all referendums
                for ref in referendums:
                    vote_value = request.form.get(f"referendum_{ref.id}")
                    if vote_value:
                        ref_repo.add_vote(user_id, ref.id, vote_value)

                session.pop("vote_party", None)
                flash("投票成功！")
                return redirect(url_for("home"))

            return render_template("vote_referendum.html", referendums=referendums)

    @app.route("/submit", methods=["GET", "POST"])
    @refresh_user_session
    def submit():
        tz = ZoneInfo("Asia/Taipei")

        start_date = datetime.strptime(os.getenv("CAMP_START_DATE"), "%Y-%m-%d").date()

        # Get the current time: with Taipei time zone
        now = datetime.now(timezone.utc).astimezone(tz)

        # Fix the following deadlines to let them also have time zones tz
        party_deadline = datetime.combine(
            start_date + timedelta(days=2),
            datetime.min.time(),
            tz
        ) + timedelta(hours=23, minutes=59)

        group_deadline = datetime.combine(
            start_date + timedelta(days=2),
            datetime.min.time(),
            tz
        ) + timedelta(hours=23, minutes=59)

        # These functions should also be converted to tz-aware
        candidate_deadline = get_candidate_deadline().astimezone(tz)
        alliance_deadline = get_alliance_deadline().astimezone(tz)

        expired_party = now > party_deadline
        expired_group = now > group_deadline
        can_upload_candidate = now <= candidate_deadline
        can_upload_alliance = now <= alliance_deadline

        print("[debug] upload_close_time =", get_upload_close_time())
        print("[debug] candidate_deadline =", get_candidate_deadline())
        print("[debug] camp_deadline =", get_camp_deadlines())
        print("[debug] now =", taipei_now())

        tz = timezone(timedelta(hours=8))
        user = session.get("user")
        if not user or user["role"] not in ["party", "group"]:
            abort(403)

        with get_db_session() as db:
            if user["role"] == "party":
                # Check the status of political party members and nominations
                all_members = (
                    db.query(User).filter(User.affiliation_id == user["id"]).all()
                )
                existing_candidates = (
                    db.query(Candidate).filter(Candidate.party_id == user["id"]).all()
                )
                candidate_user_ids = {
                    c.user_id for c in existing_candidates if c.user_id
                }
                remaining_slots = 6 - len(existing_candidates)

                party_doc = (
                    db.query(PartyDocument).filter_by(party_id=user["id"]).first()
                )

                if request.method == "POST":
                    form = request.form
                    photo_zip = request.files.get("photo_zip")
                    cabinet_pdf = request.files.get("cabinet_pdf")
                    alliance_pdf = request.files.get("alliance_pdf")

                    # Handle candidate nominations
                    selected_user_ids = form.getlist("selected_members")
                    description = form.get("description", "")

                    if remaining_slots <= 0:
                        flash("您已提名 6 位候選人，無法再新增", "danger")
                        return redirect(url_for("submit"))

                    if not selected_user_ids:
                        flash("請至少選擇一位小隊員作為候選人", "warning")
                        return redirect(url_for("submit"))

                    if len(selected_user_ids) > remaining_slots:
                        flash(f"最多只能提名 {remaining_slots} 位候選人", "danger")
                        return redirect(url_for("submit"))

                    # Save candidate photos
                    photo_url = None
                    if photo_zip and photo_zip.filename.endswith(".zip"):
                        fullname = user.get("fullname", "unknown")
                        filename = f"{fullname}_候選人照片"
                        photo_url = upload_file_to_drive(photo_zip, filename)

                    for selected_user_id in selected_user_ids:
                        if selected_user_id in candidate_user_ids:
                            continue  # or flash warns that the name has been nominated

                        selected_user = (
                            db.query(User).filter(User.id == selected_user_id).first()
                        )
                        if (
                            not selected_user
                            or selected_user.affiliation_id != user["id"]
                        ):
                            continue

                        candidate = Candidate(
                            id=str(uuid4()),
                            user_id=selected_user.id,
                            party_id=user["id"],
                            name=selected_user.fullname,
                            description=description,
                            created_at=datetime.now(UTC),
                            photo_url=photo_url,
                        )
                        db.add(candidate)

                    # Handle party archives
                    if not party_doc:
                        party_doc = PartyDocument(
                            id=str(uuid4()),
                            party_id=user["id"],
                            created_at=datetime.now(UTC),
                        )

                    cabinet_url = None
                    if cabinet_pdf and cabinet_pdf.filename.endswith(".pdf"):
                        fullname = user.get("fullname", "unknown")
                        filename = f"{fullname}_建設性內閣名單"
                        cabinet_url = upload_file_to_drive(cabinet_pdf, filename)
                        party_doc.cabinet_url = cabinet_url

                    alliance_url = None
                    if alliance_pdf and alliance_pdf.filename.endswith(".pdf"):
                        fullname = user.get("fullname", "unknown")
                        filename = f"{fullname}_政黨聯盟協定書"
                        alliance_url = upload_file_to_drive(alliance_pdf, filename)
                        party_doc.alliance_url = alliance_url

                    db.merge(party_doc)
                    db.commit()

                    flash("候選人提名與檔案上傳成功！", "success")
                    return redirect(url_for("home"))

                return render_template(
                    "submit.html",
                    role="party",
                    user=user,
                    members=all_members,
                    existing_candidates=existing_candidates,
                    remaining_slots=remaining_slots,
                    party_doc=party_doc,
                    current_time=taipei_now(),
                    vote_open_time=get_vote_open_time().astimezone(tz),
                    vote_close_time=get_vote_close_time().astimezone(tz),
                    register_close_time=get_register_close_time().astimezone(tz),
                    upload_close_time=get_upload_close_time().astimezone(tz),
                    expired_party=expired_party,
                    expired_group=expired_group,
                    can_upload_candidate=can_upload_candidate,
                    can_upload_alliance=can_upload_alliance,
                )

            elif user["role"] == "group":
                proposal_obj = db.query(Proposal).filter_by(group_id=user["id"]).first()

                if request.method == "POST":
                    logger.debug("[SUBMIT] 公投案 POST 被觸發了")
                    title = request.form.get("title")
                    description = request.form.get("description", "")
                    proposal_pdf = request.files.get("proposal_pdf")

                    if proposal_pdf:
                        logging.debug(
                            f"[UPLOAD] 檢查上傳：filename={proposal_pdf.filename}, content_type={proposal_pdf.content_type}"
                        )
                    else:
                        logging.debug("[UPLOAD] proposal_pdf 為 None（表單未附帶檔案）")

                    if not proposal_obj:
                        logger.debug("[SUBMIT] 尚無舊案，準備建立 Proposal 物件")
                        proposal_obj = Proposal(
                            id=str(uuid4()),
                            group_id=user["id"],
                            title=title,
                            description=description,
                            created_at=datetime.now(UTC),
                        )
                    else:
                        logger.debug("[SUBMIT] 有舊案，進行更新 title/description")
                        proposal_obj.title = title
                        proposal_obj.description = description

                    if proposal_pdf and proposal_pdf.filename:
                        fullname = user.get("fullname", "unknown")
                        filename = f"{fullname}_公投案"
                        path = os.path.join(
                            "src", "ps_camp", "static", "uploads", "proposals"
                        )
                        os.makedirs(path, exist_ok=True)
                        drive_url = upload_file_to_drive(proposal_pdf, filename)
                        proposal_obj.file_url = drive_url

                    db.merge(proposal_obj)
                    db.commit()
                    flash("公投案提交成功！", "success")
                    return redirect(url_for("home"))

                # Make sure the proposal is pure dict
                proposal_dict = None
                if proposal_obj:
                    proposal_dict = {
                        "title": proposal_obj.title,
                        "description": proposal_obj.description,
                        "file_url": proposal_obj.file_url,
                    }

                # Make sure that the user is also pure dict and avoid triggering lazyload
                user_dict = {k: user[k] for k in ("id", "fullname", "role")}

                return render_template(
                    "submit.html",
                    role="group",
                    user=user_dict,
                    proposal=proposal_dict,
                    session=session,
                    current_time=taipei_now(),
                    vote_open_time=get_vote_open_time().astimezone(tz),
                    vote_close_time=get_vote_close_time().astimezone(tz),
                    register_close_time=get_register_close_time().astimezone(tz),
                    upload_close_time=get_upload_close_time().astimezone(tz),
                    expired_party=expired_party,
                    expired_group=expired_group,
                )

    @app.route("/api/live_votes")
    def live_votes():
        with get_db_session() as db:
            vote_repo = VoteSQLRepository(db)
            ref_repo = ReferendumVoteSQLRepository(db)
            proposal_repo = ProposalSQLRepository(db)
            user_repo = UserSQLRepository(db)

            #Party votes
            party_counts = vote_repo.get_party_vote_counts()
            party_name_map = {
                str(p.id): p.fullname for p in user_repo.get_all() if p.role == "party"
            }

            # Referendum
            proposals = proposal_repo.get_all()
            proposal_ids = [p.id for p in proposals]

            referendum_votes = {
                str(k): v
                for k, v in ref_repo.get_vote_counts_by_referendum_ids(
                    proposal_ids
                ).items()
            }
            referendum_titles = {str(p.id): p.title for p in proposals}

            return jsonify(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "votes": {
                        "party_votes": party_counts,
                        "party_names": party_name_map,
                        "referendum_votes": referendum_votes,
                        "referendum_titles": referendum_titles,
                    },
                }
            )

    @app.route("/results")
    def vote_results():
        return render_template("vote_results.html")

    @app.context_processor
    def inject_common_time():
        return {
            "current_time": taipei_now(),
            "vote_open_time": get_vote_open_time(),
            "vote_close_time": get_vote_close_time(),
            "register_close_time": get_register_close_time(),
            "upload_close_time": get_upload_close_time(),
        }

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
