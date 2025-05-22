import shelve
import uuid
import json
from datetime import date, datetime, time
from operator import attrgetter

# --------------------
# フィールド定義
# --------------------
class Field:
    """
    フィールドの基底クラス
    全てのフィールドタイプはこのクラスを継承する
    """
    def __init__(self, required=False, default=None, unique=False):
        """
        フィールドを初期化する

        Args:
            required (bool): 必須フィールドかどうか
            default: デフォルト値
            unique (bool): ユニーク制約があるかどうか
        """
        self.required = required
        self.default = default
        self.unique = unique
        self.name = None  # ModelMetaによって後で設定される

    def validate(self, value):
        """
        値のバリデーションを行う

        Args:
            value: 検証する値

        Raises:
            ValueError: 必須フィールドに値がない場合
        """
        if self.required and value is None:
            raise ValueError(f"{self.name} は必須です")

class AutoField(Field):
    _counter = 0
    _counter_initialized = False
    _counter_file = "autofield_counter.dat"

    def __init__(self):
        super().__init__(required=True)

    @classmethod
    def _initialize_counter(cls):
        """カウンターの初期化（アプリケーション起動時に一度だけ実行）"""
        if cls._counter_initialized:
            return

        try:
            # カウンター値をファイルから読み込む
            with open(cls._counter_file, 'r') as f:
                cls._counter = int(f.read().strip())
        except (FileNotFoundError, ValueError):
            # ファイルがない場合や値が不正な場合は0から開始
            cls._counter = 0

        # 既存のデータベースから最大値を取得
        for model_cls in Model.__subclasses__():
            for field_name, field in model_cls._fields.items():
                if isinstance(field, AutoField):
                    try:
                        # 全オブジェクトを取得して最大値を探す
                        objects = model_cls.all()
                        if objects:
                            max_value = max(getattr(obj, field_name, 0) or 0 for obj in objects)
                            cls._counter = max(cls._counter, max_value)
                    except Exception:
                        # エラーが発生した場合は無視して続行
                        pass

        cls._counter_initialized = True

    @classmethod
    def _save_counter(cls):
        """カウンター値をファイルに保存"""
        try:
            with open(cls._counter_file, 'w') as f:
                f.write(str(cls._counter))
        except Exception:
            # エラーが発生した場合は無視（次回起動時に再取得される）
            pass

    def get_default(self):
        # カウンターの初期化
        AutoField._initialize_counter()

        # カウンターをインクリメント
        AutoField._counter += 1

        # カウンター値を保存
        AutoField._save_counter()

        return AutoField._counter

    def validate(self, value):
        if value is None:
            value = self.get_default()
        elif isinstance(value, int) and value > AutoField._counter:
            # 既存の値が現在のカウンターより大きい場合、カウンターを更新
            AutoField._counter = value
            AutoField._save_counter()

        if not isinstance(value, int):
            raise TypeError(f"{self.name} は自動採番された整数である必要があります")

        return value

class IntegerField(Field):
    def validate(self, value):
        super().validate(value)
        if value is not None and not isinstance(value, int):
            raise TypeError(f"{self.name} は数値である必要があります")

class FloatField(Field):
    def validate(self, value):
        super().validate(value)
        if value is not None and not isinstance(value, float):
            raise TypeError(f"{self.name} は浮動小数点数である必要があります")

class CharField(Field):
    def __init__(self, max_length=None, **kwargs):
        super().__init__(**kwargs)
        self.max_length = max_length

    def validate(self, value):
        super().validate(value)
        if value is not None and not isinstance(value, str):
            raise TypeError(f"{self.name} は文字列である必要があります")
        if self.max_length and len(value) > self.max_length:
            raise ValueError(f"{self.name} は最大 {self.max_length} 文字です")

class TextField(Field):
    def validate(self, value):
        super().validate(value)
        if value is not None and not isinstance(value, str):
            raise TypeError(f"{self.name} は文字列である必要があります")

class BooleanField(Field):
    def validate(self, value):
        super().validate(value)
        if value is not None and not isinstance(value, bool):
            raise TypeError(f"{self.name} は True/False である必要があります")

