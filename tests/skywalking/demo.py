import time
import logging
import json
import os

from dotenv import load_dotenv
load_dotenv()


from bdp_api.bdp_logger import logger as bdp_logger
from bdp_api.decorators import logtime
from skywalking.trace.context import get_context
from skywalking import config, agent
from skywalking.decorators import trace
import urllib3


# # 假设有以下环境变量
# JOB_NAME="calculate-acceleration"
# PROJECT_NAME="public"
# LOG_SERVICE_ADDR=http://10.66.12.37:31667/logs
# SCENE_SERVICE_ADDR=http://10.66.12.37:31667/scene-processes
#
# SW_AGENT_NAME=your-service-name
# SW_AGENT_COLLECTOR_BACKEND_SERVICES=10.66.12.37:31811
# SW_AGENT_LOG_REPORTER_ACTIVE=True
# SW_AGENT_LOG_REPORTER_LEVEL=INFO
# SW_AGENT_LOGGING_LEVEL=INFO
# SW_AGENT_SW_PYTHON_BOOTSTRAP_PROPAGATE=False
#
# SW_AGENT_INSTANCE_NAME=your-instance-name

# 定义配置字典
env_config = {
    "project_name": os.getenv('PROJECT_NAME'),
    "job_name": os.getenv('JOB_NAME'),
    "log_service_addr": os.getenv('LOG_SERVICE_ADDR'),
    "scene_service_addr": os.getenv('SCENE_SERVICE_ADDR'),
    "sw_agent_collector_backend_services": os.getenv('SW_AGENT_COLLECTOR_BACKEND_SERVICES', '127.0.0.1:11800'),
}

# 从环境变量加载配置
skywalking_backend = env_config.get("sw_agent_collector_backend_services")
config.init(agent_collector_backend_services=skywalking_backend)
agent.start()


def bind_trace(taskid):
    try:
        context = get_context()
        trace_id = context.segment.related_traces[0].value

        print("创建的trace_id:", trace_id)
        logging.getLogger('bdpLogger').info("trace_id: %s" % trace_id)

        arg = {
            "task_id": taskid,
            "trace_id": trace_id,
            "project_name": env_config.get("project_name"),
            "job_name": env_config.get("job_name"),
        }

        urllib3.PoolManager().request(
            "POST",
            env_config.get("log_service_addr"),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            body=json.dumps(arg),
        )
    except Exception as e:
        logging.warning("exception happens in bind_trace[%s]: %s" % (taskid, str(e)))


def report_state(taskid, state):
    try:
        s = "%s_%s" % (state, taskid)
        arg = {
            "phase": s,
            "status": state,
            "task_id": taskid,
        }

        urllib3.PoolManager().request(
            "PATCH",
            env_config.get("scene_service_addr"),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            body=json.dumps(arg),
        )
    except Exception as e:
        logging.warning("exception happens in report_state[%s]: %s" % (taskid, str(e)))


@trace()
@logtime
def flink_job_execute(inputMessage):
    taskid = inputMessage.get("taskid")

    # 创建任务日志trace
    bind_trace(taskid)
    # 更新任务状态为开始
    report_state(taskid, "begin")

    # 模拟执行任务
    time.sleep(10)

    # 更新任务状态为结束
    report_state(taskid, "end")


if __name__ == "__main__":
    inputMessage = {
        "taskid": "9cf99967-aa69-44cd-b4f2-d22d886817fb",
    }
    flink_job_execute(inputMessage)
