必要なライブラリ
以下のPythonライブラリが必要です。これらは、requirements.txtファイルに記載しておくと便利です。

著作権を所有する
Flask
Flask-SQLAlchemy
Flask-Mail
Flask-APScheduler
python-dotenv
requirements.txtファイルの内容
上記のライブラリをrequirements.txt記載します。

著作権を所有する
Flask==2.0.1
Flask-SQLAlchemy==2.5.1
Flask-Mail==0.9.1
Flask-APScheduler==1.12.3
python-dotenv==0.19.2
実行手順
仮想環境の作成と有効化

プロジェクトディレクトリで仮想環境を作成し、有効化します。
python3 -m venv venv
source venv/bin/activate  # Windowsの場合は venv\Scripts\activate
依存関係のインストール

requirements.txtを使って必要なライブラリをインストールします。

pip install -r requirements.txt
環境変数の設定

.envファイルをプロジェクトのルートディレクトリに作成するには、以下のように設定します。

SECRET_KEY=your-secret-key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
データベースの初期化

アプリケーションを初めて実行する前に、データベースを初期化します。

python app.py
アプリケーションの実行

アプリケーションを実行します。

python app.py
これでアプリケーションが実行され、ブラウザでhttp://127.0.0.1:5000/アクセスすると動作が確認できます。
