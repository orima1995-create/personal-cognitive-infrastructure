# 沼外部脳 / Personal Cognitive Infrastructure V0.1

未知から「世界を見る定規」を1本だけ拾い、分かりやすい Hook で渡す。本人が自発的に潜った場合だけ深くし、後の実生活で生じた価値を観測して次回へ学習するための最小実装です。

これは推薦精度や知識量を最大化するシステムではありません。VINTAGE ALARM / watchdiary から独立した正本であり、それらは将来の利用側です。

## V0.1 の契約

- 1エントリにつき Hook は必ず1つ。
- 状態は `AI_PROPOSED → USER_CONFIRMED → OBSERVED` の一方向。
- AIの提案だけでは本人モデルへ昇格しない。
- Impact は `RICHNESS / FEEL / EASE / GROW / CONNECT / CREATE / TRANSFER` を別々に保持し、総合点を作らない。
- `expected_impact` と `observed_impact` を別々に保持する。
- `JOY` と `MUST` を別々に記録し、MUSTだけの反応を成功信号として学習しない。
- serendipity は `unexpected` と `relevant` の両方、および既知から未知への `bridge` を必要とする。
- 永続化先は1つのJSONファイルだけ。新しいDB、queue、profile storeは作らない。

## 使い方

Python 3.11+ だけで動き、実行時依存はありません。

```bash
python -m pci.cli --store data/pci.json init
python -m pci.cli --store data/pci.json propose \
  --seed "心理音響学" \
  --hook "同じ音量なのに、蚊の音だけうるさく感じるのはなぜ？" \
  --ruler "音の大きさをdBだけでなく、人間の知覚特性でも見る" \
  --bridge "時計のアラーム音から、人間の聴覚へ" \
  --unexpected --relevant --joy \
  --expected FEEL=HIGH --expected RICHNESS=MEDIUM
python -m pci.cli --store data/pci.json confirm <ID>
python -m pci.cli --store data/pci.json observe <ID> \
  --experience "別のアラーム音でも周波数を意識した" \
  --impact TRANSFER=HIGH --impact RICHNESS=MEDIUM
python -m pci.cli --store data/pci.json show <ID>
```

`propose` は候補を1件返します。候補一覧を大量生成するコマンドは意図的にありません。

## データ構造

単一ストアの各エントリは `Seed → Hook → Ruler → Experience → Impact` の最小閉ループです。`Experience` と実測 Impact は観測段階まで空です。`learnable` は保存値ではなく、本人確認・実観測・JOY・serendipity・実測Impactから毎回導出されます。

詳細は [docs/DESIGN.md](docs/DESIGN.md) を参照してください。

## テスト

```bash
python -m unittest discover -s tests -v
```

