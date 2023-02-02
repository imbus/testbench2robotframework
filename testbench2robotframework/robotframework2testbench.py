import os
import sys
from typing import Dict

from robot.api import ExecutionResult

from .config import Configuration
from .log import logger, setup_logger
from .result_writer import ResultWriter


def robot2testbench(
    json_input_report: str,
    robot_result_xml: str,
    json_output_result: str = None,
    config: Dict = None,
):
    if not os.path.exists(json_input_report):
        sys.exit("Could not find json directory or zip file at the given path.")
    if not os.path.exists(robot_result_xml):
        sys.exit("Robot result xml does not exist at the given path.")
    configuration = Configuration.from_dict(config)
    setup_logger(configuration)
    logger.debug("Config file loaded.")
    result = ExecutionResult(robot_result_xml)
    logger.debug("Robot framework result xml loaded.")
    result.visit(
        ResultWriter(json_input_report, json_output_result, configuration, robot_result_xml)
    )