class DateTimeField(Field):
    def __init__(self, min_value=None, max_value=None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value):
        super().validate(value)
        if value is None:
            return

        # 型チェック
        if not isinstance(value, datetime):
            try:
                # 文字列からの変換を試みる
                value = datetime.fromisoformat(str(value))
            except (ValueError, TypeError):
                raise TypeError(f"{self.name} は datetime 型または ISO 形式の文字列である必要があります")

        # 最小値チェック
        if self.min_value is not None and value < self.min_value:
            raise ValueError(f"{self.name} は {self.min_value} 以降である必要があります")

        # 最大値チェック
        if self.max_value is not None and value > self.max_value:
            raise ValueError(f"{self.name} は {self.max_value} 以前である必要があります")

        return value

class DateField(Field):
    def __init__(self, min_value=None, max_value=None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value):
        super().validate(value)
        if value is None:
            return

        # 型チェック
        if not isinstance(value, date):
            try:
                # 文字列からの変換を試みる
                value = date.fromisoformat(str(value))
            except (ValueError, TypeError):
                raise TypeError(f"{self.name} は date 型または ISO 形式の文字列である必要があります")

        # 最小値チェック
        if self.min_value is not None and value < self.min_value:
            raise ValueError(f"{self.name} は {self.min_value} 以降である必要があります")

        # 最大値チェック
        if self.max_value is not None and value > self.max_value:
            raise ValueError(f"{self.name} は {self.max_value} 以前である必要があります")

        return value

class TimeField(Field):
    def __init__(self, min_value=None, max_value=None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value):
        super().validate(value)
        if value is None:
            return

        # 型チェック
        if not isinstance(value, time):
            try:
                # 文字列からの変換を試みる
                value = time.fromisoformat(str(value))
            except (ValueError, TypeError):
                raise TypeError(f"{self.name} は time 型または ISO 形式の文字列である必要があります")

        # 最小値チェック
        if self.min_value is not None and value < self.min_value:
            raise ValueError(f"{self.name} は {self.min_value} 以降である必要があります")

        # 最大値チェック
        if self.max_value is not None and value > self.max_value:
            raise ValueError(f"{self.name} は {self.max_value} 以前である必要があります")

        return value

class ForeignKey(Field):
    """
    外部キー（1対多）フィールド
    他のモデルへの参照を保持する
    """
    def __init__(self, model_class, backref=None, required=False, null=False, on_delete=None):
        """
        外部キーフィールドを初期化する

        Args:
            model_class: 参照先のモデルクラス
            backref (str, optional): 逆参照の名前
            required (bool): 必須かどうか
            null (bool): Noneを許容するかどうか
            on_delete (str, optional): 親オブジェクト削除時の動作（"cascade"で子も削除）
        """
        super().__init__(required=required)
        self.model_class = model_class
        self.backref = backref
        self.null = null
        self.on_delete = on_delete

    def validate(self, value):
        """値のバリデーション"""
        if not self.null:
            super().validate(value)
        if value is not None and not isinstance(value, self.model_class):
            raise TypeError(f"{self.name} は {self.model_class.__name__} のインスタンスである必要があります")

class ManyToManyField(Field):
    """
    多対多フィールド
    他のモデルへの複数の参照を保持する
    """
    def __init__(self, model_class, backref=None):
        """
        多対多フィールドを初期化する

        Args:
            model_class: 参照先のモデルクラス
            backref (str, optional): 逆参照の名前
        """
        super().__init__(required=False)  # 多対多は常にrequired=False
        self.model_class = model_class
        self.backref = backref

    def validate(self, value):
        """値のバリデーション"""
        if value is not None and not isinstance(value, list):
            raise TypeError(f"{self.name} はリストである必要があります")
        for item in value or []:  # valueがNoneの場合に対応
            if not isinstance(item, self.model_class):
                raise TypeError(f"{self.name} の要素は {self.model_class.__name__} である必要があります")

# --------------------
# モデル定義
# --------------------
class ModelMeta(type):
    """
    モデルクラスのメタクラス
    クラス定義時にフィールドを自動的に収集し、逆参照メソッドを設定する
    """
    def __new__(cls, name, bases, attrs):
        # フィールドの収集
        fields = {}
        for key, val in list(attrs.items()):
            if isinstance(val, Field):
                val.name = key  # フィールド名を設定
                fields[key] = val
        attrs['_fields'] = fields  # クラスに_fieldsとして保存
        new_cls = super().__new__(cls, name, bases, attrs)

        # 逆参照（backref）の設定
        for field in fields.values():
            if isinstance(field, (ForeignKey, ManyToManyField)) and field.backref:
                def make_backref(fname, model_cls):
                    def related(self):
                        """逆参照によって関連オブジェクトを取得するメソッド"""
                        objs = model_cls.all()
                        if isinstance(model_cls._fields[fname], ForeignKey):
                            # 外部キーの場合
                            return [o for o in objs if getattr(o, fname) and getattr(o, fname).id == self.id]
                        elif isinstance(model_cls._fields[fname], ManyToManyField):
                            # 多対多の場合
                            return [o for o in objs if self in getattr(o, fname)]
                        return []
                    return related
                method = make_backref(field.name, new_cls)
                setattr(field.model_class, field.backref, method)

        return new_cls

