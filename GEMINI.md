# ComfyUI 워크플로 제작 지시서

이 문서는 Gemini 같은 다른 AI에게 ComfyUI 워크플로 작업을 맡길 때 쓰는 규칙입니다. 답변은 한국어로 합니다. 노드명, 파일명, 코드는 원문으로 둡니다.

## 먼저 읽을 파일

| 파일 | 내용 |
|---|---|
| `skills/comfyui-workflow/SKILL.md` | 전체 작업 순서 |
| `skills/comfyui-workflow/references/제작_규격.md` | 내 워크플로 틀: 기준 파일, JSON 형식, 자동화 수식, 색 |
| `skills/comfyui-workflow/references/요구사항.md` | 사용자 요구사항 전체 |
| `skills/comfyui-workflow/references/노드_함정.md` | 결과를 조용히 망치는 노드 동작 |
| `skills/comfyui-workflow/references/클라우드_사실.md` | Comfy Cloud 제약과 모델 이름 규칙 |
| `workflows/00_어떤걸쓸까.md` | 기존 워크플로 안내 |
| `reports/2026-11-09_최신_인기_대조.md` | 모델별 최신·인기 대조와 Cloud 테스트 결과 |

이 문서와 위 파일이 다르면 위 파일과 사용자의 최신 지시를 따릅니다.

## 결과물

- ComfyUI에서 바로 열리는 UI 형식 JSON을 줍니다. 개념도, 의사코드, 일부만 적은 JSON은 결과물이 아닙니다.
- 없는 노드 이름이나 입력 이름을 지어내지 않습니다. `workflows/`의 같은 모델 파일에서 노드 형태를 복사해서 만듭니다.
- 기존 파일을 덮어쓰지 않습니다. 새 번호의 새 파일로 만듭니다.
- 실행해 보지 못했으면 "Comfy Cloud 실행 안 함"이라고 분명히 적습니다. 실행하지 않은 품질 향상을 주장하지 않습니다.

## 실행 환경

- Comfy Cloud에서 추가 설치 없이 돌아가야 합니다. 코어 노드와 Cloud 사전 설치 팩(KJNodes, WAS, layerstyle, Image-Filters, Impact, VHS, Essentials, ControlNet aux, IPAdapter, AnimateDiff-Evolved)만 씁니다. 새 노드 팩은 설치할 수 없습니다.
- Cloud 기본 모델은 파일명 그대로 씁니다. 직접 가져온 모델은 `소유자__저장소__파일명` 형식이고, 저장소 이름의 점은 지웁니다. 예: `lightx2v__Minimax-h3-Turbo__파일명.safetensors`.
- 모델을 불러오는 노드의 `properties.models`에 `{name, url, directory}`를 넣습니다. url은 Hugging Face의 `/resolve/` 직접 링크입니다.

## 그래프 구조

- `입력 노드 → 메인 서브그래프 노드 1개 → 저장 노드` 구조로 만듭니다. 영상·이미지 로드와 저장, 대화형 에디터만 서브그래프 밖에 둡니다.
- 프롬프트, 길이, 시드, 스위치, 모델·LoRA 선택처럼 사람이 바꾸는 값은 메인 노드에 노출합니다.
- 최상위 그룹은 `01 입력 · 이 칸부터`, `02 편집`, `03 결과`입니다. 서브그래프 안은 번호가 붙은 한국어 그룹으로 나눕니다.
- 노드는 최소로 씁니다. 문어발처럼 늘어놓지 않고, 그래프가 무거워지면 안 됩니다.
- 노드 위치와 크기는 15의 배수로 잡고, 제목 표시줄 30px까지 포함해 겹치지 않게 합니다.
- 한 번 실행에 최종 저장은 1개입니다. 비교본, 미리보기 저장은 넣지 않습니다.
- 매트와 알파는 MP4로 저장합니다. 프레임별 PNG 저장은 넣지 않습니다. 116프레임 영상에서 PNG 저장을 뺐더니 5분 넘게 걸리던 작업이 10초로 줄었습니다.
- 짧은 사용법 노트와, 모델·설정·한계를 적은 상세 노트를 MarkdownNote로 넣습니다. 노트 내용은 실제 동작과 같아야 합니다.

