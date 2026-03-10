# 手写 + 语音时间轴匹配功能规划（Web Demo -> Android 原生迁移）

## 1. 需求理解

### 1.1 目标本质
构建一个“过程可记录、提交看结果”的时空关联系统：
- 输入期：用户手写 + 语音并行发生，完整记录事件流（含被擦除轨迹）。
- 提交期：仅基于“提交时仍保留的笔迹”进行聚类与匹配。
- 输出期：生成带时间戳标注图；可选送入 AI 生成摘要/说明。

### 1.2 关键难点
1. **手写对象化**：point/stroke 是底层事件，业务识别单元应是 cluster/object。
2. **跨模态匹配**：不是一对一，而是“语音片段 ↔ 手写对象”的多对多评分匹配。
3. **可迁移性**：Web 仅做验证与调参，核心算法与配置模型需可迁移到 Android 原生。
4. **擦除影响建模**：最终保留态与过程事件要并存，支持后续高级回溯与优化。

---

## 2. 总体方案结论

### 2.1 三层架构（建议）
- **交互与可视化层（Web/Android UI）**
  - 负责采集输入、展示画布、时间轴、调参面板、输出预览。
- **领域逻辑层（可复用核心）**
  - 负责 retained 计算、聚类、匹配、标签落点、评分解释。
  - 应做成平台无关模块（TypeScript Core + 可移植算法说明/测试集）。
- **服务与任务层（后端）**
  - 负责转写服务接入、AI 总结、版本化配置、结果持久化。

### 2.2 结论摘要
- Web Demo 用于**验证流程 + 调参 + 可视化解释**。
- Android 端未来重点迁移：**输入采集、渲染、云端协同、性能优化**。
- 算法与配置优先独立：**统一数据契约 + 纯函数算法 + 配置驱动**。

### 2.3 当前已确认的业务约束（根据评审意见）
- 语音转写：走**云端 ASR（Qwen ASR 接口）**。
- 画布形态：支持**多页面/多画布**。
- 擦除语义：被擦除内容可视为“未写过”，V1 不做 stroke 子段切分。
- 时间戳展示：核心要求是**与录音时间可对齐**，允许绝对/相对双格式内部并存。
- Cluster 对应时间：每个 cluster 最终输出**一个时间范围**。
- AI 输出：聚焦**摘要**。
- 部署形态：匹配与标注可放云端，不要求离线。
- 账号/历史：先做**轻量日志与会话记录**。

---

## 3. 推荐技术栈及原因

## 3.1 备选对比

### Vue
- 优点：上手快、模板直观、配置面板开发效率高。
- 风险：若团队已有 React 资产，跨团队复用成本稍高。

### React（推荐）
- 优点：
  - 生态成熟，调试组件和状态管理工具完善，适合做“实验台/参数台”。
  - 对 Canvas/WebAudio/WebWorker 集成成熟。
  - 与 RN/跨平台技术经验迁移更顺畅（即便最终安卓原生，也利于原型验证）。
- 风险：若不约束，状态复杂度易膨胀。

### Flutter Web
- 优点：绘制与跨端一致性好。
- 风险：
  - Web 调试与生态（音频、浏览器能力细节）相对前端主流栈弱一些。
  - 对“算法调参台 + 开发者可视化”并非最省力路径。

### 纯 Canvas 架构
- 适合底层绘制引擎，但不建议“纯 Canvas + 手写 DOM 框架”。
- 推荐：**Canvas 负责绘制，React 负责状态与工具面板**。

### 前后端分离 or 一体化
- 推荐：**前后端分离（轻量）**。
  - Web Demo 前端直连 mock/本地算法，必要时调用后端 API。
  - 后端负责转写、AI、持久化。

## 3.2 推荐组合（Web Demo）
- 前端：`React + TypeScript + Vite`
- 绘制：`HTML Canvas 2D`（必要时 OffscreenCanvas/WebWorker）
- 状态：`Zustand`（轻量）+ `immer`
- 可视化：自绘时间轴 + 调试图层（bbox/cluster/label）
- 后端：`FastAPI` 或 `Node (Nest/Express)` 二选一，提供转写与AI编排
- 契约：`JSON Schema / OpenAPI`

---

## 4. 前后端职责划分

## 4.1 前端负责
1. 输入采集：笔迹点流、擦除事件、音频录制状态。
2. 本地预处理：stroke 分段、实时渲染、参数调整。
3. 提交触发：将 session 数据 + config snapshot 送入处理流程。
4. 调试可视化：cluster 边界、匹配连线、评分明细。
5. 输出展示：原图、标注图、AI结果（如有）。

