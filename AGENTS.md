# AGENTS.md

## 项目定位

本目录用于沉淀“事理图谱”方案、原型代码与后续实现说明。设计需要结合已有课程系统资料，尤其是 `/Users/yukii/Desktop/Kimi_Agent_AI Scratch功能升级` 中的项目库、知识点库、图谱、项目插件和教案生成链路。

核心目标：

- 以系统中 100+ 项目为底座，形成可查询、可解释、可生成、可审核、可入库的事理图谱。
- 支撑“一句话备课”和“项目生成”：教师输入一个教学思路后，系统能判断它适合插入哪个年龄层、哪个项目阶段、哪些前后知识点之间，并生成可拔插项目包草案。
- 让新生成项目通过项目插件机制审核，审核通过后进入项目库、RAG 知识库和图谱。

## 关键资料源

优先读取这些本地文件，不要凭空编造项目数量和字段：

- `/Users/yukii/Desktop/Kimi_Agent_AI Scratch功能升级/data/vsle_growth_map.db`
  - 当前运行态数据库。
  - 已观测到：`projects` 非废弃项目 145 个，`knowledge_points` 324 个，`graph_edges` 2889 条。
  - 主要关系包括 `supports_project`、`belongs_to_competency`、`suitable_for_age_band`、`applied_in_competition`、`requires_hardware`、`produces_deliverable`、`recommended_next`、`successor_of`、`prerequisite_of`。
- `/Users/yukii/Desktop/Kimi_Agent_AI Scratch功能升级/data/project_plugins/wsl_160_projects.json`
  - 项目插件池源文件，当前 `project_count=136`。
  - 分布：L1 12、L2 40、L3 32、L4 28、L5 24。
- `/Users/yukii/Desktop/Kimi_Agent_AI Scratch功能升级/唯思乐项目反向设计整合报告.md`
  - 反向设计与知识点覆盖总报告。
  - 包含 46 精选项目、92 替代项目、125 编号知识点、考试/竞赛映射。
- `/Users/yukii/Desktop/Kimi_Agent_AI Scratch功能升级/唯思乐五层课程项目制设计.md`
  - 五层项目制课程整体设计。
- `/Users/yukii/Desktop/Kimi_Agent_AI Scratch功能升级/sections/sec09_oneline_project.md`
  - “一句话项目设计”现有 PRD。
  - 尤其注意防认知卸载、解释门、只生成骨架不直接生成代码等边界。
- `/Users/yukii/Desktop/Kimi_Agent_AI Scratch功能升级/backend/app/models/graph.py`
  - 现有 `GraphEdge` 和 `CompetencyNode` 模型。
- `/Users/yukii/Desktop/Kimi_Agent_AI Scratch功能升级/backend/app/models/project.py`
  - 现有 `Project` 字段，包含项目分层、知识点、竞赛、教案、AI 边界和插件状态。
- `/Users/yukii/Desktop/Kimi_Agent_AI Scratch功能升级/backend/app/models/project_plugin.py`
  - 项目包、版本、校验、RAG 索引和审计日志模型。
- `/Users/yukii/Desktop/Kimi_Agent_AI Scratch功能升级/backend/app/services/project_plugin_service.py`
  - 项目插件机制的实际约束。
- `/Users/yukii/Desktop/Kimi_Agent_AI Scratch功能升级/backend/app/services/project_recommendation_engine.py`
  - 当前项目推荐逻辑，可作为事理图谱匹配的前置实现参考。

## 已确认的系统事实

- 当前数据库运行态项目数为 145 个非废弃项目，分布为 L1 13、L2 41、L3 37、L4 30、L5 24。
- 项目池 JSON 文件记录 136 个项目，适合作为插件池导入源。
- 项目插件包需要包含这些文件：
  - `project.json`
  - `curriculum.md`
  - `lesson_plan.json`
  - `knowledge_map.json`
  - `materials.json`
  - `assessment.json`
  - `ai_guardrails.json`
  - `zongping_map.json`
  - `competition_map.json`
  - `parent_view.md`
  - `teacher_notes.md`
  - `README.md`
