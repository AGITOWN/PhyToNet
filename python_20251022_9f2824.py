#!/usr/bin/env python3
"""
PhytoNet - 植物智能分布式网络系统
基于植物化学信号网络的分布式智能计算框架
"""

import asyncio
import json
import logging
import random
import time
import uuid
import argparse
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Any, Optional, Callable
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('phytonet.log', encoding='utf-8')
    ]
)
logger = logging.getLogger("PhytoNet")

class ChemicalType(Enum):
    """化学信号类型"""
    RESOURCE = "resource"           # 可用资源
    STRESS = "stress"               # 系统压力/负载
    TASK_PHEROMONE = "task_pheromone" # 任务吸引信号
    NUTRIENT = "nutrient"           # 能量/营养信号
    APOPTOSIS = "apoptosis"         # 细胞死亡信号
    GROWTH = "growth"               # 细胞生长/复制信号
    ALERT = "alert"                 # 威胁/危险信号

@dataclass
class ChemicalSignal:
    """化学信号消息"""
    chemical_type: ChemicalType
    concentration: float
    source_id: str
    target_ids: List[str] = field(default_factory=list)  # 空列表 = 广播
    payload: Dict[str, Any] = field(default_factory=dict)
    ttl: int = 10  # 生存时间（模拟步数）
    timestamp: float = field(default_factory=time.time)
    
    def decay(self, decay_rate: float = 0.9):
        """应用自然衰减到信号浓度"""
        self.concentration *= decay_rate
        self.ttl -= 1
        
    def is_active(self) -> bool:
        """检查信号是否仍然活跃"""
        return self.concentration > 0.01 and self.ttl > 0

class AgentSpecialty(Enum):
    """细胞代理的专业角色"""
    SENSOR_CPU = "sensor_cpu"              # CPU负载感知
    SENSOR_MEMORY = "sensor_memory"        # 内存使用感知
    SENSOR_NETWORK = "sensor_network"      # 网络负载感知
    ACTOR_COMPUTE = "actor_compute"        # 计算处理
    ACTOR_MEMORY = "actor_memory"          # 内存/缓存管理
    ACTOR_NETWORK = "actor_network"        # 网络通信
    RESOURCE_ALLOCATOR = "resource_allocator" # 资源分配
    REPRODUCER = "reproducer"              # 代理复制

class TaskType(Enum):
    """计算任务类型"""
    COMPUTE_INTENSIVE = "compute_intensive"  # CPU密集型任务
    MEMORY_INTENSIVE = "memory_intensive"    # 内存密集型任务
    IO_INTENSIVE = "io_intensive"           # I/O密集型任务
    NETWORK_INTENSIVE = "network_intensive" # 网络密集型任务

