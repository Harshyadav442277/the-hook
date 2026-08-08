from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def test_decision_room_loads_and_switches_scenarios() -> None:
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception
    assert app.title or app.markdown
    assert len(app.selectbox) == 2
    app.selectbox[0].select_index(1).run()
    assert not app.exception


def test_how_it_works_loads() -> None:
    app = AppTest.from_file(
        str(ROOT / "pages" / "1_How_It_Works.py"), default_timeout=30
    ).run()
    assert not app.exception
    assert app.title[0].value == "How THE HOOK works"


def test_runtime_pages_do_not_import_network_clients() -> None:
    source = (ROOT / "app.py").read_text(encoding="utf-8") + (
        ROOT / "pages" / "1_How_It_Works.py"
    ).read_text(encoding="utf-8")
    assert "requests" not in source
    assert "pybaseball" not in source
