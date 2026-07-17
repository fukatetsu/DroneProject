# 染地児童館操作方法

演目は3つに分かれています。
この演目を順番にターミナルに入力していってください。
入力後は特別な操作はいりません。
最後まで実行されたらEnterキーの待機待ちとなります。
実行されてから離陸までにわざとラグを入れている箇所もあります。

## 1つ目の演目

離陸→上下移動→着陸→離陸→フープ追従→着陸

python src/main.py --scenario src/scenarios/someji_start.json

## 2つ目の演目

離陸→ドローンが自由に移動→着陸

python src/main.py --scenario src/scenarios/someji_mid.json

## 3つ目の演目

離陸→ドローンが弧を描く→フープ追従→着陸
python src/main.py --scenario src/scenarios/someji_last.json

# コマンド

実行中にターミナルに入力してEnterを押すことで発行されます

- p, pp ドローンの停止 Pauseキーです
- land ドローンの着陸 Pauseの後に実行してください

# ドローンとの接続

ドローンとはWi-Fiで接続しています。
ドローンの起動・再起動時にはTello から始まるアクセスポイントにPCからアクセスしてください。

# フープとの接続

GeoMotionを用いて接続しています。
アプリケーションで接続が確認できれば、特に特別な操作は必要ありません。


