from faceforge.config import Settings
from faceforge.ui.i18n import LANGUAGES, i18n, tr


def test_main_window_language_and_theme_switch(qapp, isolated_home):
    from faceforge.ui.main_window import MainWindow
    from faceforge.ui.theme import theme

    theme.apply(qapp, "dark")
    window = MainWindow(Settings())
    window.show()
    qapp.processEvents()
    for code in LANGUAGES:
        window.lang.language_selected.emit(code)
        qapp.processEvents()
        assert i18n.language == code
        assert window.start_btn.text() == tr("action.start")
    window._toggle_theme()
    qapp.processEvents()
    assert theme.name == "light"
    window._toggle_theme()
    window.settings_panel.preset_buttons["maximum"].click()
    qapp.processEvents()
    assert window.settings.get("preset") == "maximum"
    assert window.settings.get("face_swapper_pixel_boost") == 512
    window.close()
    i18n.set_language("en")
