# Patch Proposal · auto-v43

- 目标文件: `src/judgment/judgment_engine.py`
- 描述: 给 judge 增加 diversity prompt 标记
- 理由: 增加 judge 多样性 + 语义反驳

## 变更说明

## 高层修改建议（mock/离线模式下不生成具体代码 diff）

- **目标**: 给 judge 增加 diversity prompt 标记
- **理由**: 增加 judge 多样性 + 语义反驳
- 请人工审查后手动实现，或切换到真实 LLM（provider=ollama/openai/dashscope）再跑一次以生成具体代码。

参考文献：
- [web (offline)] Dempster-Shafer evidence theory 与 Zadeh 悖论 — 经典 Dempster 组合规则在高冲突证据下会出现反直觉结论（Zadeh 悖论）。ParaJudge 当前用近似正交和应谨慎对待冲突情形。...  (https://en.wikipedia.org/wiki/Dempster%27s_rule_of_combination)
- [web (offline)] DS theory 用于多源融合 — DS 理论在辩论系统中融合多位 judge 评分时，冲突权重调整非常关键。...  (https://www.sciencedirect.com/)
- [web (offline)] Argumentation mining 中的反驳检测 — 现代论点-反驳关系检测一般采用句子嵌入（如 sentence-transformers），关键词重叠只是基线方法，通常相关度在 0.3~0.5 之间。...  (https://aclanthology.org/)

---
> 由 scripts.autodriver_agents.CodeEditor 自动生成
