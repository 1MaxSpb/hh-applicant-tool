"""Веб-оболочка для взаимодействия с HH.RU API через браузер"""
import argparse
import json
import logging
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from ..api import ApiClient, ApiError
from ..main import BaseOperation
from ..main import Namespace as BaseNamespace

logger = logging.getLogger(__package__)


class Namespace(BaseNamespace):
    port: int
    host: str
    no_browser: bool


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HH Applicant Tool - Веб-оболочка</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        .content {
            padding: 30px;
        }
        .section {
            margin-bottom: 30px;
        }
        .section h2 {
            color: #667eea;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #333;
        }
        input[type="text"], select, textarea {
            width: 100%;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        textarea {
            resize: vertical;
            min-height: 100px;
            font-family: monospace;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        button:active {
            transform: translateY(0);
        }
        .response {
            background: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 15px;
            margin-top: 15px;
            max-height: 500px;
            overflow-y: auto;
        }
        .response pre {
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }
        .info-box {
            background: #e3f2fd;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }
        .warning-box {
            background: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }
        .error {
            color: #d32f2f;
            background: #ffebee;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
        }
        .success {
            color: #388e3c;
            background: #e8f5e9;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
        }
        .quick-actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .quick-action-btn {
            padding: 15px;
            text-align: center;
            background: white;
            border: 2px solid #667eea;
            color: #667eea;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .quick-action-btn:hover {
            background: #667eea;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
        }
        footer {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 HH Applicant Tool</h1>
            <p>Веб-интерфейс для работы с HH.RU API</p>
        </header>

        <div class="content">
            <div class="info-box">
                <strong>ℹ️ Информация:</strong> Этот веб-интерфейс позволяет выполнять любые операции с HH.RU API через браузер.
                Все запросы выполняются локально на вашем компьютере.
            </div>

            <div class="warning-box">
                <strong>⚠️ Внимание:</strong> Для работы необходима авторизация. Если вы не авторизованы,
                выполните команду <code>hh-applicant-tool authorize</code> в терминале.
            </div>

            <div class="section">
                <h2>⚡ Быстрые действия</h2>
                <div class="quick-actions">
                    <div class="quick-action-btn" onclick="quickAction('/me', 'GET')">
                        👤 Моя информация
                    </div>
                    <div class="quick-action-btn" onclick="quickAction('/resumes/mine', 'GET')">
                        📄 Мои резюме
                    </div>
                    <div class="quick-action-btn" onclick="quickAction('/negotiations', 'GET')">
                        💬 Мои отклики
                    </div>
                    <div class="quick-action-btn" onclick="quickAction('/vacancies', 'GET', {text: 'python', per_page: 10})">
                        🔍 Поиск вакансий (Python)
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🔧 Произвольный API запрос</h2>
                <form id="apiForm" onsubmit="return submitApiRequest(event)">
                    <div class="form-group">
                        <label for="method">HTTP Метод:</label>
                        <select id="method" name="method">
                            <option value="GET">GET</option>
                            <option value="POST">POST</option>
                            <option value="PUT">PUT</option>
                            <option value="DELETE">DELETE</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="endpoint">Эндпоинт (например: /me, /vacancies):</label>
                        <input type="text" id="endpoint" name="endpoint" placeholder="/me" required>
                    </div>

                    <div class="form-group">
                        <label for="params">Параметры (JSON формат, опционально):</label>
                        <textarea id="params" name="params" placeholder='{"text": "python", "per_page": 10}'></textarea>
                    </div>

                    <button type="submit">🚀 Выполнить запрос</button>
                </form>

                <div id="response" class="response" style="display: none;">
                    <strong>Ответ сервера:</strong>
                    <pre id="responseContent"></pre>
                </div>
            </div>

            <div class="section">
                <h2>📚 Полезные ссылки</h2>
                <ul style="line-height: 2;">
                    <li><a href="https://api.hh.ru/openapi/redoc" target="_blank">📖 HH.RU OpenAPI документация</a></li>
                    <li><a href="https://github.com/hhru/api" target="_blank">💻 GitHub репозиторий HH API</a></li>
                    <li><a href="https://github.com/s3rgeym/hh-applicant-tool" target="_blank">🛠️ HH Applicant Tool на GitHub</a></li>
                </ul>
            </div>
        </div>

        <footer>
            <p>HH Applicant Tool Web Shell | Powered by Python 🐍</p>
        </footer>
    </div>

    <script>
        function quickAction(endpoint, method, params = {}) {
            document.getElementById('method').value = method;
            document.getElementById('endpoint').value = endpoint;
            document.getElementById('params').value = Object.keys(params).length > 0 ? JSON.stringify(params, null, 2) : '';
            submitApiRequest(new Event('submit'));
        }

        function submitApiRequest(event) {
            if (event && event.preventDefault) {
                event.preventDefault();
            }

            const method = document.getElementById('method').value;
            const endpoint = document.getElementById('endpoint').value;
            const paramsText = document.getElementById('params').value.trim();

            let params = {};
            if (paramsText) {
                try {
                    params = JSON.parse(paramsText);
                } catch (e) {
                    showResponse('❌ Ошибка: Неверный формат JSON параметров', true);
                    return false;
                }
            }

            const requestData = {
                method: method,
                endpoint: endpoint,
                params: params
            };

            showResponse('⏳ Выполняется запрос...', false);

            fetch('/api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showResponse('❌ Ошибка:\\n' + JSON.stringify(data, null, 2), true);
                } else {
                    showResponse('✅ Успешно:\\n' + JSON.stringify(data, null, 2), false);
                }
            })
            .catch(error => {
                showResponse('❌ Ошибка сети: ' + error.message, true);
            });

            return false;
        }

        function showResponse(content, isError) {
            const responseDiv = document.getElementById('response');
            const responseContent = document.getElementById('responseContent');
            responseContent.textContent = content;
            responseDiv.style.display = 'block';
            responseDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    </script>
</body>
</html>
"""


class WebShellHandler(BaseHTTPRequestHandler):
    api_client: ApiClient = None

    def log_message(self, format: str, *args: Any) -> None:
        """Override to use custom logger"""
        logger.info("%s - %s", self.address_string(), format % args)

    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        else:
            self.send_error(404)

    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                request_data = json.loads(post_data.decode('utf-8'))
                method = request_data.get('method', 'GET')
                endpoint = request_data.get('endpoint', '/me')
                params = request_data.get('params', {})

                logger.info("API Request: %s %s %s", method, endpoint, params)

                # Execute API request
                result = self.api_client.request(method, endpoint, params=params)

                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False, indent=2).encode('utf-8'))

            except ApiError as ex:
                logger.error("API Error: %s", ex)
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                error_response = {
                    'error': True,
                    'message': str(ex),
                    'data': ex.data if hasattr(ex, 'data') else {}
                }
                self.wfile.write(json.dumps(error_response, ensure_ascii=False, indent=2).encode('utf-8'))

            except Exception as ex:
                logger.exception("Unexpected error: %s", ex)
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                error_response = {
                    'error': True,
                    'message': f'Неожиданная ошибка: {str(ex)}'
                }
                self.wfile.write(json.dumps(error_response, ensure_ascii=False, indent=2).encode('utf-8'))
        else:
            self.send_error(404)


class Operation(BaseOperation):
    """Запустить веб-оболочку для работы с HH.RU API через браузер"""

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            '--port',
            type=int,
            default=8080,
            help='Порт для веб-сервера (по умолчанию: 8080)'
        )
        parser.add_argument(
            '--host',
            type=str,
            default='127.0.0.1',
            help='Хост для веб-сервера (по умолчанию: 127.0.0.1)'
        )
        parser.add_argument(
            '--no-browser',
            action='store_true',
            help='Не открывать браузер автоматически'
        )

    def run(self, args: Namespace, api_client: ApiClient, *_) -> None:
        # Set the API client for the handler
        WebShellHandler.api_client = api_client

        # Create and start the server
        server_address = (args.host, args.port)
        httpd = HTTPServer(server_address, WebShellHandler)

        url = f"http://{args.host}:{args.port}"

        print(f"🚀 Веб-оболочка запущена на {url}")
        print(f"📖 Откройте {url} в браузере для начала работы")
        print("🛑 Для остановки нажмите Ctrl+C")

        # Open browser in a separate thread
        if not args.no_browser:
            threading.Timer(1.0, lambda: webbrowser.open(url)).start()

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n⏹️  Веб-оболочка остановлена")
            httpd.shutdown()
            return 0
