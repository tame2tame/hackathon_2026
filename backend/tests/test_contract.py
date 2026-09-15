from scripts.export_openapi import CONTRACT_PATH, render


def test_contract_matches_application_schema() -> None:
    assert CONTRACT_PATH.exists(), "Нет contracts/openapi.yaml: выполните make openapi"
    assert CONTRACT_PATH.read_text(encoding="utf-8") == render(), (
        "Схема приложения изменилась: выполните make openapi и закоммитьте контракт"
    )
