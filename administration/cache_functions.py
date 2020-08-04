import datetime
import sqlite3
from typing import Optional

import coverage

cov = coverage.CoverageData()


def get_coverage_last_time() -> Optional[datetime.datetime]:
    """
    returns last time of coverage collection.
    """
    with sqlite3.connect(cov.base_filename()) as conn:
        cursor = conn.cursor()
        cursor.execute('select value from meta where key ="when"')
        [row] = cursor.fetchone()
        operation_time = datetime.datetime.fromisoformat(row) if row else None

    return operation_time


