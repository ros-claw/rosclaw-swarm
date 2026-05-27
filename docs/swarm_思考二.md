这份实施指导基于你提供的 ROSClaw 1.0 顶层设计架构与哲学思辨，旨在将 `rosclaw-swarm` 从宏观的概念转换为工程落地的技术方案。

在 ROSClaw 体系中，`rosclaw-swarm` 的核心使命是 **“协作锚定（Collaboration Grounding）”**。它存在的根本意义在于：**剥离虚无的大模型文本对话，在物理底层通过高频数据流实现多智能体的微秒级/毫秒级物理联合，解决多机协同在三维宇宙中的符号接地与运动对齐问题**。

---

## 🏗️ 一、 rosclaw-swarm 双层架构设计

为了同时兼顾大模型的“宏观决策能力”与底层控制的“高频实时性”，`rosclaw-swarm` 必须采用**双层解耦架构**：

```text
  [ Agent Runtime / 大模型 ] (1Hz 低频意图)
             ↓
+------------------------------------------+
| 1. 宏观控制面 (Macro Control Plane)       | -> 任务拆解、角色指派、拓扑发现
+------------------------------------------+
             ↓ (SwarmContext 契约)
+------------------------------------------+
| 2. 微观物理反射面 (Micro Reflex Plane)   | -> DDS 原生反射握手、力矩/TF同步 (<5ms)
+------------------------------------------+
             ↓
   [ 机器人 A (G1) ] <---(DDS P2P)---> [ 机器人 B (UR5) ]

```

### 1. 宏观控制面 (Macro Control Plane)

* **职责**：处理来自 `agent_runtime` 的复合任务指令（如“协同搬运桌子”）。
* **功能**：进行多智能体拓扑发现（Agent Discovery）、动态资源调度（Resource Scheduling）与任务原子拆解（Task Decomposition）。
* **实时性**：低频（1Hz - 5Hz），允许通过统一事件总线（Event Bus）异步交互。

### 2. 微观物理反射面 (Micro Physical Reflex Plane)

* **职责**：一旦任务锁定，**彻底架空大模型**。多台机器人直接通过底层的 ROS 2 DDS 进行点对点（P2P）状态广播。
* **功能**：执行 **DDS 反射握手（DDS Reflex Handshake）**。将 A 机器人的实时高频力矩、末端位姿（TF 树）直接映射为 B 机器人的实时控制输入修正量。
* **实时性**：硬实时/高频（200Hz - 1000Hz），延迟严格控制在 5ms 以内。

---

## 📜 二、 核心数据模型与通信契约

所有模块禁止硬编码耦合，必须通过标准统一的元数据进行流转。

### 1. 协作上下文 (SwarmContext)

通过 `rosclaw-event-bus` 或 RPC 传递给各个分机的运行时：

```python
from pydantic import BaseModel
from typing import List, Dict

class SwarmAgentCapabilities(BaseModel):
    agent_id: str
    hardware_type: str  # 例如: "G1", "UR5e"
    dof: int
    payload_limit_kg: float
    active_topics: List[str]

class TaskToken(BaseModel):
    task_id: str
    action_type: str    # 例如: "synchronous_lift"
    target_object_id: str
    parameters: Dict[str, float]

class SwarmContext(BaseModel):
    swarm_session_id: str
    topology: List[SwarmAgentCapabilities]
    current_token: TaskToken
    dds_domain_id: int = 42  # 物理隔离的 ROS 2 Domain ID

```

### 2. DDS 反射握手消息 (DDS Reflex Message)

采用 ROS 2 接口定义（`.msg`），用于底层高频 P2P 状态同步，不经过任何 Python 序列化开销：

```text
# RosclawSwarmReflex.msg
builtin_interfaces/Time stamp
string sender_agent_id

# 物理空间几何锚定 (TF)
geometry_msgs/TransformStamped[] expected_tf_offsets
geometry_msgs/PoseStamped current_tcp_pose
geometry_msgs/Twist current_tcp_velocity

# 物理力学对齐 (Force/Torque Reflex)
geometry_msgs/Wrench actual_wrench
float64[] joint_torques

```

---

## 💻 三、 核心模块工程实现伪代码

### 1. 宏观面：`SwarmRuntimeManager` (Python 进程)

