# Stellar MCP Server (Python)

Servidor MCP Stellar implementado em Python com suporte completo para ferramentas, recursos e prompts.

## 🚀 Início Rápido

### Pré-requisitos
- Python 3.10 ou superior
- pip ou uv para gerenciamento de pacotes

### Instalação

```bash
# Instalar dependências
pip install -r requirements.txt

# Ou usando uv (recomendado)
uv add mcp click anyio starlette uvicorn httpx
```

### Executando o Servidor

```bash
# Modo SSE (padrão - porta 8181)
python memory_mcp_server.py

# Modo SSE com debug
python memory_mcp_server.py --debug

# Modo stdio
python memory_mcp_server.py --transport stdio

# Porta personalizada
python memory_mcp_server.py --port 8080
```

## 📦 Estrutura do Projeto

```
stellar/
├── memory_mcp_server.py      # Servidor principal MCP
├── pyproject.toml         # Configuração do projeto Python
├── requirements.txt       # Dependências
├── smithery.yaml         # Configuração Smithery
└── README.md            # Este arquivo
```

## 🛠️ Recursos Disponíveis

### Ferramentas
- **hello**: Cumprimenta uma pessoa
  - Input: `{"name": "string"}`
  - Output: Mensagem de saudação

### Recursos
- **history://hello-world**: História do programa "Hello, World"

### Prompts
- **greet**: Template para gerar saudações personalizadas
  - Parâmetros: `{"name": "string"}`

## 🔧 Configuração

O servidor suporta as seguintes opções:

- `--port`: Porta para o servidor SSE (padrão: 8181)
- `--transport`: Tipo de transporte - `sse` ou `stdio` (padrão: sse)
- `--debug`: Ativa modo debug com logs detalhados

## 🧪 Testando o Servidor

### Teste via CURL

```bash
# Inicializar sessão
curl -X POST "http://127.0.0.1:8181/mcp?debug=true" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"clientInfo":{"name":"test-client","version":"1.0.0"}}}'

# Chamar ferramenta hello
curl -X POST "http://127.0.0.1:8181/mcp?debug=true" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"hello","arguments":{"name":"João"}}}'
```

## 📚 Desenvolvimento

### Adicionando Novas Ferramentas

Edite o arquivo `memory_mcp_server.py` e adicione sua ferramenta no método `_register_handlers`:

```python
# Em list_tools(), adicione:
types.Tool(
    name="sua_ferramenta",
    title="Título da Ferramenta",
    description="Descrição",
    inputSchema={...}
)

# Em call_tool(), adicione:
elif name == "sua_ferramenta":
    return await self.sua_ferramenta(arguments)

# Implemente o método:
async def sua_ferramenta(self, arguments: dict[str, Any]) -> list[types.ContentBlock]:
    # Sua lógica aqui
    return [types.TextContent(type="text", text="resultado")]
```

## 🚀 Deploy

Para deploy em produção:

1. Instale as dependências em um ambiente virtual
2. Configure a porta e modo de transporte apropriados
3. Use um gerenciador de processos como systemd ou supervisor
4. Configure um proxy reverso (nginx/apache) se necessário

## 📄 Licença

MIT