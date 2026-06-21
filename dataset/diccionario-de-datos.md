# Diccionario de datos — `tickets.csv`

Origen: exportación de sistema de soporte (puede contener nulos o formatos inconsistentes).

| Columna | Descripción |
|---------|-------------|
| Ticket ID | Identificador único del ticket (entero). |
| Customer Name | Nombre del cliente. |
| Customer Email | Email de contacto. |
| Customer Age | Edad (puede venir vacía o no numérica). |
| Customer Gender | Género autodeclarado (texto libre). |
| Product Purchased | Producto asociado al caso. |
| Date of Purchase | Fecha de compra en texto; se parsea a `purchase_date`. |
| Ticket Type | Tipo/categoría originales del sistema fuente. |
| Ticket Subject | Asunto breve. |
| Ticket Description | Descripción detallada del problema. |
| Ticket Status | Estado del flujo (abierto, cerrado, etc.). |
| Ticket Priority | Prioridad declarada en origen (se normaliza a low/medium/high/critical). |
| Ticket Channel | Canal (email, chat, teléfono…). |
| First Response Time | Métrica textual de primera respuesta. |
| Time to Resolution | Métrica textual hasta resolución. |
| Customer Satisfaction Rating | Valor numérico de satisfacción si existe. |

Coloca el archivo **`tickets.csv`** en esta carpeta (`dataset/tickets.csv`) o en la raíz del repositorio; la API resuelve la ruta automáticamente.
