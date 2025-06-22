import os
from datetime import datetime
from uuid import uuid4, UUID
from flask import Flask, render_template, request, redirect, url_for, session, abort, jsonify
from ps_camp.db.session import SessionLocal
from ps_camp.sql_models.user_model import User
from ps_camp.sql_models.post_model import Post
from ps_camp.sql_models.npc_model import NPC
from ps_camp.repos.user_sql_repo import UserSQLRepository
from ps_camp.repos.post_sql_repo import PostSQLRepository
from ps_camp.repos.npc_sql_repo import NPCSQLRepository
from ps_camp.utils.password_hasher import PasswordHasher

import markdown

def create_app():
    app = Flask(__name__)
    app.secret_key = "2025ntupscamp"

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        db = SessionLocal()
        repo = UserSQLRepository(db)
        if request.method == "POST":
            data = request.form
            new_user = User(
                username=data["username"],
                fullname=data["fullname"],
                hashed_password=data["password"],
                role=data["role"],
            )
            repo.add(new_user)
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
            preview = post.content[:300]  # 避免一整篇太重
            post.content = markdown.markdown(preview, extensions=["nl2br"])

        return render_template("posts.html", posts=posts)

    @app.route("/npcs")
    def npcs():
        db = SessionLocal()
        repo = NPCSQLRepository(db)
        all_npcs = repo.get_all()
        return render_template("npcs.html", npcs=all_npcs)

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

        # Markdown 處理
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
            post = Post(
                id=uuid4(),
                title=data["title"],
                category=data["category"],
                content=data["content"],
                created_at=datetime.utcnow(),
                created_by=UUID(session["user"]["id"]),
                replies=[],
                likes=[],
            )
            repo.add(post)
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

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
