# -*- coding: utf-8 -*-
'''
AI客户端模块 - 支持流式输出和工具调用
'''

import json
import threading
import requests
from . import config, tools, logger


class AIClient:
    """AI客户端"""
    
    def __init__(self):
        self.session = requests.Session()
        self.is_reasoning_model = False
    
    def set_config(self, api_config):
        """设置API配置"""
        self.api_url = api_config.get('api_url', '')
        self.api_key = api_config.get('api_key', '')
        self.model = api_config.get('model', '')
        self.is_reasoning_model = api_config.get('is_reasoning_model', False)
    
    def _get_headers(self):
        """获取请求头"""
        return {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.api_key)
        }
    
    def _get_system_prompt(self):
        """获取系统提示词"""
        return """你是一个PyMOL分子可视化助手。你可以使用提供的工具来控制PyMOL软件。

可用的工具包括：
- pymol_load: 加载分子结构（PDB ID或文件）
- pymol_select: 创建选择集
- pymol_color: 设置颜色
- pymol_show: 设置显示样式（lines, sticks, spheres, surface, ribbon, cartoon等）
- pymol_hide: 隐藏显示样式
- pymol_zoom: 缩放视图
- pymol_orient: 定向视图
- pymol_reset: 重置视图
- pymol_set: 设置参数
- pymol_get_info: 获取分子信息
- pymol_distance: 测量距离
- pymol_delete: 删除对象
- pymol_save: 保存文件
- pymol_label: 添加标签

请根据用户的请求，思考需要执行哪些步骤，然后调用相应的工具。
每次调用工具后，你会收到执行结果，然后根据结果决定下一步操作。

重要提示：
1. 操作前先思考整体方案
2. 可以调用多个工具来完成复杂任务
3. 调用工具后等待结果再继续
4. 如果操作失败，尝试其他方法
5. 如果用户询问关于分子结构的问题但没有明确提供PDB ID或文件路径，默认假设结构已经加载到PyMOL中，直接使用pymol_get_info等工具查询当前加载的结构，而不是尝试加载新结构
"""
    
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
        if not self.api_url or not self.api_key or not self.model:
            if on_error:
                on_error("API配置不完整")
            return
        
        # 准备请求数据
        data = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': self._get_system_prompt()}
            ] + messages,
            'stream': True,
            'tools': tools.TOOLS,
            'tool_choice': 'auto'
        }
        
        # 记录请求
        logger.logger.debug(
            logger.AI_REQUEST,
            "发送AI请求",
            {"model": self.model, "messages": messages}
        )
        
        try:
            response = self.session.post(
                self.api_url + '/chat/completions',
                headers=self._get_headers(),
                json=data,
                stream=True,
                timeout=120
            )
            response.raise_for_status()
            
            # 用于累积tool_calls
            tool_calls_buffer = {}
            content_buffer = ""
            thinking_buffer = ""
            is_thinking = False
            
            for line in response.iter_lines():
                if not line:
                    continue
                
                line = line.decode('utf-8')
                
                # 处理SSE格式
                if line.startswith('data: '):
                    line = line[6:]
                
                if line == '[DONE]':
                    break
                
                try:
                    chunk = json.loads(line)
                    delta = chunk.get('choices', [{}])[0].get('delta', {})
                    
                    # 处理思考内容（适用于支持reasoning的模型）
                    if self.is_reasoning_model:
                        reasoning = delta.get('reasoning_content') or delta.get('reasoning')
                        if reasoning:
                            if not is_thinking:
                                is_thinking = True
                                thinking_buffer = ""
                            thinking_buffer += reasoning
                            if on_thinking:
                                on_thinking(reasoning, False)
                    
                    # 处理普通内容
                    content = delta.get('content', '')
                    if content:
                        # 如果之前有思考内容，标记思考结束
                        if is_thinking and thinking_buffer:
                            is_thinking = False
                            if on_thinking:
                                on_thinking("", True)  # 标记思考结束
                        
                        content_buffer += content
                        if on_content:
                            on_content(content, False)
                    
                    # 处理工具调用
                    tool_calls = delta.get('tool_calls')
                    if tool_calls:
                        for tc in tool_calls:
                            index = tc.get('index', 0)
                            if index not in tool_calls_buffer:
                                tool_calls_buffer[index] = {
                                    'id': tc.get('id', ''),
                                    'type': tc.get('type', 'function'),
                                    'function': {'name': '', 'arguments': ''}
                                }
                            
                            if 'function' in tc:
                                func = tc['function']
                                if 'name' in func:
                                    tool_calls_buffer[index]['function']['name'] += func['name']
                                if 'arguments' in func:
                                    tool_calls_buffer[index]['function']['arguments'] += func['arguments']
                
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    if on_error:
                        on_error(str(e))
                    continue
            
            # 标记内容结束
            if on_content:
                on_content("", True)
            if on_thinking:
                on_thinking("", True)
            
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
                    
                    # 将工具结果返回给AI继续对话（无论成功还是失败）
                    follow_up_messages = messages + [
                        {'role': 'assistant', 'content': content_buffer, 'tool_calls': [{'id': tc.get('id', ''), 'type': 'function', 'function': {'name': tool_name, 'arguments': arguments}}]},
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
        
        except requests.exceptions.RequestException as e:
            error_msg = "网络请求错误: {}".format(str(e))
            logger.logger.error(logger.ERRORS, error_msg)
            if on_error:
                on_error(error_msg)
        except Exception as e:
            error_msg = "AI请求错误: {}".format(str(e))
            logger.logger.error(logger.ERRORS, error_msg)
            if on_error:
                on_error(error_msg)
    
    def test_connection(self):
        """测试连接"""
        try:
            # 使用 chat/completions 端点发送简单请求测试
            test_data = {
                'model': self.model,
                'messages': [{'role': 'user', 'content': 'hi'}],
                'max_tokens': 5,
                'stream': False
            }
            response = self.session.post(
                self.api_url + '/chat/completions',
                headers=self._get_headers(),
                json=test_data,
                timeout=30
            )
            response.raise_for_status()
            return True, "连接成功"
        except Exception as e:
            return False, str(e)


# 全局AI客户端实例
ai_client = AIClient()
