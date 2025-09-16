# AGENTS.md

Bem-vindo ao **Servidor MCP memory_mcp_server Python**!

Este é um servidor Model Context Protocol (MCP) implementado em Python que fornece ferramentas, recursos e prompts para aplicações de IA.

## O que está Incluído

- **Servidor MCP Python** com suporte completo ao protocolo MCP
- **Fluxo de Desenvolvimento** (`python memory_mcp_server.py` para testes locais)
- **Suporte a Transporte SSE e STDIO** para diferentes tipos de integração
- **CORS Configurado** para compatibilidade com aplicações web

## Comandos de Início Rápido

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar servidor de desenvolvimento (SSE na porta 8181)
python memory_mcp_server.py

# Executar com modo debug
python memory_mcp_server.py --debug

# Executar com transporte STDIO
python memory_mcp_server.py --transport stdio
```

## Fluxo de Desenvolvimento

Baseado na [arquitetura do Model Context Protocol](https://modelcontextprotocol.io/docs/learn/architecture.md), servidores MCP fornecem três primitivas principais:

### 1. Ferramentas (para ações)
Adicione funções executáveis que aplicações de IA podem invocar para realizar ações:

```python
@self.app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
    if name == "hello":
        return await self.hello_tool(arguments)
    raise ValueError(f"Ferramenta desconhecida: {name}")

async def hello_tool(self, arguments: dict[str, Any]) -> list[types.ContentBlock]:
    name = arguments.get("name", "Mundo")
    greeting = f"DEBUG: Olá, {name}!" if self.debug else f"Olá, {name}!"
    return [types.TextContent(type="text", text=greeting)]
```

### 2. Recursos (para dados estáticos)
Adicione fontes de dados que fornecem informações contextuais:

```python
@self.app.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="history://hello-world",
            name="História do Hello World",
            description="A história de origem do famoso programa 'Hello, World'",
            mimeType="text/plain",
        )
    ]

@self.app.read_resource()
async def read_resource(uri: str) -> types.ResourceContent:
    if uri == "history://hello-world":
        return types.ResourceContent(
            uri=uri,
            mimeType="text/plain",
            text='"Hello, World" apareceu pela primeira vez...',
        )
```

### 3. Prompts (para templates de interação)
Adicione templates reutilizáveis que ajudam a estruturar interações:

```python
@self.app.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    return [
        types.Prompt(
            name="greet",
            title="Prompt de Saudação",
            description="Diga olá para alguém",
            arguments=[
                types.PromptArgument(
                    name="name",
                    description="Nome da pessoa para cumprimentar",
                    required=True,
                )
            ],
        )
    ]

@self.app.get_prompt()
async def get_prompt(name: str, arguments: dict[str, Any]) -> types.PromptResponse:
    if name == "greet":
        person_name = arguments.get("name", "Mundo")
        return types.PromptResponse(
            description=f"Saudação para {person_name}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Diga olá para {person_name}"
                    ),
                )
            ],
        )
```

### Estrutura do Projeto

```
memory/
├── memory_mcp_server.py      # Implementação principal do servidor
├── pyproject.toml        # Configuração do projeto Python
├── requirements.txt      # Dependências do projeto
├── smithery.yaml        # Especificação do runtime (runtime: python)
└── README.md           # Documentação
```

### Personalizando Seu Projeto

**Importante:** Você vai querer personalizar o servidor para corresponder ao seu projeto real:

1. **Atualize o pyproject.toml:**
   ```toml
   [project]
   name = "seu-projeto-mcp"
   version = "1.0.0"
   description = "Descrição do seu servidor MCP"
   authors = [
       { name = "Seu Nome" }
   ]
   ```

2. **Atualize sua classe de servidor:**
   ```python
   class memoryMCPServer:
       def __init__(self, debug: bool = False):
           self.debug = debug
           self.app = Server("Nome do Seu Servidor")
           self._register_handlers()
   ```

3. **Teste se seu servidor funciona:**
   ```bash
   python memory_mcp_server.py
   ```

## Configuração de Sessão

O servidor Python suporta configuração através de parâmetros de linha de comando:

- `--port`: Define a porta para o servidor SSE (padrão: 8181)
- `--transport`: Escolhe o tipo de transporte: `sse` ou `stdio`
- `--debug`: Ativa o modo debug para logs detalhados

### Exemplo de Configuração

```bash
# Servidor com debug em porta customizada
python memory_mcp_server.py --port 8080 --debug

