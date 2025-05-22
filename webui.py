from bottle import Bottle, run, template, request, redirect, static_file, response
from shelflet import Model, CharField, ForeignKey, ManyToManyField
import os

# Bottleアプリケーションの初期化
app = Bottle()

# --- 簡易ログイン認証 ---
ADMIN_USER = "admin"  # 管理者ユーザー名
ADMIN_PASS = "password"  # 管理者パスワード

def check_login():
    """
    ログイン状態をチェックする

    Returns:
        bool: ログインしている場合はTrue、していない場合はFalse
    """
    return request.get_cookie("auth") == "ok"

def require_login(func):
    """
    ログインが必要なルートに対するデコレータ
    ログインしていない場合はログインページにリダイレクトする

    Args:
        func: デコレートする関数

    Returns:
        function: ラッパー関数
    """
    def wrapper(*args, **kwargs):
        if not check_login():
            return redirect("/login")
        return func(*args, **kwargs)
    return wrapper

# --- モデル定義 ---
class User(Model):
    """
    ユーザーモデル
    管理画面で管理するユーザー情報を表す
    """
    name = CharField(required=True)  # ユーザー名（必須）
    db_file = "admin_user.db"  # データベースファイル名

class Group(Model):
    """
    グループモデル
    複数のユーザーをまとめたグループを表す
    """
    name = CharField(required=True)  # グループ名（必須）
    members = ManyToManyField(User, backref="groups")  # グループメンバー（多対多）
    db_file = "admin_group.db"  # データベースファイル名

class Message(Model):
    """
    メッセージモデル
    ユーザーが投稿したメッセージを表す
    """
    user = ForeignKey(User, backref="messages", on_delete="cascade")  # 投稿者（外部キー）
    content = CharField(required=True)  # メッセージ内容（必須）
    db_file = "admin_msg.db"  # データベースファイル名

# データベースを開き、インデックスをメモリにロード（高速化のため）
User.open(index=True)
Group.open(index=True)
Message.open(index=True)

# --- スタティックファイル ---
@app.route('/static/<filename>')
def send_static(filename):
    """
    静的ファイル（CSS、JavaScript、画像など）を提供するルート

    Args:
        filename (str): 要求されたファイル名

    Returns:
        file: 静的ファイル
    """
    return static_file(filename, root='./static')

# --- 認証 ---
@app.route('/login')
def login_form():
    """
    ログインフォームを表示するルート

    Returns:
        str: ログインフォームのHTML
    """
    return '''
    <h2>Login</h2>
    <form method="post">
        <input name="user" placeholder="Username" required><br>
        <input name="pw" type="password" placeholder="Password" required><br>
        <button class="btn btn-primary mt-2">Login</button>
    </form>
    '''

@app.post('/login')
def login_submit():
    """
    ログインフォームの送信を処理するルート
    ユーザー名とパスワードを検証し、正しければクッキーを設定してトップページにリダイレクト

    Returns:
        redirect: 認証成功時はトップページへリダイレクト
        str: 認証失敗時はエラーメッセージ
    """
    user = request.forms.get("user")
    pw = request.forms.get("pw")
    if user == ADMIN_USER and pw == ADMIN_PASS:
        response.set_cookie("auth", "ok")
        return redirect("/")
    return "ログイン失敗：ユーザー名またはパスワードが正しくありません"

@app.route('/logout')
def logout():
    """
    ログアウト処理を行うルート
    認証クッキーを削除してログインページにリダイレクト

    Returns:
        redirect: ログインページへのリダイレクト
    """
    response.delete_cookie("auth")
    return redirect("/login")

# --- 共通テンプレート ---
def html_head(title):
    """
    共通のHTMLヘッダーを生成する

    Args:
        title (str): ページタイトル

    Returns:
        str: HTMLヘッダー部分
    """
    return f'''
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{title} - Shelflet Admin</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="container mt-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>{title}</h1>
        <div>
            <a href="/" class="btn btn-outline-primary me-2">Home</a>
            <a href="/logout" class="btn btn-outline-secondary">Logout</a>
        </div>
    </div>
    '''

# --- ルート ---
@app.route('/')
@require_login
def index():
    """
    トップページを表示するルート
    各モデルへのリンクと、それぞれのレコード数を表示

    Returns:
        str: トップページのHTML
    """
    return html_head("管理画面") + f'''
        <div class="list-group">
            <a href="/users" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                ユーザー管理
                <span class="badge bg-primary rounded-pill">{len(User.all())}</span>
            </a>
            <a href="/groups" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                グループ管理
                <span class="badge bg-primary rounded-pill">{len(Group.all())}</span>
            </a>
            <a href="/messages" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                メッセージ管理
                <span class="badge bg-primary rounded-pill">{len(Message.all())}</span>
            </a>
        </div>
    </body></html>'''

