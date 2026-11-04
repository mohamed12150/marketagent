"""
输入校验工具
防止路径遍历攻击：所有用于构建文件系统路径的外部输入（项目ID、模拟ID、
报告ID、平台名等）必须先经过本模块校验。

参见 Issue #306 / #488 / #489。
"""

import re

# 内部生成的ID形如 proj_xxxxxxxx / sim_xxxxxxxx / report_xxxxxxxx，
# 只允许字母、数字、下划线和连字符，且不能以符号开头，长度上限64。
SAFE_ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$')

# OASIS 仅支持的模拟平台
ALLOWED_PLATFORMS = ('twitter', 'reddit')


def is_safe_id(value) -> bool:
    """检查值是否为可安全用于文件路径的ID"""
    return isinstance(value, str) and bool(SAFE_ID_RE.match(value))


def ensure_safe_id(value, name: str = 'id') -> str:
    """校验ID，非法时抛出 ValueError

    Args:
        value: 待校验的ID
        name: 参数名（用于错误信息）

    Returns:
        原值（校验通过时）
    """
    if not is_safe_id(value):
        raise ValueError(f"非法的{name}: {value!r}")
    return value


def is_allowed_platform(value) -> bool:
    """检查平台名是否在白名单内"""
    return value in ALLOWED_PLATFORMS


def ensure_platform(value) -> str:
    """校验平台名，非法时抛出 ValueError"""
    if not is_allowed_platform(value):
        raise ValueError(f"不支持的平台: {value!r}")
    return value
