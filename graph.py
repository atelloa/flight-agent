from langgraph.graph import StateGraph, END
from state import AgentState
from nodes import encontrar_barato, validar_escalas

# Crear el grafo
graph = StateGraph(AgentState)

# Agregar los nodes
graph.add_node("buscar_barato", encontrar_barato)
graph.add_node("validar", validar_escalas)

# Conectar los nodes (edges = conexiones)
graph.add_edge("buscar_barato", "validar")
graph.add_edge("validar", END)

# Decir dónde empieza
graph.set_entry_point("buscar_barato")

# Compilar (transformar a ejecutable)
compiled_graph = graph.compile()