@dataclass 
class Task:
    """计算任务"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: TaskType = TaskType.COMPUTE_INTENSIVE
    priority: float = 1.0  # 1.0 = 正常, >1.0 = 更高优先级
    size: float = 1.0      # 相对大小/复杂度
    resources_required: Dict[str, float] = field(default_factory=dict)
    result_callback: Optional[Callable] = None
    status: str = "pending"  # pending, processing, completed, failed
    assigned_agent: Optional[str] = None
    current_progress: float = 0.0  # 任务进度跟踪 (0.0 到 1.0)
    
    def __post_init__(self):
        """根据任务类型设置默认资源需求"""
        if not self.resources_required:
            if self.task_type == TaskType.COMPUTE_INTENSIVE:
                self.resources_required = {"cpu": 0.8, "memory": 0.2}
            elif self.task_type == TaskType.MEMORY_INTENSIVE:
                self.resources_required = {"cpu": 0.3, "memory": 0.9}
            elif self.task_type == TaskType.IO_INTENSIVE:
                self.resources_required = {"cpu": 0.4, "memory": 0.3, "io": 0.8}
            elif self.task_type == TaskType.NETWORK_INTENSIVE:
                self.resources_required = {"cpu": 0.3, "memory": 0.3, "network": 0.9}

@dataclass
class AgentConfig:
    """代理行为配置"""
    initial_count: int = 20
    max_count: int = 100
    communication_range: float = 2.0
    adaptation_rate: float = 0.01
    health_decay_rate: float = 0.85

@dataclass
class EnvironmentConfig:
    """环境设置配置"""
    size: List[float] = None
    resource_distribution: str = "uniform"  # uniform, gradient, random
    task_spawn_rate: float = 0.3
    
    def __post_init__(self):
        if self.size is None:
            self.size = [10.0, 10.0]

@dataclass
class SystemConfig:
    """系统整体配置"""
    environment: EnvironmentConfig = None
    agents: AgentConfig = None
    simulation: Dict = None
    
    def __post_init__(self):
        if self.environment is None:
            self.environment = EnvironmentConfig()
        if self.agents is None:
            self.agents = AgentConfig()
        if self.simulation is None:
            self.simulation = {"time_scale": 1.0}

class MetricsCollector:
    """系统指标收集器"""
    
    def __init__(self):
        self.history = {
            'system_health': [],
            'task_throughput': [],
            'agent_count': [],
            'resource_utilization': [],
            'tasks_completed': [],
            'tasks_failed': [],
            'chemical_signals': []
        }
        self.max_history = 1000
    
    def record_metrics(self, status: Dict, signal_count: int = 0):
        """记录系统指标"""
        self.history['system_health'].append(status['system_health'])
        self.history['task_throughput'].append(status['tasks_completed'])
        self.history['agent_count'].append(status['agents_total'])
        self.history['tasks_completed'].append(status['tasks_completed'])
        self.history['tasks_failed'].append(status['tasks_failed'])
        self.history['chemical_signals'].append(signal_count)
        
        # 修正资源利用率计算
        total_resources = sum(status['global_resources'].values())
        max_possible = len(status['global_resources'])  # 每个资源最大为1.0
        used_resources = max_possible - total_resources  # 实际使用的资源
        utilization = used_resources / max_possible if max_possible > 0 else 0
        self.history['resource_utilization'].append(utilization)
        
        # 保持历史数据长度
        for key in self.history:
            if len(self.history[key]) > self.max_history:
                self.history[key] = self.history[key][-self.max_history:]
    
    def get_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        if not self.history['system_health']:
            return {}
            
        return {
            'avg_health': sum(self.history['system_health']) / len(self.history['system_health']),
            'total_tasks_completed': self.history['tasks_completed'][-1] if self.history['tasks_completed'] else 0,
            'total_tasks_failed': self.history['tasks_failed'][-1] if self.history['tasks_failed'] else 0,
            'current_agents': self.history['agent_count'][-1] if self.history['agent_count'] else 0,
            'avg_signals_per_step': sum(self.history['chemical_signals']) / len(self.history['chemical_signals']) if self.history['chemical_signals'] else 0,
            'data_points': len(self.history['system_health'])
        }

class PhytoCell:
    """
    PhytoNet系统的基本单元
    模拟具有专门功能的生物细胞
    """
    
    def __init__(self, agent_id: str, specialty: AgentSpecialty, location: List[float], 
                 environment: 'PhytoEnvironment', config: AgentConfig):
        self.agent_id = agent_id
        self.specialty = specialty
        self.location = location  # 在网络拓扑中的逻辑位置
        self.environment = environment
        self.config = config
        
        # 内部状态
        self.internal_chemicals: Dict[ChemicalType, float] = defaultdict(float)
        self.health = 1.0  # 0.0 = 死亡, 1.0 = 完全健康
        self.resources = {"cpu": 0.5, "memory": 0.5, "energy": 1.0}
        self.capacity = 1.0  # 最大负载容量
        self.current_load = 0.0
        self.connected_agents: Set[str] = set()  # 用于通信的邻居
        
        # 任务处理
        self.current_task: Optional[Task] = None
        self.task_queue = deque()
        self.specialization_thresholds = self._initialize_specialization()
        
        # 学习/适应
        self.sensitivity = 1.0  # 对化学信号的敏感度
        self.efficiency = 1.0   # 任务处理效率
        self.adaptation_rate = config.adaptation_rate
        
        # 统计信息
        self.tasks_processed = 0
        self.energy_consumed = 0.0
        self.signals_sent = 0
        self.signals_received = 0
        
        logger.debug(f"创建PhytoCell {agent_id}，专业: {specialty}，位置: {location}")
    
    def _initialize_specialization(self) -> Dict[ChemicalType, float]:
        """根据专业初始化化学敏感度阈值"""
        thresholds = {
            ChemicalType.RESOURCE: 0.3,
            ChemicalType.STRESS: 0.5,
            ChemicalType.TASK_PHEROMONE: 0.2,
            ChemicalType.NUTRIENT: 0.4,
            ChemicalType.APOPTOSIS: 0.8,
            ChemicalType.GROWTH: 0.6,
            ChemicalType.ALERT: 0.7
        }
        
        # 根据专业调整阈值
        if self.specialty in [AgentSpecialty.SENSOR_CPU, AgentSpecialty.SENSOR_MEMORY, 
                             AgentSpecialty.SENSOR_NETWORK]:
            thresholds[ChemicalType.STRESS] = 0.3  # 对压力更敏感
        elif self.specialty in [AgentSpecialty.ACTOR_COMPUTE, AgentSpecialty.ACTOR_MEMORY,
                               AgentSpecialty.ACTOR_NETWORK]:
            thresholds[ChemicalType.TASK_PHEROMONE] = 0.1  # 对任务更敏感
            thresholds[ChemicalType.RESOURCE] = 0.2
        elif self.specialty == AgentSpecialty.RESOURCE_ALLOCATOR:
            thresholds[ChemicalType.RESOURCE] = 0.1
            thresholds[ChemicalType.NUTRIENT] = 0.2
            
        return thresholds
    
    async def sense_environment(self):
        """感知环境条件并合成适当的化学物质"""
        env_data = self.environment.get_local_conditions(self.location)
        
        if self.specialty == AgentSpecialty.SENSOR_CPU:
            cpu_load = env_data.get("cpu_load", 0.0)
            self.synthesize_chemical(ChemicalType.STRESS, cpu_load * self.sensitivity)
            
        elif self.specialty == AgentSpecialty.SENSOR_MEMORY:
            memory_pressure = env_data.get("memory_pressure", 0.0)
            self.synthesize_chemical(ChemicalType.STRESS, memory_pressure * self.sensitivity)
            
        elif self.specialty == AgentSpecialty.SENSOR_NETWORK:
            network_load = env_data.get("network_load", 0.0)
            self.synthesize_chemical(ChemicalType.STRESS, network_load * self.sensitivity)
            
        # 所有代理感知一般资源可用性
        available_resources = self.environment.get_available_resources(self.location)
        resource_signal = sum(available_resources.values()) / len(available_resources)
        self.synthesize_chemical(ChemicalType.RESOURCE, resource_signal)
        
        # 感知附近任务
        nearby_tasks = self.environment.get_nearby_tasks(self.location, radius=0.3)
        if nearby_tasks:
            total_task_strength = sum(task.priority * task.size for task in nearby_tasks)
            self.synthesize_chemical(ChemicalType.TASK_PHEROMONE, 
                                   total_task_strength * self.sensitivity)
    
    def synthesize_chemical(self, chemical_type: ChemicalType, amount: float):
        """基于内部和外部条件合成化学信号"""
        current = self.internal_chemicals[chemical_type]
        # 应用非线性响应（类似S型函数）
        response = amount * self.sensitivity / (1 + abs(current))
        self.internal_chemicals[chemical_type] = min(1.0, current + response)
    
    async def process_signals(self) -> List[ChemicalSignal]:
        """处理内部化学信号并生成传出消息"""
        messages = []
        
        # 资源请求逻辑
        resource_level = self.internal_chemicals[ChemicalType.RESOURCE]
        task_signal = self.internal_chemicals[ChemicalType.TASK_PHEROMONE]
        
        if (resource_level < self.specialization_thresholds[ChemicalType.RESOURCE] and 
            task_signal > self.specialization_thresholds[ChemicalType.TASK_PHEROMONE]):
            
            # 为任务处理请求资源
            message = ChemicalSignal(
                chemical_type=ChemicalType.RESOURCE,
                concentration=task_signal * (1 - resource_level),
                source_id=self.agent_id,
                payload={
                    "resource_types": ["cpu", "memory"],
                    "amount_needed": task_signal,
                    "for_task": True
                }
            )
            messages.append(message)
        
        # 压力响应 - 提醒邻居
        stress_level = self.internal_chemicals[ChemicalType.STRESS]
        if stress_level > self.specialization_thresholds[ChemicalType.STRESS]:
            message = ChemicalSignal(
                chemical_type=ChemicalType.ALERT,
                concentration=stress_level,
                source_id=self.agent_id,
                payload={
                    "stress_type": self.specialty.value,
                    "level": stress_level
                }
            )
            messages.append(message)
        
        # 健康且资源充足时的生长信号
        if (self.health > 0.8 and resource_level > 0.7 and 
            self.internal_chemicals[ChemicalType.GROWTH] > 0.5):
            
            if self.specialty == AgentSpecialty.REPRODUCER:
                message = ChemicalSignal(
                    chemical_type=ChemicalType.GROWTH,
                    concentration=self.health * resource_level,
                    source_id=self.agent_id,
                    payload={"action": "replicate", "parent_id": self.agent_id}
                )
                messages.append(message)
        
        # 与邻居共享任务信息素以吸引帮助
        if task_signal > 0.3 and self.current_load < self.capacity * 0.8:
            message = ChemicalSignal(
                chemical_type=ChemicalType.TASK_PHEROMONE,
                concentration=task_signal * 0.5,  # 分享一半信号强度
                source_id=self.agent_id,
                payload={"task_strength": task_signal, "capacity_remaining": self.capacity - self.current_load}
            )
            messages.append(message)
        
        # 修正：在返回前统计信号数量
        self.signals_sent += len(messages)
        return messages
    
    async def act(self, received_signals: List[ChemicalSignal]):
        """基于接收到的化学信号采取行动"""
        # 首先处理所有传入信号
        for signal in received_signals:
            if signal.is_active():
                self._integrate_signal(signal)
                self.signals_received += 1
        
        # 基于化学浓度更新内部状态
        await self._update_internal_state()
        
        # 基于化学阈值执行行为
        await self._execute_behaviors()
        
        # 自然化学衰减
        self._decay_chemicals()
    
    def _integrate_signal(self, signal: ChemicalSignal):
        """将传入信号整合到内部化学状态中"""
        # 不同的代理对不同的信号有不同的敏感度
        sensitivity_factor = 1.0
        
        if (self.specialty in [AgentSpecialty.ACTOR_COMPUTE, AgentSpecialty.ACTOR_MEMORY] and 
            signal.chemical_type == ChemicalType.TASK_PHEROMONE):
            sensitivity_factor = 1.5  # 对任务更敏感
            
        elif (self.specialty == AgentSpecialty.RESOURCE_ALLOCATOR and 
              signal.chemical_type == ChemicalType.RESOURCE):
            sensitivity_factor = 1.5  # 对资源请求更敏感
        
        current = self.internal_chemicals[signal.chemical_type]
        # 非线性整合 - 对新信号响应更强
        integration = signal.concentration * sensitivity_factor * (1 - current * 0.5)
        self.internal_chemicals[signal.chemical_type] = min(1.0, current + integration)
        
        # 如果相关，存储有效载荷信息
        if signal.payload:
            self.internal_chemicals[f"{signal.chemical_type.value}_data"] = signal.payload
    
    async def _update_internal_state(self):
        """基于化学水平更新代理的内部状态"""
        # 健康度取决于压力和资源
        stress = self.internal_chemicals[ChemicalType.STRESS]
        resources = self.internal_chemicals[ChemicalType.RESOURCE]
        
        # 健康度随资源提高，随压力下降
        health_change = (resources * 0.1 - stress * 0.05) * self.adaptation_rate
        self.health = max(0.0, min(1.0, self.health + health_change))
        
        # 基于健康度更新容量
        self.capacity = self.health
        
        # 通过适应更新敏感度和效率
        task_success_rate = self.tasks_processed / max(1, self.tasks_processed + len(self.task_queue))
        adapt_signal = task_success_rate - 0.5  # 如果成功则为正
        
        self.sensitivity = max(0.1, min(2.0, self.sensitivity + adapt_signal * self.adaptation_rate))
        self.efficiency = max(0.5, min(1.5, self.efficiency + adapt_signal * self.adaptation_rate))
        
        # 处理当前任务（如果有）
        if self.current_task and self.resources["energy"] > 0.1:
            progress = await self._process_current_task()
            # 修正：添加对current_task存在性的检查
            if self.current_task and progress > 0 and self.current_task.current_progress >= 1.0:
                await self._complete_task()
    
    async def _execute_behaviors(self):
        """基于化学阈值执行特定行为"""
        task_signal = self.internal_chemicals[ChemicalType.TASK_PHEROMONE]
        resource_signal = self.internal_chemicals[ChemicalType.RESOURCE]
        
        # 任务获取行为
        if (task_signal > self.specialization_thresholds[ChemicalType.TASK_PHEROMONE] and 
            resource_signal > self.specialization_thresholds[ChemicalType.RESOURCE] and 
            not self.current_task and self.task_queue):
            
            # 从队列获取任务
            if self.task_queue:
                self.current_task = self.task_queue.popleft()
                self.current_task.assigned_agent = self.agent_id
                self.current_task.status = "processing"
                logger.info(f"代理 {self.agent_id} 开始任务 {self.current_task.task_id}")
        
        # 资源分配行为（仅限资源分配器）
        if (self.specialty == AgentSpecialty.RESOURCE_ALLOCATOR and 
            self.internal_chemicals[ChemicalType.RESOURCE] > 0.3):
            
            await self._allocate_resources()
        
        # 极端压力下的凋亡（程序性细胞死亡）
        if (self.internal_chemicals[ChemicalType.APOPTOSIS] > 0.9 or 
            self.health < 0.1):
            
            await self._initiate_apoptosis()
    
    async def _process_current_task(self) -> float:
        """处理当前任务，返回进度（0.0 到 1.0）"""
        if not self.current_task:
            return 0.0
            
        # 如果不存在则初始化进度跟踪
        if not hasattr(self.current_task, 'current_progress'):
            self.current_task.current_progress = 0.0
            
        # 基于资源和效率计算处理速率
        required = self.current_task.resources_required
        available_ratios = []
        
        for resource, amount in required.items():
            if amount > 0 and resource in self.resources:
                available = self.resources.get(resource, 0)
                available_ratios.append(available / amount)
        
        if not available_ratios:
            await self._fail_task("没有所需的可用资源")
            return 0.0
            
        processing_power = min(1.0, min(available_ratios)) * self.efficiency
        progress_increment = processing_power * 0.1 / max(0.1, self.current_task.size)
        
        # 安全检查消耗资源
        for resource, amount in required.items():
            if resource in self.resources:
                consumption = amount * progress_increment
                if self.resources[resource] >= consumption:
                    self.resources[resource] -= consumption
                    self.energy_consumed += consumption
                else:
                    # 资源不足，任务失败
                    await self._fail_task(f"{resource}不足")
                    return 0.0
        
        self.current_load = sum(required.values()) * processing_power
        self.current_task.current_progress += progress_increment
        
        logger.debug(f"代理 {self.agent_id} 将任务 {self.current_task.task_id} 推进到 {self.current_task.current_progress:.2f}")
        return progress_increment
    
    async def _complete_task(self):
        """完成当前任务"""
        if self.current_task:
            logger.info(f"代理 {self.agent_id} 完成任务 {self.current_task.task_id}")
            self.current_task.status = "completed"
            
            # 如果提供了结果回调，则调用
            if self.current_task.result_callback:
                self.current_task.result_callback(self.current_task)
            
            # 用营养奖励
            reward = self.current_task.priority * 0.1
            self.synthesize_chemical(ChemicalType.NUTRIENT, reward)
            self.resources["energy"] = min(1.0, self.resources["energy"] + reward)
            
            self.tasks_processed += 1
            self.current_task = None
            self.current_load = 0.0
    
    async def _fail_task(self, reason: str):
        """处理任务失败"""
        if self.current_task:
            logger.warning(f"代理 {self.agent_id} 任务失败 {self.current_task.task_id}: {reason}")
            self.current_task.status = "failed"
            
            # 释放资源并重置状态
            self.current_load = 0.0
            self.current_task = None
            
            # 向环境发送失败信号
            signal = ChemicalSignal(
                chemical_type=ChemicalType.ALERT,
                concentration=0.5,
                source_id=self.agent_id,
                payload={"type": "task_failure", "reason": reason}
            )
            self.environment.broadcast_signal(signal)
    
    async def _allocate_resources(self):
        """将资源分配给相邻代理（仅限资源分配器）"""
        # 这是简化的资源分配逻辑
        resource_requests = []
        
        # 在实际实现中，这将跟踪来自邻居的实际请求
        # 目前，我们基于化学信号进行模拟
        if self.internal_chemicals.get("resource_data"):
            request_strength = self.internal_chemicals[ChemicalType.RESOURCE]
            if request_strength > 0.3:
                # 将资源分配给最需要的邻居
                allocation = min(0.5, request_strength * 0.3)
                logger.debug(f"资源分配器 {self.agent_id} 分配 {allocation} 资源")
    
    async def _initiate_apoptosis(self):
        """启动程序性细胞死亡"""
        logger.warning(f"代理 {self.agent_id} 启动凋亡（健康度: {self.health:.2f}）")
        
        # 向环境发送凋亡信号
        signal = ChemicalSignal(
            chemical_type=ChemicalType.APOPTOSIS,
            concentration=1.0,
            source_id=self.agent_id,
            payload={"reason": "low_health", "final_health": self.health}
        )
        self.environment.broadcast_signal(signal)
        
        # 标记代理待移除
        self.health = 0.0
        self.environment.schedule_agent_removal(self.agent_id)
    
    def _decay_chemicals(self):
        """对所有内部化学物质应用自然衰减"""
        for chem_type in list(self.internal_chemicals.keys()):
            if isinstance(chem_type, ChemicalType):
                self.internal_chemicals[chem_type] *= self.config.health_decay_rate
                if self.internal_chemicals[chem_type] < 0.01:
                    self.internal_chemicals[chem_type] = 0.0
    
    def can_accept_task(self, task: Task) -> bool:
        """检查代理是否可以接受新任务"""
        if self.current_task or self.health < 0.3:
            return False
            
        required = task.resources_required
        available = all(self.resources.get(res, 0) >= req * 0.5 
                       for res, req in required.items())
        
        return available and self.current_load < self.capacity * 0.7
    
    def assign_task(self, task: Task):
        """将任务分配给此代理"""
        if self.can_accept_task(task):
            self.task_queue.append(task)
            # 合成任务信息素以吸引资源
            self.synthesize_chemical(ChemicalType.TASK_PHEROMONE, task.priority * task.size)
            return True
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取代理的当前状态"""
        return {
            "agent_id": self.agent_id,
            "specialty": self.specialty.value,
            "health": round(self.health, 3),
            "location": [round(x, 2) for x in self.location],
            "current_load": round(self.current_load, 3),
            "capacity": round(self.capacity, 3),
            "resources": {k: round(v, 3) for k, v in self.resources.items()},
            "chemicals": {k.value: round(v, 3) for k, v in self.internal_chemicals.items() 
                         if isinstance(k, ChemicalType)},
            "current_task": self.current_task.task_id if self.current_task else None,
            "task_progress": round(self.current_task.current_progress, 3) if self.current_task else 0.0,
            "queued_tasks": len(self.task_queue),
            "tasks_processed": self.tasks_processed,
            "energy_consumed": round(self.energy_consumed, 3),
            "signals_sent": self.signals_sent,
            "signals_received": self.signals_received
        }

