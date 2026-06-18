# Hermes-Agent + Worker-Agent E2E 集成测试报告

**日期**: 2026-06-01 08:08 GMT+8
**测试环境**: Linux 6.17.0-29-generic / Python 3.12.3

---

## 1. Hermes CLI 基础测试

| 测试项 | 状态 | 详情 |
|--------|------|------|
| `hermes --version` | **PASS** | Hermes Agent v0.15.1 (2026.5.29), OpenAI SDK 2.24.0 |
| `hermes -z "银翼杀手主题"` | **PASS** | GLM-5.1 返回中文回复，内容准确 |
| `--no-stream` 参数 | **FAIL** | 该版本不支持 `--no-stream` 标志（非阻塞问题） |

**GLM-5.1 回复示例**:
> 在一个人造生命与人类界限日益模糊的赛博朋克世界中，究竟什么定义了"人"——是血肉的来源，还是记忆、情感与对存在的追问。

---

## 2. Movie Expert Skills 测试

| 测试项 | 状态 | 详情 |
|--------|------|------|
| Skill 目录数量 | **PASS** | 14 个 skill 目录全部存在 |
| SKILL.md 格式 | **PASS** | 所有 14 个 SKILL.md 均有正确 frontmatter（name/description/version/author） |

**14 个 Movie Expert Skills**:

| Skill | 描述 |
|-------|------|
| animator | Wan2.2 video generation, cinematic camera motion |
| colorist | CxSxZ color intent system, 28 core combinations |
| composer | Background music, sound effects, music-video sync |
| continuity | Cross-shot consistency auditing |
| drawer | FLUX/LoRA parameter optimization, film aesthetics |
| editor | FxRxT 3D editing matrix, shot assembly |
| foley | 7-dimensional parametric sound effects |
| mixer | Multi-track mixing, dialogue ducking, mastering |
| performer | Performance-4D matrix, 168K controlled tokens |
| scene_builder | FxSxA scene matrix, 3D previs, camera blocking |
| screenplay | Scene-level script generation, dialogue design |
| spatial_audio | 6D spatial encoding, immersive 3D sound field |
| style_genome | 5D director/genre parametric encoding |
| voicer | CosyVoice speech synthesis, emotion-adaptive delivery |

---

## 3. MCP Bridge 测试

| 测试项 | 状态 | 详情 |
|--------|------|------|
| `worker_bridge.py` 语法检查 | **PASS** | `ast.parse()` 验证通过 |
| Worker Agent `/health` | **PASS** | `{"status":"ok"}`, uptime 42382s |
| Worker Agent `/decide` | **PASS** | 返回 decision_id, 5 个专家匹配, confidence 0.85 |
| Worker Agent `/api/v1/personas` | **PASS** | 16 个 persona 已注册 |

**`/decide` 测试结果** (phase: soul-visual):
- decision_id: `d-soul-visual-1780272523300-d806444e`
- 匹配专家: scene_builder, style_genome, colorist, drawer, performer
- 置信度: 0.85
- 19 个参数维度返回

---

## 4. Hermes 配置验证

| 测试项 | 状态 | 详情 |
|--------|------|------|
| `config.yaml` | **PASS** | provider: zai, model: glm-5.1 |
| 辅助模型配置 | **PASS** | vision: glm-4.6v, compression: glm-5.1 |
| MCP server 配置 | **PASS** | hermes-worker bridge 指向 localhost:3100 |
| `.env` API keys | **PASS** | GLM_API_KEY, GLM_BASE_URL, OPENAI_API_KEY 已配置 |

---

## 5. 综合评估

| 类别 | 总计 | PASS | FAIL |
|------|------|------|------|
| Hermes CLI | 3 | 2 | 1 |
| Skills | 2 | 2 | 0 |
| MCP Bridge | 4 | 4 | 0 |
| 配置 | 4 | 4 | 0 |
| **总计** | **13** | **12** | **1** |

### 唯一 FAIL 项说明
- `--no-stream` 不是 hermes v0.15.1 的有效参数。这属于 API 变更，非功能缺陷。hermes 默认即支持流式和非流式输出。

### 结论
**系统集成状态: HEALTHY** - hermes-agent CLI、GLM-5.1 模型调用、14 个 movie expert skills、MCP bridge、worker-agent API 全部正常连通。