## 4.2 后端负责
1. 语音处理：ASR 接入、时间戳对齐、分段标准化。
2. 任务编排：异步处理、结果存储、回放。
3. AI 调用：prompt 模板管理、模型调用、结果结构化。
4. 配置治理：默认配置、版本管理、实验组管理。

## 4.3 前端可暴露调参项
- 聚类阈值（时间/空间）
- 匹配权重
- 标签显示样式（字体/颜色/位置策略）
- 时间格式（绝对/相对）
- 是否显示调试图层

## 4.4 应收口于后端/核心层
- 转写后处理规则
- 匹配评分主逻辑（防止多端漂移）
- AI prompt 模板生产配置（避免前端泄漏和失控）
- 配置版本审计

## 4.5 安卓可复用策略
- 复用：数据结构、配置协议、聚类/匹配核心逻辑、测试样例。
- 重写：输入采集层、渲染层、设备能力适配（墨水屏刷新策略）。

---

## 5. 数据结构设计

> 以下为建议字段（V1），统一使用毫秒时间戳 `ts_ms`，坐标为画布归一化 + 像素双轨。

## 5.1 基础结构

### Point
```json
{
  "point_id": "p_001",
  "stroke_id": "s_001",
  "x": 120.5,
  "y": 300.2,
  "nx": 0.32,
  "ny": 0.44,
  "pressure": 0.61,
  "ts_ms": 1710000123456,
  "tool": "pen"
}
```

### Stroke
```json
{
  "stroke_id": "s_001",
  "page_id": "page_1",
  "canvas_id": "canvas_A",
  "points": ["p_001", "p_002"],
  "start_ts_ms": 1710000123000,
  "end_ts_ms": 1710000124200,
  "bbox": {"x": 100, "y": 280, "w": 80, "h": 60},
  "style": {"color": "#000", "width": 2.0},
  "created_by": "user",
  "status": "active"
}
```

### EraseEvent
```json
{
  "erase_id": "e_001",
  "page_id": "page_1",
  "mode": "path",
  "path_points": ["..."],
  "radius": 12,
  "ts_ms": 1710000125000,
  "affected_stroke_ids": ["s_001"]
}
```

### RetainedStroke
```json
{
  "stroke_id": "s_001",
  "retained": false,
  "retained_ratio": 0.0,
  "invalidated_by": ["e_001"],
  "erase_policy": "hard_delete",
  "state_at_submit_ts_ms": 1710000130000
}
```

## 5.2 语音与文本结构

### AudioSegment
```json
{
  "audio_seg_id": "a_001",
  "session_id": "sess_001",
  "start_offset_ms": 0,
  "end_offset_ms": 8000,
  "start_ts_ms": 1710000120000,
  "end_ts_ms": 1710000128000,
  "audio_uri": "blob://...",
  "speaker": "user",
  "confidence": 0.92
}
```

### TranscriptSegment
```json
{
  "transcript_seg_id": "t_001",
  "audio_seg_id": "a_001",
  "asr_provider": "qwen_asr",
  "text": "这里画一个三角形",
  "tokens": [
    {"token": "这里", "start_ts_ms": 1710000120100, "end_ts_ms": 1710000120300}
  ],
  "start_ts_ms": 1710000120000,
  "end_ts_ms": 1710000122000,
  "asr_confidence": 0.88
}
```

## 5.3 聚类与匹配结构

### HandwritingCluster/Object
```json
{
  "cluster_id": "c_001",
  "page_id": "page_1",
  "canvas_id": "canvas_A",
  "member_stroke_ids": ["s_010", "s_011"],
  "bbox": {"x": 200, "y": 120, "w": 140, "h": 100},
  "centroid": {"x": 260, "y": 170},
  "start_ts_ms": 1710000121000,
  "end_ts_ms": 1710000129000,
  "last_touch_ts_ms": 1710000135000,
  "continuity_score": 0.73,
  "spatial_density": 0.61,
  "retained_only": true
}
```

### ClusterTimeRange
```json
{
  "cluster_id": "c_001",
  "time_start_offset_ms": 23000,
  "time_end_offset_ms": 27000,
  "source_transcript_seg_ids": ["t_003", "t_004"],
  "aggregation": "union_then_compact"
}
```

