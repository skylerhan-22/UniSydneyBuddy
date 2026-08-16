# Canonical schemas

这些 Schema 保存课程事实，不保存面向用户的最终文案。

- 原始英文名称放在 `*_original`。
- 翻译放在 `*_localized`，键为 BCP 47 语言代码，如 `zh-CN`。
- 所有关键事实通过 `evidence_ids` 指向 Evidence。
- `null` 表示资料尚未提供；不得由模型猜测。

