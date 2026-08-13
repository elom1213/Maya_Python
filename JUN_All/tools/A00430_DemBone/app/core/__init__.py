# A00430_DemBone core - 스키닝 분해 로직 (UI 비의존).
#
# 여기는 **일부러 아무것도 import 하지 않는다**. 솔버 모듈(convex_ls / laplacian /
# solver_*)은 numpy 만 쓰는 순수 계산 코드라 Maya 없이도 import 되어야 하고
# (mayapy 헤드리스 검증), 나머지(scene_sampler / skin_writer / joint_writer /
# alembic_cache)는 maya.cmds 를 쓴다. 여기서 한꺼번에 끌어오면 그 경계가 무너진다.