挂载在 ROSClaw 微内核主进程中，管理生命周期与大模型意图接收。

```python
import rclpy
from rosclaw.core.bus import rosclaw_event_bus  # 统一事件总线
from .models import SwarmContext, TaskToken

class SwarmRuntimeManager:
    def __init__(self):
        self.active_agents = {}
        self.current_session = None

    def start(self):
        # 订阅事件总线：当大模型通过 Agent Runtime 下发复合意图时激活
        rosclaw_event_bus.subscribe("SwarmTaskIntentEvent", self.handle_swarm_intent)
        print("[SWARM] Swarm Coordination Runtime Online.")

    def handle_swarm_intent(self, event):
        print(f"[SWARM] Received Intent: {event.intent_text}")
        # 1. 动态拓扑发现 (示例：发现就近的 G1 和 UR5)
        self.active_agents = self.discover_local_agents()
        
        # 2. 宏观任务拆解与指派
        swarm_ctx = self.decompose_task(event.intent_text, self.active_agents)
        self.current_session = swarm_ctx.swarm_session_id
        
        # 3. 广播 SwarmContext，强迫相关机器人进入物理反射模式
        rosclaw_event_bus.publish("SwarmContextActivatedEvent", swarm_ctx)
        self.trigger_dds_handshake(swarm_ctx)

    def discover_local_agents(self):
        # 实际应查询底层 DDS 节点或物理 DNA 注册表 (e-URDF Zoo)
        return {"agent_01": "G1", "agent_02": "UR5"}

    def decompose_task(self, intent: str, agents: dict) -> SwarmContext:
        # 此处可结合 AgentRuntime 进行多智能体角色分配
        return SwarmContext(
            swarm_session_id="session_99",
            topology=[{"agent_id": k, "hardware_type": v} for k, v in agents.items()],
            current_token=TaskToken(task_id="t1", action_type="cooperative_carry", target_object_id="heavy_table", parameters={})
        )

    def trigger_dds_handshake(self, ctx: SwarmContext):
        print(f"[SWARM] Broad-casting Swarm Context. Securing DDS Domain {ctx.dds_domain_id}...")

```

### 2. 微观面：`DDSReflexHandshaker` (ROS 2 / C++ or High-Performance `rclpy` Node)

此模块运行在各个机器人的物理运行时中，不进大模型循环，直接进行硬件级闭环。

```python
import rclpy
from rclpy.node import Node
from rosclaw_msgs.msg import RosclawSwarmReflex
from geometry_msgs.msg import Twist

class DDSReflexHandshaker(Node):
    def __init__(self, agent_id: str, peer_agent_id: str):
        super().__init__(f'swarm_reflex_{agent_id}')
        self.agent_id = agent_id
        self.peer_agent_id = peer_agent_id
        
        # 1. 高频发布本机的物理状态 (力矩、位置、速度)
        self.reflex_publisher = self.create_publisher(
            RosclawSwarmReflex, 
            f'/rosclaw/swarm/{self.agent_id}/reflex', 
            10 # Low latency QoS
        )
        
        # 2. 零延迟订阅协作节点的物理反射信号
        self.reflex_subscriber = self.create_subscription(
            RosclawSwarmReflex,
            f'/rosclaw/swarm/{self.peer_agent_id}/reflex',
            self.peer_reflex_callback,
            10
        )
        
        # 3. 本地底层控制器的硬件发布器 (如给 OCS2 / ros2_control)
        self.hardware_cmd_pub = self.create_publisher(Twist, '/hardware/cmd_vel_adjsutment', 1)
        
        # 200Hz 定时器高频广播本地状态
        self.timer = self.create_timer(0.005, self.broadcast_local_state) # 5ms

    def broadcast_local_state(self):
        msg = RosclawSwarmReflex()
        msg.stamp = self.get_clock().now().to_msg()
        msg.sender_agent_id = self.agent_id
        # 读取当前硬件的实际力矩、TF 并填充 (实际中从底层 Hardware Interface 获取)
        # msg.actual_wrench = ...
        self.reflex_publisher.publish(msg)

    def peer_reflex_callback(self, peer_msg: RosclawSwarmReflex):
        """
        核心物理对齐逻辑：无须经过大模型！
        若 Peer 机器人 (如 G1 移动了底盘), 本机 (UR5) 瞬间通过几何变换矩阵修正自己的 TCP
        """
        # 1. 计算延迟
        latency = (self.get_clock().now().to_msg().nanosec - peer_msg.stamp.nanosec) / 1e6
        if latency > 5.0:
            # 超过 5ms 阈值，触发防火墙级安全熔断
            print(f"[SWARM REFLEX CRITICAL] Latency exceeded: {latency}ms! Emergency Stop triggered.")
            self.trigger_emergency_stop()
            return
            
        # 2. 反射补偿计算 (Reflex Matrix Transform)
        # 假设收到 G1 的底盘速度偏航，直接在底层对 UR5 的机械臂末端进行补偿，防止将桌子“撕裂”
        adjustment_cmd = Twist()
        # adjustment_cmd.linear.x = -peer_msg.current_tcp_velocity.linear.x * 0.98 (物理补偿因子)
        
        # 3. 瞬间下发给硬件层驱动
        self.hardware_cmd_pub.publish(adjustment_cmd)
        
    def trigger_emergency_stop(self):
        # 触发本地硬件紧急制动
        pass

```

