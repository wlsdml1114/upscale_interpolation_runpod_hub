# Upscale & Frame Interpolation

이 프로젝트는 이미지 업스케일링과 프레임 보간을 위한 RunPod 서버리스 함수입니다.

## 기능

### 1. 이미지 업스케일링 (Image Upscaling)
- 다양한 업스케일링 방법 지원 (bicubic, lanczos, nearest)
- 사용자 정의 스케일 팩터 설정 가능
- Base64 인코딩된 이미지 입력/출력 지원

### 2. 프레임 보간 (Frame Interpolation)
- 두 프레임 사이에 중간 프레임 생성
- 선형 보간을 사용한 자연스러운 전환
- 다중 보간 프레임 생성 지원

### 3. 비디오 프레임 보간 (Video Frame Interpolation)
- 비디오에서 프레임 추출
- 연속된 프레임들 사이에 보간 프레임 생성
- 프레임 추출 간격 조정 가능

## 사용법

### 이미지 업스케일링
```json
{
  "task_type": "upscale",
  "image_path": "path/to/image.jpg",
  "scale_factor": 2,
  "method": "bicubic"
}
```

**파라미터:**
- `task_type`: "upscale"
- `image_path`: 입력 이미지 경로 또는 Base64 문자열
- `scale_factor`: 스케일 팩터 (기본값: 2)
- `method`: 업스케일링 방법 ("bicubic", "lanczos", "nearest")

### 프레임 보간
```json
{
  "task_type": "interpolate",
  "frame1_path": "path/to/frame1.jpg",
  "frame2_path": "path/to/frame2.jpg",
  "num_frames": 1
}
```

**파라미터:**
- `task_type`: "interpolate"
- `frame1_path`: 첫 번째 프레임 경로 또는 Base64 문자열
- `frame2_path`: 두 번째 프레임 경로 또는 Base64 문자열
- `num_frames`: 생성할 보간 프레임 수 (기본값: 1)

### 비디오 프레임 보간
```json
{
  "task_type": "video_interpolate",
  "video_path": "path/to/video.mp4",
  "frame_interval": 1,
  "interpolation_factor": 1
}
```

**파라미터:**
- `task_type`: "video_interpolate"
- `video_path`: 입력 비디오 경로 또는 Base64 문자열
- `frame_interval`: 프레임 추출 간격 (기본값: 1)
- `interpolation_factor`: 보간 팩터 (기본값: 1)

## 응답 형식

### 업스케일링 응답
```json
{
  "task_type": "upscale",
  "result": "base64_encoded_image",
  "scale_factor": 2,
  "method": "bicubic"
}
```

### 프레임 보간 응답
```json
{
  "task_type": "interpolate",
  "result": ["base64_frame1", "base64_frame2", ...],
  "num_frames": 1
}
```

### 비디오 보간 응답
```json
{
  "task_type": "video_interpolate",
  "result": ["base64_frame1", "base64_frame2", ...],
  "original_frames": 10,
  "interpolated_frames": 20
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
- OpenCV (cv2)
- Pillow (PIL)
- NumPy
- RunPod SDK

## 주의사항

- 입력 이미지/비디오는 Base64 인코딩된 문자열 또는 파일 경로로 전달할 수 있습니다.
- 임시 파일은 작업 완료 후 자동으로 정리됩니다.
- 메모리 사용량을 고려하여 큰 파일 처리 시 주의하세요.
