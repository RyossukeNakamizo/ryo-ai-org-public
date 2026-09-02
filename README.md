# ryo-ai-org-public

AI を「単発のアシスタント」ではなく **役割を分けた組織** として運用するための、規律とメソッドのスキル集です。
司令塔・実装・独立検証・調査という席の分離、判断の構造化（Fact→Insight→Decision→Proposal）、
検収と振り返りの型、記憶の運用といった、日々の実務で繰り返し効いた作法を 25 本のスキルとして切り出しています。

- ライセンス: Apache License 2.0（`LICENSE`）／第三者帰属は `NOTICE`
- 想定利用: Claude Code などのエージェント環境に `skills/<name>/SKILL.md` として読み込ませる
- 収録: 25 本（対話エージェント向け 16 本 ＋ チャット運用向け 9 本）

## 収録スキル

### エージェント運用系（出自: `skills/`）— 16 本

| スキル | 概要 |
|---|---|
| `explanation-bridge` | | ユーザーの思考特性（現象→本質→ゴール→評価基準→制約→最適解を高速で走らせ、 発話では中間を省略して「現象→結論」だけが出る）に起因する 「話が飛ぶ」「前提未共有」問題を補正するスキル。 |
| `preemptive-challenger` | | Claudeが回答・評価・提案を出す前に、自分の判断の盲点・弱点・反論を先に列挙するスキル。 |
| `senior-software` | Act as a senior software engineer for design, implementation, and refactoring in one workflow. |
| `senior-qa` | Senior QA engineer workflow combining code review and debugging into one pass. |
| `memory-gc` | プロジェクトMEMORY. |
| `memory-pull` | グローバル(~/memory/MEMORY. |
| `memory-push` | プロジェクトMEMORY. |
| `frontend-mockup` | > 自然言語の要望または手書きメモ・ワイヤーフレーム画像から、Webフロントエンドの 動くモックアップ（イメージファイル/HTML）を最短で生成するスキル。 |
| `aws-multicloud-mentor` | > AWSの学習・設計・実装を初級から上級まで支援するメンタースキル。 |
| `gcp-multicloud-mentor` | > GCP（Google Cloud）の学習・設計・実装を初級から上級まで支援するメンタースキル。 |
| `structured-doc-frontmatter` | | 統一 frontmatter + 8セクション（Goal/Context/Decisions/Architecture/Evaluation/Failure/Reusable Pattern/Next Action）… |
| `save-instruction` | | chat Claude（Judge）が起草した Worker 指示書全文を、クリップボードから Downloads 受け渡し規約（claude_YYYY-MM-DD_<topic>_worker_instructio… |
| `web-app-architecture` | > Webアプリの構成（フロント×BFF×バックエンド×接続方式×レンダリング×認証×デプロイ）を 要件から選定するアーキテクチャ判断スキル。 |
| `graph-de` | | インタラクティブなグラフ・チャート・データビジュアライゼーションをウィジェットとして表示するスキル。 |
| `review-agent-essence` | | Claude Codeグローバルスキルの品質レビューエンジン。 |
| `eli5-visual-explainer-v1` | むずかしい話を「まったく知らない人」向けに、大きな図と少ない文字の1枚HTMLで説明する係。 |

### チャット運用系（出自: `chat-only/`）— 9 本

| スキル | 概要 |
|---|---|
| `premise-pre-verification` | chat Claude が応答内に未確認前提 (numeric / structural / semantic / channel / improvement premise の 5 系統) を embed することを構… |
| `structural-weakness-typology` | chat Claude が発火する構造的弱点 12 類型を一元的に参照する類型カタログ skill。 |
| `step-by-step-strict-execution` | chat Claude が handoff MD / Worker directive / multi-step task 等で複数 step を literal 列挙した局面で、1 step ずつ literal 実行… |
| `verbatim-quote-diff-interpretation-discipline` | | ユーザー が前 turn の chat Claude 応答を verbatim quote 形式で再掲しつつ一部に差分 (diff) を含めて返してきた局面で、その diff signal が「承認 + 部分修正」「… |
| `jikai-reflection` | | 日々の自戒と感謝のリフレクションを促すスキル。 |
| `feedback-loop` | Slack #project-feedback（Claude Code Loop サンドボックス）の巡回トリアージを1語で発火する。 |
| `notion-io-discipline` | | Chat Claude が Notion connector 経由で書き込み系操作（create / update）を行う際の、 保存先判定・命名規約・更新規律を強制する規律スキル。 |
| `plan-first-gate` | | 「最短でゴールを組み立てて」型の曖昧指示による誤走・手戻りを防ぐ実行前ゲート。 |
| `memory-discipline` | | userMemories (memory_user_edits tool) への entry 追加・削除・編集・整理時の判定規律スキル。 |

いずれも本リポジトリでは `skills/` 配下に統一して配置しています。上表の「出自」は、元の運用環境で
エージェント側（`skills/`）に置いていたか、チャット側（`chat-only/`）に置いていたかの区別です。

## 公開にあたっての処理

公開前に、案件コード・顧客名・担当者名・利用者名・絶対パスを機械的に置換しています
（それぞれ `〈案件〉` `〈顧客〉` `〈担当者〉` `ユーザー` `~` に置換）。
置換の痕跡が文意を損ねている箇所がありうるため、実運用に取り込む際は各スキルの記述を一読してください。

`skills/eli5-visual-explainer-v1` は第三者の成果物を土台とする派生物です。帰属は `NOTICE` および
当該ディレクトリ内の記述を参照してください。

## 免責

本スキル集は特定の業務・組織での運用経験から抽出したものであり、あらゆる文脈での有効性を保証するものでは
ありません。Apache License 2.0 の定めるとおり、無保証（AS IS）で提供されます。利用によって生じた結果に
ついて、著作権者は責任を負いません。
