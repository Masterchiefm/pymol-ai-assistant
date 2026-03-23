# -*- coding: utf-8 -*-
'''
AI客户端模块 - 使用LiteLLM，非流式调用
LiteLLM提供统一的API接口，支持100+LLM提供商
'''

import hashlib
import json
import secrets
import string
from typing import Any

import json_repair
import litellm
litellm.drop_params = True
litellm.suppress_debug_info = True
litellm.set_verbose = False
litellm.cost_per_token = {}
from litellm import completion
from . import config, tools, logger

_ALNUM = string.ascii_letters + string.digits


def _short_tool_id() -> str:
    """Generate a 9-char alphanumeric ID compatible with all providers."""
    return "".join(secrets.choice(_ALNUM) for _ in range(9))


def _normalize_tool_call_id(tool_call_id: Any) -> Any:
    """Normalize tool_call_id to a provider-safe 9-char alphanumeric form."""
    if not isinstance(tool_call_id, str):
        return tool_call_id
    if len(tool_call_id) == 9 and tool_call_id.isalnum():
        return tool_call_id
    return hashlib.sha1(tool_call_id.encode()).hexdigest()[:9]


class AIClient:
    """AI客户端 - 基于LiteLLM，非流式调用"""

    def __init__(self):
        self.provider = None
        self.api_url = None
        self.api_key = None
        self.model = None
        self.api_version = None
        self.is_reasoning_model = False
        self.is_vision_model = False
        self.temperature = 0.7
        self.max_tokens = 4096
        self.timeout = 60
        self.max_iterations = 40

    def set_config(self, api_config):
        """设置API配置"""
        self.provider = api_config.get('provider', 'custom')
        self.api_url = api_config.get('api_url', '')
        self.api_key = api_config.get('api_key', '')
        self.model = api_config.get('model', '')
        self.api_version = api_config.get('api_version', '')
        self.is_reasoning_model = api_config.get('is_reasoning_model', False)
        self.is_vision_model = api_config.get('is_vision_model', False)
        self.temperature = api_config.get('temperature', 0.7)
        self.max_tokens = api_config.get('max_tokens', 4096)
        self.timeout = api_config.get('timeout', 60)

    def _get_model_name(self):
        """获取LiteLLM格式的模型名称"""
        if not self.model:
            return None
        
        provider_info = config.get_provider_info(self.provider)
        prefix = provider_info.get('prefix', 'openai/')
        
        if self.model.startswith(prefix):
            return self.model
        
        known_prefixes = ['openai/', 'azure/', 'anthropic/', 'gemini/', 
                          'ollama/', 'zhipu/', 'openrouter/', 'together_ai/',
                          'huggingface/', 'bedrock/', 'vertex_ai/', 'groq/']
        for known_prefix in known_prefixes:
            if self.model.startswith(known_prefix):
                return self.model
        
        return f"{prefix}{self.model}"

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
- pymol_capture_view: 捕获当前PyMOL视图的截图（仅视觉模型可用，让你能够看到实际的画面效果）

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
7. 如果需要查看当前渲染效果，可以使用 pymol_capture_view 工具捕获截图，这样可以直观地看到画面的实际效果
"""

    def _sanitize_messages(self, messages: list[dict]) -> list[dict]:
        """清理消息格式，标准化 tool_call_id"""
        id_map: dict[str, str] = {}
        
        def map_id(value: Any) -> Any:
            if not isinstance(value, str):
                return value
            return id_map.setdefault(value, _normalize_tool_call_id(value))
        
        sanitized = []
        for msg in messages:
            clean = dict(msg)
            
            if isinstance(clean.get("tool_calls"), list):
                normalized_tool_calls = []
                for tc in clean["tool_calls"]:
                    if not isinstance(tc, dict):
                        normalized_tool_calls.append(tc)
                        continue
                    tc_clean = dict(tc)
                    tc_clean["id"] = map_id(tc_clean.get("id"))
                    normalized_tool_calls.append(tc_clean)
                clean["tool_calls"] = normalized_tool_calls
            
            if "tool_call_id" in clean and clean["tool_call_id"]:
                clean["tool_call_id"] = map_id(clean["tool_call_id"])
            
            sanitized.append(clean)
        
        return sanitized

    def _chat(self, messages: list[dict], use_tools: bool = True, images=None) -> dict:
        """
        发送非流式聊天请求
        
        Returns:
            dict: {
                'content': str,
                'tool_calls': list,
                'reasoning_content': str,
                'finish_reason': str
            }
        """
        model_name = self._get_model_name()
        
        # 处理视觉模型的图片输入
        if images and self.is_vision_model:
            # 修改最后一条用户消息以包含图片
            processed_messages = self._process_vision_messages(messages, images)
        else:
            processed_messages = self._sanitize_messages(messages)
        
        request_params = {
            'model': model_name,
            'messages': processed_messages,
            'temperature': self.temperature,
            'max_tokens': max(1, self.max_tokens),
            'timeout': self.timeout,
        }

        if self.api_key:
            request_params['api_key'] = self.api_key

        if self.api_url:
            request_params['api_base'] = self.api_url

        if self.provider == 'azure' and self.api_version:
            request_params['api_version'] = self.api_version

        # 工具调用：普通模型和视觉模型都支持工具调用
        if use_tools:
            request_params['tools'] = tools.TOOLS
            request_params['tool_choice'] = 'auto'

        logger.logger.debug(
            logger.AI_REQUEST,
            "发送AI请求",
            {"provider": self.provider, "model": self.model, "has_images": bool(images)}
        )

        response = completion(**request_params)
        return self._parse_response(response)
    
    def _process_vision_messages(self, messages: list[dict], images: list) -> list:
        """
        处理视觉模型的消息格式
        
        Args:
            messages: 原始消息列表
            images: 图片数据列表
            
        Returns:
            list: 处理后的消息列表，最后一条用户消息包含图片
        """
        processed = []
        import base64
        
        for msg in messages:
            processed_msg = dict(msg)
            
            # 如果是最后一条用户消息且有图片，转换格式
            if msg.get('role') == 'user' and images:
                content_list = []
                
                # 添加文本内容
                if msg.get('content'):
                    content_list.append({
                        "type": "text",
                        "text": msg.get('content')
                    })
                
                # 添加图片
                for img_data in images:
                    # 将图片数据转换为base64
                    img_bytes = img_data.get('data')
                    if img_bytes:
                        # img_bytes 现在是 bytes 类型，直接编码为 base64
                        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                        
                        content_list.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}"
                            }
                        })
                
                if content_list:
                    processed_msg['content'] = content_list
            
            # 处理工具返回的图片（pymol_capture_view）
            # 工具消息的content必须是字符串，所以我们需要在工具消息后添加一个用户消息来传递图片
            elif msg.get('role') == 'tool' and msg.get('content'):
                try:
                    content = msg.get('content')
                    if isinstance(content, str):
                        try:
                            tool_result = json.loads(content)
                            if tool_result.get('has_image') and tool_result.get('image_url'):
                                # 先添加工具消息（字符串格式）
                                processed_msg['content'] = tool_result.get('message', '截图成功')
                                processed.append(processed_msg)
                                # 然后添加一个用户消息包含图片
                                processed.append({
                                    'role': 'user',
                                    'content': [
                                        {
                                            "type": "text",
                                            "text": "这是刚才捕获的PyMOL视图截图："
                                        },
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": tool_result.get('image_url')
                                            }
                                        }
                                    ]
                                })
                                continue
                        except json.JSONDecodeError:
                            pass
                except:
                    pass
            
            processed.append(processed_msg)
        
        return self._sanitize_messages(processed)

    def _parse_response(self, response) -> dict:
        """解析 LiteLLM 响应"""
        choice = response.choices[0]
        message = choice.message
        content = message.content or ""
        finish_reason = choice.finish_reason or "stop"

        raw_tool_calls = []
        for ch in response.choices:
            msg = ch.message
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                raw_tool_calls.extend(msg.tool_calls)
            if not content and msg.content:
                content = msg.content

        tool_calls = []
        for tc in raw_tool_calls:
            args = tc.function.arguments
            if isinstance(args, str):
                args = json_repair.loads(args)
            
            tool_calls.append({
                'id': _short_tool_id(),
                'name': tc.function.name,
                'arguments': args,
            })

        reasoning_content = getattr(message, "reasoning_content", None) or None

        return {
            'content': content,
            'tool_calls': tool_calls,
            'reasoning_content': reasoning_content,
            'finish_reason': finish_reason,
        }

    def chat(
        self,
        messages: list[dict],
        on_thinking=None,
        on_content=None,
        on_tool_call=None,
        on_error=None,
        images=None,
    ) -> str:
        """
        非流式聊天，支持多轮工具调用

        Args:
            messages: 消息列表
            on_thinking: 思考内容回调
            on_content: 内容回调
            on_tool_call: 工具调用回调
            on_error: 错误回调
            images: 图片列表（仅视觉模型支持）

        Returns:
            str: 最终响应内容
        """
        provider_info = config.get_provider_info(self.provider)
        requires_key = provider_info.get('requires_api_key', True)
        
        if not self.model:
            if on_error:
                on_error("请选择模型")
            return ""
        
        if requires_key and not self.api_key:
            if on_error:
                on_error("请输入 API Key")
            return ""

        full_messages = [
            {'role': 'system', 'content': self._get_system_prompt()}
        ] + messages

        iteration = 0
        final_content = ""

        while iteration < self.max_iterations:
            iteration += 1

            try:
                # 如果是视觉模型，处理消息中的图片
                if self.is_vision_model:
                    processed_full_messages = self._process_vision_messages(full_messages, images)
                else:
                    processed_full_messages = self._sanitize_messages(full_messages)
                
                response = self._chat(processed_full_messages, use_tools=True)
            except litellm.AuthenticationError as e:
                error_msg = "API认证失败: %s" % str(e)
                logger.logger.error(logger.ERRORS, error_msg)
                if on_error:
                    on_error(error_msg)
                return ""
            except litellm.RateLimitError as e:
                error_msg = "API速率限制: %s" % str(e)
                logger.logger.error(logger.ERRORS, error_msg)
                if on_error:
                    on_error(error_msg)
                return ""
            except litellm.APIError as e:
                error_msg = "API错误: %s" % str(e)
                logger.logger.error(logger.ERRORS, error_msg)
                if on_error:
                    on_error(error_msg)
                return ""
            except Exception as e:
                error_msg = "AI请求错误: %s" % str(e)
                logger.logger.error(logger.ERRORS, error_msg)
                if on_error:
                    on_error(error_msg)
                return ""

            content = response['content'] or ""
            tool_calls = response['tool_calls']
            reasoning_content = response['reasoning_content']

            if reasoning_content and on_thinking:
                on_thinking(reasoning_content, True)

            if content and on_content:
                on_content(content, True)

            if not tool_calls:
                final_content = content
                break

            tool_call_dicts = []
            for tc in tool_calls:
                tool_call_dicts.append({
                    'id': tc['id'],
                    'type': 'function',
                    'function': {
                        'name': tc['name'],
                        'arguments': json.dumps(tc['arguments'], ensure_ascii=False),
                    }
                })

            assistant_msg = {
                'role': 'assistant',
                'content': content,
                'tool_calls': tool_call_dicts,
            }
            if reasoning_content:
                assistant_msg['reasoning_content'] = reasoning_content
            
            full_messages.append(assistant_msg)

            for tc in tool_calls:
                tool_name = tc['name']
                params = tc['arguments']
                arguments_str = json.dumps(params, ensure_ascii=False)

                if on_tool_call:
                    on_tool_call(tool_name, arguments_str, None)

                result = tools.tool_executor.execute(tool_name, params)

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
                    on_tool_call(tool_name, arguments_str, result)

                tool_response_content = result.get('message', '')
                
                if tool_name == 'pymol_capture_view' and result.get('success') and result.get('image_data'):
                    image_base64 = result.get('image_data')
                    tool_response_content = json.dumps({
                        'message': result.get('message'),
                        'has_image': True,
                        'image_url': f'data:image/png;base64,{image_base64}',
                        'width': result.get('width'),
                        'height': result.get('height')
                    }, ensure_ascii=False)
                elif result.get('output'):
                    tool_response_content = result.get('output')
                elif result.get('data'):
                    tool_response_content = json.dumps(result.get('data'), ensure_ascii=False)
                elif not tool_response_content:
                    tool_response_content = json.dumps(result, ensure_ascii=False)

                full_messages.append({
                    'role': 'tool',
                    'tool_call_id': tc['id'],
                    'content': tool_response_content,
                })

        if iteration >= self.max_iterations and not final_content:
            final_content = "已达到最大迭代次数 (%d)，任务可能未完成。" % self.max_iterations

        return final_content

    def test_connection(self):
        """测试连接"""
        try:
            provider_info = config.get_provider_info(self.provider)
            requires_key = provider_info.get('requires_api_key', True)
            
            if not self.model:
                return False, "请选择模型"
            
            if requires_key and not self.api_key:
                return False, "请输入 API Key"

            model_name = self._get_model_name()
            
            request_params = {
                'model': model_name,
                'messages': [{'role': 'user', 'content': 'hi'}],
                'max_tokens': 5,
                'timeout': 30,
            }
            
            if self.api_key:
                request_params['api_key'] = self.api_key
            
            if self.api_url:
                request_params['api_base'] = self.api_url
            
            if self.provider == 'azure' and self.api_version:
                request_params['api_version'] = self.api_version
            
            response = completion(**request_params)
            return True, "连接成功"
        except litellm.AuthenticationError as e:
            return False, "认证失败: %s" % str(e)
        except litellm.RateLimitError as e:
            return False, "速率限制: %s" % str(e)
        except litellm.APIError as e:
            return False, "API错误: %s" % str(e)
        except Exception as e:
            return False, str(e)


ai_client = AIClient()
