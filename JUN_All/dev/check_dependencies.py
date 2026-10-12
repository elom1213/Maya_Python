# -*- coding: utf-8 -*-
# dev/check_dependencies.py - 얇은 재노출 (2026-10-12)
#
# 로직은 dev/A00530_dependency_check/app/core/dependency_check.py 로 옮겼다. docs/DEPENDENCIES.md 와
# 계획서들이 `import dev.check_dependencies as chk; chk.run()` 을 적어 두어 이름만 지킨다.
# 새 코드는 dev.A00530_dependency_check 를 직접 쓴다.

from dev.A00530_dependency_check.app.core.dependency_check import (  # noqa: F401
    CHECKS,
    QT_CANDIDATES,
    run,
)

if __name__ == "__main__":
    run(check_standalone=True)