class Model(metaclass=ModelMeta):
    """
    モデルの基底クラス
    全てのモデルはこのクラスを継承する
    """
    db_file = 'data.db'  # デフォルトのデータベースファイル名
    _index_cache = None  # インデックスキャッシュ（高速化のため）
    __version__ = '1.0'  # バージョン情報

    def __init__(self, **kwargs):
        """
        モデルのインスタンスを初期化する

        Args:
            **kwargs: フィールド名と値のペア
        """
        self.id = kwargs.get("id", str(uuid.uuid4()))  # IDがない場合はUUIDを生成
        for name, field in self._fields.items():
            value = kwargs.get(name, field.default)
            validated_value = field.validate(value)  # 値のバリデーション
            # AutoFieldの場合は、validate()が返した値を使用する
            if isinstance(field, AutoField) and validated_value is not None:
                value = validated_value
            setattr(self, name, value)

    def to_dict(self):
        """オブジェクトを辞書形式に変換する"""
        data = {}
        for k, field in self._fields.items():
            val = getattr(self, k)
            if isinstance(field, ForeignKey):
                data[k] = val.id if val else None
            elif isinstance(field, ManyToManyField):
                data[k] = [obj.id for obj in val] if val else []
            elif isinstance(field, (DateField, DateTimeField, TimeField)) and val:
                data[k] = val.isoformat()
            else:
                data[k] = val
        data["id"] = self.id
        return data

    @classmethod
    def _from_dict(cls, data):
        """辞書形式からオブジェクトを生成する"""
        obj_data = {}
        for k, field in cls._fields.items():
            val = data.get(k)
            if isinstance(field, ForeignKey):
                obj_data[k] = field.model_class.get_by_id(val) if val else None
            elif isinstance(field, ManyToManyField):
                obj_data[k] = [field.model_class.get_by_id(i) for i in val or []]
            elif isinstance(field, DateField) and isinstance(val, str):
                obj_data[k] = date.fromisoformat(val)
            elif isinstance(field, DateTimeField) and isinstance(val, str):
                obj_data[k] = datetime.fromisoformat(val)
            elif isinstance(field, TimeField) and isinstance(val, str):
                obj_data[k] = time.fromisoformat(val)
            else:
                obj_data[k] = val
        obj_data["id"] = data["id"]
        return cls(**obj_data)

    def save(self):
        """
        オブジェクトをデータベースに保存する
        新規作成の場合は追加、既存の場合は更新
        ユニーク制約のチェックも行う
        """
        # ユニーク制約のチェック
        cls = self.__class__
        for field_name, field in cls._fields.items():
            if field.unique:
                value = getattr(self, field_name)
                if value is not None:  # None値はユニーク制約チェックから除外
                    # 同じ値を持つ他のオブジェクトを検索
                    existing = cls.where(**{field_name: value})
                    # 自分自身以外に同じ値を持つオブジェクトがあればエラー
                    if any(obj.id != self.id for obj in existing):
                        raise ValueError(f"{field_name}の値 '{value}' は既に使用されています。ユニークな値を指定してください。")

        with shelve.open(self.db_file, writeback=True) as db:
            db[self.id] = self.to_dict()  # 辞書形式に変換して保存
        if self.__class__._index_cache is not None:
            self.__class__._index_cache[self.id] = self  # キャッシュも更新

    def delete(self):
        """
        オブジェクトをデータベースから削除する
        関連するオブジェクトも適切に処理する
        """
        cls = self.__class__
        # 全モデルクラスをチェック
        for model in Model.__subclasses__():
            for fname, field in model._fields.items():
                # 外部キーの場合
                if isinstance(field, ForeignKey) and field.model_class == cls:
                    if field.on_delete == "cascade":
                        # カスケード削除が指定されている場合、関連オブジェクトも削除
                        for obj in model.where(**{fname: self}):
                            obj.delete()
                # 多対多の場合
                if isinstance(field, ManyToManyField) and field.model_class == cls:
                    # 関連オブジェクトから自分への参照を削除
                    for obj in model.all():
                        old = getattr(obj, fname)
                        new = [o for o in old if o.id != self.id]
                        if len(old) != len(new):
                            setattr(obj, fname, new)
                            obj.save()
        # データベースから削除
        with shelve.open(cls.db_file, writeback=True) as db:
            if self.id in db:
                del db[self.id]
        # キャッシュからも削除
        if cls._index_cache:
            cls._index_cache.pop(self.id, None)

    @classmethod
    def open(cls, index=False):
        """
        データベースを開き、必要に応じてインデックスをメモリにロードする

        Args:
            index (bool): Trueの場合、全データをメモリにキャッシュする（高速化）
        """
        if index:
            with shelve.open(cls.db_file) as db:
                # 全データをメモリにロード
                cls._index_cache = {k: cls._from_dict(v) for k, v in db.items()}
        else:
            # キャッシュを無効化
            cls._index_cache = None

    @classmethod
    def all(cls, order_by=None, limit=None, offset=None):
        """
        モデルの全オブジェクトを取得する

        Args:
            order_by (str, optional): ソートするフィールド名。'-'で始まる場合は降順
            limit (int, optional): 取得する最大件数
            offset (int, optional): スキップする件数（ページネーション用）

        Returns:
            list: モデルオブジェクトのリスト
        """
        # キャッシュがあればそれを使用、なければDBから読み込み
        data = list(cls._index_cache.values()) if cls._index_cache else [
            cls._from_dict(v) for v in shelve.open(cls.db_file).values()
        ]
        # ソート処理
        if order_by:
            reverse = order_by.startswith("-")  # '-'で始まる場合は降順
            key = order_by.lstrip("-")
            data.sort(key=attrgetter(key), reverse=reverse)
        # オフセット処理（ページネーション）
        if offset:
            data = data[offset:]
        # 件数制限（ページネーション）
        if limit:
            data = data[:limit]
        return data

    @classmethod
    def where(cls, **conditions):
        """
        条件に一致するオブジェクトを検索する

        Args:
            **conditions: フィールド名と値のペア（例: name="Alice", age=20）

        Returns:
            list: 条件に一致するモデルオブジェクトのリスト
        """
        results = []
        for obj in cls.all():
            match = True
            for k, v in conditions.items():
                val = getattr(obj, k, None)
                if isinstance(val, Model):
                    # モデルオブジェクトの場合はIDで比較
                    match = match and (val.id == v.id)
                else:
                    # 通常の値は等価比較
                    match = match and (val == v)
            if match:
                results.append(obj)
        return results

    @classmethod
    def filter(cls, fn):
        """
        関数による高度なフィルタリングを行う

        Args:
            fn (callable): 各オブジェクトを引数に取り、真偽値を返す関数

        Returns:
            list: 条件に一致するモデルオブジェクトのリスト
        """
        return [obj for obj in cls.all() if fn(obj)]

    @classmethod
    def get_by_id(cls, obj_id):
        """
        IDによってオブジェクトを取得する

        Args:
            obj_id (str): 取得するオブジェクトのID

        Returns:
            Model: 見つかったオブジェクト、存在しない場合はNone
        """
        if cls._index_cache:
            # キャッシュがあればそこから取得（高速）
            return cls._index_cache.get(obj_id)
        # キャッシュがなければDBから直接取得
        with shelve.open(cls.db_file) as db:
            raw = db.get(obj_id)
            return cls._from_dict(raw) if raw else None

    @classmethod
    def export_json(cls, path):
        """
        モデルの全データをJSONファイルにエクスポートする

        Args:
            path (str): 出力先のJSONファイルパス
        """
        with open(path, 'w', encoding='utf-8') as f:
            json.dump([obj.to_dict() for obj in cls.all()], f, ensure_ascii=False, indent=2)

    @classmethod
    def import_json(cls, path):
        """
        JSONファイルからデータをインポートする

        Args:
            path (str): インポート元のJSONファイルパス
        """
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
            for row in data:
                obj = cls._from_dict(row)
                obj.save()

    def __repr__(self):
        fields = ", ".join(f"{k}={getattr(self, k)!r}" for k in self._fields)
        return f"<{self.__class__.__name__} id={self.id}, {fields}>"
