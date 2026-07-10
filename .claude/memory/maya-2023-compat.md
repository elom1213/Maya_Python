---
name: maya-2023-compat
description: Maya tools may need to run on Maya 2023 — avoid native sin/cos math nodes (2024+ only)
metadata: 
  node_type: memory
  type: project
  originSessionId: 7c6914b5-25ff-4ed9-a106-0f035a816a95
---

일부 툴은 **Maya 2023** 에서도 동작해야 한다. Maya 2024 부터 추가된 네이티브 math 노드
(`sin`, `cos`, `tan` 등)는 **Maya 2023 에 없다**.

**Why:** A00160_sphericalEye Live 빌드 모드 작업 시 사용자가 "마야2023 버전에서도 써야 한다"고 명시.

**How to apply:** 노드 기반 삼각함수가 필요하면 네이티브 sin/cos 대신 `eulerToQuat` 을 쓴다.
입력 회전 φ(rad)에 대해 `outputQuatX=sin(φ/2)`, `outputQuatW=cos(φ/2)` 이므로, θ(도)에 `π/90` 을
곱해 넣으면 deg→rad 변환과 반각 ×2 가 한 번에 처리되어 `quatX=sin θ`, `quatW=cos θ` 를 얻는다.
참고: [[ui-text-english-only]]
