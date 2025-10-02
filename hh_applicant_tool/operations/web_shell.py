# Интерактивная оболочка для работы с API HH
import argparse
import code
import json
import logging
import sys

from ..api import ApiClient, ApiError
from ..main import BaseOperation
from ..main import Namespace as BaseNamespace

logger = logging.getLogger(__package__)


class Namespace(BaseNamespace):
    pass


class Operation(BaseOperation):
    """Интерактивная оболочка для работы с API HH.RU"""

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    def run(self, args: Namespace, api_client: ApiClient, _) -> None:
        """Запускает интерактивную оболочку для работы с API"""

        banner = """
╔═══════════════════════════════════════════════════════════════════════╗
║  HH.RU API Interactive Shell                                          ║
╚═══════════════════════════════════════════════════════════════════════╝

Доступные функции:
  - get(endpoint, **params)    : GET запрос к API
  - post(endpoint, **params)   : POST запрос к API
  - put(endpoint, **params)    : PUT запрос к API
  - delete(endpoint, **params) : DELETE запрос к API
  - request(method, endpoint, **params) : Произвольный HTTP запрос
  - api_client                 : Объект ApiClient для продвинутого использования
  - help()                     : Показать эту справку
  - exit() или Ctrl+D          : Выйти из оболочки

Примеры использования:
  >>> get('/me')
  >>> get('/resumes/mine')
  >>> get('/vacancies', text='Python', area=1)
  >>> post('/negotiations', resume_id='xxx', vacancy_id='yyy')

Документация API: https://github.com/hhru/api
"""

        def get(endpoint: str, **params):
            """GET запрос к API"""
            try:
                result = api_client.get(endpoint, params=params)
                output = json.dumps(
                    result, ensure_ascii=False, indent=2, sort_keys=True
                )
                print(output)
                return result
            except ApiError as ex:
                print(f"❗ Ошибка API: {ex}", file=sys.stderr)
                if hasattr(ex, 'data'):
                    error_data = json.dumps(
                        ex.data, ensure_ascii=False, indent=2
                    )
                    print(error_data, file=sys.stderr)
                return None

        def post(endpoint: str, **params):
            """POST запрос к API"""
            try:
                result = api_client.post(endpoint, params=params)
                if result:
                    output = json.dumps(
                        result, ensure_ascii=False, indent=2, sort_keys=True
                    )
                    print(output)
                else:
                    print("✅ Успешно")
                return result
            except ApiError as ex:
                print(f"❗ Ошибка API: {ex}", file=sys.stderr)
                if hasattr(ex, 'data'):
                    error_data = json.dumps(
                        ex.data, ensure_ascii=False, indent=2
                    )
                    print(error_data, file=sys.stderr)
                return None

        def put(endpoint: str, **params):
            """PUT запрос к API"""
            try:
                result = api_client.put(endpoint, params=params)
                if result:
                    output = json.dumps(
                        result, ensure_ascii=False, indent=2, sort_keys=True
                    )
                    print(output)
                else:
                    print("✅ Успешно")
                return result
            except ApiError as ex:
                print(f"❗ Ошибка API: {ex}", file=sys.stderr)
                if hasattr(ex, 'data'):
                    error_data = json.dumps(
                        ex.data, ensure_ascii=False, indent=2
                    )
                    print(error_data, file=sys.stderr)
                return None

        def delete(endpoint: str, **params):
            """DELETE запрос к API"""
            try:
                result = api_client.delete(endpoint, params=params)
                if result:
                    output = json.dumps(
                        result, ensure_ascii=False, indent=2, sort_keys=True
                    )
                    print(output)
                else:
                    print("✅ Успешно")
                return result
            except ApiError as ex:
                print(f"❗ Ошибка API: {ex}", file=sys.stderr)
                if hasattr(ex, 'data'):
                    error_data = json.dumps(
                        ex.data, ensure_ascii=False, indent=2
                    )
                    print(error_data, file=sys.stderr)
                return None

        def request(method: str, endpoint: str, **params):
            """Произвольный HTTP запрос к API"""
            try:
                result = api_client.request(method, endpoint, params=params)
                if result:
                    output = json.dumps(
                        result, ensure_ascii=False, indent=2, sort_keys=True
                    )
                    print(output)
                else:
                    print("✅ Успешно")
                return result
            except ApiError as ex:
                print(f"❗ Ошибка API: {ex}", file=sys.stderr)
                if hasattr(ex, 'data'):
                    error_data = json.dumps(
                        ex.data, ensure_ascii=False, indent=2
                    )
                    print(error_data, file=sys.stderr)
                return None

        # Создаем локальное окружение для интерактивной оболочки
        local_vars = {
            'api_client': api_client,
            'get': get,
            'post': post,
            'put': put,
            'delete': delete,
            'request': request,
            'json': json,
        }

        print(banner)

        # Запускаем интерактивную оболочку Python
        try:
            code.interact(local=local_vars, banner="", exitmsg="\n👋 До свидания!")
        except (EOFError, KeyboardInterrupt):
            print("\n👋 До свидания!")
