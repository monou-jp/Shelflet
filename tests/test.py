import os
import pytest
from datetime import datetime, date, time
from shelflet import (
    Model, CharField, ForeignKey, ManyToManyField, 
    IntegerField, BooleanField, FloatField, TextField, 
    DateTimeField, DateField, TimeField, AutoField
)

# テスト用モデル定義
class User(Model):
    name = CharField(required=True)
    db_file = "test_user.db"

class Group(Model):
    name = CharField(required=True)
    members = ManyToManyField(User, backref="groups")
    db_file = "test_group.db"

class Message(Model):
    user = ForeignKey(User, backref="messages", on_delete="cascade")
    content = CharField(required=True)
    db_file = "test_msg.db"

# 全フィールドタイプをテストするためのモデル
class AllFieldsModel(Model):
    # 基本フィールド
    char_field = CharField(required=True)
    text_field = TextField()
    int_field = IntegerField()
    float_field = FloatField()
    bool_field = BooleanField()

    # 日付・時間フィールド
    date_field = DateField()
    time_field = TimeField()
    datetime_field = DateTimeField()

    # 自動採番フィールド
    auto_field = AutoField()

    db_file = "test_all_fields.db"

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # 初期化
    User.open(index=True)
    Group.open(index=True)
    Message.open(index=True)
    AllFieldsModel.open(index=True)

    # テスト前にDBファイルを削除
    db_files = ["test_user.db", "test_group.db", "test_msg.db", "test_all_fields.db"]
    for path in db_files:
        for ext in ["", ".bak", ".dat", ".dir"]:
            try:
                os.remove(path + ext)
            except FileNotFoundError:
                pass
    yield

    # テスト後の後片付け
    for path in db_files:
        for ext in ["", ".bak", ".dat", ".dir"]:
            try:
                os.remove(path + ext)
            except FileNotFoundError:
                pass

def test_create_user():
    u = User(name="Test")
    u.save()
    assert len(User.all()) == 1

def test_foreignkey_and_cascade():
    u = User(name="Taro"); u.save()
    m1 = Message(user=u, content="Hi")
    m2 = Message(user=u, content="Yo")
    m1.save(); m2.save()
    assert len(Message.where(user=u)) == 2
    u.delete()
    assert len(Message.all()) == 0

def test_many_to_many():
    u1 = User(name="A"); u1.save()
    u2 = User(name="B"); u2.save()
    g = Group(name="G1", members=[u1, u2]); g.save()
    assert u1 in g.members
    assert g in u1.groups()
    g.members.remove(u1)
    g.save()
    assert u1 not in g.members
    assert g not in u1.groups()

def test_export_import(tmp_path):
    # JSONエクスポート・インポートのテスト
    u = User(name="ExportTest"); u.save()
    export_path = tmp_path / "export.json"
    User.export_json(export_path)
    for path in ["test_user.db", "test_user.db.bak", "test_user.db.dat", "test_user.db.dir"]:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
    User.import_json(export_path)
    users = User.all()
    assert len(users) == 1
    assert users[0].name == "ExportTest"

def test_all_field_types():
    """全フィールドタイプのテスト"""
    # 現在の日時を取得
    now = datetime.now()
    today = date.today()
    current_time = time(12, 34, 56)

    # 全フィールドタイプを含むオブジェクトを作成
    obj = AllFieldsModel(
        char_field="テスト文字列",
        text_field="これは長いテキストフィールドです。",
        int_field=42,
        float_field=3.14,
        bool_field=True,
        date_field=today,
        time_field=current_time,
        datetime_field=now
    )
    obj.save()

    # データベースから取得して値を検証
    saved = AllFieldsModel.get_by_id(obj.id)
    assert saved.char_field == "テスト文字列"
    assert saved.text_field == "これは長いテキストフィールドです。"
    assert saved.int_field == 42
    assert saved.float_field == 3.14
    assert saved.bool_field is True
    assert saved.date_field == today
    assert saved.time_field.hour == current_time.hour
    assert saved.time_field.minute == current_time.minute
    assert saved.datetime_field.date() == now.date()
    assert saved.auto_field is not None  # 自動採番フィールドは値が設定されているはず

def test_validation():
    """バリデーションのテスト"""
    # 必須フィールドがない場合はエラー
    with pytest.raises(ValueError):
        AllFieldsModel().save()

    # 型が間違っている場合はエラー
    with pytest.raises(TypeError):
        AllFieldsModel(char_field=123).save()

    with pytest.raises(TypeError):
        AllFieldsModel(char_field="OK", int_field="not an integer").save()

    with pytest.raises(TypeError):
        AllFieldsModel(char_field="OK", bool_field="not a boolean").save()

    with pytest.raises(TypeError):
        AllFieldsModel(char_field="OK", date_field="not a date").save()

def test_filtering_and_sorting():
    """フィルタリングとソートのテスト"""
    # テストデータ作成
    for i in range(10):
        User(name=f"User{i}").save()

    # フィルタリングのテスト
    filtered = User.filter(lambda u: int(u.name[-1]) % 2 == 0)
    assert len(filtered) == 5  # 偶数のユーザーのみ

    # ソートのテスト（昇順）
    sorted_asc = User.all(order_by="name")
    assert sorted_asc[0].name == "User0"
    assert sorted_asc[-1].name == "User9"

    # ソートのテスト（降順）
    sorted_desc = User.all(order_by="-name")
    assert sorted_desc[0].name == "User9"
    assert sorted_desc[-1].name == "User0"

    # ページネーションのテスト
    page1 = User.all(limit=3, offset=0)
    assert len(page1) == 3

    page2 = User.all(limit=3, offset=3)
    assert len(page2) == 3
    assert page1[0].id != page2[0].id

def test_datetime_json():
    """日付・時間フィールドのJSONシリアライズ/デシリアライズのテスト"""
    # 現在の日時を取得
    now = datetime.now()
    today = date.today()
    current_time = time(12, 34, 56)

    # オブジェクト作成
    obj = AllFieldsModel(
        char_field="DateTimeTest",
        date_field=today,
        time_field=current_time,
        datetime_field=now
    )
    obj.save()

    # JSONエクスポート
    export_path = "test_datetime.json"
    AllFieldsModel.export_json(export_path)

    # DBをクリア
    for ext in ["", ".bak", ".dat", ".dir"]:
        try:
            os.remove("test_all_fields.db" + ext)
        except FileNotFoundError:
            pass

    # JSONからインポート
    AllFieldsModel.import_json(export_path)

    # 検証
    loaded = AllFieldsModel.all()[0]
    assert loaded.date_field.isoformat() == today.isoformat()
    assert loaded.time_field.hour == current_time.hour
    assert loaded.time_field.minute == current_time.minute
    assert loaded.datetime_field.date() == now.date()

    # 後片付け
    os.remove(export_path)