@app.route('/users')
@require_login
def list_users():
    """
    ユーザー一覧を表示するルート
    検索機能、編集、削除、新規作成のUIを提供

    Returns:
        str: ユーザー一覧ページのHTML
    """
    # 検索クエリがあれば、名前でフィルタリング
    query = request.query.get('q', '').lower()
    users = [u for u in User.all() if query in u.name.lower()] if query else User.all()

    body = '''
        <form method="get" class="mb-3">
            <div class="input-group">
                <input name="q" value="{{query}}" class="form-control" placeholder="ユーザー名で検索">
                <button class="btn btn-outline-secondary" type="submit">検索</button>
            </div>
        </form>
        <ul class="list-group mb-4">
            % for u in users:
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    {{u.name}}
                    <span>
                        <a href="/edit/user/{{u.id}}" class="btn btn-sm btn-warning">編集</a>
                        <a href="/delete/user/{{u.id}}" class="btn btn-sm btn-danger" 
                           onclick="return confirm('本当に削除しますか？')">削除</a>
                    </span>
                </li>
            % end
        </ul>
        <div class="card">
            <div class="card-header">新規ユーザー作成</div>
            <div class="card-body">
                <form method="post">
                    <div class="mb-3">
                        <label for="name" class="form-label">ユーザー名</label>
                        <input id="name" name="name" placeholder="新しいユーザー名" class="form-control" required>
                    </div>
                    <button class="btn btn-primary">追加</button>
                </form>
            </div>
        </div>
    '''
    return html_head("ユーザー管理") + template(body, users=users, query=query) + '</body></html>'

@app.post('/users')
@require_login
def add_user():
    """
    新規ユーザーを作成するルート
    フォームから送信されたデータを使ってユーザーを作成し、一覧ページにリダイレクト

    Returns:
        redirect: ユーザー一覧ページへのリダイレクト
    """
    name = request.forms.get('name')
    if not name:
        return redirect('/users')  # 名前が空の場合は何もせずリダイレクト

    User(name=name).save()
    return redirect('/users')

@app.route('/edit/user/<id>')
@require_login
def edit_user(id):
    """
    ユーザー編集フォームを表示するルート

    Args:
        id (str): 編集するユーザーのID

    Returns:
        str: ユーザー編集ページのHTML
        redirect: ユーザーが見つからない場合は一覧ページへリダイレクト
    """
    user = User.get_by_id(id)
    if not user:
        return redirect('/users')

    body = f'''
        <div class="card">
            <div class="card-header">ユーザー編集</div>
            <div class="card-body">
                <form method="post">
                    <div class="mb-3">
                        <label for="name" class="form-label">ユーザー名</label>
                        <input id="name" name="name" value="{user.name}" class="form-control" required>
                    </div>
                    <button class="btn btn-success">保存</button>
                    <a href="/users" class="btn btn-secondary">キャンセル</a>
                </form>
            </div>
        </div>
    '''
    return html_head("ユーザー編集") + body + '</body></html>'

@app.post('/edit/user/<id>')
@require_login
def save_user(id):
    """
    ユーザー編集フォームの送信を処理するルート

    Args:
        id (str): 編集するユーザーのID

    Returns:
        redirect: ユーザー一覧ページへのリダイレクト
    """
    user = User.get_by_id(id)
    if not user:
        return redirect('/users')

    name = request.forms.get('name')
    if not name:
        return redirect(f'/edit/user/{id}')  # 名前が空の場合は編集ページに戻る

    user.name = name
    user.save()
    return redirect('/users')

@app.route('/groups')
@require_login
def list_groups():
    """
    グループ一覧を表示するルート
    グループの表示、削除、新規作成のUIを提供

    Returns:
        str: グループ一覧ページのHTML
    """
    # グループとユーザーの一覧を取得
    groups = Group.all()
    users = User.all()

    body = '''
        <ul class="list-group mb-4">
            % for g in groups:
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <strong>{{g.name}}</strong>
                        <span class="text-muted">（メンバー数: {{len(g.members)}}人）</span>
                        <div class="small text-muted">
                            % if g.members:
                                メンバー: {{", ".join(u.name for u in g.members)}}
                            % else:
                                メンバーなし
                            % end
                        </div>
                    </div>
                    <div>
                        <a href="/edit/group/{{g.id}}" class="btn btn-sm btn-warning">編集</a>
                        <a href="/delete/group/{{g.id}}" class="btn btn-sm btn-danger"
                           onclick="return confirm('本当に削除しますか？')">削除</a>
                    </div>
                </li>
            % end
        </ul>

        <div class="card">
            <div class="card-header">新規グループ作成</div>
            <div class="card-body">
                <form method="post">
                    <div class="mb-3">
                        <label for="name" class="form-label">グループ名</label>
                        <input id="name" name="name" placeholder="新しいグループ名" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label for="members" class="form-label">メンバー（複数選択可）</label>
                        <select id="members" name="members" multiple class="form-select" size="5">
                            % for u in users:
                                <option value="{{u.id}}">{{u.name}}</option>
                            % end
                        </select>
                        <div class="form-text">Ctrlキーを押しながらクリックで複数選択できます</div>
                    </div>
                    <button class="btn btn-primary">追加</button>
                </form>
            </div>
        </div>
    '''
    return html_head("グループ管理") + template(body, groups=groups, users=users) + '</body></html>'