## 자동화와 정확도

- 출력의 가로·세로, 프레임 수, FPS는 원본을 자동으로 따라갑니다. 값을 고정하지 않습니다.
- 프레임 드랍과 크롭이 없어야 합니다. 모델 규격을 맞추려고 패딩했다면 생성 뒤 원본 길이와 크기로 되돌립니다.
- H3는 24fps, 17k+5 프레임, 32의 배수 크기입니다. LTX는 8n+1 프레임입니다. 크기 처리는 같은 모델의 기존 파일을 따릅니다.
- VFX 작업은 바꾸는 부분 외에 색감, 움직임, 프레임이 틀어지면 안 됩니다.
- 마스크는 흰색이 바꿀 곳입니다. 마스크를 받는 파일에는 반전 스위치를 둡니다.
- 소스 영상에 오디오가 없어도 실패하면 안 됩니다.

## JSON에서 자주 틀리는 부분

- `widgets_values`와 `widgets_values_named`가 함께 있으면 둘 다 바꿉니다. Cloud는 이름 있는 값을 먼저 읽을 수 있습니다.
- 메인 노드의 `widgets_values`는 위치 순서로 읽힙니다. 안쪽 위젯으로 이어지는 입력은 바깥에서 연결되어 있어도 칸을 차지합니다. 하나 빠지면 뒤의 값이 전부 밀립니다.
- 서브그래프 안에 다른 서브그래프가 있으면 `definitions.subgraphs`에서 자식을 부모보다 앞에 둡니다.
- 노드의 `mode`를 지우지 않습니다. 지우면 꺼 둔 노드가 켜집니다.
- `model`처럼 선택에 따라 칸이 바뀌는 콤보는 메인 노드로 올리지 않습니다.
- 스위치 노드는 실행을 건너뛰어도 검증은 합니다. 꺼진 경로의 모델 파일도 있어야 합니다.
- 크기를 맞추는 노드 일부는 가운데를 잘라냅니다(`ResizeImageMaskNode`의 배수 맞춤, `MiniMaxH3AddGuide`). HDR 값에는 lanczos를 쓰지 않습니다.
- `ImageBlend`의 difference는 한쪽 방향 차이입니다. 절대 차이가 필요하면 양쪽으로 구해 screen으로 합칩니다.

## 프롬프트

- H3 편집은 재생 속도와 타이밍을 적습니다. 예: `each frame shows the same moment as the same frame of <Video 1>, at the original playback speed`.
- 지우기는 사라진 뒤의 빈 장면만 묘사합니다. "Remove the man"이라고 쓰면 새 사람이 생길 수 있습니다.
- LTX 인페인팅으로 지울 때는 프롬프트를 비웁니다.
- LoRA 트리거를 지킵니다. 예: `vfx_edit:`, `edit_anything:`. EditAnything은 Replace, Add, Remove, Restyle 동사만 씁니다.

## 모델 선택

- 같은 기능에서 파일 날짜, 좋아요, 다운로드 수를 함께 비교합니다. 날짜와 호환성만 보고 유지로 끝내지 않습니다.
- 다만 Cloud에 없는 노드 팩이 필요하면 쓸 수 없습니다. 기본 모델이 다르면 중복이 아닙니다.
- Ref2VA 그래프에는 ref2v 터보, FL2VA 그래프에는 fl2v 터보를 씁니다. 터보 LoRA는 강도 1, CFG 1, euler, simple을 기준으로 합니다. ref2v는 시프트 12/3, fl2v 8스텝 v1.1 768p는 6/3입니다.
- 스텝은 가볍게 잡습니다. 28스텝은 무겁다는 지시가 있었고 터보 4~8스텝을 씁니다.
- 잘 나온다고 확인된 기본값은 시험 없이 바꾸지 않습니다. 고치면 새 파일이나 선택 옵션으로 추가합니다.
- 우선순위는 H3와 LTX입니다. WAN은 가장 뒤입니다.

