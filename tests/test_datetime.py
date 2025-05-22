import os
from shelflet import Model, CharField, DateTimeField, TimeField, DateField
from datetime import datetime, date, time

# テスト用のモデル定義
class DateTimeModel(Model):
    name = CharField(required=True)
    created_at = DateTimeField()
    event_date = DateField()
    event_time = TimeField()
    db_file = "test_datetime.db"

# 前回のテストデータを削除
for ext in ["", ".bak", ".dat", ".dir"]:
    try:
        os.remove("test_datetime.db" + ext)
    except FileNotFoundError:
        pass

# テストデータの作成
now = datetime.now()
today = date.today()
current_time = time(12, 34, 56)

# オブジェクト作成
obj = DateTimeModel(
    name="Test",
    created_at=now,
    event_date=today,
    event_time=current_time
)
obj.save()

# JSONエクスポート
DateTimeModel.export_json("test_datetime.json")

# DBをクリア
for ext in ["", ".bak", ".dat", ".dir"]:
    try:
        os.remove("test_datetime.db" + ext)
    except FileNotFoundError:
        pass

# JSONからインポート
DateTimeModel.import_json("test_datetime.json")

# 検証
loaded = DateTimeModel.all()[0]
print(f"Name: {loaded.name}")
print(f"Created at: {loaded.created_at}")
print(f"Event date: {loaded.event_date}")
print(f"Event time: {loaded.event_time}")

# 元のデータと比較
print(f"DateTime equal: {loaded.created_at.isoformat() == now.isoformat()}")
print(f"Date equal: {loaded.event_date.isoformat() == today.isoformat()}")
print(f"Time equal: {loaded.event_time.isoformat() == current_time.isoformat()}")

# 後片付け
os.remove("test_datetime.json")
for ext in ["", ".bak", ".dat", ".dir"]:
    try:
        os.remove("test_datetime.db" + ext)
    except FileNotFoundError:
        pass