@app.post('/groups')
@require_login
def add_group():
    """
    新規グループを作成するルート
    フォームから送信されたデータを使ってグループを作成し、一覧ページにリダイレクト

    Returns:
        redirect: グループ一覧ページへのリダイレクト
    """
    name = request.forms.get('name')
    if not name:
        return redirect('/groups')  # 名前が空の場合は何もせずリダイレクト

    member_ids = request.forms.getall('members')
    members = [User.get_by_id(mid) for mid in member_ids if User.get_by_id(mid)]
    Group(name=name, members=members).save()
    return redirect('/groups')

@app.route('/edit/group/<id>')
@require_login
def edit_group(id):
    """
    グループ編集フォームを表示するルート

    Args:
        id (str): 編集するグループのID

    Returns:
        str: グループ編集ページのHTML
        redirect: グループが見つからない場合は一覧ページへリダイレクト
    """
    group = Group.get_by_id(id)
    if not group:
        return redirect('/groups')

    users = User.all()

    body = f'''
        <div class="card">
            <div class="card-header">グループ編集</div>
            <div class="card-body">
                <form method="post">
                    <div class="mb-3">
                        <label for="name" class="form-label">グループ名</label>
                        <input id="name" name="name" value="{group.name}" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label for="members" class="form-label">メンバー（複数選択可）</label>
                        <select id="members" name="members" multiple class="form-select" size="5">
                            % for u in users:
                                <option value="{{u.id}}" {{'selected' if u in group.members else ''}}>{{u.name}}</option>
                            % end
                        </select>
                        <div class="form-text">Ctrlキーを押しながらクリックで複数選択できます</div>
                    </div>
                    <button class="btn btn-success">保存</button>
                    <a href="/groups" class="btn btn-secondary">キャンセル</a>
                </form>
            </div>
        </div>
    '''
    return html_head("グループ編集") + template(body, users=users, group=group) + '</body></html>'

@app.post('/edit/group/<id>')
@require_login
def save_group(id):
    """
    グループ編集フォームの送信を処理するルート

    Args:
        id (str): 編集するグループのID

    Returns:
        redirect: グループ一覧ページへのリダイレクト
    """
    group = Group.get_by_id(id)
    if not group:
        return redirect('/groups')

    name = request.forms.get('name')
    if not name:
        return redirect(f'/edit/group/{id}')  # 名前が空の場合は編集ページに戻る

    member_ids = request.forms.getall('members')
    members = [User.get_by_id(mid) for mid in member_ids if User.get_by_id(mid)]

    group.name = name
    group.members = members
    group.save()
    return redirect('/groups')

@app.route('/messages')
@require_login
def list_messages():
    """
    メッセージ一覧を表示するルート
    メッセージの表示、削除、新規作成のUIを提供

    Returns:
        str: メッセージ一覧ページのHTML
    """
    # メッセージを新しい順に取得
    messages = Message.all(order_by='-content')
    users = User.all()

    body = '''
        <ul class="list-group mb-4">
            % for m in messages:
                <li class="list-group-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>{{m.user.name}}</strong>: {{m.content}}
                        </div>
                        <a href="/delete/message/{{m.id}}" class="btn btn-sm btn-danger"
                           onclick="return confirm('本当に削除しますか？')">削除</a>
                    </div>
                </li>
            % end
        </ul>

        <div class="card">
            <div class="card-header">新規メッセージ投稿</div>
            <div class="card-body">
                <form method="post">
                    <div class="mb-3">
                        <label for="user" class="form-label">投稿者</label>
                        <select id="user" name="user" class="form-select" required>
                            <option value="">-- 投稿者を選択 --</option>
                            % for u in users:
                                <option value="{{u.id}}">{{u.name}}</option>
                            % end
                        </select>
                    </div>
                    <div class="mb-3">
                        <label for="content" class="form-label">メッセージ内容</label>
                        <input id="content" name="content" placeholder="メッセージを入力" class="form-control" required>
                    </div>
                    <button class="btn btn-primary">投稿</button>
                </form>
            </div>
        </div>
    '''
    return html_head("メッセージ管理") + template(body, messages=messages, users=users) + '</body></html>'

