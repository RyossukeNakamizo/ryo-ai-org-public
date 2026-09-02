# 04. 参照構成 — CLAUDE.md に書かないための 7 層

docs/01 は「CLAUDE.md を短く保つ理由」、docs/03 は「役割を分ける理由」を扱った。本書はその実装側で、Claude Code が公式に用意している 7 つの置き場所を、**何を置くか／モデルの判断に委ねるか強制するか** の 2 軸で整理し、最小の実例を添える。

本書の記述は 2026-09-02 時点の Claude Code 公式ドキュメント（末尾の参考文献）に照らして確認した。仕様は変わるので、導入前に必ず一次資料を再確認すること。

## 1. 出発点：CLAUDE.md は「お願い」であって「境界」ではない

公式ドキュメントは、CLAUDE.md と auto memory を「文脈であって、強制される設定ではない」と明記している。ある操作をモデルの判断に関係なく止めたいなら PreToolUse hook を使え、という書き方になっている。

ここから設計方針が 1 つ決まる。

| 守らせたいことの性質 | 置き場所 |
|---|---|
| 毎回思い出してほしい事実・方針（破っても即時に損害が出ない） | CLAUDE.md、rules |
| 特定の作業にだけ必要な手順 | skills |
| 別の目で見てほしい作業 | agents（サブエージェント） |
| 破られたら困る境界（秘密情報、破壊操作、外部送信、本番） | settings.json の permissions・sandbox、hooks |

「CLAUDE.md に強く書けば守る」という発想を捨て、**破られて困るものほど CLAUDE.md から遠ざける**。これが本書全体の原則である。

## 2. 7 層の地図

| 層 | 場所 | 役割 | 読み込み | 誰が守らせるか |
|---|---|---|---|---|
| 1 | `~/.claude/CLAUDE.md` | 全プロジェクト共通の個人ルール | 毎セッション起動時 | モデル |
| 2 | `./CLAUDE.md`（または `./.claude/CLAUDE.md`） | リポジトリ固有の契約。チームで共有 | 毎セッション起動時 | モデル |
| 3 | `.claude/rules/*.md` | 話題別の規則。`paths` を付ければ該当ファイルを扱う時だけ | 起動時、または対象ファイル読取時 | モデル |
| 4 | `.claude/skills/<name>/SKILL.md` | 複数工程の手順。呼ばれるまで本文は読まれない | 呼び出し時 | モデル（`disable-model-invocation` で人間限定にできる） |
| 5 | `.claude/agents/<name>.md` | 別コンテキストで動く担当（調査・レビュー） | 委任時 | モデル |
| 6 | `.claude/settings.json`（permissions・sandbox・hooks） | 実行できる／できないの境界 | 常時 | **クライアント（Claude Code 本体）** |
| 7 | auto memory（`~/.claude/projects/<project>/memory/`） | Claude 自身が書く学習メモ | 起動時に先頭 200 行／25KB | モデル |

補足として、`CLAUDE.local.md` は層 2 の個人版（`.gitignore` に入れる）、`.claude/rules/` の `paths` なしファイルは層 2 と同じ扱いで起動時に読まれる。

層 1〜5・7 と層 6 の間に太い線がある。前者はすべて「モデルが読んで判断する」もので、後者だけが「モデルの判断と無関係に効く」。

## 3. 層 1・2：CLAUDE.md に残すもの

公式は 1 ファイル 200 行未満を目安とし、`/doctor` は「コードから推測できる内容」の削除を提案する。残すべきは、コードや設定を読んでも分からない事実だけである。

判定の問いは 1 つ。**「この行を消すと、Claude は実際に間違えるか」**。答えが No なら消す。

残る典型は次のような行である。

- テストは通常のコマンドではなく専用ラッパー経由で実行する（理由つき）
- 生成ファイルは直接編集しない。編集すると CI で戻される
- 一見不要に見える分岐は互換性のために残している（該当パス）
- 完了報告には実行したコマンドと結果を含め、未実行を「成功」と書かない

逆に、ディレクトリ一覧・依存ライブラリ一覧・API 仕様の全文・スタイル規約は入れない。前二者はコードから分かり、後二者はリンターとフォーマッターの仕事である。

注意点を 2 つ。`@path` による import は整理には使えるが、import 先も起動時に展開されるので文脈量の節約にはならない。また、ブロック形式の HTML コメントは文脈に注入される前に除去されるので、保守者向けメモはそこに書ける（コードブロック内のコメントは除去されない）。

