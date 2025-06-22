import os
from uuid import UUID
from flask import Flask, render_template, request, redirect, url_for, session
from ps_camp.db.session import SessionLocal
from ps_camp.sql_models.user_model import User
from ps_camp.sql_models.post_model import Post
from ps_camp.sql_models.npc_model import NPC
from ps_camp.repos.user_sql_repo import UserSQLRepository
from ps_camp.repos.post_sql_repo import PostSQLRepository
from ps_camp.repos.npc_sql_repo import NPCSQLRepository


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

        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            user = repo.get_by_username(username)

            if user and user.hashed_password == password:
                session["user"] = {
                    "id": user.id,
                    "fullname": user.fullname,
                    "coins": user.coins,
                }
                return redirect(url_for("home"))
            else:
                return "登入失敗", 401

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("home"))

    @app.route("/posts")
    def posts():
        db = SessionLocal()
        repo = PostSQLRepository(db)
        all_posts = repo.get_all()
        return render_template("posts.html", posts=all_posts)

    @app.route("/npcs")
    def npcs():
        db = SessionLocal()
        repo = NPCSQLRepository(db)
        all_npcs = repo.get_all()
        return render_template("npcs.html", npcs=all_npcs)

    @app.route("/posts/new", methods=["GET", "POST"])
    def new_post():
        if not session.get("user"):
            return redirect(url_for("login"))

        db = SessionLocal()
        repo = PostSQLRepository(db)

        if request.method == "POST":
            data = request.form
            post = Post(
                title=data["title"],
                content=data["content"],
                category=data["category"],
                created_by=session["user"]["fullname"],
            )
            repo.add(post)
            return redirect(url_for("posts"))

        return render_template("new_post.html")

    @app.route("/api/posts/<string:post_id>/like", methods=["POST", "DELETE"])
    def like_post(post_id: UUID):
        if not session.get("user"):
            return {"success": False, "message": "請先登入"}, 401

        db = SessionLocal()
        repo = PostSQLRepository(db)
        post = repo.get_by_id(post_id)
        if not post:
            return {"success": False, "message": "貼文不存在"}, 404

        if request.method == "POST":
            post.likes += 1
        elif request.method == "DELETE":
            post.likes = max(0, post.likes - 1)

        db.commit()
        return {"success": True, "likes": post.likes}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))