## 파일 이름과 보고

- 이름은 `번호_모델버전_기능_방식.json`으로 씁니다. 모델 버전과 마스크 필요 여부를 이름에서 알 수 있게 합니다. 측정한 시간이 있으면 끝에 초를 붙입니다.
- 보고는 고친 파일, 고친 이유, 확인한 범위, 확인 못 한 것을 나눠서 씁니다. 확인된 문제와 추측을 섞지 않습니다.

## 납품 전 점검

1. JSON이 파싱되고 모든 링크의 양쪽 끝이 일치하는가
2. 없는 노드·모델을 쓰지 않았는가
3. 원본 크기·길이·FPS를 자동으로 따르는가
4. 메인 노드의 값이 올바른 칸에 들어가는가
5. 노트와 제목이 실제 동작과 같은가
6. 노드가 겹치지 않고 저장이 1개인가

## 제작·수정 규격

라이브러리 파일에서 뽑은 실제 구조입니다. 새로 만들 때와 고칠 때 모두 이 틀을 따릅니다. 처음부터 그래프를 짜지 말고, 아래 표의 기준 파일을 복사해서 바꿉니다.

### 1. 기준 파일

경로는 `workflows/` 기준입니다.

| 만들 것 | 복사할 파일 |
|---|---|
| H3 글로만 편집 | `01_영상편집_VFX/01_글로만_지시/03_H3_R2V_글로편집_Turbo4.json` |
| H3 참고 사진으로 교체 | `01_영상편집_VFX/02_참고사진으로_교체_마스크없음/03_H3_VFX_의상·사물교체_참고사진_60초_H3-03.json` |
| H3 고친 첫 프레임 전파 | `01_영상편집_VFX/03_첫프레임_고쳐서_전체에_전파/02_H3_Ripple_앵커프레임전파_37초_H3-01.json` |
| H3 얼굴 교체 | `02_인물·얼굴_교체/01_H3_HeadSwap_얼굴만교체_사진1장_41초.json` |
| H3 인물 전체 교체 | `02_인물·얼굴_교체/02_H3_CharacterSwap_인물전체·의상교체_64초.json` |
| H3 화면 밖 확장 | `04_화면밖_확장/02_H3_아웃페인팅_41초.json` |
| H3 영상 연장 | `05_영상_뒤로_연장/01_H3_영상연장_Turbo8_80초.json` |
| Pika 사물 교체 | `01_영상편집_VFX/02_참고사진으로_교체_마스크없음/02_Pika_Ref2VA_사물교체_제품사진1장_50초_H3-02.json` |
| LTX 첫 프레임 전파 | `01_영상편집_VFX/03_첫프레임_고쳐서_전체에_전파/01_LTX_Ripple_첫프레임전파_34초_LTX-02.json` |
| LTX 마스크 인페인팅 | `01_영상편집_VFX/04_마스크로_영역지정_원본보존/01_LTX_인페인팅_마스크+첫프레임_18초_LTX-01.json` |
| LTX 글로만 편집 | `01_영상편집_VFX/01_글로만_지시/01_LTX_EditAnything_글로편집_23초_LTX-03.json` |
| LTX 화면 밖 확장 | `04_화면밖_확장/01_LTX2.5_아웃페인팅_원본1대1_43초.json` |
| 로토·매트 | `08_로토·마스크·패스/01_SAM3.1_로토매트_글자·클릭지정_55초.json` |
| 이미지 편집 | `09_이미지_생성·편집/01_Qwen2.1_이미지편집_글로지시_14초.json` |

### 2. 최상위 배치

H3 VFX 파일의 실제 값입니다. 좌표는 15의 배수로 씁니다.

