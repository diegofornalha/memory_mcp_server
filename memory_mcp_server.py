#!/usr/bin/env python3
"""
Memory MCP Server - Servidor MCP com funcionalidades de memória e categorização
"""

import sys
import json
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime
from dataclasses import dataclass, field

import anyio
import click
import mcp.types as types
from mcp.server.lowlevel import Server
from starlette.requests import Request


# Categorias de memória
MemoryCategory = Literal["personal", "professional", "technical", "general"]


@dataclass
class MemoryItem:
    """Estrutura para um item de memória"""
    id: str
    content: str
    category: MemoryCategory
    timestamp: str
    user_id: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "metadata": self.metadata
        }


class MemoryMCPServer:
    """Servidor MCP com capacidades de memória e categorização"""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.app = Server("Memory Agent MCP")
        self.memories: Dict[str, List[MemoryItem]] = {}
        self._register_handlers()

    def _generate_memory_id(self) -> str:
        """Gera um ID único para memória"""
        return f"mem_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    def _categorize_content(self, content: str) -> MemoryCategory:
        """Categoriza o conteúdo automaticamente"""
        content_lower = content.lower()

        # Palavras-chave para categorização
        personal_keywords = ["família", "amigo", "casa", "hobby", "sentimento", "pessoal", "vida", "relacionamento"]
        professional_keywords = ["trabalho", "empresa", "projeto", "cliente", "reunião", "carreira", "negócio", "profissional"]
        technical_keywords = ["código", "programa", "api", "servidor", "database", "algoritmo", "software", "bug", "feature"]

        # Conta ocorrências
        personal_score = sum(1 for word in personal_keywords if word in content_lower)
        professional_score = sum(1 for word in professional_keywords if word in content_lower)
        technical_score = sum(1 for word in technical_keywords if word in content_lower)

        # Determina categoria
        scores = {
            "personal": personal_score,
            "professional": professional_score,
            "technical": technical_score
        }

        if max(scores.values()) == 0:
            return "general"

        return max(scores, key=scores.get)

    def _register_handlers(self):
        """Registra todas as ferramentas, recursos e prompts"""

        @self.app.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
            """Manipulador para chamadas de ferramentas"""

            if name == "save_memory":
                return await self.save_memory_tool(arguments)
            elif name == "retrieve_memories":
                return await self.retrieve_memories_tool(arguments)
            elif name == "categorize_text":
                return await self.categorize_text_tool(arguments)
            elif name == "delete_memory":
                return await self.delete_memory_tool(arguments)
            elif name == "search_memories":
                return await self.search_memories_tool(arguments)
            elif name == "get_memory_stats":
                return await self.get_memory_stats_tool(arguments)

            raise ValueError(f"Ferramenta desconhecida: {name}")

        @self.app.list_tools()
        async def list_tools() -> list[types.Tool]:
            """Lista todas as ferramentas disponíveis"""
            return [
                types.Tool(
                    name="save_memory",
                    title="Salvar Memória",
                    description="Salva uma nova memória com categorização automática",
                    inputSchema={
                        "type": "object",
                        "required": ["content"],
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Conteúdo da memória para salvar"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "ID do usuário (opcional)",
                                "default": "default"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["personal", "professional", "technical", "general"],
                                "description": "Categoria manual (opcional, será auto-categorizada se não fornecida)"
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Metadados adicionais (opcional)"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="retrieve_memories",
                    title="Recuperar Memórias",
                    description="Recupera memórias salvas, opcionalmente filtradas por categoria",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "ID do usuário",
                                "default": "default"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["personal", "professional", "technical", "general"],
                                "description": "Filtrar por categoria (opcional)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Número máximo de memórias para retornar",
                                "default": 10
                            }
                        }
                    }
                ),
                types.Tool(
                    name="categorize_text",
                    title="Categorizar Texto",
                    description="Categoriza um texto em personal, professional, technical ou general",
                    inputSchema={
                        "type": "object",
                        "required": ["text"],
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Texto para categorizar"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="delete_memory",
                    title="Deletar Memória",
                    description="Deleta uma memória específica pelo ID",
                    inputSchema={
                        "type": "object",
                        "required": ["memory_id"],
                        "properties": {
                            "memory_id": {
                                "type": "string",
                                "description": "ID da memória para deletar"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "ID do usuário",
                                "default": "default"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="search_memories",
                    title="Buscar Memórias",
                    description="Busca memórias por palavra-chave",
                    inputSchema={
                        "type": "object",
                        "required": ["query"],
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Termo de busca"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "ID do usuário",
                                "default": "default"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["personal", "professional", "technical", "general"],
                                "description": "Filtrar por categoria (opcional)"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_memory_stats",
                    title="Estatísticas de Memória",
                    description="Obtém estatísticas sobre as memórias armazenadas",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "ID do usuário",
                                "default": "default"
                            }
                        }
                    }
                )
            ]

        @self.app.list_resources()
        async def list_resources() -> list[types.Resource]:
            """Lista todos os recursos disponíveis"""
            return [
                types.Resource(
                    uri="memory://guide",
                    name="Guia do Sistema de Memória",
                    description="Como usar o sistema de memória e categorização",
                    mimeType="text/plain"
                )
            ]

        @self.app.read_resource()
        async def read_resource(uri: str) -> types.ResourceContents:
            """Lê o conteúdo de um recurso"""
            if uri == "memory://guide":
                return types.ResourceContents(
                    uri=uri,
                    mimeType="text/plain",
                    text="""
                    GUIA DO SISTEMA DE MEMÓRIA MCP
                    ===============================

                    Este servidor MCP oferece capacidades avançadas de memória com categorização automática.

                    CATEGORIAS:
                    - Personal: Informações pessoais, família, hobbies
                    - Professional: Trabalho, carreira, negócios
                    - Technical: Código, programação, tecnologia
                    - General: Conhecimento geral, outros

                    FUNCIONALIDADES:
                    1. save_memory: Salva novas memórias com categorização automática
                    2. retrieve_memories: Recupera memórias filtradas por categoria
                    3. categorize_text: Categoriza texto automaticamente
                    4. delete_memory: Remove memórias específicas
                    5. search_memories: Busca memórias por palavra-chave
                    6. get_memory_stats: Estatísticas de uso

                    EXEMPLOS DE USO:
                    - "Salve que meu projeto favorito é o MCP"
                    - "Quais são minhas memórias profissionais?"
                    - "Busque memórias sobre Python"
                    - "Mostre estatísticas das minhas memórias"
                    """
                )
            raise ValueError(f"Recurso desconhecido: {uri}")

    async def save_memory_tool(self, arguments: dict[str, Any]) -> list[types.ContentBlock]:
        """Salva uma nova memória"""
        content = arguments.get("content", "")
        user_id = arguments.get("user_id", "default")
        category = arguments.get("category")
        metadata = arguments.get("metadata", {})

        if not content:
            return [types.TextContent(type="text", text="❌ Erro: Conteúdo não pode estar vazio")]

        # Auto-categoriza se não fornecida
        if not category:
            category = self._categorize_content(content)

        # Cria o item de memória
        memory = MemoryItem(
            id=self._generate_memory_id(),
            content=content,
            category=category,
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            metadata=metadata
        )

        # Armazena a memória
        if user_id not in self.memories:
            self.memories[user_id] = []
        self.memories[user_id].append(memory)

        if self.debug:
            print(f"DEBUG: Memória salva - {memory.id}: {content[:50]}...")

        return [types.TextContent(
            type="text",
            text=f"✅ Memória salva com sucesso!\n"
                 f"ID: {memory.id}\n"
                 f"Categoria: {category}\n"
                 f"Conteúdo: {content[:100]}..."
        )]

    async def retrieve_memories_tool(self, arguments: dict[str, Any]) -> list[types.ContentBlock]:
        """Recupera memórias do usuário"""
        user_id = arguments.get("user_id", "default")
        category = arguments.get("category")
        limit = arguments.get("limit", 10)

        if user_id not in self.memories or not self.memories[user_id]:
            return [types.TextContent(type="text", text="📭 Nenhuma memória encontrada")]

        memories = self.memories[user_id]

        # Filtra por categoria se especificada
        if category:
            memories = [m for m in memories if m.category == category]

        # Ordena por timestamp (mais recentes primeiro)
        memories = sorted(memories, key=lambda x: x.timestamp, reverse=True)[:limit]

        if not memories:
            return [types.TextContent(type="text", text=f"📭 Nenhuma memória encontrada na categoria '{category}'")]

        # Formata a saída
        output = f"📚 {len(memories)} memória(s) encontrada(s):\n\n"
        for mem in memories:
            output += f"🔹 [{mem.category.upper()}] {mem.id}\n"
            output += f"   📅 {mem.timestamp}\n"
            output += f"   📝 {mem.content}\n\n"

        return [types.TextContent(type="text", text=output)]

    async def categorize_text_tool(self, arguments: dict[str, Any]) -> list[types.ContentBlock]:
        """Categoriza um texto"""
        text = arguments.get("text", "")

        if not text:
            return [types.TextContent(type="text", text="❌ Erro: Texto não pode estar vazio")]

        category = self._categorize_content(text)

        return [types.TextContent(
            type="text",
            text=f"🏷️ Categoria identificada: {category.upper()}\n"
                 f"📝 Texto: {text[:100]}..."
        )]

    async def delete_memory_tool(self, arguments: dict[str, Any]) -> list[types.ContentBlock]:
        """Deleta uma memória específica"""
        memory_id = arguments.get("memory_id", "")
        user_id = arguments.get("user_id", "default")

        if not memory_id:
            return [types.TextContent(type="text", text="❌ Erro: ID da memória é obrigatório")]

        if user_id not in self.memories:
            return [types.TextContent(type="text", text="❌ Erro: Usuário não encontrado")]

        # Procura e remove a memória
        initial_count = len(self.memories[user_id])
        self.memories[user_id] = [m for m in self.memories[user_id] if m.id != memory_id]

        if len(self.memories[user_id]) < initial_count:
            return [types.TextContent(type="text", text=f"✅ Memória {memory_id} deletada com sucesso")]
        else:
            return [types.TextContent(type="text", text=f"❌ Memória {memory_id} não encontrada")]

    async def search_memories_tool(self, arguments: dict[str, Any]) -> list[types.ContentBlock]:
        """Busca memórias por palavra-chave"""
        query = arguments.get("query", "").lower()
        user_id = arguments.get("user_id", "default")
        category = arguments.get("category")

        if not query:
            return [types.TextContent(type="text", text="❌ Erro: Query de busca é obrigatória")]

        if user_id not in self.memories or not self.memories[user_id]:
            return [types.TextContent(type="text", text="📭 Nenhuma memória encontrada")]

        memories = self.memories[user_id]

        # Filtra por categoria se especificada
        if category:
            memories = [m for m in memories if m.category == category]

        # Busca pela query
        results = [m for m in memories if query in m.content.lower()]

        if not results:
            return [types.TextContent(type="text", text=f"📭 Nenhuma memória encontrada com '{query}'")]

        # Formata a saída
        output = f"🔍 {len(results)} resultado(s) para '{query}':\n\n"
        for mem in results[:10]:  # Limita a 10 resultados
            output += f"🔹 [{mem.category.upper()}] {mem.id}\n"
            output += f"   📅 {mem.timestamp}\n"
            output += f"   📝 {mem.content}\n\n"

        return [types.TextContent(type="text", text=output)]

    async def get_memory_stats_tool(self, arguments: dict[str, Any]) -> list[types.ContentBlock]:
        """Obtém estatísticas das memórias"""
        user_id = arguments.get("user_id", "default")

        if user_id not in self.memories or not self.memories[user_id]:
            return [types.TextContent(type="text", text="📊 Nenhuma memória armazenada ainda")]

        memories = self.memories[user_id]

        # Calcula estatísticas
        total = len(memories)
        categories = {}
        for mem in memories:
            categories[mem.category] = categories.get(mem.category, 0) + 1

        # Formata a saída
        output = f"📊 ESTATÍSTICAS DE MEMÓRIA\n"
        output += f"{'='*30}\n\n"
        output += f"📚 Total de memórias: {total}\n\n"
        output += f"📂 Por categoria:\n"
        for cat, count in categories.items():
            percentage = (count / total) * 100
            output += f"  • {cat.upper()}: {count} ({percentage:.1f}%)\n"

        # Memória mais antiga e mais recente
        if memories:
            oldest = min(memories, key=lambda x: x.timestamp)
            newest = max(memories, key=lambda x: x.timestamp)
            output += f"\n⏰ Memória mais antiga: {oldest.timestamp}\n"
            output += f"⏰ Memória mais recente: {newest.timestamp}\n"

        return [types.TextContent(type="text", text=output)]


@click.command()
@click.option("--port", default=8181, help="Porta para escutar (SSE)")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="sse",
    help="Tipo de transporte",
)
@click.option("--debug", is_flag=True, help="Ativa modo debug")
def main(port: int, transport: str, debug: bool) -> int:
    """Memory MCP Server - Servidor com capacidades de memória"""

    server = MemoryMCPServer(debug=debug)

    if transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.middleware.cors import CORSMiddleware
        from starlette.responses import Response
        from starlette.routing import Mount, Route

        print(f"🧠 Memory MCP Server iniciando na porta {port}")
        print(f"🔧 Modo debug: {'Ativado' if debug else 'Desativado'}")

        sse = SseServerTransport("/messages/")

        async def handle_sse(request: Request):
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await server.app.run(streams[0], streams[1], server.app.create_initialization_options())
            return Response()

        async def handle_mcp(request: Request):
            # Manipula requisições POST do MCP via HTTP simples
            from starlette.responses import JSONResponse

            if request.method == "POST":
                try:
                    body = await request.json()

                    method = body.get("method")

                    # Resposta de inicialização
                    if method == "initialize":
                        return JSONResponse({
                            "jsonrpc": "2.0",
                            "id": body.get("id", 0),
                            "result": {
                                "protocolVersion": "2025-06-18",
                                "capabilities": {
                                    "tools": {
                                        "listChanged": True
                                    },
                                    "resources": {
                                        "subscribe": False,
                                        "listChanged": False
                                    }
                                },
                                "serverInfo": {
                                    "name": "Memory Agent MCP",
                                    "version": "1.0.0"
                                }
                            }
                        })

                    # Notificação de inicializado
                    elif method == "notifications/initialized":
                        return JSONResponse({
                            "jsonrpc": "2.0",
                            "result": {}
                        })

                    # Listar ferramentas
                    elif method == "tools/list":
                        # Retorna lista de ferramentas em formato JSON simples
                        tools = [
                            {
                                "name": "save_memory",
                                "description": "Salva uma nova memória com categorização automática",
                                "inputSchema": {
                                    "type": "object",
                                    "required": ["content"],
                                    "properties": {
                                        "content": {"type": "string", "description": "Conteúdo da memória"},
                                        "user_id": {"type": "string", "description": "ID do usuário (opcional)"},
                                        "category": {"type": "string", "enum": ["personal", "professional", "technical", "general"]},
                                        "metadata": {"type": "object", "description": "Metadados adicionais"}
                                    }
                                }
                            },
                            {
                                "name": "retrieve_memories",
                                "description": "Recupera memórias salvas",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "user_id": {"type": "string", "description": "ID do usuário"},
                                        "category": {"type": "string", "enum": ["personal", "professional", "technical", "general"]},
                                        "limit": {"type": "integer", "description": "Número máximo de memórias"}
                                    }
                                }
                            },
                            {
                                "name": "categorize_text",
                                "description": "Categoriza um texto",
                                "inputSchema": {
                                    "type": "object",
                                    "required": ["text"],
                                    "properties": {
                                        "text": {"type": "string", "description": "Texto para categorizar"}
                                    }
                                }
                            },
                            {
                                "name": "search_memories",
                                "description": "Busca memórias por palavra-chave",
                                "inputSchema": {
                                    "type": "object",
                                    "required": ["query"],
                                    "properties": {
                                        "query": {"type": "string", "description": "Termo de busca"},
                                        "user_id": {"type": "string", "description": "ID do usuário"},
                                        "category": {"type": "string", "enum": ["personal", "professional", "technical", "general"]}
                                    }
                                }
                            },
                            {
                                "name": "delete_memory",
                                "description": "Deleta uma memória pelo ID",
                                "inputSchema": {
                                    "type": "object",
                                    "required": ["memory_id"],
                                    "properties": {
                                        "memory_id": {"type": "string", "description": "ID da memória"},
                                        "user_id": {"type": "string", "description": "ID do usuário"}
                                    }
                                }
                            },
                            {
                                "name": "get_memory_stats",
                                "description": "Obtém estatísticas das memórias",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "user_id": {"type": "string", "description": "ID do usuário"}
                                    }
                                }
                            }
                        ]
                        return JSONResponse({
                            "jsonrpc": "2.0",
                            "id": body.get("id"),
                            "result": {
                                "tools": tools
                            }
                        })

                    # Executar ferramenta
                    elif method == "tools/call":
                        params = body.get("params", {})
                        tool_name = params.get("name")
                        tool_args = params.get("arguments", {})

                        # Chama a ferramenta específica
                        if tool_name == "save_memory":
                            result = await server.save_memory_tool(tool_args)
                        elif tool_name == "retrieve_memories":
                            result = await server.retrieve_memories_tool(tool_args)
                        elif tool_name == "categorize_text":
                            result = await server.categorize_text_tool(tool_args)
                        elif tool_name == "delete_memory":
                            result = await server.delete_memory_tool(tool_args)
                        elif tool_name == "search_memories":
                            result = await server.search_memories_tool(tool_args)
                        elif tool_name == "get_memory_stats":
                            result = await server.get_memory_stats_tool(tool_args)
                        else:
                            result = [types.TextContent(type="text", text=f"Ferramenta '{tool_name}' não encontrada")]
                        return JSONResponse({
                            "jsonrpc": "2.0",
                            "id": body.get("id"),
                            "result": {
                                "content": [
                                    {"type": block.type, "text": block.text}
                                    for block in result
                                ]
                            }
                        })

                    # Listar recursos
                    elif method == "resources/list":
                        # Define recursos disponíveis em formato JSON simples
                        resources = [
                            {
                                "uri": "memory://guide",
                                "name": "Guia do Sistema de Memória",
                                "description": "Como usar o sistema de memória e categorização",
                                "mimeType": "text/plain"
                            }
                        ]
                        return JSONResponse({
                            "jsonrpc": "2.0",
                            "id": body.get("id"),
                            "result": {
                                "resources": resources
                            }
                        })

                    # Ler recurso
                    elif method == "resources/read":
                        params = body.get("params", {})
                        uri = params.get("uri")

                        if uri == "memory://guide":
                            result = {
                                "uri": uri,
                                "mimeType": "text/plain",
                                "text": "Guia do Sistema de Memória MCP\n\nFerramentas disponíveis:\n- save_memory: Salva memórias\n- retrieve_memories: Recupera memórias\n- categorize_text: Categoriza texto\n- search_memories: Busca memórias\n- delete_memory: Deleta memórias\n- get_memory_stats: Estatísticas"
                            }
                        else:
                            result = {
                                "uri": uri,
                                "mimeType": "text/plain",
                                "text": "Recurso não encontrado"
                            }
                        return JSONResponse({
                            "jsonrpc": "2.0",
                            "id": body.get("id"),
                            "result": result
                        })

                    # Para outros métodos não implementados
                    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                        await server.app.run(streams[0], streams[1], server.app.create_initialization_options())
                    return Response()

                except Exception as e:
                    if debug:
                        print(f"DEBUG: Erro em /mcp: {e}")
                    return JSONResponse({"error": str(e)}, status_code=500)

            # GET requests ainda usam SSE
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await server.app.run(streams[0], streams[1], server.app.create_initialization_options())
            return Response()

        starlette_app = Starlette(
            debug=debug,
            routes=[
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                Route("/mcp", endpoint=handle_mcp, methods=["GET", "POST"]),
                Route("/mc", endpoint=handle_mcp, methods=["GET", "POST"]),  # Alias para compatibilidade
                Route("/", endpoint=handle_mcp, methods=["GET", "POST"]),  # Root também
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        # Adiciona CORS middleware
        starlette_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        import uvicorn
        print(f"🌐 Servidor rodando em http://127.0.0.1:{port}")
        print(f"📚 Use as ferramentas de memória para salvar e recuperar informações!")
        uvicorn.run(starlette_app, host="127.0.0.1", port=port)

    else:
        from mcp.server.stdio import stdio_server

        async def arun():
            async with stdio_server() as streams:
                await server.app.run(streams[0], streams[1], server.app.create_initialization_options())

        anyio.run(arun)

    return 0


if __name__ == "__main__":
    sys.exit(main())  # type: ignore[call-arg]