import os
from shelflet import (
    Model, CharField, IntegerField, BooleanField, DateField, 
    ForeignKey, ManyToManyField, FloatField, TextField, 
    DateTimeField, TimeField, AutoField
)
from datetime import date, datetime, time

# モデル定義
class User(Model):
    name = CharField(required=True)
    db_file = "user.db"

class Group(Model):
    name = CharField(required=True)
    members = ManyToManyField(User, backref="groups")
    db_file = "group.db"

class Message(Model):
    user = ForeignKey(User, backref="messages", on_delete="cascade")
    content = CharField(required=True)
    db_file = "msg.db"

# 全フィールドタイプを使用したモデル
class Product(Model):
    # 基本フィールド
    name = CharField(required=True)
    description = TextField()
    price = FloatField()
    stock = IntegerField(default=0)
    is_available = BooleanField(default=True)

    # 日付・時間フィールド
    created_at = DateTimeField()
    release_date = DateField()
    daily_restock_time = TimeField()

    # 自動採番フィールド
    product_number = AutoField()

    db_file = "product.db"

# 初期化
User.open(index=True)
Group.open(index=True)
Message.open(index=True)
Product.open(index=True)

# ユーザー作成
alice = User(name="Alice"); alice.save()
bob = User(name="Bob"); bob.save()

# グループ作成（多対多）
g = Group(name="Team A", members=[alice, bob])
g.save()

# メッセージ作成（多対1）
Message(user=alice, content="Hello!").save()
Message(user=alice, content="How are you?").save()

# 逆参照：User.messages()
for msg in alice.messages():
    print("[Alice's message]", msg.content)

# 逆参照：User.groups()
for group in alice.groups():
    print("[Alice's group]", group.name)

# 外部キー検索
msgs = Message.where(user=alice)
for m in msgs:
    print("[Search result]", m.content)

# カスケード削除：User削除で関連Messageも削除
alice.delete()

print("[All remaining users]", User.all())
print("[All remaining messages]", Message.all())

# 全フィールドタイプの使用例
print("\n--- 全フィールドタイプの使用例 ---")
# 現在の日時を取得
now = datetime.now()
today = date.today()
current_time = time(12, 30, 0)

# 製品の作成
laptop = Product(
    name="ノートパソコン",
    description="高性能ノートパソコン、8GB RAM、256GB SSD",
    price=89999.99,
    stock=10,
    is_available=True,
    created_at=now,
    release_date=today,
    daily_restock_time=current_time
)
laptop.save()

smartphone = Product(
    name="スマートフォン",
    description="最新モデルのスマートフォン",
    price=79999.99,
    stock=20,
    is_available=True,
    created_at=now,
    release_date=today,
    daily_restock_time=current_time
)
smartphone.save()

# フィルタリングの例
print("\n--- フィルタリングの例 ---")
expensive_products = Product.filter(lambda p: p.price > 80000)
print(f"高価な製品: {[p.name for p in expensive_products]}")

# ソートの例（昇順）
print("\n--- ソートの例 ---")
sorted_by_price_asc = Product.all(order_by="price")
print(f"価格の安い順: {[p.name for p in sorted_by_price_asc]}")

# ソートの例（降順）
sorted_by_price_desc = Product.all(order_by="-price")
print(f"価格の高い順: {[p.name for p in sorted_by_price_desc]}")

# ページネーションの例
print("\n--- ページネーションの例 ---")
page1 = Product.all(limit=1, offset=0)
print(f"1ページ目: {[p.name for p in page1]}")
page2 = Product.all(limit=1, offset=1)
print(f"2ページ目: {[p.name for p in page2]}")

# バリデーションの例
print("\n--- バリデーションの例 ---")
try:
    # 必須フィールドがない場合
    invalid_product = Product(description="説明のみ")
    invalid_product.save()
except ValueError as e:
    print(f"バリデーションエラー: {e}")

# JSONエクスポート
print("\n--- JSONエクスポート/インポート ---")
Group.export_json("groups.json")
User.export_json("users.json")
Message.export_json("messages.json")
Product.export_json("products.json")

# JSONインポートの例（既存のデータを削除してからインポート）
for path in ["product.db", "product.db.bak", "product.db.dat", "product.db.dir"]:
    try:
        os.remove(path)
    except FileNotFoundError:
        pass

Product.import_json("products.json")
print(f"インポートされた製品: {[p.name for p in Product.all()]}")