@app.post('/messages')
@require_login
def add_message():
    """
    新規メッセージを作成するルート
    フォームから送信されたデータを使ってメッセージを作成し、一覧ページにリダイレクト

    Returns:
        redirect: メッセージ一覧ページへのリダイレクト
    """
    user_id = request.forms.get('user')
    content = request.forms.get('content')

    # バリデーション
    if not user_id or not content:
        return redirect('/messages')  # 必須項目が空の場合は何もせずリダイレクト

    user = User.get_by_id(user_id)
    if not user:
        return redirect('/messages')  # ユーザーが見つからない場合は何もせずリダイレクト

    Message(user=user, content=content).save()
    return redirect('/messages')

@app.route('/edit/message/<id>')
@require_login
def edit_message(id):
    """
    メッセージ編集フォームを表示するルート

    Args:
        id (str): 編集するメッセージのID

    Returns:
        str: メッセージ編集ページのHTML
        redirect: メッセージが見つからない場合は一覧ページへリダイレクト
    """
    message = Message.get_by_id(id)
    if not message:
        return redirect('/messages')

    users = User.all()

    body = f'''
        <div class="card">
            <div class="card-header">メッセージ編集</div>
            <div class="card-body">
                <form method="post">
                    <div class="mb-3">
                        <label for="user" class="form-label">投稿者</label>
                        <select id="user" name="user" class="form-select" required>
                            % for u in users:
                                <option value="{{u.id}}" {{'selected' if u.id == message.user.id else ''}}>{{u.name}}</option>
                            % end
                        </select>
                    </div>
                    <div class="mb-3">
                        <label for="content" class="form-label">メッセージ内容</label>
                        <input id="content" name="content" value="{message.content}" class="form-control" required>
                    </div>
                    <button class="btn btn-success">保存</button>
                    <a href="/messages" class="btn btn-secondary">キャンセル</a>
                </form>
            </div>
        </div>
    '''
    return html_head("メッセージ編集") + template(body, users=users, message=message) + '</body></html>'

@app.post('/edit/message/<id>')
@require_login
def save_message(id):
    """
    メッセージ編集フォームの送信を処理するルート

    Args:
        id (str): 編集するメッセージのID

    Returns:
        redirect: メッセージ一覧ページへのリダイレクト
    """
    message = Message.get_by_id(id)
    if not message:
        return redirect('/messages')

    user_id = request.forms.get('user')
    content = request.forms.get('content')

    # バリデーション
    if not user_id or not content:
        return redirect(f'/edit/message/{id}')  # 必須項目が空の場合は編集ページに戻る

    user = User.get_by_id(user_id)
    if not user:
        return redirect(f'/edit/message/{id}')  # ユーザーが見つからない場合は編集ページに戻る

    message.user = user
    message.content = content
    message.save()
    return redirect('/messages')

@app.route('/delete/<kind>/<id>')
@require_login
def delete(kind, id):
    """
    オブジェクトを削除するルート
    指定されたタイプとIDのオブジェクトを削除し、一覧ページにリダイレクト

    Args:
        kind (str): オブジェクトの種類（'user', 'group', 'message'）
        id (str): 削除するオブジェクトのID

    Returns:
        redirect: 対応する一覧ページへのリダイレクト
    """
    # 種類に応じたモデルクラスを取得
    cls = {'user': User, 'group': Group, 'message': Message}.get(kind)
    if cls:
        obj = cls.get_by_id(id)
        if obj:
            obj.delete()
    return redirect(f"/{kind}s")

if __name__ == '__main__':
    """
    アプリケーションのエントリーポイント
    静的ファイル用のディレクトリを作成し、Webサーバーを起動
    """
    # 静的ファイル用のディレクトリを作成
    os.makedirs("static", exist_ok=True)

    # 初期データがない場合はサンプルデータを作成
    if len(User.all()) == 0:
        print("サンプルデータを作成しています...")
        # サンプルユーザー
        user1 = User(name="山田太郎"); user1.save()
        user2 = User(name="佐藤花子"); user2.save()

        # サンプルグループ
        group1 = Group(name="開発チーム", members=[user1, user2]); group1.save()
        group2 = Group(name="マーケティングチーム", members=[user2]); group2.save()

        # サンプルメッセージ
        Message(user=user1, content="こんにちは！").save()
        Message(user=user2, content="新機能の開発が完了しました").save()
        print("サンプルデータの作成が完了しました")

    # Webサーバーを起動
    print("Webサーバーを起動しています...")
    print("http://localhost:8080/ にアクセスしてください")
    print("ユーザー名: admin, パスワード: password")
    run(app, host='localhost', port=8080, debug=True, reloader=True)