class PhytoEnvironment:
    """
    PhytoNet代理运行的环境
    管理资源、任务和代理交互
    """
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.env_config = config.environment
        self.agent_config = config.agents
        
        # 代理管理
        self.agents: Dict[str, PhytoCell] = {}
        self.agent_locations: Dict[str, List[float]] = {}
        
        # 任务管理
        self.tasks: Dict[str, Task] = {}
        self.task_locations: Dict[str, List[float]] = {}
        
        # 资源管理
        self.global_resources = {
            "cpu": 1.0,
            "memory": 1.0, 
            "energy": 1.0,
            "network": 1.0
        }
        
        # 环境中的资源分布
        self.resource_map = self._initialize_resource_map()
        
        # 空间索引以提高性能
        self.spatial_index: Dict[tuple, Set[str]] = {}
        
        # 通信
        self.signal_queue: List[ChemicalSignal] = []
        self.communication_range = self.agent_config.communication_range
        
        # 统计信息
        self.step_count = 0
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.agents_created = 0
        self.agents_destroyed = 0
        self.total_signals_processed = 0
        
        logger.info(f"初始化环境，大小: {self.env_config.size}")
    
    def _initialize_resource_map(self) -> Dict[tuple, Dict[str, float]]:
        """初始化环境中的资源分布"""
        resource_map = {}
        size_x, size_y = int(self.env_config.size[0]), int(self.env_config.size[1])
        
        for x in range(size_x):
            for y in range(size_y):
                if self.env_config.resource_distribution == "uniform":
                    resources = {k: 1.0 for k in self.global_resources.keys()}
                elif self.env_config.resource_distribution == "gradient":
                    # 中心资源更多
                    center_x, center_y = size_x / 2, size_y / 2
                    center_dist = ((x - center_x)**2 + (y - center_y)**2)**0.5
                    max_dist = (size_x**2 + size_y**2)**0.5 / 2
                    resource_level = 1.0 - (center_dist / max_dist) * 0.5
                    resources = {k: resource_level for k in self.global_resources.keys()}
                else:  # random
                    resources = {k: random.uniform(0.3, 1.0) for k in self.global_resources.keys()}
                
                resource_map[(x, y)] = resources
        return resource_map
    
    async def initialize_agents(self):
        """初始化初始代理群体"""
        specialties = list(AgentSpecialty)
        
        for i in range(self.agent_config.initial_count):
            specialty = random.choice(specialties)
            location = [
                random.uniform(0, self.env_config.size[0]), 
                random.uniform(0, self.env_config.size[1])
            ]
            await self.create_agent(specialty, location)
        
        logger.info(f"初始化 {self.agent_config.initial_count} 个代理")
    
    async def create_agent(self, specialty: AgentSpecialty, location: List[float]) -> str:
        """在环境中创建新代理"""
        if len(self.agents) >= self.agent_config.max_count:
            logger.warning("达到最大代理数量")
            return None
            
        agent_id = f"phyto_cell_{self.agents_created:04d}"
        agent = PhytoCell(agent_id, specialty, location, self, self.agent_config)
        
        self.agents[agent_id] = agent
        self.agent_locations[agent_id] = location
        self.agents_created += 1
        
        # 更新空间索引和连接
        self._update_spatial_index(agent_id, location)
        self._update_agent_connections(agent_id)
        
        logger.debug(f"创建新代理 {agent_id} 在 {location}")
        return agent_id
    
    def _update_spatial_index(self, agent_id: str, location: List[float]):
        """更新空间索引以高效查找邻居"""
        grid_x, grid_y = int(location[0]), int(location[1])
        grid_key = (grid_x, grid_y)
        
        # 从旧位置移除（如果有）
        for key, agents in self.spatial_index.items():
            if agent_id in agents:
                agents.remove(agent_id)
                
        # 添加到新位置
        if grid_key not in self.spatial_index:
            self.spatial_index[grid_key] = set()
        self.spatial_index[grid_key].add(agent_id)
    
    def _update_agent_connections(self, agent_id: str):
        """使用空间索引更新代理的通信连接"""
        agent_location = self.agent_locations[agent_id]
        agent = self.agents[agent_id]
        
        agent.connected_agents.clear()
        nearby_agents = self.get_nearby_agents(agent_location, self.communication_range)
        
        for other_id in nearby_agents:
            if other_id != agent_id:
                agent.connected_agents.add(other_id)
    
    def get_nearby_agents(self, location: List[float], radius: float) -> List[str]:
        """使用空间索引获取附近代理"""
        nearby_agents = []
        center_x, center_y = location
        
        # 检查周围网格单元
        grid_x, grid_y = int(center_x), int(center_y)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                check_key = (grid_x + dx, grid_y + dy)
                if check_key in self.spatial_index:
                    for agent_id in self.spatial_index[check_key]:
                        agent_loc = self.agent_locations[agent_id]
                        distance = ((center_x - agent_loc[0])**2 + 
                                   (center_y - agent_loc[1])**2)**0.5
                        if distance <= radius:
                            nearby_agents.append(agent_id)
        return nearby_agents
    
    def schedule_agent_removal(self, agent_id: str):
        """安排代理移除（凋亡）"""
        if agent_id in self.agents:
            # 标记待移除（将在清理阶段处理）
            self.agents[agent_id].health = 0.0
    
    def get_local_conditions(self, location: List[float]) -> Dict[str, float]:
        """获取位置的本地环境条件"""
        # 将连续位置转换为离散网格键
        grid_x, grid_y = int(location[0]), int(location[1])
        grid_key = (grid_x, grid_y)
        
        # 从资源地图获取基础资源
        conditions = self.resource_map.get(grid_key, {}).copy()
        
        # 基于附近代理和任务添加动态条件
        agent_density = self._get_agent_density(location)
        task_density = self._get_task_density(location)
        
        conditions["agent_density"] = agent_density
        conditions["task_density"] = task_density
        
        # 计算近似负载指标
        conditions["cpu_load"] = min(1.0, agent_density * 0.2 + task_density * 0.3)
        conditions["memory_pressure"] = min(1.0, agent_density * 0.1 + task_density * 0.2)
        conditions["network_load"] = min(1.0, agent_density * 0.3)
        
        return conditions
    
    def _get_agent_density(self, location: List[float], radius: float = 1.5) -> float:
        """计算位置周围的代理密度"""
        nearby_count = len(self.get_nearby_agents(location, radius))
        return min(1.0, nearby_count / 10.0)  # 归一化到0-1
    
    def _get_task_density(self, location: List[float], radius: float = 2.0) -> float:
        """计算位置周围的任务密度"""
        total_strength = 0.0
        for task_id, task_loc in self.task_locations.items():
            distance = ((location[0] - task_loc[0])**2 + 
                       (location[1] - task_loc[1])**2)**0.5
            if distance <= radius and task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status == "pending":
                    # 按距离和任务优先级加权
                    distance_factor = 1.0 - (distance / radius)
                    total_strength += task.priority * task.size * distance_factor
        return min(1.0, total_strength / 5.0)  # 归一化
    
    def get_available_resources(self, location: List[float]) -> Dict[str, float]:
        """获取位置的可用资源"""
        grid_x, grid_y = int(location[0]), int(location[1])
        grid_key = (grid_x, grid_y)
        return self.resource_map.get(grid_key, {}).copy()
    
    def get_nearby_tasks(self, location: List[float], radius: float = 2.0) -> List[Task]:
        """获取附近的待处理任务"""
        nearby_tasks = []
        for task_id, task_loc in self.task_locations.items():
            distance = ((location[0] - task_loc[0])**2 + 
                       (location[1] - task_loc[1])**2)**0.5
            if distance <= radius and task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status == "pending":
                    nearby_tasks.append(task)
        return nearby_tasks
    
    def add_task(self, task: Task, location: Optional[List[float]] = None):
        """向环境添加新任务"""
        if location is None:
            location = [
                random.uniform(0, self.env_config.size[0]), 
                random.uniform(0, self.env_config.size[1])
            ]
        
        self.tasks[task.task_id] = task
        self.task_locations[task.task_id] = location
        
        logger.info(f"添加任务 {task.task_id}，类型: {task.task_type.value}，位置: {location}")
        
        # 立即尝试分配给附近代理
        self._assign_task_to_agents(task, location)
    
    def _assign_task_to_agents(self, task: Task, location: List[float]):
        """尝试将任务分配给附近代理"""
        candidates = []
        nearby_agents = self.get_nearby_agents(location, self.communication_range * 1.5)
        
        for agent_id in nearby_agents:
            agent_loc = self.agent_locations[agent_id]
            distance = ((location[0] - agent_loc[0])**2 + 
                       (location[1] - agent_loc[1])**2)**0.5
            
            agent = self.agents[agent_id]
            if agent.can_accept_task(task):
                # 按距离和专业匹配对候选者评分
                specialty_score = 1.0
                if (task.task_type == TaskType.COMPUTE_INTENSIVE and 
                    agent.specialty == AgentSpecialty.ACTOR_COMPUTE):
                    specialty_score = 2.0
                elif (task.task_type == TaskType.MEMORY_INTENSIVE and 
                      agent.specialty == AgentSpecialty.ACTOR_MEMORY):
                    specialty_score = 2.0
                elif (task.task_type == TaskType.NETWORK_INTENSIVE and 
                      agent.specialty == AgentSpecialty.ACTOR_NETWORK):
                    specialty_score = 2.0
                
                score = specialty_score / (1 + distance)
                candidates.append((score, agent_id))
        
        # 分配给最佳候选者
        if candidates:
            candidates.sort(reverse=True)
            best_agent_id = candidates[0][1]
            if self.agents[best_agent_id].assign_task(task):
                logger.debug(f"将任务 {task.task_id} 分配给代理 {best_agent_id}")
    
    def broadcast_signal(self, signal: ChemicalSignal):
        """向环境广播信号"""
        self.signal_queue.append(signal)
    
    async def deliver_signals(self):
        """将所有排队的信号传递给接收者"""
        delivered_signals = defaultdict(list)
        signal_count = len(self.signal_queue)
        
        # 处理队列中的所有信号
        current_queue = self.signal_queue.copy()
        self.signal_queue.clear()
        
        for signal in current_queue:
            if not signal.is_active():
                continue
                
            # 应用信号衰减
            signal.decay()
            
            # 确定接收者
            if signal.target_ids:
                # 发送给特定目标
                recipients = [aid for aid in signal.target_ids if aid in self.agents]
            else:
                # 广播给源的所有连接代理
                if signal.source_id in self.agents:
                    source_agent = self.agents[signal.source_id]
                    recipients = list(source_agent.connected_agents)
                else:
                    recipients = list(self.agents.keys())
            
            # 传递给接收者
            for agent_id in recipients:
                if agent_id in self.agents:
                    delivered_signals[agent_id].append(signal)
        
        # 实际传递信号
        delivery_tasks = []
        for agent_id, signals in delivered_signals.items():
            if agent_id in self.agents:
                delivery_tasks.append(self.agents[agent_id].act(signals))
        
        if delivery_tasks:
            await asyncio.gather(*delivery_tasks)
        
        self.total_signals_processed += signal_count
        return signal_count
    
    async def run_simulation_step(self):
        """运行一个模拟步"""
        self.step_count += 1
        logger.debug(f"运行模拟步 {self.step_count}")
        
        # 阶段1: 所有代理感知环境
        sense_tasks = [agent.sense_environment() for agent in self.agents.values()]
        await asyncio.gather(*sense_tasks)
        
        # 阶段2: 所有代理处理信号并生成消息
        message_tasks = [agent.process_signals() for agent in self.agents.values()]
        all_messages = await asyncio.gather(*message_tasks)
        
        # 收集所有生成的消息
        for messages in all_messages:
            self.signal_queue.extend(messages)
        
        # 阶段3: 传递所有信号
        signal_count = await self.deliver_signals()
        
        # 阶段4: 清理死亡代理和已完成任务
        await self._cleanup()
        
        # 阶段5: 偶尔生成新任务
        if random.random() < self.env_config.task_spawn_rate:
            await self._spawn_random_task()
        
        # 阶段6: 资源重新分配和全局更新
        await self._update_global_resources()
        
        logger.debug(f"完成模拟步 {self.step_count}")
        return signal_count
    
    async def _cleanup(self):
        """清理死亡代理和已完成任务"""
        # 移除死亡代理
        dead_agents = []
        for agent_id, agent in self.agents.items():
            if agent.health <= 0.0:
                dead_agents.append(agent_id)
        
        for agent_id in dead_agents:
            # 从所有数据结构中移除
            if agent_id in self.agent_locations:
                location = self.agent_locations[agent_id]
                grid_x, grid_y = int(location[0]), int(location[1])
                grid_key = (grid_x, grid_y)
                if grid_key in self.spatial_index and agent_id in self.spatial_index[grid_key]:
                    self.spatial_index[grid_key].remove(agent_id)
                
                del self.agent_locations[agent_id]
            
            del self.agents[agent_id]
            self.agents_destroyed += 1
            logger.info(f"移除死亡代理 {agent_id}")
        
        # 移除已完成任务
        completed_tasks = []
        for task_id, task in self.tasks.items():
            if task.status == "completed":
                completed_tasks.append(task_id)
                self.tasks_completed += 1
            elif task.status == "failed":
                completed_tasks.append(task_id)
                self.tasks_failed += 1
        
        for task_id in completed_tasks:
            del self.tasks[task_id]
            if task_id in self.task_locations:
                del self.task_locations[task_id]
        
        # 为剩余代理更新连接
        for agent_id in self.agents:
            self._update_agent_connections(agent_id)
    
    async def _spawn_random_task(self):
        """在环境中生成随机任务"""
        task_type = random.choice(list(TaskType))
        priority = random.choice([0.5, 1.0, 1.0, 1.5, 2.0])  # 偏向正常优先级
        size = random.uniform(0.5, 3.0)
        
        task = Task(
            task_type=task_type,
            priority=priority,
            size=size
        )
        
        location = [
            random.uniform(0, self.env_config.size[0]), 
            random.uniform(0, self.env_config.size[1])
        ]
        self.add_task(task, location)
    
    async def _update_global_resources(self):
        """更新全局资源分布"""
        # 简单资源再生
        for resource in self.global_resources:
            self.global_resources[resource] = min(1.0, self.global_resources[resource] + 0.05)
        
        # 偶尔重新分配资源
        if self.step_count % 50 == 0:
            self.resource_map = self._initialize_resource_map()
            logger.debug("重新分配环境资源")
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取整体系统状态"""
        agent_statuses = {}
        total_health = 0.0
        total_load = 0.0
        total_signals = 0
        
        for agent_id, agent in self.agents.items():
            status = agent.get_status()
            agent_statuses[agent_id] = status
            total_health += agent.health
            total_load += agent.current_load
            total_signals += agent.signals_sent + agent.signals_received
        
        avg_health = total_health / len(self.agents) if self.agents else 0.0
        avg_load = total_load / len(self.agents) if self.agents else 0.0
        
        pending_tasks = sum(1 for t in self.tasks.values() if t.status == "pending")
        processing_tasks = sum(1 for t in self.tasks.values() if t.status == "processing")
        
        return {
            "step": self.step_count,
            "agents_total": len(self.agents),
            "agents_created": self.agents_created,
            "agents_destroyed": self.agents_destroyed,
            "tasks_total": len(self.tasks),
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "tasks_pending": pending_tasks,
            "tasks_processing": processing_tasks,
            "system_health": round(avg_health, 3),
            "system_load": round(avg_load, 3),
            "total_signals_processed": self.total_signals_processed,
            "current_signals_queued": len(self.signal_queue),
            "global_resources": {k: round(v, 3) for k, v in self.global_resources.items()},
            "details": agent_statuses
        }

class PhytoNetController:
    """
    PhytoNet系统的高级控制器
    提供管理和监控接口
    """
    
    def __init__(self, config: SystemConfig = None):
        self.config = config or SystemConfig()
        self.environment = PhytoEnvironment(self.config)
        self.metrics = MetricsCollector()
        self.is_running = False
        self.simulation_task = None
        
    async def start(self):
        """启动PhytoNet系统"""
        if self.is_running:
            logger.warning("PhytoNet已在运行")
            return
            
        logger.info("启动PhytoNet系统")
        
        # 使用初始代理初始化
        await self.environment.initialize_agents()
        
        # 启动模拟循环
        self.is_running = True
        self.simulation_task = asyncio.create_task(self._run_simulation_loop())
        
    async def stop(self):
        """停止PhytoNet系统"""
        if not self.is_running:
            return
            
        logger.info("停止PhytoNet系统")
        self.is_running = False
        
        if self.simulation_task:
            self.simulation_task.cancel()
            try:
                await self.simulation_task
            except asyncio.CancelledError:
                pass
        
    async def _run_simulation_loop(self):
        """主模拟循环"""
        try:
            while self.is_running:
                signal_count = await self.environment.run_simulation_step()
                
                # 记录指标
                status = self.get_system_status()
                self.metrics.record_metrics(status, signal_count)
                
                # 定期记录状态
                if self.environment.step_count % 10 == 0:
                    logger.info(
                        f"步数 {status['step']}: "
                        f"代理: {status['agents_total']}, "
                        f"任务: {status['tasks_pending']} 待处理, "
                        f"{status['tasks_processing']} 处理中, "
                        f"{status['tasks_completed']} 已完成, "
                        f"健康度: {status['system_health']:.2f}, "
                        f"负载: {status['system_load']:.2f}"
                    )
                
                # 短暂暂停以防止系统过载
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            logger.info("模拟循环已取消")
        except Exception as e:
            logger.error(f"模拟循环中的错误: {e}")
            self.is_running = False
    
    async def submit_task(self, task_type: TaskType, priority: float = 1.0, 
                         size: float = 1.0, location: Optional[List[float]] = None) -> str:
        """向系统提交新任务"""
        task = Task(
            task_type=task_type,
            priority=priority,
            size=size
        )
        
        self.environment.add_task(task, location)
        return task.task_id
    
    async def health_check(self) -> Dict[str, Any]:
        """执行系统健康检查"""
        status = self.get_system_status()
        
        health_status = {
            "overall": "healthy",
            "issues": [],
            "recommendations": [],
            "metrics": self.metrics.get_summary()
        }
        
        # 检查代理健康
        unhealthy_agents = [aid for aid, agent in self.environment.agents.items() 
                          if agent.health < 0.5]
        if unhealthy_agents:
            health_status["issues"].append(f"{len(unhealthy_agents)} 个不健康代理")
            health_status["recommendations"].append("考虑重新平衡资源")
        
        # 检查任务积压
        pending_tasks = status["tasks_pending"]
        if pending_tasks > 10:
            health_status["issues"].append(f"{pending_tasks} 个待处理任务")
            health_status["recommendations"].append("添加更多计算代理")
        
        # 检查系统健康
        if status["system_health"] < 0.6:
            health_status["issues"].append(f"系统健康度低: {status['system_health']:.2f}")
            health_status["recommendations"].append("调查资源分布")
        
        # 检查信号队列
        if status["current_signals_queued"] > 50:
            health_status["issues"].append(f"信号队列过长: {status['current_signals_queued']}")
            health_status["recommendations"].append("优化通信范围或代理密度")
            
        if health_status["issues"]:
            health_status["overall"] = "degraded"
        if status["system_health"] < 0.3:
            health_status["overall"] = "critical"
            
        return health_status
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取当前系统状态"""
        return self.environment.get_system_status()
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取特定代理的状态"""
        if agent_id in self.environment.agents:
            return self.environment.agents[agent_id].get_status()
        return None
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取特定任务的状态"""
        if task_id in self.environment.tasks:
            task = self.environment.tasks[task_id]
            return {
                "task_id": task.task_id,
                "type": task.task_type.value,
                "priority": task.priority,
                "size": task.size,
                "status": task.status,
                "progress": getattr(task, 'current_progress', 0.0),
                "assigned_agent": task.assigned_agent
            }
        return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        return self.metrics.history
    
    def save_state(self, filename: str):
        """保存系统状态到文件"""
        state = {
            "config": {
                "environment": self.config.environment.__dict__,
                "agents": self.config.agents.__dict__,
                "simulation": self.config.simulation
            },
            "status": self.get_system_status(),
            "metrics": self.metrics.get_summary()
        }
        
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"系统状态已保存到 {filename}")

