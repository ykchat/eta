from pathlib import Path
from contextlib import closing

import pytest

from eta import config
from eta.models import Operator
from eta.storage.sqlite import SQLiteStaticDB, SQLITE_FILE_NAME

TOEI = Operator(id="odpt.Operator:Toei", name="Toei", titles={"ja": "東京都交通局"})
RINKO = Operator(id="odpt.Operator:Rinko", name="Rinko", titles={"ja": "川崎鶴見臨港バス"})

def test_empty_at_first(tmp_path: Path) -> None:

    static_db = SQLiteStaticDB(tmp_path / SQLITE_FILE_NAME)

    with closing(static_db.connection()):
        assert static_db.get_operators() == []

def test_save_and_get_operators(tmp_path: Path) -> None:

    static_db = SQLiteStaticDB(tmp_path / SQLITE_FILE_NAME)

    with closing(static_db.connection()):

        static_db.save_operators([TOEI, RINKO])

        assert static_db.get_operators() == [RINKO, TOEI] # id の順に並ぶ

def test_save_replaces_all(tmp_path: Path) -> None:

    static_db = SQLiteStaticDB(tmp_path / SQLITE_FILE_NAME)

    with closing(static_db.connection()):
        static_db.save_operators([TOEI, RINKO])
        static_db.save_operators([TOEI]) # 保存し直すと、前の事業者は残らない

        assert static_db.get_operators() == [TOEI]

def test_saved_operators_remain_after_commit(tmp_path: Path) -> None:

    static_db = SQLiteStaticDB(tmp_path / SQLITE_FILE_NAME)

    with closing(static_db.connection()): # close のみ
        with static_db.connection(): # commit/roleback のみ
            static_db.save_operators([TOEI])

    static_db = SQLiteStaticDB(tmp_path / SQLITE_FILE_NAME)

    with closing(static_db.connection()):
        assert static_db.get_operators() == [TOEI] # commit すれば、接続し直しても残っている

def test_folder_is_created(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setattr(config, "DB_DIR_PATH", tmp_path / ".cache")   # このテストの間だけ差し替える

    path = config.path_db(SQLITE_FILE_NAME)

    assert path.parent.exists()