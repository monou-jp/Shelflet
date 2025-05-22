# Shelflet

**Shelflet** は Python 組み込みの `shelve` をベースとした、軽量データ管理ORM + Web UI システムです。SQLiteすら不要で、設定もゼロ。シンプルに始めたい開発者のために作られました。

## 特徴

- Python標準ライブラリのみ（外部DB不要）
- モデル定義ベースのバリデーション・リレーション対応
- 多対1 / 多対多リレーション
- BottleベースのWeb管理画面
- BootstrapベースのUI
- JSONインポート・エクスポート対応
- ログイン認証付き

## 起動方法

```bash
pip install bottle
python admin_ui.py