# Servidor com transporte STDIO (para integração direta)
python memory_mcp_server.py --transport stdio
```

## Transporte SSE vs STDIO

### SSE (Server-Sent Events)
Ideal para aplicações web e clientes HTTP:

```python
if transport == "sse":
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette

    sse = SseServerTransport("/messages/")
    # Configuração do servidor Starlette com rotas SSE
```

**Use SSE para:**
- Aplicações web
- APIs REST
- Clientes remotos
- Desenvolvimento com hot reload

### STDIO (Standard Input/Output)
Para integração direta com processos:

```python
else:
    from mcp.server.stdio import stdio_server

    async def arun():
        async with stdio_server() as streams:
            await server.app.run(streams[0], streams[1], ...)
```

**Use STDIO para:**
- Integração com CLI tools
- Pipes de processos
- Scripts automatizados
- Integração com editores

## Adicionando Novas Funcionalidades

### Nova Ferramenta

1. Adicione a definição na lista de ferramentas:
```python
@self.app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        # ... ferramentas existentes ...
        types.Tool(
            name="minha_ferramenta",
            title="Minha Ferramenta",
            description="Descrição da ferramenta",
            inputSchema={
                "type": "object",
                "required": ["parametro"],
                "properties": {
                    "parametro": {
                        "type": "string",
                        "description": "Descrição do parâmetro",
                    }
                },
            },
        )
    ]
```

2. Implemente o manipulador:
```python
async def minha_ferramenta(self, arguments: dict[str, Any]) -> list[types.ContentBlock]:
    parametro = arguments.get("parametro")
    # Sua lógica aqui
    resultado = f"Processado: {parametro}"
    return [types.TextContent(type="text", text=resultado)]
```

3. Registre no call_tool:
```python
@self.app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
    if name == "minha_ferramenta":
        return await self.minha_ferramenta(arguments)
    # ... outras ferramentas ...
```

## Testando Seu Servidor

### Teste via CURL

```bash
# 1. Inicializar sessão
curl -X POST "http://127.0.0.1:8181/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"clientInfo":{"name":"test-client","version":"1.0.0"}}}'

# 2. Listar ferramentas disponíveis
curl -X POST "http://127.0.0.1:8181/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'

# 3. Executar ferramenta
curl -X POST "http://127.0.0.1:8181/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"hello","arguments":{"name":"João"}}}'
```

### Teste com Cliente Python

```python
import httpx
import json

# Cliente para testar o servidor
async def test_server():
    async with httpx.AsyncClient() as client:
        # Inicializar
        response = await client.post(
            "http://127.0.0.1:8181/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "test", "version": "1.0"}
                }
            }
        )
        print(response.json())
```

## Implantação

### Desenvolvimento Local
```bash
# Instalar dependências
pip install -r requirements.txt

# Executar servidor
python memory_mcp_server.py --debug
```

### Produção com Docker
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY memory_mcp_server.py .
CMD ["python", "memory_mcp_server.py", "--port", "8080"]
```

### Produção com Systemd
```ini
[Unit]
Description=memory MCP Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/memory
ExecStart=/usr/bin/python3 /path/to/memory/memory_mcp_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Notas de Arquitetura

### Dependências Principais
- **mcp**: SDK Python oficial do MCP
- **click**: Parsing de argumentos de linha de comando
- **anyio**: Suporte assíncrono agnóstico
- **starlette**: Framework ASGI para SSE
- **uvicorn**: Servidor ASGI de produção
- **httpx**: Cliente HTTP para requisições

### Considerações de Segurança
- CORS configurado para permitir acesso de aplicações web
- Validação de entrada em todas as ferramentas
- Tratamento de erros robusto
- Modo debug separado para produção

## Solução de Problemas

### Problemas de Porta
```bash
# Verificar porta em uso
lsof -i :8181

# Matar processo usando a porta
kill -9 $(lsof -t -i:8181)

# Usar porta alternativa
python memory_mcp_server.py --port 8080
```

### Problemas de Dependências
```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Reinstalar dependências
pip install -r requirements.txt
```

### Problemas de Importação
- Verifique que está usando Python 3.10 ou superior
- Confirme que todas as dependências estão instaladas
- Verifique o PYTHONPATH se necessário

## Recursos

- **Documentação MCP**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **Python SDK**: [github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)
- **Smithery**: [smithery.ai](https://smithery.ai)
- **Starlette**: [starlette.io](https://www.starlette.io)

## Comunidade & Suporte

- **Discord MCP**: Junte-se à comunidade para ajuda e discussões
- **GitHub Issues**: Relate problemas no repositório do SDK Python
- **Stack Overflow**: Use a tag `model-context-protocol` para perguntas