# BookSearcherBot
# 📚 Biblioteca Híbrida  - Telegram Bot

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Telebot](https://img.shields.io/badge/Library-pyTelegramBotAPI-orange.svg)
![BeautifulSoup](https://img.shields.io/badge/WebScraping-BeautifulSoup4-green.svg)
![Deploy](https://img.shields.io/badge/Deployment-Render-purple.svg)

##  Descripción del Proyecto
Este proyecto es un bot de Telegram . Funciona como un **agregador literario híbrido** que permite a los usuarios buscar y descargar libros o documentos en diversos formatos (PDF, EPUB, MOBI) directamente desde la interfaz de Telegram.

El sistema implementa una arquitectura de búsqueda en dos fases (Mecanismo de *Fallback*), combinando la extracción de datos mediante APIs RESTful (fuentes de dominio público) y técnicas avanzadas de Web Scraping e Ingeniería Inversa de frontend.

##  Características Principales
* **Mecanismo Híbrido de Búsqueda:** Consulta primaria a la API oficial de Gutendex (Project Gutenberg). Si no hay resultados, realiza un *fallback* automático haciendo scraping asíncrono en repositorios externos.
* **Procesamiento de Lenguaje Natural (Regex):** Capacidad para entender sintaxis flexible en las búsquedas. El usuario puede aplicar filtros en cualquier orden:
  * Filtro de formato: `kindle`
  * Filtro de autor: `(Nombre del Autor)`
  * Filtro de idioma: `[es]`, `[ing]`, `[en]`, etc.
* **Extracción de Metadatos:** Análisis del DOM para extraer el peso, formato e idioma de los archivos mediante `BeautifulSoup4`.
* **Sistema de Paginación:** Gestión del estado de la sesión de los usuarios mediante un mapeo en memoria para navegar entre múltiples páginas de resultados.
* **Anti-Idling (Keep-Alive):** Integración de un servidor Flask ligero ejecutándose en un hilo secundario (`Threading`) para mantener el servicio activo 24/7 en plataformas Cloud gratuitas (Render).

##  Stack Tecnológico
* **Lenguaje:** Python 3
* **Librerías principales:** `pyTelegramBotAPI`, `requests`, `beautifulsoup4`, `flask`
* **Despliegue (CI/CD):** GitHub (Control de versiones) + Render (Hosting 24/7) + Cron-job.org (Mantenimiento de sesión)

##  Uso del Bot
Para interactuar con el bot en Telegram, busca el usuario asignado e introduce el comando:
`/buscar [título del libro] (autor) kindle [idioma]`

**Ejemplos:**
> `/buscar el resplandor`
> `/buscar habitos atomicos kindle`
> `/buscar a good girls guide to murder (holly jackson) [en]`

## ⚠️ Aviso Legal
Este proyecto ha sido desarrollado con fines puramente **académicos y de investigación** en el ámbito de la ciberseguridad, automatización y extracción de datos. El código demuestra la viabilidad técnica de eludir ciertas barreras de protección de *frontend* y automatizar peticiones web. El autor no se hace responsable del uso indebido del código fuente ni del contenido indexado por las plataformas de terceros integradas en el motor de *scraping*.