### MatchResult
```json
{
  "match_id": "m_001",
  "cluster_id": "c_001",
  "transcript_seg_id": "t_003",
  "time_score": 0.82,
  "space_score": 0.30,
  "semantic_score": 0.55,
  "final_score": 0.69,
  "rank": 1,
  "explain": {
    "time_gap_ms": 2300,
    "rules_triggered": ["time_window_hit", "late_spatial_merge"]
  }
}
```

### TimestampLabel/Anchor
```json
{
  "label_id": "l_001",
  "cluster_id": "c_001",
  "text": "00:23-00:27",
  "anchor": {"x": 345, "y": 205},
  "placement": "bbox_top_right",
  "avoid_overlap_shift": {"dx": 8, "dy": -12},
  "style": {"font_size": 14, "color": "#D22", "bg": "#FFF"},
  "source_match_ids": ["m_001", "m_004"]
}
```

---

## 6. 算法设计（V1 可落地版）

## 6.1 第一层：手写对象聚类

### Step A: 点 -> Stroke
- 输入设备事件按“落笔/抬笔”形成 stroke。
- 对点序列做轻量平滑与降采样（保留时间）。

### Step B: Stroke -> 初始 Cluster（空间主导）
- 构图：每个 retained stroke 为节点。
- 若满足任一条件则连边：
  1. bbox 最短距离 < `d_bbox`
  2. 最近点距离 < `d_point`
  3. 轨迹相交/包围关系
- 用并查集/连通域得初始 cluster。

### Step C: 时间连续性修正（时空联合）
- 计算 cluster 时间窗 `[start, end]`。
- 若两个 cluster 空间接近且时间间隔 < `t_merge`，合并。
- 特殊规则：`late_spatial_merge`
  - 即使时间间隔大于 `t_merge`，若新增 stroke 落在既有 cluster bbox 扩张区内且形态相似，允许归并（权重惩罚）。

### Step D: 输出 retained-only 对象
- 只保留提交时 retained stroke 参与对象输出。
- 但保留被擦除历史用于解释与后续学习。
- 按当前范围，擦除视为 hard delete：被擦除笔迹不参与后续 cluster，不做子段重建。

## 6.2 第二层：语音与手写对象匹配

### 候选召回
- 对每个 transcript segment，召回时间窗内 cluster（`[seg_start - pre_roll, seg_end + post_roll]`）。

### 打分
`final = w_t * time_score + w_s * space_score + w_c * continuity_score + w_sem * semantic_score`

- `time_score`：基于 segment 与 cluster 时间重叠/最近距离。
- `space_score`：V1 可选弱化（无语义定位时设低权重），若有“指示词+局部序号”可增强。
- `continuity_score`：前后 segment 已归属同 cluster 时加分（HMM-like 平滑）。
- `semantic_score`：V1 可先启发式关键词（“左边/上面/这里”）或置 0。

### 决策
- Top-1 且 `final_score > min_accept`：建立主匹配。
- 否则标记为 `unassigned` 或 `multi-candidate`，供人工调参查看。
- 每个 cluster 最终聚合为一个 `ClusterTimeRange`（单时间范围输出）。

## 6.3 第三层：时间戳落点策略

1. 候选锚点序列：
   - `bbox_top_right` -> `bbox_bottom_right` -> `bbox_top_left` -> `centroid_offset`
2. 可读性评分：
   - 与笔迹重叠面积最小
   - 与已有标签碰撞最小
   - 不超出画布边界
3. 冲突处理：
   - 局部搜索偏移 `(dx, dy)`
   - 仍冲突则缩短文本（仅起始时间）或合并同 cluster 多段时间
4. 墨水屏友好：
   - 高对比、低填充、少透明、避免频繁动画。
5. 时间制式：
   - 内部保存 `offset_ms`（相对录音）+ `ts_ms`（绝对）双轨，展示默认以“可与录音对齐”为准。

---

## 7. 可配置项清单

## 7.1 算法配置

### 前端可调（调参台）
- `cluster.d_bbox`, `cluster.d_point`
- `cluster.t_merge`, `cluster.late_spatial_merge_ratio`
- `match.pre_roll_ms`, `match.post_roll_ms`
- `match.weights.{w_t,w_s,w_c,w_sem}`
- `match.min_accept`

### 后端/核心控制
- 语音分段策略（VAD/ASR后处理，Qwen ASR接口）
- 语义规则词典与版本
- 默认参数版本与灰度策略
- 云端开关与路由配置（不开离线模式）

## 7.2 展示配置

