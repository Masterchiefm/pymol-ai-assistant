# -*- coding: utf-8 -*-
'''
AI客户端模块 - 使用OpenAI Python SDK，支持流式输出和工具调用
'''

import json
import re
from openai import OpenAI
from . import config, tools, logger


class AIClient:
    """AI客户端 - 基于OpenAI SDK"""

    def __init__(self):
        self.client = None
        self.is_reasoning_model = False

    def set_config(self, api_config):
        """设置API配置"""
        self.api_url = api_config.get('api_url', '')
        self.api_key = api_config.get('api_key', '')
        self.model = api_config.get('model', '')
        self.is_reasoning_model = api_config.get('is_reasoning_model', False)

        # 初始化OpenAI客户端
        if self.api_url and self.api_key:
            self.client = OpenAI(
                base_url=self.api_url,
                api_key=self.api_key,
                timeout=120.0
            )

    def _get_system_prompt(self):
        """获取系统提示词"""
        return """你是一个PyMOL分子可视化助手。你可以使用提供的工具来控制PyMOL软件。

【重要原则】
- 请使用与用户相同的语言进行回答（用户用中文就用中文，用户用英文就用英文）- 这是最重要的规则，必须严格遵守
- 执行大量简单重复任务时，尽量采用运行脚本的形式（使用 pymol_do_command 或 pymol_run_pml 工具），这样可以提高效率
- 完成用户明确要求的需求后，立即停止，不要擅自给出额外建议或提示，用户知道自己要做什么

【可用工具】
结构加载：
- pymol_fetch: 从 PDB 数据库下载并加载分子结构（支持 PDB ID 如 1ake）
- pymol_load: 从本地文件加载分子结构（支持 PDB、mmCIF、MOL2 等格式）
- pymol_run_script: 执行 Python 脚本文件（.py 或 .pym）
- pymol_run_pml: 执行 PyMOL 脚本文件（.pml）
- pymol_do_command: 执行一个或多个 PyMOL 命令（适合快速执行简单命令或批量操作）

信息查询：
- pymol_get_info: 获取当前加载分子的基本信息（原子数、对象列表、链列表）
- pymol_get_selection_details: 获取选择集的详细信息（残基名称、编号、链、原子数等）
- pymol_get_atom_info: 获取单个或多个原子的详细信息（原子名、元素、残基、链、B因子、坐标等）
- pymol_get_residue_info: 获取残基的详细信息（残基名、残基号、链、二级结构、原子数等）
- pymol_get_chain_info: 获取链的详细信息（链标识、残基范围、原子数等）
- pymol_get_object_info: 获取对象的详细信息（对象名、状态数、原子数、残基数、链等）
- pymol_get_distance: 计算两个选择之间的距离（埃）
- pymol_get_angle: 计算三个原子之间的角度（度）
- pymol_get_dihedral: 计算四个原子之间的二面角（度）
- pymol_find_contacts: 查找两个选择之间的原子接触（距离小于指定阈值）

显示与样式：
- pymol_show: 显示指定表示形式（lines, sticks, spheres, surface, mesh, ribbon, cartoon, dots, labels, nonbonded）
- pymol_hide: 隐藏指定表示形式或所有表示
- pymol_color: 设置选择区域的颜色（支持 rainbow, by_element, by_chain, by_ss, by_resi, by_b 等特殊颜色）
- pymol_bg_color: 设置背景颜色
- pymol_label: 为原子添加标签（支持 %s 残基名, %i 残基号, %n 原子名, %a 元素, %chain 链, %b B-factor 等占位符）

视图操作：
- pymol_zoom: 缩放视图到指定选择
- pymol_rotate: 旋转视图或选择（支持 x, y, z 轴）
- pymol_center: 将视图中心移动到指定选择
- pymol_reset: 重置视图到默认状态

其他操作：
- pymol_select: 创建命名的选择集（支持 chain A, resi 1-100, name CA, resn ASP, elem C 等表达式）
- pymol_set: 设置 PyMOL 参数（如 ray_shadows, cartoon_cylindrical_helices, bg_gradient, transparency 等）
- pymol_ray: 使用光线追踪渲染高质量图像
- pymol_png: 保存当前视图为 PNG 图像
- pymol_remove: 删除对象或选择集

【工作流程】
1. 理解用户需求，思考需要执行哪些步骤
2. 调用相应的工具获取信息或执行操作
3. 根据工具返回的结果决定下一步操作
4. 批量或重复性任务优先使用 pymol_do_command 一次性执行多个命令，或者使用 pymol_run_pml 运行脚本

【重要提示】
1. 操作前先思考整体方案
2. 可以调用多个工具来完成复杂任务
3. 调用工具后等待结果再继续
4. 如果操作失败，尝试其他方法
5. 如果用户询问关于分子结构的问题但没有明确提供PDB ID或文件路径，默认假设结构已经加载到PyMOL中，直接使用pymol_get_info等工具查询当前加载的结构，而不是尝试加载新结构
6. 选择表达式语法示例：chain A, resi 1-100, name CA, resn ASP, elem C, chain A and resi 50, /1abc//A/50/CA
"""

    def _parse_tool_calls_from_content(self, content):
        """
        从内容中解析工具调用（处理某些模型将工具调用输出到content中的情况）
        支持格式：<|tool_calls_section_begin|><|tool_call_begin|>functions.xxx:id<|tool_call_argument_begin|>{...}<|tool_call_end|><|tool_calls_section_end|>
        """
        tool_calls = []

        # 匹配工具调用格式
        pattern = r'<\|tool_call_begin\|>([^<]+)<\|tool_call_argument_begin\|>(\{[^}]*\})<\|tool_call_end\|>'
        matches = re.findall(pattern, content)

        for match in matches:
            func_full_name = match[0].strip()
            arguments_str = match[1]

            # 解析函数名和ID
            # 格式可能是: functions.tool_name:id 或 tool_name:id
            if ':' in func_full_name:
                func_part, call_id = func_full_name.rsplit(':', 1)
            else:
                func_part = func_full_name
                call_id = '0'

            # 移除 'functions.' 前缀
            if func_part.startswith('functions.'):
                tool_name = func_part[10:]
            else:
                tool_name = func_part

            tool_calls.append({
                'id': call_id,
                'type': 'function',
                'function': {
                    'name': tool_name,
                    'arguments': arguments_str
                }
            })

        return tool_calls

    def chat_stream(self, messages, on_thinking=None, on_content=None, on_tool_call=None, on_error=None):
        """
        流式聊天

        Args:
            messages: 消息列表
            on_thinking: 思考内容回调
            on_content: 内容回调
            on_tool_call: 工具调用回调
            on_error: 错误回调

        Returns:
            generator: 流式生成器
        """
        # 检查配置
        if not self.client or not self.model:
            if on_error:
                on_error("API配置不完整")
            return

        # 检查是否是工具调用后的跟进请求（包含tool角色的消息）
        has_tool_messages = any(msg.get('role') == 'tool' for msg in messages)

        # 准备请求参数
        request_params = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': self._get_system_prompt()}
            ] + messages,
            'stream': True
        }

        # 只有在非工具跟进请求时才添加tools参数
        if not has_tool_messages:
            request_params['tools'] = tools.TOOLS

        # 记录请求
        logger.logger.debug(
            logger.AI_REQUEST,
            "发送AI请求",
            {"model": self.model, "messages": messages}
        )

        try:
            # 使用OpenAI SDK创建流式请求
            stream = self.client.chat.completions.create(**request_params)

            # 用于累积tool_calls
            tool_calls_buffer = {}
            content_buffer = ""
            thinking_buffer = ""
            is_thinking = False
            has_standard_tool_calls = False

            for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None

                if not delta:
                    continue

                # 处理思考内容（适用于支持reasoning的模型）
                if self.is_reasoning_model:
                    reasoning = getattr(delta, 'reasoning_content', None) or getattr(delta, 'reasoning', None)
                    if reasoning:
                        if not is_thinking:
                            is_thinking = True
                            thinking_buffer = ""
                        thinking_buffer += reasoning
                        if on_thinking:
                            on_thinking(reasoning, False)

                # 处理普通内容
                content = delta.content or ''
                if content:
                    # 如果之前有思考内容，标记思考结束
                    if is_thinking and thinking_buffer:
                        is_thinking = False
                        if on_thinking:
                            on_thinking("", True)

                    content_buffer += content
                    if on_content:
                        on_content(content, False)

                # 处理标准工具调用（OpenAI格式）
                tool_calls = delta.tool_calls
                if tool_calls:
                    has_standard_tool_calls = True
                    for tc in tool_calls:
                        index = tc.index if tc.index is not None else 0
                        if index not in tool_calls_buffer:
                            tool_calls_buffer[index] = {
                                'id': tc.id or '',
                                'type': tc.type or 'function',
                                'function': {'name': '', 'arguments': ''}
                            }

                        if tc.function:
                            if tc.function.name:
                                tool_calls_buffer[index]['function']['name'] += tc.function.name
                            if tc.function.arguments:
                                tool_calls_buffer[index]['function']['arguments'] += tc.function.arguments

                yield chunk

            # 标记内容结束
            if on_content:
                on_content("", True)
            if on_thinking:
                on_thinking("", True)

            # 如果没有标准工具调用，尝试从内容中解析（某些模型的特殊格式）
            if not has_standard_tool_calls and content_buffer:
                parsed_tool_calls = self._parse_tool_calls_from_content(content_buffer)
                if parsed_tool_calls:
                    for i, tc in enumerate(parsed_tool_calls):
                        tool_calls_buffer[i] = tc

            # 执行工具调用
            if tool_calls_buffer:
                for tc in tool_calls_buffer.values():
                    func = tc['function']
                    tool_name = func.get('name', '')
                    arguments = func.get('arguments', '{}')

                    if on_tool_call:
                        on_tool_call(tool_name, arguments, None)

                    # 执行工具
                    try:
                        params = json.loads(arguments) if arguments else {}
                    except:
                        params = {}

                    result = tools.tool_executor.execute(tool_name, params)

                    # 记录工具调用
                    logger.logger.info(
                        logger.TOOL_CALL,
                        "工具执行: %s" % tool_name,
                        {
                            "tool": tool_name,
                            "params": params,
                            "result": result
                        }
                    )

                    if on_tool_call:
                        on_tool_call(tool_name, arguments, result)

                    # 将工具结果返回给AI继续对话
                    assistant_msg = {
                        'role': 'assistant',
                        'content': content_buffer,
                        'tool_calls': [{'id': tc.get('id', ''), 'type': 'function', 'function': {'name': tool_name, 'arguments': arguments}}]
                    }
                    # 如果是reasoning模型，添加reasoning_content字段
                    if self.is_reasoning_model:
                        assistant_msg['reasoning_content'] = thinking_buffer if thinking_buffer else ''

                    follow_up_messages = messages + [
                        assistant_msg,
                        {'role': 'tool', 'tool_call_id': tc.get('id', ''), 'content': json.dumps(result)}
                    ]

                    # 递归调用获取AI对工具结果的响应
                    for item in self.chat_stream(
                        follow_up_messages,
                        on_thinking=on_thinking,
                        on_content=on_content,
                        on_tool_call=on_tool_call,
                        on_error=on_error
                    ):
                        yield item
                    return

        except Exception as e:
            error_msg = "AI请求错误: %s" % str(e)
            logger.logger.error(logger.ERRORS, error_msg)
            if on_error:
                on_error(error_msg)

    def test_connection(self):
        """测试连接"""
        try:
            if not self.client:
                return False, "客户端未初始化"

            # 使用 chat.completions.create 发送简单请求测试
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{'role': 'user', 'content': 'hi'}],
                max_tokens=5,
                stream=False
            )
            return True, "连接成功"
        except Exception as e:
            return False, str(e)


# 全局AI客户端实例
ai_client = AIClient()
