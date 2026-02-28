# Web小説サイト — セットアップガイド

GitHub Pages として動作する多作品対応の Web 小説リーダーです。

---

## 構成図

```
[メインサイトリポジトリ]  ← GitHub Pages として公開
  ├── index.html           # 小説一覧 + 検索
  ├── reader.html          # 章リーダー
  ├── novels-config.json   # 小説リポジトリの登録リスト（手動編集）
  ├── novels-index.json    # 自動生成される検索インデックス
  └── .github/workflows/update-index.yml   # CI ワークフロー

[小説リポジトリ A]  [小説リポジトリ B]  ...
  ├── 1.txt                # 第1話
  ├── 2.txt                # 第2話
  ├── ...
  ├── meta.json            # タイトル・説明・タグなど
  └── .github/workflows/notify.yml   # push 時にメインサイトを更新
```

---

## STEP 1 — メインサイトリポジトリのセットアップ

### 1-1. リポジトリを作成する

GitHub で新しいリポジトリを作成します（例: `web-novel-site`）。

### 1-2. ファイルをプッシュする

このフォルダ内のファイルをすべてプッシュしてください。

```bash
cd web-novel-site
git init
git add .
git commit -m "initial setup"
git remote add origin https://github.com/YOUR_USERNAME/web-novel-site.git
git push -u origin main
```

### 1-3. GitHub Pages を有効にする

1. リポジトリの **Settings → Pages** を開く
2. **Source** を `Deploy from a branch` に設定
3. **Branch** を `main` / `/ (root)` に設定
4. **Save** をクリック

しばらくすると `https://YOUR_USERNAME.github.io/web-novel-site/` で公開されます。

---

## STEP 2 — novels-config.json に小説リポジトリを登録する

`novels-config.json` を編集して、各小説リポジトリを追加します。

```json
{
  "site": {
    "title": "あなたのサイト名",
    "description": "サイトの説明"
  },
  "repositories": [
    {
      "owner": "YOUR_GITHUB_USERNAME",
      "repo": "novel-repo-1",
      "branch": "main"
    },
    {
      "owner": "OTHER_AUTHOR_USERNAME",
      "repo": "another-novel",
      "branch": "main"
    }
  ]
}
```

編集したらコミット & プッシュしてください。

---

## STEP 3 — 小説リポジトリのセットアップ

### 3-1. 小説リポジトリを作成する

各作品ごとに GitHub リポジトリを作成します（例: `my-fantasy-novel`）。

### 3-2. ファイル構成

```
my-fantasy-novel/
  ├── meta.json            ← タイトル・説明・タグ
  ├── 1.txt                ← 第1話
  ├── 2.txt                ← 第2話
  ├── 3.txt                ← 第3話
  └── .github/
      └── workflows/
          └── notify.yml   ← push 時の通知ワークフロー
```

### 3-3. meta.json の例

```json
{
  "title": "異世界冒険記",
  "description": "平凡な高校生がある日突然異世界に転移して...",
  "author": "あなたの名前",
  "tags": ["異世界転移", "ファンタジー", "冒険"],
  "cover": "https://example.com/cover.jpg",
  "status": "連載中",
  "created_at": "2025-01-01"
}
```

**status の値:**
- `連載中` （緑バッジ）
- `完結` （青バッジ）
- `休止中` （黄バッジ）

### 3-4. txt ファイルの書き方

`1.txt`, `2.txt`, ... と番号順に配置します。

**第1行に章タイトルを書く場合（省略可）:**

```
# プロローグ 〜異世界の扉〜

　目を覚ますと、見慣れない草原の中に倒れていた。
　空は紫がかった青色で、遠くに二つの月が浮かんでいる。
```

第1行が `#`、`【`、`「`、`≪` で始まる場合、自動的に章タイトルとして認識されます。

---

## STEP 4 — push 時の自動更新を設定する

小説リポジトリに push するたびにメインサイトが自動更新されるよう設定します。

### 4-1. PAT（Personal Access Token）を作成する

1. GitHub → **Settings → Developer Settings → Personal access tokens → Fine-grained tokens**
2. **Generate new token** をクリック
3. **Repository access** で `web-novel-site` リポジトリを選択
4. **Permissions → Contents** を `Read and write` に設定
5. トークンを生成してコピーしておく

### 4-2. 小説リポジトリに Secrets を登録する

各小説リポジトリの **Settings → Secrets and variables → Actions → New repository secret** で以下を追加します。

| Secret 名 | 値 |
|---|---|
| `MAIN_SITE_TOKEN` | STEP 4-1 で作成した PAT |
| `MAIN_SITE_OWNER` | メインサイトの GitHub ユーザー名 |
| `MAIN_SITE_REPO` | メインサイトのリポジトリ名（例: `web-novel-site`）|

### 4-3. notify.yml をコピーする

`novel-template/.github/workflows/notify.yml` を小説リポジトリの `.github/workflows/notify.yml` にコピーしてコミットします。

---

## 動作フロー

```
小説リポジトリに push
    ↓
notify.yml が実行される
    ↓
メインサイトの update-index.yml がトリガーされる
    ↓
build_index.py が novels-config.json を読み込む
    ↓
各リポジトリから meta.json と話数を取得
    ↓
novels-index.json を更新してコミット
    ↓
GitHub Pages が自動的に再デプロイされる
```

---

## FAQ

**Q: 手動でインデックスを更新したい**
A: メインサイトリポジトリの **Actions → Update Novel Index → Run workflow** から手動実行できます。

**Q: インデックスは毎日自動更新される？**
A: はい。push 通知に加えて、毎日 0:00 JST に自動更新が走ります。

**Q: 非公開リポジトリの小説は読める？**
A: raw.githubusercontent.com から取得するため、プライベートリポジトリはそのままでは読めません。PAT をサイト側で使う仕組みが必要です（現時点では非対応）。

**Q: カバー画像はどこに置く？**
A: 外部 URL（例: GitHub の issue にアップロードした画像の URL）か、リポジトリに置いて raw URL を指定してください。