| 칸 | 그룹 제목 | 들어가는 노드 | 노드 위치 |
|---|---|---|---|
| 왼쪽 | `01 입력 · 원본 영상 + 참고 사진` | LoadVideo, LoadImage | x 30, y 60부터 |
| 가운데 | `02 편집 · 지시와 설정` | 메인 서브그래프 노드 1개 | x 555, y 60 |
| 오른쪽 | `03 결과 · 확인 후 저장` | SaveVideo | x 1365, y 60 |
| 아래 | `안내 · 사용법과 검증 범위` | MarkdownNote | x 30, y 1080 |

입력 노드 제목은 `① 원본 영상`, `② 참고 사진`처럼 순서를 붙입니다. 메인 노드 제목은 `H3 · VFX 사진 참조 편집 · 일반`처럼 모델과 기능을 적습니다.

### 3. 메인 서브그래프 JSON

서브그래프는 `definitions.subgraphs`에 정의하고, 최상위 노드의 `type`에 그 `id`를 넣습니다. 형식은 `version: 0.4` 파일을 따릅니다.

정의에 필요한 키는 `id, version, state, revision, config, name, inputNode, outputNode, inputs, outputs, widgets, nodes, groups, links, extra`입니다. `inputNode.id`는 `-10`, `outputNode.id`는 `-20`입니다.

링크 형식이 위치에 따라 다릅니다.

```json
최상위: [1, 1, 0, 38, 0, "VIDEO"]
서브그래프: {"id": 1, "origin_id": -10, "origin_slot": 0, "target_id": 4, "target_slot": 0, "type": "VIDEO"}
```

메인 노드에 값을 노출하는 입력입니다. 소켓과 위젯의 모양이 다릅니다.

```json
소켓: {"name": "VIDEO", "type": "VIDEO", "link": 1, "label": "① 원본 영상", "localized_name": "VIDEO"}
위젯: {"name": "prompt", "type": "STRING", "link": null, "widget": {"name": "prompt"}, "label": "③ 편집 지시", "localized_name": "prompt"}
서브그래프 입력: {"id": "uuid", "name": "prompt", "type": "STRING", "linkIds": [58], "localized_name": "prompt", "label": "③ 편집 지시", "pos": [0, 0]}
```

메인 노드의 `widgets_values`는 위젯 입력 순서대로 씁니다. 소켓 입력은 칸을 차지하지 않습니다. `widgets_values_named`에도 같은 값을 넣습니다.

노출할 값은 프롬프트, LoRA, 추론 해상도, 시드, 스텝처럼 사람이 바꾸는 것만 고릅니다. 라벨은 `시드 · 고정 = 같은 조건 비교`처럼 한국어로 뜻을 적습니다.

### 4. 서브그래프 안 그룹

모델과 작업에 맞춰 번호를 붙여 왼쪽에서 오른쪽으로 놓습니다. 그룹 `font_size`는 24입니다.

| 파일 | 그룹 순서 |
|---|---|
| H3 VFX | 01 추론 크기, 02 모델, 03 조건과 샘플링, 04 프레임 준비, 05 출력 · 원본 규격 복원, 06 첫 프레임 추출 |
| LTX Ripple | 01 모델 로드, 02 LoRA · 모델 패치, 03 설정값, 04 프롬프트, 05 입력 · 크기 · 길이, 06 샘플링, 07 디코드 · 출력, 08 출력 · 원본 FPS 무음 |

### 5. 자동화 체인

크기, 길이, FPS는 입력 영상에서 계산합니다. 숫자를 직접 넣지 않습니다. `ComfyMathExpression`은 `values.a`, `values.b` 등을 받고, 출력 슬롯은 FLOAT 0, INT 1, BOOL 2입니다.

#### 공통 시작

1. 서브그래프 입력 VIDEO를 `GetVideoComponents`에 연결합니다. 출력은 images 0, audio 1, fps 2입니다.
2. images를 `GetImageSize`에 연결합니다. 출력은 width 0, height 1, batch_size 2이고, batch_size가 프레임 수 N입니다.
3. 마지막 `CreateVideo`의 `fps`에 위 fps를 연결합니다.

