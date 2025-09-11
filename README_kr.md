# 비디오 업스케일 & 프레임 보간

이 프로젝트는 ComfyUI를 사용하여 비디오 업스케일링과 프레임 보간을 수행하는 RunPod 서버리스 함수입니다.

## 기능

### 1. 비디오 업스케일링 (Video Upscaling)
- ComfyUI의 ImageUpscaleWithModelBatched 노드를 사용한 고품질 비디오 업스케일링
- VHS (Video Helper Suite) 노드를 활용한 비디오 처리
- Base64 인코딩된 비디오 입력/출력 지원

### 2. 비디오 업스케일링 + 프레임 보간 (Video Upscaling + Frame Interpolation)
- 비디오 업스케일링 후 RIFE 모델을 사용한 고품질 프레임 보간
- VHS (Video Helper Suite) 노드를 활용한 비디오 처리
- Base64 인코딩된 비디오 입력/출력 지원

## 사용법

### 1. 비디오 업스케일링만
```json
{
  "task_type": "upscale",
  "video_path": "path/to/video.mp4"
}
```

### 2. 비디오 업스케일링 + 프레임 보간
```json
{
  "task_type": "upscale_and_interpolation",
  "video_path": "path/to/video.mp4"
}
```

**파라미터:**
- `task_type`: 작업 타입 ("upscale" 또는 "upscale_and_interpolation")
- `video_path`: 입력 비디오 경로 또는 Base64 문자열

## 응답 형식

### 업스케일링만 응답
```json
{
  "task_type": "upscale",
  "videos": ["base64_encoded_video"]
}
```

### 업스케일링 + 프레임 보간 응답
```json
{
  "task_type": "upscale_and_interpolation",
  "videos": ["base64_encoded_video"]
}
```

## 설치 및 실행

1. Docker 이미지 빌드:
```bash
docker build -t upscale-interpolation .
```

2. 컨테이너 실행:
```bash
docker run -p 8000:8000 upscale-interpolation
```

## 의존성

- Python 3.8+
- ComfyUI
- ComfyUI-Frame-Interpolation
- ComfyUI_LayerStyle
- PyTorch (CUDA 지원)
- RunPod SDK
- 업스케일링 모델: 2x-AnimeSharpV4, 4x-AnimeSharpV4
- 프레임 보간 모델: RIFE v4.6

## 주의사항

- 입력 비디오는 Base64 인코딩된 문자열 또는 파일 경로로 전달할 수 있습니다.
- 임시 파일은 작업 완료 후 자동으로 정리됩니다.
- 비디오 파일은 메모리 사용량이 크므로 큰 파일 처리 시 주의하세요.
- 처리 시간은 비디오 길이와 해상도에 따라 달라집니다.

## 예제 사용법

### 1. 비디오 업스케일링만
```python
import requests
import base64

# 비디오 파일을 Base64로 인코딩
with open("input.mp4", "rb") as f:
    video_data = base64.b64encode(f.read()).decode()

# API 호출
response = requests.post("your-runpod-endpoint", json={
    "input": {
        "task_type": "upscale",
        "video_path": video_data
    }
})

# 결과 비디오 저장
result = response.json()
if "videos" in result:
    with open("upscaled.mp4", "wb") as f:
        f.write(base64.b64decode(result["videos"][0]))
```

### 2. 비디오 업스케일링 + 프레임 보간
```python
# 비디오 파일을 Base64로 인코딩
with open("input.mp4", "rb") as f:
    video_data = base64.b64encode(f.read()).decode()

# API 호출
response = requests.post("your-runpod-endpoint", json={
    "input": {
        "task_type": "upscale_and_interpolation",
        "video_path": video_data
    }
})

# 결과 비디오 저장
result = response.json()
if "videos" in result:
    with open("upscaled_interpolated.mp4", "wb") as f:
        f.write(base64.b64decode(result["videos"][0]))
```
