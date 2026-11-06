---
name: skill-directory
description: 使用时机：接到任务不确定该用它哪些技能、或用户点名"盘一下技能/按目录来"时使用：扫描 .agents/skills 全池 frontmatter 描述，产出 ≤10 个候选技能与加载顺序；本工作区 114+ 技能、目录直灌容易落灰，用本技能做首轮索引官。排除：任务已明确点名技能、或需要领域专家子代理时（expert 路由走 chinasim-expert-routing）；论文科研主线走 sci-paper-writing；不索引 skills/ 之外的普通 docs。
metadata:
  version: 0.1.0
  pool_size: 114（2026-11-06，以 ls 当下为准）
  audit_tool: ~/mydsh/bin/dsh-skill-audit.sh（零调用遥测，M18）
---

# 技能目录索引官（skill-directory）

## 为什么需要你

工作区技能池 114+（第三方库集成约 60 / codearts 16 / chinasim 14 / 流程方法约 15 / qt6 2 / sci 3），目录消息把全部条目每轮注入上下文，但历史遥测显示调用率几乎为零（175/177 个名字零调用，2026-11-06 audit）。模型是唯一的匹配器——所以本技能的作用是：**把"匹配"变成看得见的一轮显式检索**，而不是靠模型扫一遍 2.5 万字符的目录。

## 三步索引程序

1. **盘池**（每次必做，防名单过期）：
   ```bash
   ls /home/wsc/wsc/ChinaSimStdio/.agents/skills/
   ```
2. **抽取触发面**：对候选名（按任务词初筛 ≤20 个）grep 其 `SKILL.md` frontmatter 的 description 首两行：
   ```bash
   grep -m2 "^description:" <name>/SKILL.md
   ```
3. **打分排序**（三条硬规则，输出前自检）：
   - 交叠分：任务关键词与 description 出现 ≥2 个实词 ⇒ 加 2 分；出现技能名本体词条 ⇒ 加 3 分。
   - 家族优先：任务落在本目录"家族"里（如"网格"/"求解器"/"评审"，见下地图），同分情况下家族多奖最佳。
   - 试错成本：库集成类技能（*-library）正文大，首轮最多全量加载 2 个；其余只列名不加载（渐进披露）。

## 家族地图（ Radar 以 2026-11-06 盘点为准，新技能入池先补此行）

| 家族 | 前缀/代表 | 触发词例 |
|---|---|---|
| 第三方库集成（≈60） | `arpack-library`、`dealii-library`、`mumps-library`、`vtk-library`…（配构建/调用于 ChinaSimStdio bin/third_party 下） | 库名、数值算法、链接/构建错误 |
| 华为云 CodeArts（16） | `codearts-bugfix`、`codearts-sdd`、`codearts-static-root-cause`… | 华为云、CodeArts、码道、工单/缺陷/规格 |
| 工程内部（14） | `chinasim-3d-expert`、`chinasim-motor-tdd`、`chinasim-ui-design`、`chinasim-verification`… | 电机、UI、验收、TDD、本工程流程 |
| 流程方法（≈15） | `writing-plans`、`executing-plans`、`systematic-debugging`、`dispatching-parallel-agents`、`verification-before-completion`、`test-driven-development`… | 计划/调试/并行/验收行为动词 |
| 论文科研（3） | `sci-paper-writing`、`sci-paper-search`、`sci-journal-sosym` | SCI、期刊、审稿、文献检索 |
| 图形 UI（2） | `qt6-library`、`qt6-ui-development` | Qt、界面 |

（精确数字每以 `ls` 现盘为准；本文只负责"形"，不负责"值"。）

## 输出契约

最终答复必须是一张 ≤10 行表：

```
| 序 | 技能名 | 交叠点（引用其 desc 原词） | 加载动作（正文全载/留名待用） |
```

并显式写一句收尾：**本轮只全量加载 top1–top2；其余候选名是否需要，任务推进到某一步再定**（这半句是防目录再次被整段吞进上下文的护栏）。

## 排除项（硬边界）

- 不与 `chinasim-expert-routing` 抢活：那是"专家→子代理"的路由（28 方向，末端用 subagent 派发）；本技能只索引"技能正文是否值得加载"。
- 不索引 `docs/`、普通 README、非 SKILL.md 的文件。
- 论文主线（sci-*）自管流程，除非用户请求盘点，否则不重复索引。

## 维护

- 新技能入池：在本文件家族地图补一行（家族/前缀/触发词例）。
- 遥测防复发：`bash ~/mydsh/bin/dsh-skill-audit.sh`（零调用榜单会说明哪些家族从未被真实调用——按分数决定是否下池或改写 description）。
- 描述卫生：每个 SKILL.md 的 description 保持"信号词前置 + 包含一个排除句"；200–480 字符之间（目录条目截断宽限 500）。
