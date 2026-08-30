# DroneProject

小型ドローンと人間の身体動作を組み合わせた、インタラクティブパフォーマンスシステム。

フープに取り付けたIMUセンサーからフープの姿勢を取得し、その動きに応じてドローンを制御します。

JSONで定義したタイムラインに沿ってドローンを動作させることができます。

# Concepts

別ファイルを確認してください。

[作品のコンセプト](docs\concepts\concept.md)

[作品の説明](docs\concepts\description.md)

# Features

- IMUによるフープの姿勢取得
- フープの動きとドローンのリアルタイム連動
- JSONによる演目（Scenario）の定義
- 複数のShowの実行・管理
- 緊急着陸などのオペレーション機能

# Documentation

詳細はdocs/を参照してください。

```text
docs/
├── concept/      # 作品概要・コンセプト
├── usage/        # 操作方法
└── technical/    # 技術仕様
```

# Requirements
- Python
- DJI Tello
- DJITelloPy
- IMU sensor(Geo Motion)
- BLE

# Getting Started
pip install -r requirements.txt
python main.py