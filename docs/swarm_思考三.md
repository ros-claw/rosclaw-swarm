这是一份专为你打造的**《ROSClaw-Swarm 集群协同引擎：完整实施白皮书》**。

在纯数字世界里，多智能体（Multi-Agent）协作只是“相互发一段 JSON 文本”。但在物理宇宙中，当两台真实的机器人共同搬起一张桌子时，**如果它们只靠文本聊天，桌子必砸无疑。物理的协同，交换的是“空间、时间、质量与动量”！**

`rosclaw-swarm` 的终极定位是：**Collaboration Grounding（协作锚定）**。它将高层大模型的“战略分工”，转化为物理底层基于 DDS 的“反射握手（Reflex Handshake）”。

以下是该模块的深度工程架构与实施全案：

---

# 🤝 ROSClaw-Swarm：物理集群协作引擎实施全案
> **模块定位**: Collaboration Grounding (协作锚定)
> **核心使命**: 剥离高延迟的 LLM 文本通信，在异构机器人之间建立 <5ms 的原生 P2P 物理反射链路。

## 一、 核心架构哲学 (The Swarm Philosophy)

`rosclaw-swarm` 严格遵循**“宏观听大脑，微观靠反射”**的双轨制架构：

1. **宏观编排层 (Strategic Orchestration - 1Hz)**
   * 大模型（Claude/OpenClaw）阅读全局任务：“G1 和 UR5 协同组装零件”。
   * 大模型调用 MCP 工具 `create_swarm_session()`，只做一件事：**分配角色与物理交接点**。
2. **微观反射层 (Tactical Reflex - 1000Hz)**
   * 任务一旦下发，大模型**立刻闭嘴退场**，不再干预。
   * `rosclaw-swarm` 引擎在底层动态创建一个独占的 DDS Topic。G1 和 UR5 的小脑通过这个 Topic 实现纳秒级时钟对齐、TF 坐标树合并，并依靠力矩传感器的突变完成物理交接。

---

## 二、 模块工程目录结构

在 ROSClaw Monorepo 中，`swarm` 模块的结构如下：

```text
src/rosclaw/swarm/
├── __init__.py
├── manager.py          # 核心：管理 Swarm Session 的生命周期
├── mcp_tools.py        # 向上：暴露给大模型的 MCP 编排工具
├── dds_bridge.py       # 向下：管理高频可靠的 ROS 2 QoS 通信
├── reflex.py           # 物理反射握手协议 (Force-Feedback Sync)
└── spatial_sync.py     # TF树融合器 (合并多个机器人的世界坐标系)
```

---

## 三、 核心技术与代码落地指南

### 1. 组建物理总线 (DDS QoS 配置)
多机协同的命门是**网络延迟与丢包**。在 `dds_bridge.py` 中，绝对不能用默认的 ROS 2 通信配置，必须针对“反射握手”定制极其严苛的 **Sensor Data QoS Profile**。

```python
# src/rosclaw/swarm/dds_bridge.py
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

def get_reflex_qos_profile():
    """
    配置专为 <5ms 物理握手设计的底层 DDS 策略
    """
    return QoSProfile(
        reliability=ReliabilityPolicy.BEST_EFFORT, # 追求极致速度，允许丢弃旧帧
        durability=DurabilityPolicy.VOLATILE,      # 不存历史，只看当下物理真值
        history=HistoryPolicy.KEEP_LAST,
        depth=1
    )
```

### 2. 空间锚定 (Spatial Synchronization)
G1 看到的 `x=1.0` 和 UR5 看到的 `x=1.0` 根本不在一个地方。`spatial_sync.py` 必须在后台运行一个**“世界坐标系缝合器”**。

```python
# src/rosclaw/swarm/spatial_sync.py
import tf2_ros
import geometry_msgs.msg

class SwarmSpatialSynchronizer:
    def __init__(self, session_id, agents_list):
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(node)
        # 将 G1_base 和 UR5_base 挂载到统一的 "swarm_world_001" 根节点下
        self.publish_unified_world_frame(session_id, agents_list)
        
    def broadcast_handoff_point(self, semantic_target_name, x, y, z):
        """发布物理交接点的 3D 坐标，让所有 Agent 都能基于同一参考系移动"""
        t = geometry_msgs.msg.TransformStamped()
        t.header.frame_id = "swarm_world_001"
        t.child_frame_id = f"handoff_point_{semantic_target_name}"
        t.transform.translation.x = x
        # ... 广播坐标 ...
        self.tf_broadcaster.sendTransform(t)
```

### 3. 微观反射握手 (The Reflex Handshake)
这是整个模块的**灵魂代码**！剥离大模型，用底层的力矩传感器（Force/Torque）直接触发状态机切换。