#### H3

| 값 | 수식 |
|---|---|
| 추론 가로 (a=W, b=H, c=MP) | `max(32,round(a*min(1,sqrt(max(0.01,c)*1000000/(a*b)))/32)*32)` |
| 추론 세로 | `max(32,round(b*min(1,sqrt(max(0.01,c)*1000000/(a*b)))/32)*32)` |
| 모델 길이 M = 17k+5 (a=N) | `max(5,5+17*ceil(max(0,a-5)/17)) if 1<=a<=362 else 1/0` |
| 임시 꼬리 길이 (a=M, b=N) | `max(1,a-b)` |

362프레임을 넘으면 `1/0`으로 멈춰서 조용히 잘리지 않게 합니다.

순서: 마지막 프레임을 `ImageFromBatch`로 꺼내 `RepeatImageBatch`로 꼬리 길이만큼 반복하고 `ImageBatch`로 붙입니다. `ImageFromBatch`로 길이 M을 맞춰 가이드로 씁니다. 디코드 뒤에는 `ImageFromBatch`로 길이 N을 맞추고 원본 W×H로 되돌린 다음 `CreateVideo`로 저장합니다.

#### LTX

| 값 | 수식 |
|---|---|
| 모델 길이 M = 8n+1, 수정 프레임 1장 포함 (a=N) | `1 + ceil(a / 8) * 8` |
| 추론 가로 (c=짧은 변, 0이면 원본) | `max(64, floor(a * ((c if c > 0 else min(a, b)) / min(a, b)) / 32 + 0.5) * 32)` |
| 추론 세로 | `max(64, floor(b * ((c if c > 0 else min(a, b)) / min(a, b)) / 32 + 0.5) * 32)` |

Ripple은 수정 프레임을 앞에 붙이므로 출력은 `ImageFromBatch`로 1번부터 N장을 잘라 1프레임 밀림을 맞춥니다.

### 6. 노드 색

| color | bgcolor | 쓰는 곳 |
|---|---|---|
| `#31506a` | `#1d2f41` | 모델 로더 (UNET, CLIP, VAE, LoRA) |
| `#68532c` | `#342b1d` | 설정값 (Primitive, Seed) |
| `#4e4369` | `#2a2540` | 프롬프트와 조건 (CLIPTextEncode, AddGuide, ReferenceToVideo) |
| `#27575a` | `#1a3538` | 크기·길이 계산과 프레임 처리 (Math, ImageFromBatch, GetImageSize) |
| `#5d3c68` | `#312039` | 샘플링 (RandomNoise, KSampler, SigmaShift) |
| `#68503c` | `#382a20` | 디코드와 합성 |
| `#365963` | `#202c32` | 최종 출력 (CreateVideo, SaveVideo) |

### 7. 고칠 때

1. 대상 파일을 읽고 메인 노드의 입력과 내부 그룹을 파악합니다.
2. 고칠 곳만 고칩니다. 구조, 기본값, 노드 색과 배치는 유지합니다.
3. 값을 바꾸면 `widgets_values`와 `widgets_values_named`를 같이 바꿉니다.
4. 노드를 추가하면 링크 양쪽(`links`, `inputs[].link`, `outputs[].links`)과 `state.lastNodeId`, `state.lastLinkId`를 갱신합니다.
5. 새 파일 이름으로 저장하고, 안내 노트 맨 위에 바뀐 내용을 적습니다.

### 8. 새로 만들 때

1. 1번 표에서 가장 가까운 파일을 복사합니다.
2. 모델 로더와 LoRA, 조건 노드만 필요한 것으로 바꿉니다. 자동화 체인은 그대로 둡니다.
3. 메인 노드 라벨, 저장 접두사, 안내 노트를 새 내용으로 바꿉니다.
4. `properties.models`에 다운로드 링크를 넣습니다.
5. 최상위 `id`는 새 UUID로 바꿉니다.
