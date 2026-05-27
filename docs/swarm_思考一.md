在最初的 ROSClaw 架构里，**Swarm 只是一个多机协同模块**。
但在 Grounding 哲学体系里，Swarm 实际上应该升级为：

> **Physical Intelligence 的社会层（Society Layer）**
>
> 单个 Agent 解决 Symbol Grounding。
>
> Swarm 解决 Collective Grounding。

这是 ROSClaw-Swarm 真正的战略价值。

---

# 一、重新定义 ROSClaw-Swarm

很多人理解的 Swarm：

```text
多机器人协同

G1
UR5
AGV

一起干活
```

这是工程层理解。

ROSClaw 应该提升到：

```text
Physical Intelligence Society Runtime
```

即：

```text
Agent
↓
Memory
↓
Skill
↓
Society
```

形成：

```text
Individual Intelligence
↓
Collective Intelligence
```

---

# 二、ROSClaw 生态中的位置

完整闭环：

```text
Physical World
        ↓
Practice
        ↓
Memory
        ↓
How
        ↓
Skill
        ↓
Agent Runtime
        ↓
Swarm Runtime
        ↓
Physical World
```

其中：

Practice：

```text
我经历了什么
```

Memory：

```text
我学到了什么
```

Skill：

```text
我会做什么
```

Swarm：

```text
谁最适合做什么
```

这其实是：

```text
Skill Routing
```

---

# 三、Swarm 核心职责

我建议拆成五大子系统：

```text
rosclaw-swarm

├── planner
├── scheduler
├── discovery
├── coordination
├── evolution
```

---

# 四、Swarm Planner

任务分解引擎

输入：

```text
帮老人拿药
```

Planner：

```text
任务树

Take Medicine
│
├── Locate Medicine
├── Navigate
├── Pick
└── Deliver
```

输出：

```python
TaskGraph
```

例如：

```python
class Task:
    id
    parent
    dependencies
    skill
```

最终形成：

```text
DAG
```

---

# 五、Role Assignment

角色分配引擎

例如：

环境：

```text
G1
UR5
Camera
Drone
```

能力：

```yaml
G1:
  locomotion
  manipulation

UR5:
  precision_pick

Drone:
  inspection

Camera:
  perception
```

来自：

```text
e-urdf-zoo
```

中的：

```yaml
capabilities.yaml
```

Swarm 自动生成：

```text
Locate
↓
Camera

Navigate
↓
G1

Pick
↓
UR5

Verify
↓
Drone
```

---

# 六、Capability Graph

这是最重要的基础设施之一。

新增：

```text
Capability Graph
```

SeekDB：

```text
Robot
↓
Capability
↓
Skill
↓
Experience
```

例如：

```text
UR5
 ↓
precision_pick
 ↓
plug_insert
 ↓
success_rate=92%
```

Swarm 调度依据：

不是：

```text
谁声明会
```

而是：

```text
谁历史成功率高
```

这是 Memory 和 Swarm 联动。

---

# 七、Agent Discovery

类似：

```text
Kubernetes Service Discovery
```

新增：

```python
AgentRegistry
```

注册：

```text
Robot
Agent
Skill
Sensor
Tool
```

例如：

```text
robot://g1
robot://ur5
agent://claude
agent://openclaw
sensor://zed
```

查询：

```python
find(
 capability="pick"
)
```

返回：

```python
[
 UR5,
 G1
]
```

---

# 八、Swarm Scheduler

这是 Swarm 大脑。

负责：

```text
资源调度
```

类似：

```text
Kubernetes Scheduler
```

但对象变成：

```text
机器人
传感器
Agent
GPU
```

---

调度指标：

```text
距离

电量

负载

经验

成功率

风险
```

综合评分：

```python
score =
 capability
 + success_rate
 + proximity
 - risk
```

选择最优执行者。

---

# 九、Coordination Runtime

真正执行层。

新增：

```text
DDS Reflex Handshake
```

理念来自：