### 前端可调
- 标签字体大小、颜色、线宽、背景色
- 时间格式（`HH:mm:ss` / `+23.4s`）
- 标签位置策略优先级
- 是否显示调试层（bbox、连线、分数）

### 固化或低频调整
- 导出分辨率、压缩质量
- 墨水屏模式（黑白阈值、抖动）

## 7.3 AI 配置

### 后端配置优先
- prompt 模板、模型路由、温度、输出 schema
- 可选任务：默认摘要（V1 仅开放摘要）

### 前端仅暴露有限项
- 输出风格预设（严谨/简要/教学）
- 是否启用 AI 结果

---

## 8. 页面结构建议（Web Demo）

1. **左侧主画布区（60%）**
   - 手写、擦除、重写
   - 页面切换（Page 1/2/...）与缩略图
   - 图层切换：原笔迹/聚类/bbox/标签
2. **右侧参数面板（25%）**
   - 算法参数折叠分组
   - 一键恢复默认、保存参数快照
3. **底部时间轴区（15%）**
   - 录音状态、语音段、转写文本
   - 点击文本高亮对应 cluster
4. **顶部操作栏**
   - 开始录音、停止、提交、导出
5. **结果区（弹层或右侧Tab）**
   - 原图 / 时间戳图 / AI 输出
6. **调试面板**
   - 本次提交ID、处理耗时、匹配 Top-K、未匹配列表

---

## 9. MVP 开发阶段计划

## 阶段1：输入与回放基础（必须）
- 目标：可靠采集“写/擦/重写 + 录音时间线”。
- 范围：Canvas 输入、erase 事件、会话存储、回放。
- 交付：可导出 session JSON。
- 风险：不同输入设备事件精度差异。

## 阶段2：Retained 计算 + 聚类V1（必须）
- 目标：提交时生成 retained strokes 和 cluster。
- 范围：空间连通 + 时间修正 + late merge 规则。
- 交付：可视化 cluster、可调阈值。
- 风险：阈值在不同书写风格下泛化差。

## 阶段3：语音匹配 + 标签渲染（必须）
- 目标：将 transcript segment 与 cluster 建立可解释匹配。
- 范围：时间召回、加权打分、标签落点冲突处理。
- 交付：标注图导出，评分明细面板。
- 风险：ASR 分段质量影响匹配稳定性。

## 阶段4：AI 编排与评估闭环（建议）
- 目标：形成“图 + 文 + prompt -> 摘要”闭环。
- 范围：后端任务接口、摘要模板管理、结果结构化。
- 交付：一键生成摘要。
- 风险：Prompt 漂移与输出稳定性。

## 阶段5：安卓迁移预研（建议）
- 目标：验证墨水屏可用性与性能。
- 范围：输入延迟、局部刷新策略、云端接口稳定性。
- 交付：迁移清单与风险报告。
- 风险：Web 参数在 Android 上需要重标定。

## 阶段6：轻量日志与会话记录（建议）
- 目标：满足基础可追踪与问题回放。
- 范围：session 日志、提交结果索引、简单查询。
- 交付：可按 session_id 回看输入与输出。
- 风险：日志字段设计不当会影响后续统计扩展。

---

## 10. 风险与注意事项

1. **数据契约先行**：不要先写死 UI，再补数据结构。
2. **参数爆炸风险**：前端只暴露“高价值调参项”，其余交由配置版本管理。
3. **评估集缺失风险**：尽早建立小规模标注样本（手写对象-语音对应真值）。
4. **墨水屏约束**：减少动画与高频重绘，重点验证静态可读性和操作延迟。
5. **可解释性优先**：每个匹配结果需有评分构成与规则命中说明。
6. **保留历史但按提交输出**：同时满足“最终态业务需求”和“过程学习需求”。

---

## 已确认需求冻结项（用于直接开工）

1. ASR 使用云端 Qwen ASR 接口。
2. 支持多页面/多画布。
3. 擦除按 hard delete 处理，被擦除内容视为未写过。
4. 时间戳输出以“与录音对齐”为目标，内部可双轨存储（绝对 + 相对）。
5. 每个 cluster 输出一个聚合后的时间范围。
6. AI 输出先做摘要，不扩展教学说明类任务。
7. 不做离线匹配，核心处理放云端并可配置路由。
8. 安卓端技术栈暂不设限，优先选择实现成本低、稳定性高方案。
9. 做轻量日志与会话记录，支持回放排查。
10. 下一步先给“简化版 API 字段说明 + 前端状态切片”，不走完整 OpenAPI 大文档。
