"""Веб-оболочка для взаимодействия с HH.RU API через браузер"""
import argparse
import json
import logging
import random
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from ..api import ApiClient, ApiError
from ..main import BaseOperation
from ..main import Namespace as BaseNamespace

logger = logging.getLogger(__package__)

# Global state for mass application progress
mass_apply_progress = {
    "active": False,
    "total": 0,
    "processed": 0,
    "applied": 0,
    "skipped": 0,
    "errors": 0,
    "log": []
}


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
        .progress-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin: 15px 0;
            padding: 15px;
            background: #f0f0f0;
            border-radius: 5px;
        }
        .progress-stats div {
            padding: 10px;
            background: white;
            border-radius: 4px;
            text-align: center;
        }
        .progress-stats strong {
            display: block;
            font-size: 1.5em;
            color: #667eea;
            margin-top: 5px;
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
                <h2>🚀 Массовая рассылка откликов</h2>
                <div class="info-box">
                    <strong>ℹ️ Массовая рассылка:</strong> Автоматически откликается на все подходящие вакансии. 
                    Процесс может занять несколько минут в зависимости от количества вакансий.
                </div>
                <form id="massApplyForm" onsubmit="return startMassApply(event)">
                    <div class="form-group">
                        <label for="resumeId">ID резюме (опционально):</label>
                        <input type="text" id="resumeId" name="resumeId" placeholder="Оставьте пустым для использования основного резюме">
                    </div>
                    
                    <div class="form-group">
                        <label for="searchText">Поисковый запрос (опционально):</label>
                        <input type="text" id="searchText" name="searchText" placeholder="python разработчик москва">
                    </div>

                    <div class="form-group">
                        <label for="schedule">Тип графика (опционально):</label>
                        <select id="schedule" name="schedule">
                            <option value="">Не важно</option>
                            <option value="remote">Удаленная работа</option>
                            <option value="fullDay">Полный день</option>
                            <option value="shift">Сменный график</option>
                            <option value="flexible">Гибкий график</option>
                            <option value="flyInFlyOut">Вахтовый метод</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="coverLetter">Сопроводительное письмо (опционально):</label>
                        <textarea id="coverLetter" name="coverLetter" placeholder="Если оставите пустым, будет использовано стандартное сообщение"></textarea>
                    </div>

                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="dryRun" name="dryRun">
                            Тестовый режим (не отправлять отклики, только показать что будет)
                        </label>
                    </div>

                    <button type="submit" id="massApplyBtn">🚀 Начать массовую рассылку</button>
                    <button type="button" onclick="stopMassApply()" id="stopApplyBtn" style="display:none; background: #f44336;">⏹️ Остановить</button>
                </form>

                <div id="massApplyProgress" style="display: none;">
                    <h3>📊 Прогресс рассылки</h3>
                    <div class="progress-stats">
                        <div>Всего вакансий: <strong id="totalVacancies">0</strong></div>
                        <div>Обработано: <strong id="processedVacancies">0</strong></div>
                        <div>Откликнулись: <strong id="appliedVacancies">0</strong></div>
                        <div>Пропущено: <strong id="skippedVacancies">0</strong></div>
                        <div>Ошибок: <strong id="errorVacancies">0</strong></div>
                    </div>
                    <div class="response">
                        <strong>Лог операций:</strong>
                        <pre id="massApplyLog"></pre>
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
        let progressCheckInterval = null;

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

        function startMassApply(event) {
            event.preventDefault();

            const resumeId = document.getElementById('resumeId').value.trim();
            const searchText = document.getElementById('searchText').value.trim();
            const schedule = document.getElementById('schedule').value;
            const coverLetter = document.getElementById('coverLetter').value.trim();
            const dryRun = document.getElementById('dryRun').checked;

            const params = {
                resume_id: resumeId || null,
                search: searchText || null,
                schedule: schedule || null,
                message: coverLetter || null,
                dry_run: dryRun
            };

            // Show progress section
            document.getElementById('massApplyProgress').style.display = 'block';
            document.getElementById('massApplyBtn').style.display = 'none';
            document.getElementById('stopApplyBtn').style.display = 'inline-block';
            
            // Reset progress
            updateProgress({
                total: 0,
                processed: 0,
                applied: 0,
                skipped: 0,
                errors: 0,
                log: ['⏳ Запуск массовой рассылки...']
            });

            fetch('/apply-mass', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(params)
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Ошибка: ' + data.message);
                    resetMassApplyUI();
                } else {
                    // Start polling for progress
                    startProgressPolling();
                }
            })
            .catch(error => {
                alert('Ошибка сети: ' + error.message);
                resetMassApplyUI();
            });

            return false;
        }

        function startProgressPolling() {
            progressCheckInterval = setInterval(() => {
                fetch('/apply-progress')
                    .then(response => response.json())
                    .then(data => {
                        updateProgress(data);
                        if (!data.active) {
                            stopProgressPolling();
                            document.getElementById('massApplyBtn').style.display = 'inline-block';
                            document.getElementById('stopApplyBtn').style.display = 'none';
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching progress:', error);
                    });
            }, 1000);
        }

        function stopProgressPolling() {
            if (progressCheckInterval) {
                clearInterval(progressCheckInterval);
                progressCheckInterval = null;
            }
        }

        function updateProgress(data) {
            document.getElementById('totalVacancies').textContent = data.total;
            document.getElementById('processedVacancies').textContent = data.processed;
            document.getElementById('appliedVacancies').textContent = data.applied;
            document.getElementById('skippedVacancies').textContent = data.skipped;
            document.getElementById('errorVacancies').textContent = data.errors;
            
            const logElement = document.getElementById('massApplyLog');
            logElement.textContent = data.log.join('\\n');
            logElement.scrollTop = logElement.scrollHeight;
        }

        function stopMassApply() {
            fetch('/apply-stop', { method: 'POST' })
                .then(() => {
                    stopProgressPolling();
                    resetMassApplyUI();
                })
                .catch(error => {
                    console.error('Error stopping:', error);
                });
        }

        function resetMassApplyUI() {
            document.getElementById('massApplyBtn').style.display = 'inline-block';
            document.getElementById('stopApplyBtn').style.display = 'none';
            stopProgressPolling();
        }
    </script>
</body>
</html>
"""


class WebShellHandler(BaseHTTPRequestHandler):
    api_client: ApiClient = None
    stop_requested: bool = False

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
        elif self.path == '/apply-progress':
            # Return current progress
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(mass_apply_progress, ensure_ascii=False).encode('utf-8'))
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

        elif self.path == '/apply-mass':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                params = json.loads(post_data.decode('utf-8'))

                # Check if already running
                if mass_apply_progress['active']:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    error_response = {
                        'error': True,
                        'message': 'Массовая рассылка уже выполняется'
                    }
                    self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
                    return

                # Start mass apply in a separate thread
                thread = threading.Thread(
                    target=self._run_mass_apply,
                    args=(params,),
                    daemon=True
                )
                thread.start()

                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                success_response = {
                    'success': True,
                    'message': 'Массовая рассылка запущена'
                }
                self.wfile.write(json.dumps(success_response, ensure_ascii=False).encode('utf-8'))

            except Exception as ex:
                logger.exception("Error starting mass apply: %s", ex)
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                error_response = {
                    'error': True,
                    'message': f'Ошибка запуска: {str(ex)}'
                }
                self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))

        elif self.path == '/apply-stop':
            WebShellHandler.stop_requested = True
            mass_apply_progress['active'] = False
            mass_apply_progress['log'].append('⏹️ Остановка по запросу пользователя...')

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            success_response = {'success': True}
            self.wfile.write(json.dumps(success_response, ensure_ascii=False).encode('utf-8'))

        else:
            self.send_error(404)

    def _run_mass_apply(self, params: dict) -> None:
        """Run mass application in background"""
        global mass_apply_progress

        # Reset state
        mass_apply_progress = {
            "active": True,
            "total": 0,
            "processed": 0,
            "applied": 0,
            "skipped": 0,
            "errors": 0,
            "log": ['🚀 Начало массовой рассылки...']
        }
        WebShellHandler.stop_requested = False

        try:
            # Get resume ID
            resume_id = params.get('resume_id')
            if not resume_id:
                mass_apply_progress['log'].append('📄 Получение основного резюме...')
                resumes = self.api_client.get('/resumes/mine')
                if not resumes.get('items'):
                    mass_apply_progress['log'].append('❌ Не найдено ни одного резюме')
                    mass_apply_progress['active'] = False
                    return
                resume_id = resumes['items'][0]['id']
                mass_apply_progress['log'].append(f'✅ Используется резюме: {resume_id}')

            # Get similar vacancies
            mass_apply_progress['log'].append('🔍 Поиск подходящих вакансий...')
            vacancies = self._get_vacancies(resume_id, params)
            mass_apply_progress['total'] = len(vacancies)
            mass_apply_progress['log'].append(f'📊 Найдено вакансий: {len(vacancies)}')

            if not vacancies:
                mass_apply_progress['log'].append('ℹ️ Подходящие вакансии не найдены')
                mass_apply_progress['active'] = False
                return

            # Get user info for message templates
            me = self.api_client.get('/me')
            message_template = params.get('message') or 'Меня заинтересовала ваша вакансия {vacancy_name}'
            dry_run = params.get('dry_run', False)

            if dry_run:
                mass_apply_progress['log'].append('🧪 ТЕСТОВЫЙ РЕЖИМ - отклики не отправляются')

            # Apply to vacancies
            for vacancy in vacancies:
                if WebShellHandler.stop_requested:
                    mass_apply_progress['log'].append('⏹️ Остановлено пользователем')
                    break

                vacancy_name = vacancy.get('name', 'Без названия')
                vacancy_id = vacancy['id']
                vacancy_url = vacancy.get('alternate_url', '')

                mass_apply_progress['processed'] += 1

                # Skip if already applied
                relations = vacancy.get('relations', [])
                if relations:
                    mass_apply_progress['log'].append(f'⏭️ Пропуск (уже откликались): {vacancy_name}')
                    mass_apply_progress['skipped'] += 1
                    continue

                # Skip if has test
                if vacancy.get('has_test'):
                    mass_apply_progress['log'].append(f'⏭️ Пропуск (есть тест): {vacancy_name}')
                    mass_apply_progress['skipped'] += 1
                    continue

                # Skip if archived
                if vacancy.get('archived'):
                    mass_apply_progress['log'].append(f'⏭️ Пропуск (в архиве): {vacancy_name}')
                    mass_apply_progress['skipped'] += 1
                    continue

                try:
                    # Format message
                    message = message_template.format(
                        vacancy_name=vacancy_name,
                        employer_name=vacancy.get('employer', {}).get('name', ''),
                        first_name=me.get('first_name', ''),
                        last_name=me.get('last_name', '')
                    )

                    if not dry_run:
                        # Apply to vacancy
                        self.api_client.post('/negotiations', {
                            'resume_id': resume_id,
                            'vacancy_id': vacancy_id,
                            'message': message
                        })
                        mass_apply_progress['log'].append(f'✅ Откликнулись: {vacancy_name}')
                        mass_apply_progress['applied'] += 1

                        # Delay between applications
                        time.sleep(random.uniform(1, 3))
                    else:
                        mass_apply_progress['log'].append(f'🧪 [ТЕСТ] Откликнулись бы: {vacancy_name}')
                        mass_apply_progress['applied'] += 1

                except ApiError as ex:
                    error_msg = str(ex)
                    mass_apply_progress['log'].append(f'❌ Ошибка при отклике на {vacancy_name}: {error_msg}')
                    mass_apply_progress['errors'] += 1

                    # Stop if limit exceeded
                    if 'limit' in error_msg.lower() or 'лимит' in error_msg.lower():
                        mass_apply_progress['log'].append('🛑 Достигнут лимит откликов. Остановка.')
                        break

                except Exception as ex:
                    mass_apply_progress['log'].append(f'❌ Неожиданная ошибка: {str(ex)}')
                    mass_apply_progress['errors'] += 1

            mass_apply_progress['log'].append('✅ Массовая рассылка завершена!')
            mass_apply_progress['log'].append(f'📊 Итого: откликов {mass_apply_progress["applied"]}, пропущено {mass_apply_progress["skipped"]}, ошибок {mass_apply_progress["errors"]}')

        except Exception as ex:
            logger.exception("Mass apply error: %s", ex)
            mass_apply_progress['log'].append(f'❌ Критическая ошибка: {str(ex)}')

        finally:
            mass_apply_progress['active'] = False

    def _get_vacancies(self, resume_id: str, params: dict) -> list:
        """Get similar vacancies"""
        vacancies = []
        search_text = params.get('search')
        schedule = params.get('schedule')

        for page in range(20):  # Max 20 pages
            if WebShellHandler.stop_requested:
                break

            api_params = {
                'page': page,
                'per_page': 100,
                'order_by': 'relevance'
            }

            if search_text:
                api_params['text'] = search_text
            if schedule:
                api_params['schedule'] = schedule

            try:
                result = self.api_client.get(f'/resumes/{resume_id}/similar_vacancies', api_params)
                vacancies.extend(result.get('items', []))

                if page >= result.get('pages', 1) - 1:
                    break

                # Delay between pages
                if page > 0:
                    time.sleep(random.uniform(1, 2))

            except ApiError as ex:
                logger.error("Error fetching vacancies page %d: %s", page, ex)
                break

        return vacancies


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
