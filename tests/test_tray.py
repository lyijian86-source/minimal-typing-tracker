from __future__ import annotations

from type_record.tray import TrayController


def test_tray_menu_labels_follow_zh_language() -> None:
    controller = TrayController(
        tooltip="输入记录",
        language="zh",
        on_show=lambda: None,
        on_open_history=lambda: None,
        on_open_settings=lambda: None,
        on_export_csv=lambda: None,
        on_reset_today=lambda: None,
        on_open_data_folder=lambda: None,
        on_exit=lambda: None,
    )

    assert controller._menu_label("show_window") == "显示窗口"
    assert controller._menu_label("open_history") == "打开历史记录"
    assert controller._menu_label("settings") == "设置"
    assert controller._menu_label("export_csv") == "导出数据"
    assert controller._menu_label("reset_today") == "重置今天"
    assert controller._menu_label("open_data_folder") == "打开数据目录"
    assert controller._menu_label("exit") == "退出"