async def demo_phytonet():
    """演示PhytoNet系统运行"""
    logger.info("启动PhytoNet演示")
    
    # 创建配置
    config = SystemConfig()
    config.environment.size = [8.0, 8.0]
    config.agents.initial_count = 15
    config.agents.max_count = 50
    
    # 创建并启动系统
    controller = PhytoNetController(config)
    await controller.start()
    
    # 提交一些初始任务
    logger.info("提交初始任务...")
    for i in range(5):
        task_type = random.choice(list(TaskType))
        task_id = await controller.submit_task(
            task_type=task_type,
            priority=random.uniform(0.5, 2.0),
            size=random.uniform(0.5, 2.0)
        )
        logger.debug(f"已提交任务 {task_id}")
        await asyncio.sleep(0.2)
    
    # 让系统运行一段时间
    logger.info("让系统运行30秒...")
    await asyncio.sleep(30)
    
    # 检查系统健康
    health = await controller.health_check()
    status = controller.get_system_status()
    
    logger.info("=== 演示结果 ===")
    logger.info(f"最终系统状态:")
    logger.info(f"  步数: {status['step']}")
    logger.info(f"  代理: {status['agents_total']}")
    logger.info(f"  完成任务: {status['tasks_completed']}")
    logger.info(f"  失败任务: {status['tasks_failed']}")
    logger.info(f"  系统健康度: {status['system_health']:.2f}")
    logger.info(f"  系统负载: {status['system_load']:.2f}")
    logger.info(f"  处理的信号: {status['total_signals_processed']}")
    logger.info(f"  整体健康: {health['overall']}")
    
    if health['issues']:
        logger.info("  发现问题:")
        for issue in health['issues']:
            logger.info(f"    - {issue}")
    
    # 保存状态
    controller.save_state("phytonet_demo_state.json")
    
    # 停止系统
    await controller.stop()
    logger.info("PhytoNet演示完成")

