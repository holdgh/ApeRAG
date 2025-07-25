# Anybase Integration Guide

本文档介绍如何配置和使用ApeRAG与Anybase的集成功能。

## 概述

Anybase集成允许Anybase用户无缝访问ApeRAG，无需单独注册账户。当Anybase用户跳转到ApeRAG时，系统会自动验证用户身份，创建或同步用户账户，并设置ApeRAG会话。

## 配置

### 环境变量

在`.env`文件中添加以下配置：

```bash
# 启用Anybase集成
ANYBASE_ENABLED=true

# Anybase API基础URL（不包含尾部斜杠）
ANYBASE_API_BASE_URL=https://your-anybase-domain.com

# Anybase登录页面URL，用于未认证用户的重定向
ANYBASE_LOGIN_URL=https://your-anybase-domain.com/login
```

## 认证流程

### 1. 自动用户同步

当Anybase用户首次访问ApeRAG时：

1. **Token验证**: ApeRAG接收到带有Anybase token的请求
2. **用户信息获取**: 调用Anybase的`/api/v1/user/me` API获取用户信息
3. **用户创建/同步**: 
   - 如果用户不存在，自动创建ApeRAG账户
   - 使用Anybase的`user_id`作为ApeRAG的`username`
   - 设置默认角色为`RO`（只读）
   - 自动创建默认的API Key和Bot
4. **会话建立**: 生成ApeRAG JWT token并设置session cookie

### 2. 认证方式

ApeRAG支持以下认证方式（按优先级排序）：

1. **ApeRAG Session Cookie**: 已登录用户的会话cookie
2. **Anybase Token**: Authorization header中的Bearer token
3. **ApeRAG API Key**: 用于API访问的Bearer token

## API端点

### GET /api/auth/user

获取当前用户信息，支持Anybase自动登录。

**请求示例**:
```bash
# 使用Anybase token
curl -H "Authorization: Bearer <anybase-token>" \
     https://aperag.example.com/api/auth/user
```

**响应**:
- 成功时返回用户信息并设置ApeRAG session cookie
- 失败时返回401，如果启用了Anybase集成，响应头会包含`X-Anybase-Login-URL`

### POST /api/auth/anybase-login

显式使用Anybase token登录。

**请求示例**:
```bash
curl -X POST \
     -H "Authorization: Bearer <anybase-token>" \
     https://aperag.example.com/api/auth/anybase-login
```

## 前端集成

### JavaScript示例

```javascript
// 检查localStorage中的Anybase token
const anybaseToken = localStorage.getItem('token');

if (anybaseToken) {
    // 使用Anybase token调用ApeRAG API
    fetch('/api/auth/user', {
        headers: {
            'Authorization': `Bearer ${anybaseToken}`
        }
    })
    .then(response => {
        if (response.status === 401) {
            // 检查是否需要重定向到Anybase登录
            const loginUrl = response.headers.get('X-Anybase-Login-URL');
            if (loginUrl) {
                window.location.href = loginUrl;
            }
        }
        return response.json();
    })
    .then(user => {
        console.log('User logged in:', user);
        // 后续请求会自动使用ApeRAG session cookie
    });
}
```

## 用户数据映射

| Anybase字段 | ApeRAG字段 | 说明 |
|-------------|------------|------|
| user_id | username | 用作唯一标识符 |
| email | email | 邮箱地址，如果为空则生成默认邮箱 |
| nickname | - | 暂不使用 |
| phone | - | 暂不使用 |

## 安全考虑

1. **Token验证**: 每次请求都会调用Anybase API验证token有效性
2. **用户权限**: Anybase用户默认获得只读权限
3. **会话管理**: ApeRAG会话独立于Anybase会话，可单独管理
4. **API超时**: Anybase API调用设置10秒超时

## 故障排除

### 常见问题

1. **401 Unauthorized**
   - 检查Anybase token是否有效
   - 确认ANYBASE_API_BASE_URL配置正确
   - 查看日志中的Anybase API调用错误

2. **用户创建失败**
   - 检查数据库连接
   - 确认bot_service和api_key服务正常
   - 查看详细错误日志

3. **Cookie未设置**
   - 检查JWT策略配置
   - 确认cookie域名和路径设置
   - 验证HTTPS配置（生产环境）

### 日志监控

关键日志信息：
```
INFO: Auto-created ApeRAG user for Anybase user {user_id}
INFO: Set ApeRAG session cookie for Anybase user {username}
ERROR: Failed to verify Anybase token: {error}
ERROR: Failed to create user for Anybase user {user_id}: {error}
```

## 部署注意事项

1. **环境变量**: 确保所有Anybase相关环境变量正确配置
2. **网络访问**: ApeRAG服务器需要能够访问Anybase API
3. **HTTPS**: 生产环境建议使用HTTPS确保token安全传输
4. **监控**: 监控Anybase API调用的成功率和响应时间

## 测试

### 手动测试

1. 在Anybase中登录获取token
2. 使用token调用ApeRAG API
3. 验证用户自动创建和会话建立
4. 测试后续请求使用cookie认证

### 自动化测试

建议编写集成测试覆盖：
- Anybase token验证
- 用户自动创建
- 会话管理
- 错误处理