人类协同搬桌子。

你不会说：

```text
我移动了3厘米
```

而是：

```text
通过力反馈
```

实时协调。

---

机器人：

```text
Robot A
Robot B
```

共享：

```text
Force

Pose

Velocity

Intent
```

频率：

```text
100Hz~1000Hz
```

底层：

```text
ROS2 DDS
```

---

# 十、Shared Intent Bus

比 DDS 更高层。

新增：

```text
Intent Layer
```

DDS：

```text
状态同步
```

Intent Bus：

```text
目标同步
```

例如：

```json
{
  "intent":"lift_table",
  "phase":"execute",
  "confidence":0.92
}
```

这样：

多个 Agent 可以共享：

```text
世界模型
```

而不是共享原始数据。

---

# 十一、Swarm Memory

很多项目忽略这一层。

实际上：

不仅个人有 Memory。

群体也有 Memory。

新增：

```text
Collective Memory
```

例如：

过去：

```text
搬桌子

G1 + UR5

成功
```

保存：

```text
Team Pattern
```

下一次：

```text
类似任务
```

直接复用。

---

形成：

```text
Experience
↓
Memory
↓
Team Skill
```

---

# 十二、Swarm Evolution

这是最有想象力的一层。

对应：

```text
rosclaw-darwin
```

评测：

不再评测：

```text
单机器人
```

而是：

```text
群体进化速度
```

例如：

Arena：

```text
100 个 Agent

1000 个任务
```

观察：

```text
协作拓扑

角色分工

知识传播速度

技能传播速度
```

形成：

```text
Swarm Genome
```

---

# 十三、ROSClaw-Swarm 与其它模块关系

```text
                    ROSClaw Runtime
                            │
 ┌──────────────────────────┼──────────────────────────┐
 │                          │                          │
 │                    Event Bus                        │
 │                          │                          │
 ▼                          ▼                          ▼

Practice ─────► Memory ─────► SeekDB ◄───── Darwin
                                │
                                │
                                ▼

                       Capability Graph
                                │
                                ▼

                       ROSClaw-Swarm
                                │
 ┌──────────────┬───────────────┬──────────────┐
 ▼              ▼               ▼              ▼

Planner     Scheduler     Discovery     Coordination
                                │
                                ▼

                      Agent Runtime
                                │
                                ▼

         G1 / UR5 / Drone / Camera / Human
```

---

# 十四、Sprint 实施路线（推荐）

### Sprint 1：Swarm Foundation

实现：

```text
Agent Registry
Capability Registry
```

成果：

```python
swarm.find("pick")
```

---

### Sprint 2：Task Graph

实现：

```text
Planner
Task DAG
```

成果：

```python
swarm.plan(goal)
```

---

### Sprint 3：Capability Graph

接入：

```text
SeekDB
Memory
```

成果：

```python
swarm.select_best_agent()
```

---

### Sprint 4：Coordination Runtime

实现：

```text
DDS Reflex
Intent Bus
```

成果：

```text
双机器人协作
```

---

### Sprint 5：Collective Memory

实现：

```text
Team Pattern
Team Skill
```

成果：

```text
团队经验复用
```

---

### Sprint 6：Swarm Darwin

实现：

```text
Arena
Evolution
Skill Diffusion
```

成果：

```text
群体智能进化评测
```

---

我认为，如果按照你上传文档中 **Grounding → Experience → Memory → Skill → Evolution** 的主线继续推演，那么 ROSClaw-Swarm 不应该被定义为“多机器人框架”。

更准确的定位应该是：

> **ROSClaw-Swarm = Physical Intelligence Society Runtime**
>
> 它负责将单个 Agent 的经验、技能和记忆，组织成一个能够自协作、自传播、自进化的物理智能社会。

这样它在整个 ROSClaw 版图中的层级会直接提升，与 Kubernetes 在云计算中的地位类似——不是一个模块，而是整个 Physical Intelligence Runtime 的社会组织层。