- 项目包必填字段以 `project_plugin_service.REQUIRED_PROJECT_FIELDS` 为准。
- 项目审核至少会检查：结构完整、知识点可追溯、考级/竞赛映射、年龄难度匹配、AI 使用边界、防认知卸载、七维评价体系。
- 项目状态流转已经存在：`draft -> in_review -> approved -> active`，同时支持 `deprecated`、`archived`、`replaced` 和 rollback。
- 项目激活后会触发 RAG 索引，生成 parent、teacher、knowledge、recommendation、alignment 等 chunk。

## 术语约定

- “事理图谱”不是普通知识图谱。它需要表达：
  - 事：教师想法、项目任务、课堂事件、学习证据、审核事件。
  - 理：知识点前后关系、因果关系、阶段适配、难度边界、项目生成理由、审核理由。
- “插入阶段”不是只指年龄段，还包括：
  - 前置补齐
  - 同步承载
  - 延伸挑战
  - 复盘修复
  - 竞赛包装
  - 综合评价
- “项目可拔插机制”必须对应现有 ProjectPackage 生命周期与 ProjectSet/variant 机制。不要设计成无法落到现有模型的孤立概念。

## 写作与实现原则

- 文档优先使用中文，保留系统已有术语：L1-L5、ProjectSet、ProjectPackage、knowledge_map、ai_guardrails、RAG、解释门、防认知卸载、七维评价。
- 引用项目数量时区分：
  - 数据库运行态：145 个非废弃项目。
  - JSON 插件池：136 个项目。
  - 反向设计报告：46 精选 + 92 替代 = 138 项目池。
- 如果后续写代码，优先复用现有表和服务；新增表要说明为什么不能用 `graph_edges.edge_metadata` 承载。
- 不要绕过项目包审核流程直接把生成项目设为 active。
- L1 不直接推荐竞赛路径，只能作为前置能力和展示项目。
- AI 辅助比例除 L1 教师端演示外，应随学生层级升高逐步下降：
  - L1：0%，教师端辅助。
  - L2：不超过 50%。
  - L3：不超过 30%。
  - L4：不超过 20%。
  - L5：不超过 10%。
- 对“一句话备课/项目生成”，必须保留教师确认和教研审核，不允许全自动入库。

## 独立开发、回接主系统与服务器更新流程

后续开发先在当前目录 `/Users/yukii/Desktop/事理图谱` 落代码和测试，验证通过后再回接到 `/Users/yukii/Desktop/Kimi_Agent_AI Scratch功能升级`。不要一开始就直接改主系统，除非任务明确是“接回主系统”或“修主系统 bug”。

### 阶段 0：Git 前置检查

- 每次开始前先执行：
  - `git status --short`
  - `git remote -v`
  - `git branch --show-current`
- 当前已知事实：`/Users/yukii/Desktop/事理图谱` 已初始化为本地 Git 仓库，`origin` 指向 `https://github.com/lostmyukii/-1.git`；`/Users/yukii/Desktop/Kimi_Agent_AI Scratch功能升级` 已初始化 Git 仓库，`origin` 指向 `https://github.com/lostmyukii/Kimi_Agent_AI-Scratch.git`，首个提交为 `4677147 chore: add safe gitignore`。
- 因此当前目录和主系统目录每步 commit 后都应立即 `git push`；主系统业务代码回接前仍需要先完成正式代码基线入库或确认只提交增量文件的策略。
- 推荐初始化策略：
  - 当前目录建独立仓库，用于事理图谱方案、原型和迁移脚本。
  - 主系统目录单独建仓库或接回已有远程仓库，用于正式产品代码。
  - 两边都使用功能分支，禁止直接在未确认的主分支上开发。

### 阶段 1：当前目录独立开发

- 代码目录使用 `event_graph_dev/`，测试目录使用 `tests/`。
- 当前目录只做四类内容：
  - 方案文档和实施计划。
  - 事理图谱定位、插入位、项目草案生成的可运行原型。
  - 从主系统数据库/JSON 读取事实的只读适配器。
  - 将原型结果导出为主系统可接入补丁或项目包的脚本。