## 4. 層 3：rules — 触った時だけ厳しくする

認証コードの規則を DB 移行中に常駐させる必要はない。`paths` を付けた rule は、一致するファイルを Claude が読んだ時に読み込まれる。

```markdown
---
paths:
  - "src/auth/**"
  - "src/**/middleware/**"
---

# 認証・認可まわりの規則

- 認証（誰か）と認可（何ができるか）は別の制御として扱い、保護対象の操作にはサーバ側の認可判定を必ず置く
- クライアント側の表示制御をアクセス制御とみなさない
- セッション・トークン・リダイレクト・ログアウトは、失効と失敗の経路までテストする
- 検証・レート制限・監査ログを弱める変更は、理由を最終報告に残す
```

`paths` の中括弧展開は 1 rule あたり 1,000 パターン／4 MiB の予算があり、超えた分は展開されず文字どおりの中括弧として一致しなくなる。大量のパターンを書くなら分割する。

## 5. 層 4：skills — 手順は呼ばれるまで読ませない

「再現して、テストを書いて、直して、検証して、報告する」は常設の事実ではなく手順なので、skill にする。副作用のある手順は `disable-model-invocation: true` を付け、人間が `/名前` で呼ぶ時だけ動くようにする。

```markdown
---
name: fix-reported-bug
description: 報告された不具合を再現し、失敗するテストを先に用意してから最小の修正を入れ、検証結果つきで報告する
disable-model-invocation: true
---

対象: $ARGUMENTS

1. 観測された挙動・期待される挙動・再現条件・受け入れ条件・やらないことを書き出す
2. 該当する実装・テスト・設定・履歴を読む
3. 失敗を再現する。再現できない場合は、得られた最も強い証拠を示す
4. 報告された挙動で失敗するテストを追加または特定する
5. 根本原因に対する最小の修正を入れる
6. そのテスト → 型検査 → lint → 関連する広い範囲のテストの順に実行する
7. 実装していない側（独立レビュー担当）に差分を見せる
8. 根本原因・変更ファイル・実行コマンドと結果・残る不確実性を報告する
9. commit・push・PR 作成は、別途求められない限り行わない
```

skill の `description` は「いつ読むか」を決める唯一の手がかりなので、トリガー条件と発火してはいけない条件を具体的に書く（docs/02）。

## 6. 層 5：agents — 実装した者に採点させない

長く実装した同じコンテキストは、自分の前提に引っ張られる。差分だけを新しいコンテキストに渡して疑わせる。

```markdown
---
name: fresh-eyes-reviewer
description: 完成した差分を、実装していない立場から実質的な欠陥に限って点検する
tools: Read, Grep, Glob, Bash
model: inherit
---

あなたはこの変更を実装していない。

課題または計画を読み、`git diff` を確認し、実装が置いた前提を反証しようと試みること。
報告するのは次に影響する実質的な欠陥のみ:
- 明示された要件
- 正しさ、データ整合性
- セキュリティ境界
- 後方互換性
- 並行性と失敗経路
- 検証の欠落・誤解を招く検証
- 意図しない範囲拡大

分類は BLOCKER / MATERIAL / OPTIONAL。命名やスタイルの好みは報告しない。
該当箇所はファイルと行で示す。実質的な問題がなければ、何を確認したかを書く。
```

「何か問題を見つけろ」とだけ書くと、問題がなくても指摘を量産して過剰実装を誘発する。対象を絞るのはそのためである。

仕様上の注意が 1 つ。組み込みの Explore と Plan サブエージェントは CLAUDE.md と git status を読み込まない（速度とコストのため）。それ以外の組み込み・カスタムサブエージェントは読み込む。プロジェクト規則を踏まえたレビューをさせたいなら、専用のカスタムエージェントを作る。

## 7. 層 6：permissions・sandbox — 「やらないで」を「できない」に変える

### 7-1. permissions

規則は **deny → ask → allow** の順に評価され、最初に一致したものが結果を決める。狭い allow があっても広い deny が勝つ。

```json
{
  "permissions": {
    "allow": [
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(npm test *)",
      "Bash(npm run lint)",
      "Bash(npm run typecheck)"
    ],
    "ask": [
      "Bash(git commit *)",
      "Bash(git push *)",
      "Bash(npm install *)",
      "Bash(docker *)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Bash(git reset --hard *)",
      "Bash(git clean *)",
      "Bash(git push --force *)",
      "Bash(git push -f *)",
      "Bash(curl *)",
      "Bash(wget *)"
    ],
    "disableBypassPermissionsMode": "disable"
  }
}
```

