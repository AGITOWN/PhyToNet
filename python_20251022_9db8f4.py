from phytonet import PhytoNetController, TaskType, SystemConfig
import asyncio

async def main():
    controller = PhytoNetController()
    await controller.start()
    
    # 提交任务
    task_id = await controller.submit_task(
        task_type=TaskType.COMPUTE_INTENSIVE,
        priority=1.5,
        size=2.0
    )
    
    # 监控系统
    status = controller.get_system_status()
    health = await controller.health_check()
    
    await controller.stop()

asyncio.run(main())