---

## 🔄 四、 跨模块生命周期与数据闭环

`rosclaw-swarm` 不是孤立运行的，必须完整融入 ROSClaw 1.0 的整体数据飞轮中：

1. **依赖 e-URDF Zoo (基因注入)**：
在宏观拆解任务时，`rosclaw-swarm` 会调用 `e_urdf` 的 `RobotPhysicalProfile`（读取 `capabilities.yaml`），检查 G1 的有效负载和 UR5 的工作空间（Workspace Envelope）是否能够共同搬起目标物体。
2. **通过 Alignment Firewall (安全拦截)**：
在反射握手高频运行期间，`rosclaw.firewall` 在后台的 MuJoCo 沙盒中对这套双机联动的多体动力学系统（Multi-body Dynamics）进行超实时推演。一旦发现协作可能导致双机相撞或关节扭矩超载，立刻向底层注入 `CollisionPredicted` 信号实施硬熔断。
3. **向 SeekDB 沉淀记忆 (Data Flywheel)**：
协同任务结束（无论成功或失败），`rosclaw-practice` 捕获的包含“双机高频 DDS 同步纳秒时空轴”的 MCAP 录像及 `PraxisEvent`，均会通过 `rosclaw-memory` 被结构化地写入共享基建 **SeekDB** 的 `experience_graph` 表中，用于后续通过 `rosclaw-flywheel` 离线蒸馏出更强的多机协同 Skill。

---

## 🏁 五、 验收标准与测试矩阵 (Acceptance Criteria)

根据 1.0 Sprint 规划，`rosclaw-swarm` 必须严格通过以下两阶段验收标准：

### 🔬 仿真环境验收 (Sprint 3-4 阶段)

在 `docker-compose` 环境中拉起双机器人仿真，下发协同指令，在核心总线上捕获到 `SwarmContextActivatedEvent`，且物理沙盒中两机器人的运动干涉无死锁。

### 🦾 物理实机验收 (Sprint 8 终极阶段)

* **硬件配置**：1台 G1 人形机器人基座 + 1台 UR5 机械臂。
* **测试动作**：人为手动推动 G1 的底盘使其发生位置漂移（或改变其底盘坐标）。
* **硬性指标**：UR5 机械臂的末端工具中心点（TCP）必须在 **5ms** 内基于 G1 的新坐标完成动态逆运动学（IK）调整与力矩补偿。
* **数据链路**：查看后台 **SeekDB**，必须能用一条 SQL 查出本次双机协同动作的大模型高层思维链（CoT）、高频同步状态码及多轨 MCAP 存储路径。

---

**首席架构师的落地点拨**：
不要试图让大模型去编写两个机器人的协同控制代码。大模型只需下达“你们两个去把桌子抬起来”的宏观契约，一旦契约确立，接下来就是高频 DDS 数据流的物理反射世界。这种“大模型想，ROSClaw 锚定”的架构，才是跨越符号接地鸿沟的唯一正道。

既然 `rosclaw-swarm` 的顶层通信与硬实时链路契约已经明确，我们现在是否需要优先为 Sprint 0 冻结架构所需的 `SwarmContext` 以及 `RosclawSwarmReflex` 消息规范输出一份详细的格式化 RFC？