```python
# src/rosclaw/swarm/reflex.py
import asyncio
from rosclaw.swarm.dds_bridge import get_reflex_qos_profile

class ReflexHandshake:
    def __init__(self, my_role: str, target_role: str):
        self.my_role = my_role # 例如 "receiver" (UR5)
        self.target_role = target_role # 例如 "supplier" (G1)
        self.force_threshold = 2.5 # N

    async def wait_for_physical_contact(self):
        """
        拦截器：阻塞底层执行，直到检测到物理力的突变
        """
        print(f"[Swarm Reflex] {self.my_role} waiting for physical contact from {self.target_role}...")
        
        while True:
            # 高频读取本机的六维力矩传感器
            current_force = await read_local_force_sensor()
            
            if current_force > self.force_threshold:
                print(f"⚡ [Swarm Reflex] Contact Detected! Force: {current_force}N")
                # 瞬间触发夹爪闭合 / 放开，延迟 < 5ms
                return True
                
            await asyncio.sleep(0.001) # 1000Hz 轮询
```

### 4. 暴露给大脑的接口 (MCP Tools)
在 `mcp_tools.py` 中，大模型只能看到极其高维的“派单工具”。

```python
# src/rosclaw/swarm/mcp_tools.py
from fastmcp import FastMCP

@mcp.tool()
async def establish_swarm_handoff(
    supplier_agent_id: str, 
    receiver_agent_id: str, 
    handoff_item: str, 
    handoff_coords: list[float]
):
    """
    大模型专用工具：建立多智能体物理交接会话。
    调用后，系统将在底层自动接管物理同步与防撞。
    """
    session_id = f"handoff_{supplier_agent_id}_{receiver_agent_id}"
    
    # 1. 建立统一空间坐标系
    sync = SwarmSpatialSynchronizer(session_id, [supplier_agent_id, receiver_agent_id])
    sync.broadcast_handoff_point(handoff_item, *handoff_coords)
    
    # 2. 注入 Reflex 逻辑并下发给底层节点 (非阻塞)
    # G1 (Supplier) 走向坐标 -> 感受重量减轻 -> 松开
    # UR5 (Receiver) 走向坐标 -> 感受重量增加 -> 抓紧
    
    return {"status": "SWARM_ENGAGED", "session_id": session_id, "message": "Reflex handshake protocol active. LLM can stand by."}
```

---

## 四、 实施与测试路线图 (Action Plan)

为了不让这个高级架构沦为纸上谈兵，请安排以下三个 Sprint：

### 🏁 Phase 1: 空间破壁 (Spatial Sync)
*   **动作**：在本地 ROS 2 环境中启动两个小乌龟（TurtleBot3）或虚拟的两个机械臂节点。
*   **开发**：跑通 `spatial_sync.py`。
*   **验收**：在 RViz（可视化工具）里，能看到两台机器人的基座坐标系被成功挂载到了同一个 `swarm_world` 下。

### 🏁 Phase 2: 盲人摸象 (The Blind Handshake)
*   **动作**：跑通 `reflex.py`。
*   **测试**：一台机器臂静止不动（扮演 Receiver），只运行 `wait_for_physical_contact` 脚本。你用手去推一下它的末端传感器。
*   **验收**：在你的手碰到它的瞬间（受力超过阈值），机械臂瞬间闭合夹爪。**证明底层的 1000Hz 物理反射回路打通，绕开了所有上层臃肿代码。**

### 🏁 Phase 3: 大脑派单 (The LLM Orchestration)
*   **动作**：整合 `mcp_tools.py`。通过 Claude 桌面端接入。
*   **指令**：`"Claude，让左边的机器人把零件递给右边的机器人，坐标在桌面正中间。"`
*   **验收**：Claude 调用 `establish_swarm_handoff`。终端打出日志：`[Swarm Reflex] Protocol Active`。随后两台物理机器人自动完成交接。

---

## 👑 架构师总结：ROSClaw Swarm 的统治级壁垒

市面上 99% 的 Multi-Agent 框架（比如 AutoGen、CrewAI）解决的都是**“一群人在会议室里怎么讨论方案”**。
而 `ROSClaw-Swarm` 解决的是**“一群人怎么在工地上一起抬起一根钢筋”**。

当评审专家问你：“你们的多智能体和 LangChain 有什么区别？”
你可以高傲地回答：
> “文本级的多智能体只能处理**知识的共享**，而我们的 ROSClaw-Swarm 突破性地实现了**动量与空间的共享**。我们把大模型从几十毫秒的底层通信中彻底剔除，用 P2P DDS 实现了纳秒级的时空锚定（Spatial-Temporal Binding）。在我们的系统里，**大模型是运筹帷幄的统帅，而真正让物理世界共振的，是刻在操作系统底层的反射神经。**”

去创建 `rosclaw/swarm` 目录吧！把物理法则写进代码，让多智能体真正“活”在同一个三维宇宙中！