設計の意図は単純で、頻繁で安全な作業（テスト・lint・差分確認）は自動化し、副作用のある作業（commit・push・依存追加・コンテナ操作）は毎回確認し、秘密情報と破壊操作と外部送信は拒否する。`disableBypassPermissionsMode` は、権限確認を飛ばすモードの使用自体を禁じる。

書き方の要点（公式の一致規則より）:

- `*` は末尾に置き、その前に空白を入れる。`Bash(ls *)` は `ls` にも一致するが `lsof` には一致しない。`Bash(git * main)` のようにサブコマンドの前に `*` を置くと、`-c` を含む任意の git 実行に一致してしまう
- `&&`・`||`・`;`・`|` で連結されたコマンドは、各部分が個別に規則に一致しないと許可されない
- `timeout`・`nice`・`nohup` などのラッパーは剥がして一致判定される。一方 `npx`・`docker exec`・`devbox run` のような環境ランナーは剥がされないので、`Bash(devbox run *)` は内側の任意コマンドを許可してしまう。内側のコマンドまで含めた規則を書く
- `Bash(command:rm *)` のように主要フィールドを名指しする書き方は無視される。`Bash(rm *)` と書く

### 7-2. sandbox

permissions が「どのコマンドを許すか」なら、sandbox は「許したコマンドが触れる範囲」を OS レベルで制限する。

```json
{
  "sandbox": {
    "enabled": true,
    "allowUnsandboxedCommands": false,
    "network": {
      "allowedDomains": ["github.com", "*.npmjs.org"]
    }
  }
}
```

`allowUnsandboxedCommands: false` にすると、sandbox 内で失敗したコマンドが sandbox 外で再実行される逃げ道が閉じる。書き込みが必要な場所は、コマンドを sandbox から除外するのではなく、許可パスを追加する方が推奨されている。

### 7-3. 最低限、閉じておくもの

- `.env`・`secrets/` の読取
- `git reset --hard`、破壊的な `git clean`、force push
- Bash からの外部通信（`curl`・`wget`）。取得が必要なら WebFetch の domain 規則で許可する
- sandbox 外への再実行
- 権限確認の bypass

## 8. hooks — 絶対に止めたいものは二重に止める

permissions の文字列一致は、ラッパーや複合コマンドをすべて捕捉できるとは限らない。絶対に止めたい操作は PreToolUse hook でも止める。hook が終了コード 2 を返すと、そのツール呼び出しはブロックされ、stderr がモデルに理由として渡される。allow 規則があってもブロックが優先する。

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/guard-irreversible.sh" }
        ]
      }
    ]
  }
}
```

```bash
#!/usr/bin/env bash
# .claude/hooks/guard-irreversible.sh — 取り消せない操作を止める
set -euo pipefail
cmd="$(jq -r '.tool_input.command // ""')"
case "$cmd" in
  *"rm -rf"*|*"git reset --hard"*|*"git clean -f"*|*"git push --force"*|*"git push -f"*)
    echo "blocked: irreversible operation. Do it manually after review." >&2
    exit 2 ;;
