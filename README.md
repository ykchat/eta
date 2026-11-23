# eta

バスの接近情報を表示する CLI（作成中）。

## 概要

- データ取得元: ODPT API、ODPT配布GTFS
- 保存先: `.cache/eta.sqlite3`

## 必要なもの

- Windows
- [pixi](https://pixi.sh/)
- [ODPT開発者サイト](https://developer.odpt.org/)のアクセストークン（登録が必要）

## セットアップ

### 1. 環境を作成する

```powershell
pixi install
```

### 2. ODPTアクセストークンを設定する

環境変数 `ODPT_ACCESS_TOKEN` を優先し、未設定の場合は `.secrets/odpt.env` を読み込みます。

環境変数で設定する場合:

```powershell
$env:ODPT_ACCESS_TOKEN = Read-Host "ODPT access token" -MaskInput
```

`$env:` で設定した値は、そのターミナルを閉じると消えます。

環境ファイルで設定する場合:

次のファイルを作成します。

```text
.secrets/odpt.env
```

```dotenv
ODPT_ACCESS_TOKEN=<アクセストークン>
```

### 3. 取り込むGTFSを設定する

ODPT配布GTFSのうち、取り込むデータセットを次のファイルに登録します。
取り込むフィードを変えるときは、このファイルを編集します。

```text
.eta/odpt_gtfs.toml
```

```toml
[[feeds]]
operator = "KawasakiTsurumiRinkoBus"   # files/odpt/{operator}/{name}.zip
name = "allrinko"
date = "20261101"
```

各項目の意味（各値は[ODPT データカタログ](https://ckan.odpt.org/dataset)で確認）:

- `operator`: 事業者（URL の `files/odpt/{operator}/…` の部分）
- `name`: フィードの名前（`.zip` は付けない）
- `date`: 版の日付

## 最初の使い方

まず事業者を取り込みます。ODPT API と、`.eta/odpt_gtfs.toml` に書いた GTFS の両方から取り込みます。

```powershell
pixi run eta update operators
```

取り込み後、一覧を確認できます。

```powershell
pixi run eta search operators
```

名前の一部で検索できます。

```powershell
pixi run eta search operators 臨港
```

## コマンドリファレンス

### 事業者を取り込む

```powershell
pixi run eta update operators
pixi run eta update operators --source <取得元>
```

取得元を指定しない場合は、すべての取得元から取り込みます。
`--source` を指定すると、その取得元だけを取り込みます（ほかの取得元の事業者は残ります）。

### 事業者を検索する

```powershell
pixi run eta search operators
pixi run eta search operators <検索文字列>
```

検索対象は、名前（`KeioBus` など、ID の一部）と、日本語・英語の名称です（大文字・小文字は区別しません）。

## データ取得元

| ID | 説明 | 設定 |
| --- | --- | --- |
| `odpt_json` | ODPT APIから事業者一覧を取得 | アクセストークンが必要 |
| `odpt_gtfs` | 登録したGTFSから事業者を取得 | `.eta/odpt_gtfs.toml`とアクセストークンが必要 |

## データの保存

取り込んだ事業者は `.cache/eta.sqlite3` に保存されます。
ファイルを削除すると、再取り込みが必要です。

```powershell
Remove-Item .cache/eta.sqlite3
pixi run eta update operators
```

## Bitwarden Secrets Managerを使う

ODPTアクセストークンをBitwarden Secrets Managerで管理する場合:

1. Bitwarden Secrets Manager のプロジェクトに、シークレット `ODPT_ACCESS_TOKEN` を登録する
2. [bws](https://bitwarden.com/help/secrets-manager-cli/)をインストールする
3. マシンアカウントのアクセストークンとプロジェクトIDを環境変数に設定する
4. `eta-bws` タスクを使用する

```powershell
$env:BWS_ACCESS_TOKEN = Read-Host "BWS access token" -MaskInput
$env:BWS_PROJECT_ID = "<プロジェクトID>"
pixi run eta-bws update operators
```

`$env:` で設定した値は、ターミナルを閉じると消えます。
今後も使う場合は、ユーザー環境変数に設定します。

```powershell
$token = Read-Host "BWS access token" -MaskInput
[Environment]::SetEnvironmentVariable("BWS_ACCESS_TOKEN", $token, "User")
Remove-Variable token
[Environment]::SetEnvironmentVariable("BWS_PROJECT_ID", "<プロジェクトID>", "User")
```

`pixi run eta-bws <コマンド>` を使う場合、通常の `pixi run eta <コマンド>` を置き換えます。
ODPT につながないコマンド（`search`）は、どちらで実行しても構いません。

## 開発

```powershell
pixi run -e dev typecheck   # Pyright strict
pixi run -e dev test        # pytest
```

CIではWindows上で型チェックとテストを実行します。
プルリクエストごとにチェックされ、失敗するとマージできません。

## データ利用について

事業者などのデータは公共交通オープンデータセンターから取得しています。
利用時は、各データに設定されたライセンス（公共交通オープンデータ基本ライセンスなど）に従ってください。
