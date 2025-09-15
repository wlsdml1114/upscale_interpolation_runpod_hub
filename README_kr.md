# Video Upscale & Frame Interpolation for RunPod Serverless
[English README](README.md)

이 프로젝트는 ComfyUI를 사용하여 비디오 업스케일링과 프레임 보간을 수행하는 RunPod 서버리스 템플릿입니다.

[![Runpod](https://api.runpod.io/badge/wlsdml1114/upscale_interpolation_runpod_hub)](https://console.runpod.io/hub/wlsdml1114/upscale_interpolation_runpod_hub)

## 🎨 Engui Studio 통합

[![EnguiStudio](https://raw.githubusercontent.com/wlsdml1114/Engui_Studio/main/assets/banner.png)](https://github.com/wlsdml1114/Engui_Studio)

이 InfiniteTalk 템플릿은 포괄적인 AI 모델 관리 플랫폼인 **Engui Studio**를 위해 주로 설계되었습니다. API를 통해 사용할 수 있지만, Engui Studio는 향상된 기능과 더 넓은 모델 지원을 제공합니다.

**Engui Studio의 장점:**
- **확장된 모델 지원**: API를 통해 사용 가능한 것보다 더 다양한 AI 모델에 접근
- **향상된 사용자 인터페이스**: 직관적인 워크플로우 관리 및 모델 선택
- **고급 기능**: AI 모델 배포를 위한 추가 도구 및 기능
- **원활한 통합**: Engui Studio 생태계에 최적화

> **참고**: 이 템플릿은 API 호출로도 완벽하게 작동하지만, Engui Studio 사용자는 향후 출시 예정인 추가 모델과 기능에 접근할 수 있습니다.

## ✨ 주요 기능

*   **비디오 업스케일링**: 고품질 비디오 업스케일링을 통한 해상도 향상
*   **프레임 보간**: RIFE 모델을 사용한 자연스러운 프레임 보간
*   **ComfyUI 통합**: ComfyUI 기반의 유연한 워크플로우 관리
*   **VHS 지원**: Video Helper Suite를 활용한 효율적인 비디오 처리
*   **다양한 입력 형식**: Base64, URL, 파일 경로 지원

## 🚀 RunPod 서버리스 템플릿

이 템플릿은 비디오 업스케일링과 프레임 보간을 RunPod 서버리스 워커로 실행하는 데 필요한 모든 구성 요소를 포함합니다.

*   **Dockerfile**: 모델 실행에 필요한 환경 설정 및 의존성 설치
*   **handler.py**: RunPod 서버리스 요청을 처리하는 핸들러 함수
*   **entrypoint.sh**: 워커 시작 시 초기화 작업 수행
*   **upscale.json**: 비디오 업스케일링 전용 워크플로우 설정
*   **upscale_and_interpolation.json**: 업스케일링 + 프레임 보간 워크플로우 설정

### 입력

`input` 객체는 다음 필드를 포함해야 합니다. 비디오는 **경로, URL 또는 Base64** 중 하나의 방법으로 입력할 수 있습니다.

#### 워크플로우 선택 파라미터
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `task_type` | `string` | 아니오 | `"upscale"` | 작업 타입: `"upscale"` (업스케일링만) 또는 `"upscale_and_interpolation"` (업스케일링 + 프레임 보간) |
| `network_volume` | `boolean` | 아니오 | `false` | 네트워크 볼륨 사용 여부. `true`이면 파일 경로 반환, `false`이면 Base64 인코딩된 데이터 반환 |

#### 비디오 입력 (하나만 사용)
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `video_path` | `string` | 아니오 | `/example_video.mp4` | 입력 비디오 파일의 로컬 경로 |
| `video_url` | `string` | 아니오 | `/example_video.mp4` | 입력 비디오 파일의 URL |
| `video_base64` | `string` | 아니오 | `/example_video.mp4` | 입력 비디오 파일의 Base64 인코딩 문자열 |

**요청 예시:**

#### 1. 업스케일링만 (URL 사용)
```json
{
  "input": {
    "task_type": "upscale",
    "video_url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"
  }
}
```

#### 2. 업스케일링 + 프레임 보간 (파일 경로 사용)
```json
{
  "input": {
    "task_type": "upscale_and_interpolation",
    "video_path": "/my_volume/input_video.mp4"
  }
}
```

#### 3. Base64 사용 (업스케일링만)
```json
{
  "input": {
    "task_type": "upscale",
    "video_base64": "data:video/mp4;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
  }
}
```

### 출력

#### 성공

작업이 성공하면 JSON 객체를 반환합니다. 응답 형식은 `network_volume` 파라미터에 따라 달라집니다.

**`network_volume: true`인 경우:**

| 파라미터 | 타입 | 설명 |
| --- | --- | --- |
| `video_path` | `string` | 생성된 비디오 파일의 경로 |

```json
{
  "video_path": "/runpod-volume/upscale_e5f6c1c3-e784-4e90-96a7-32f0be222d3c.mp4"
}
```

**`network_volume: false` (기본값)인 경우:**

| 파라미터 | 타입 | 설명 |
| --- | --- | --- |
| `video` | `string` | Base64 인코딩된 비디오 파일 데이터 |

```json
{
  "video": "data:video/mp4;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
}
```

#### 오류

작업이 실패하면 오류 메시지가 포함된 JSON 객체를 반환합니다.

| 파라미터 | 타입 | 설명 |
| --- | --- | --- |
| `error` | `string` | 발생한 오류에 대한 설명 |

**오류 응답 예시:**

```json
{
  "error": "비디오를 찾을 수 없습니다."
}
```

## 🛠️ 사용법 및 API 참조

1.  이 저장소를 기반으로 RunPod에서 서버리스 엔드포인트를 생성합니다.
2.  빌드가 완료되고 엔드포인트가 활성화되면 아래 API 참조에 따라 HTTP POST 요청으로 작업을 제출합니다.

### 📁 네트워크 볼륨 사용

Base64 인코딩된 파일을 직접 전송하는 대신 RunPod의 네트워크 볼륨을 사용하여 대용량 파일을 처리할 수 있습니다. 이는 특히 큰 비디오 파일을 다룰 때 유용합니다.

1.  **네트워크 볼륨 생성 및 연결**: RunPod 대시보드에서 네트워크 볼륨(예: S3 기반 볼륨)을 생성하고 서버리스 엔드포인트 설정에 연결합니다.
2.  **파일 업로드**: 사용할 비디오 파일을 생성된 네트워크 볼륨에 업로드합니다.
3.  **경로 지정**: API 요청 시 네트워크 볼륨 내의 파일 경로를 `video_path`에 지정합니다. 예를 들어 볼륨이 `/my_volume`에 마운트되고 `input_video.mp4`를 사용하는 경우 경로는 `"/my_volume/input_video.mp4"`가 됩니다.

## 🔧 워크플로우 구성

이 템플릿은 입력 파라미터에 따라 자동으로 선택되는 두 가지 워크플로우 구성을 포함합니다:

*   **upscale.json**: 비디오 업스케일링 전용 워크플로우
*   **upscale_and_interpolation.json**: 업스케일링 + 프레임 보간 워크플로우

### 워크플로우 선택 로직

핸들러는 입력 파라미터에 따라 적절한 워크플로우를 자동으로 선택합니다:

| task_type | 선택된 워크플로우 |
|-----------|------------------|
| `"upscale"` | upscale.json |
| `"upscale_and_interpolation"` | upscale_and_interpolation.json |

워크플로우는 ComfyUI를 기반으로 하며 비디오 업스케일링과 프레임 보간 처리에 필요한 모든 노드를 포함합니다. 각 워크플로우는 특정 사용 사례에 최적화되어 있으며 적절한 모델 구성을 포함합니다.

## 🙏 원본 프로젝트

이 프로젝트는 다음 원본 저장소를 기반으로 합니다. 모델 및 핵심 로직의 모든 권리는 원본 작성자에게 있습니다.

*   **ComfyUI:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
*   **ComfyUI-Frame-Interpolation:** [https://github.com/Fannovel16/ComfyUI-Frame-Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation)
*   **VHS (Video Helper Suite):** [https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)

## 📄 라이선스

이 프로젝트는 Apache 2.0 라이선스를 따릅니다.