async def advanced_demo():
    """高级演示展示系统弹性"""
    logger.info("启动高级PhytoNet演示")
    
    config = SystemConfig()
    config.environment.size = [12.0, 12.0]
    config.agents.initial_count = 20
    config.agents.max_count = 80
    
    controller = PhytoNetController(config)
    await controller.start()
    
    # 阶段1: 正常操作
    logger.info("阶段1: 正常操作")
    for i in range(15):
        await controller.submit_task(
            task_type=random.choice(list(TaskType)),
            priority=1.0,
            size=1.0
        )
    await asyncio.sleep(20)
    
    # 阶段2: 高负载
    logger.info("阶段2: 高负载压力测试")
    for i in range(40):
        await controller.submit_task(
            task_type=TaskType.COMPUTE_INTENSIVE,
            priority=2.0,
            size=2.5
        )
    await asyncio.sleep(25)
    
    # 阶段3: 恢复
    logger.info("阶段3: 恢复阶段")
    await asyncio.sleep(15)
    
    # 最终评估
    health = await controller.health_check()
    status = controller.get_system_status()
    metrics = controller.get_metrics()
    
    logger.info("=== 高级演示结果 ===")
    logger.info(f"总步数: {status['step']}")
    logger.info(f"最终代理: {status['agents_total']}")
    logger.info(f"完成任务: {status['tasks_completed']}")
    success_rate = status['tasks_completed'] / max(1, status['tasks_completed'] + status['tasks_failed'])
    logger.info(f"成功率: {success_rate:.1%}")
    logger.info(f"系统弹性: {health['overall']}")
    
    # 保存状态
    controller.save_state("phytonet_advanced_demo_state.json")
    
    await controller.stop()
    logger.info("高级演示完成")

def main():
    """带命令行接口的主入口点"""
    parser = argparse.ArgumentParser(description='PhytoNet - 植物智能分布式网络系统')
    parser.add_argument('--demo', action='store_true', help='运行基础演示')
    parser.add_argument('--advanced', action='store_true', help='运行高级演示')
    parser.add_argument('--duration', type=int, default=60, help='运行时长(秒)')
    parser.add_argument('--verbose', action='store_true', help='详细日志输出')
    parser.add_argument('--size', type=float, nargs=2, default=[10.0, 10.0], 
                       help='环境尺寸 (默认: 10.0 10.0)')
    parser.add_argument('--agents', type=int, default=20, help='初始代理数量')
    parser.add_argument('--save-state', type=str, help='保存状态到文件')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.advanced:
        asyncio.run(advanced_demo())
    elif args.demo:
        asyncio.run(demo_phytonet())
    else:
        print("PhytoNet - 植物智能分布式网络系统")
        print("使用 --demo 运行演示或 --advanced 运行高级测试")
        print("使用 --help 查看所有选项")

if __name__ == "__main__":
    main()