- 禁止在当前目录保存真实生产密钥、服务器 SSH 密钥、数据库密码或 `.env`。
- 每完成一个可验证小步，执行：
  - `python3 -m unittest discover -s tests -v`
  - `git add <changed-files>`
  - `git commit -m "<type>: <short summary>"`
  - `git push`
- 如果 `git push` 因认证、权限或远程分支冲突失败，立即停止推送动作，在任务记录中写明真实阻塞原因，不要继续假装已推送。当前目录首次提交为 `b164adb chore: initialize event graph workspace`，远程为 `origin/main`。

### 阶段 2：回接主系统

- 只有当前目录原型通过测试并形成明确接口后，才接回主系统。
- 回接目标优先顺序：
  - 后端模型/迁移：`backend/app/models/`
  - 后端服务：`backend/app/services/`
  - API：`backend/app/api/`
  - Schema：`backend/app/schemas/`
  - 测试：`backend/tests/`
  - 管理端或教师端 UI：按主系统现有 `app/`、`web/` 结构确定。
- 回接时先建主系统功能分支，再按任务拆分提交：
  - 数据模型和迁移一提交。
  - 图谱定位服务一提交。
  - 项目草案生成一提交。
  - API 一提交。
  - UI 一提交。
  - 文档和部署说明一提交。
- 每个提交后运行对应测试，再 `git push`。
- 主系统仍未配置 git remote 时，不允许进入“更新服务器”阶段。

### 阶段 3：更新服务器

服务器更新必须以“已推送的 Git 提交”为来源，不允许把本地未提交文件直接复制到服务器。

部署前置条件：

- 当前目录原型已通过测试。
- 主系统已完成回接并通过后端/前端测试。
- 主系统变更已 commit 并 push 到远程分支。
- 已确认服务器地址、部署目录、服务管理方式、数据库备份方式和回滚方式。

部署顺序：

1. 在服务器备份数据库和当前版本。
2. 服务器拉取指定分支或 tag。
3. 安装依赖或执行迁移。
4. 重启后端、前端或相关服务。
5. 运行健康检查和关键接口 smoke test。
6. 通过后打 release tag 并 push tag。
7. 如果健康检查失败，按备份和上一 tag 回滚。

### 阶段 4：每步 Git 推送规则

- 每个阶段都必须小步提交，不把大批无关变更塞进一个 commit。
- 推荐提交粒度：
  - `docs: add event graph development workflow`
  - `feat: add event graph baseline reader`
  - `test: cover insertion slot planner`
  - `feat: integrate event graph positioning api`
  - `deploy: document event graph rollout`
- 每个 commit 后都要 `git push`。如果没有远程，必须在最终说明中列出阻塞原因和需要用户提供的 remote URL。
- 严禁使用 `git reset --hard`、`git checkout --` 等破坏性命令清理用户改动。

## 常用检查命令

```bash
sqlite3 '/Users/yukii/Desktop/Kimi_Agent_AI Scratch功能升级/data/vsle_growth_map.db' \
  "select age_band, count(*) from projects where deprecated=0 group by age_band;"

jq '.project_count, (.projects|length)' \
  '/Users/yukii/Desktop/Kimi_Agent_AI Scratch功能升级/data/project_plugins/wsl_160_projects.json'

rg -n "project_plugins|GraphEdge|lesson_plan|knowledge_map|ai_guardrails|一句话" \
  '/Users/yukii/Desktop/Kimi_Agent_AI Scratch功能升级/backend' \
  '/Users/yukii/Desktop/Kimi_Agent_AI Scratch功能升级/sections'
```

## 本目录交付物

- `AGENTS.md`：本文件，给后续 agent 和工程师的工作约定。
- `事理图谱设计方案.md`：面向产品、教研和研发的完整设计方案。
- `事理图谱开发实施方案.md`：本目录落代码、回接主系统、更新服务器的实施计划。
- `主系统回接清单.md`：原型代码迁回主系统的文件映射、API 契约、测试矩阵和阻塞项。
- `event_graph_dev/`：当前目录的事理图谱原型代码。
  - `git_preflight.py`：只读检查主系统 Git/remote 状态和高风险误提交路径。
- `tests/`：当前目录原型代码的测试。
