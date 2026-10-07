# V0.1 design and audit contract

## Purpose

未知の専門世界を、拒絶しにくい入口から本人の新しい「定規」へ変換し、生活で起きた価値を本人の統制下で学習可能にする。

## Non-goals

- VINTAGE ALARM / watchdiary のデータを所有しない。
- 好みの高精度な予測、滞在時間、購入、探索量を最大化しない。
- QOL総合点、依存を促すstreak、無限フィードを作らない。
- AI推定を本人の確定事実として保存しない。
- V0.1で推薦モデル、ベクトルDB、別個のイベントDBを作らない。

## Canonical model

1. `AI_PROPOSED`: AIが Seed / 単一Hook / Ruler / 期待Impactを候補化する。
2. `USER_CONFIRMED`: 本人が入口と潜る意思を確認する。
3. `OBSERVED`: 実際のExperienceと実測Impactを記録する。

状態は逆戻りも飛び越しもしない。修正が必要ならエントリを編集して履歴を曖昧にせず、新しい提案として残す。

## Learning guard

次回選択への正の信号として利用できるのは、以下をすべて満たすエントリだけ。

- `OBSERVED`
- JOYがある（MUSTの有無とは独立）
- unexpected + relevant + bridge が成立
- 少なくとも1つの observed impact がある

MUSTだけ、AI提案だけ、期待値だけ、珍しいだけの候補は学習対象外。これにより強迫的な穴埋めと過剰特化を成功として強化しない。

## Impact

7軸は値 `LOW / MEDIUM / HIGH` または未記録。足し合わせず、平均せず、ランキング用の単一値へ変換しない。

| Axis | Meaning |
|---|---|
| RICHNESS | 視点・世界の見え方が増えた |
| FEEL | 楽しい、嬉しい、美的・物欲的満足 |
| EASE | 楽になった |
| GROW | 理解、能力感、自己効力 |
| CONNECT | 他者の喜び、会話、関係 |
| CREATE | 仕事、制作、研究への転用 |
| TRANSFER | 別領域で定規が自発的に発火 |

## Storage

単一JSONドキュメントを正本とする。安全な一時ファイル置換で書き込み、各変更に時刻を残す。別DBやキャッシュはV0.1の範囲外。