esac
exit 0
```

`chmod +x` を忘れないこと。この例は `jq` に依存する。hook は設定ファイルから読まれた場合、サブエージェント内のツール呼び出しにも同じように発火する。

hook に向くもの／向かないものの線引きは、モデルの判断で足りるなら CLAUDE.md、パス固有なら rules、必要時の手順なら skills、**絶対に守る境界だけ** permissions／hooks。何でも hook にすると、今度は設定が保守できなくなる。

## 9. 層 7：auto memory はチーム規約に使わない

auto memory は Claude が自分で書くメモで、ユーザーの好み・修正・進行中の判断を残す。マシンローカルで、起動時に読まれるのは索引の先頭 200 行／25KB まで。チーム全員に同じ規則を配る仕組みではない。

チーム規約は Git 管理下の CLAUDE.md・rules・skills・settings.json に置き、auto memory は個人最適化として `/memory` で定期的に監査する。

## 10. 入れてはいけない設定

| 設定 | 何が起きるか | 代わりに |
|---|---|---|
| 「何があっても質問するな」 | 不可逆操作・課金・権限変更・曖昧な仕様判断まで推測で進む | 安全で可逆な仮定は明示して進み、不可逆・外部副作用・データ損失・境界変更・仕様判断だけ 1 問に絞って聞く |
| 「すべての変更に詳細計画を作れ」 | 1 文字修正まで計画が儀式化する | 複数ファイル・公開 API・認証・DB・課金・未知領域だけを計画対象にする |
| 「常に全テストを実行せよ」 | 大きなリポジトリでは時間と資源を浪費する | 最小関連テスト → 型検査 → lint → 広域テストの順に広げる |
| 「パッケージは自由に追加してよい」 | サプライチェーン・ライセンス・脆弱性という信頼境界を無審査で持ち込む | 依存追加は ask に置く |
| 「commit・push・deploy まで自動でやれ」 | 副作用の異なる操作が同じ承認レベルに潰れる | 編集とテストは自動、commit と push は明示要求、deploy は別承認 |
| bypassPermissions の常用 | 保護パスを含む権限確認が全部飛ぶ | 隔離されたコンテナや VM 以外では使わない。`disableBypassPermissionsMode` で封じる |

## 11. 導入の順番と確認

1. いまの CLAUDE.md の各行に「消すと間違えるか」を問い、No を消す
2. 残りを分類する：コードから分かる → 削除／特定パスだけ → rules／複数工程 → skills／絶対禁止 → permissions・hooks／今回だけ → プロンプト／個人だけ → `CLAUDE.local.md` か層 1
3. 完了条件として最低 4 つを CLAUDE.md に残す：最小関連テスト、型検査と lint、実行コマンドと結果の報告、未実行を成功扱いしない
4. 7-3 の項目を settings.json で閉じる
5. 週に何度も貼っている一番長い手順を skill にする
6. 独立レビュー担当を 1 つ作る

作ったら、読み込まれているかを確認する。ファイルを置いただけでは効いていないことがある。

| コマンド | 確認できること |
|---|---|
| `/context` | 実際に読み込まれた CLAUDE.md・rules |
| `/memory` | 永続ルールと auto memory の編集・監査 |
| `/permissions` | allow・ask・deny の現状 |
| `/hooks` | 登録された hook |
| `/sandbox` | sandbox の状態と override |
| `/agents` | 利用可能なサブエージェント |
| `/doctor` | 設定の不整合、CLAUDE.md の肥大化と削減提案 |

最後に、禁止した操作が本当に止まるかを 1 回わざと試す。「書いた」と「効いている」は別である。

## 12. 本書と本リポジトリの対応

| 本書の層 | 本リポジトリでの実装 |
|---|---|
| 層 2 の「完了条件」「証拠ベース完了」 | `plan-first-gate`、`premise-pre-verification`、docs/03 の検収の型 |
| 層 4 の手順分離 | 本リポジトリの skills 全体。description の書き方は docs/02 |
| 層 5 の実装者と採点者の分離 | docs/03 の Judge/Worker、`preemptive-challenger`、`review-agent-essence` |
| 層 6 の機械化 | docs/03 §hooks による規律の機械化 |
| 層 7 の運用 | `memory-discipline`、`memory-pull` / `memory-push` / `memory-gc` |

## 参考文献

一次資料（いずれも 2026-09-02 に参照）:

- Claude Code Docs, "How Claude remembers your project"（CLAUDE.md・rules・auto memory・import・HTML コメント・200 行目安） — https://code.claude.com/docs/en/memory
- Claude Code Docs, "Permissions"（deny→ask→allow の評価順、一致規則、bypass の無効化） — https://code.claude.com/docs/en/permissions
- Claude Code Docs, "Sandboxing"（`allowUnsandboxedCommands`、`network.allowedDomains`） — https://code.claude.com/docs/en/sandboxing
- Claude Code Docs, "Hooks"（PreToolUse、終了コード 2、サブエージェント内での発火） — https://code.claude.com/docs/en/hooks
- Claude Code Docs, "Skills"（`disable-model-invocation`、`$ARGUMENTS`） — https://code.claude.com/docs/en/skills
- Claude Code Docs, "Subagents"（Explore/Plan が CLAUDE.md を読まないこと、`tools`・`model` フィールド） — https://code.claude.com/docs/en/sub-agents

同様の 7 層整理として参考にしたもの:

- @ai_ai_ailover の投稿（2026-08） — https://x.com/ai_ai_ailover/status/2093168450726457702
- HumanLayer, "Writing a good CLAUDE.md" — https://www.humanlayer.dev/blog/writing-a-good-claude-md

本書の例（rule・skill・agent・settings・hook）はすべて本書のために書き起こしたもので、そのまま使うのではなく自分のリポジトリに合わせて削って使うことを前提にしている。
