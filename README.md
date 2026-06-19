# 客服对话结构化提取工具

## 项目概述

从客服对话中自动提取结构化信息，帮助客服主管进行周报统计与分析。对 25 条真实客服对话进行提取，覆盖商品质量、物流配送、退款退货、产品咨询等多种场景。

## Schema 设计思路

### 设计原则

以 **"客服主管做周报"** 为目标场景设计字段。主管最关心的是：**用户在问什么、问题解决了没、用户感觉如何、客服表现怎么样**。

### 字段说明

| 字段                    | 类型      | 取值范围                                             | 设计理由                             |
| ----------------------- | --------- | ---------------------------------------------------- | ------------------------------------ |
| `conversation_id`     | str       | 对话唯一 ID                                          | 标识每条记录                         |
| `channel`             | str       | 在线 / 电话                                          | 渠道分布统计                         |
| `agent`               | str       | 客服姓名                                             | 客服维度数据统计                     |
| `turn_count`          | int       | 对话轮数                                             | 工作量和复杂度评估                   |
| `user_issue_summary`  | str       | 一句话概括                                           | 快速浏览每条对话的核心诉求           |
| `issue_categories`    | list[str] | 9 个类别                                             | 多诉求场景支持；用于统计各类问题占比 |
| `resolution_status`   | str       | resolved / partially_resolved / unresolved / pending | 客服的核心 KPI — 解决率             |
| `resolution_action`   | str       | 具体措施描述                                         | 分析客服处理方式分布                 |
| `user_sentiment`      | str       | angry / negative / neutral / positive                | 用户满意度评估                       |
| `urgency_level`       | str       | high / medium / low                                  | 紧急事件标记和优先级排序             |
| `requires_follow_up`  | bool      | true / false                                         | 遗留任务追踪                         |
| `escalation_required` | bool      | true / false                                         | 转人工率监控                         |

### 问题类别体系

- **商品质量问题**：产品破损、功能故障、品质瑕疵
- **物流配送问题**：未收到包裹、配送延迟、地址变更、快递柜问题
- **退款/退货/换货**：退款进度、退货申请、部分退货、换货、退货运费
- **订单操作**：取消订单、改址
- **产品咨询**：功能咨询、成分咨询、库存查询、产品对比
- **优惠券/促销**：优惠券使用问题
- **账号安全**：异常登录、密码修改
- **投诉/建议**：投诉服务、提建议
- **其他**：无法归类的对话

## 任务拆解

1. **数据理解**：阅读 25 条对话，识别常见模式和边界情况
2. **Schema 设计**：基于业务场景设计提取字段体系
3. **提取实现**：使用 DeepSeek API 进行结构化提取，基于规则兜底
4. **准确性验证**：人工抽检 7 条，逐字段核对准确率
5. **文档编写**：README + 代码注释

## 边界情况处理策略

| 场景                   | 案例                        | 处理策略                                                               |
| ---------------------- | --------------------------- | ---------------------------------------------------------------------- |
| **多诉求**       | conv_06（退货+查快递）      | `issue_categories` 支持多标签，summary 用分号分隔多个诉求            |
| **转人工**       | conv_09, conv_16            | `escalation_required=true`，按转人工后最终结果标注 resolution_status |
| **话题切换**     | conv_06                     | 多轮语义连贯提取，LLM 自动捕捉完整上下文                               |
| **信息缺失**     | conv_10（用户没想好问什么） | resolution_status = unresolved，标记为低优先级                         |
| **用户主动放弃** | conv_12, conv_25            | resolution_status = unresolved，requires_follow_up = false             |
| **负面情绪**     | conv_05, conv_09, conv_25   | 准确标注 sentiment 等级，urgency 相应提高                              |
| **部分解决**     | conv_03                     | resolution_status = partially_resolved                                 |
| **建议/投诉**    | conv_23                     | 归入 投诉/建议 类别                                                    |
| **重复投诉**     | conv_20（连续两次质量问题） | 在 summary 中体现历史背景                                              |

## AI 工具使用

- **DeepSeek API**（deepseek-chat）：核心提取引擎，使用 JSON response format 确保结构化输出
- **Python httpx**：API 请求
- **python-dotenv**：环境变量管理
- 代码编写：使用 AI 辅助开发

## 项目结构

```
.
├── task.md                          # 任务说明
├── task2_conversations.json         # 25 条原始对话数据
├── task2_extract_example.md         # 提取示例
├── .env.example                     # API 配置示例
├── extraction/
│   ├── __init__.py
│   ├── schema.py                    # 数据模型定义
│   ├── extractor.py                 # LLM 提取器（含 fallback 规则）
│   └── validator.py                 # 人工抽检验证
├── run_extraction.py                # 主运行入口
├── output/
│   └── extraction_results.json      # 提取结果输出
└── README.md
```

## 运行方式

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY

# 2. 运行提取
conda activate 0108
python run_extraction.py
```

## 准确率

**请运行后填写：**

人工抽检 7 条 × 6 个关键字段 = 42 个检查点，各字段准确率如下：

| 字段                | 准确率 |
| ------------------- | ------ |
| issue_categories    | 100%   |
| resolution_status   | 71%    |
| user_sentiment      | 86%    |
| urgency_level       | 71%    |
| requires_follow_up  | 86%    |
| escalation_required | 86     |
| **整体**      | 85.7%  |
