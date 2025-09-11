# Video Upscale & Frame Interpolation for RunPod Serverless
[한국어 README 보기](README_kr.md)

This project is a RunPod Serverless template for video upscaling and frame interpolation using ComfyUI.

[![Runpod](https://api.runpod.io/badge/wlsdml1114/upscale_interpolation_runpod_hub)](https://console.runpod.io/hub/wlsdml1114/upscale_interpolation_runpod_hub)

## 🎨 Engui Studio Integration

[![EnguiStudio](https://raw.githubusercontent.com/wlsdml1114/Engui_Studio/main/assets/banner.png)](https://github.com/wlsdml1114/Engui_Studio)

This InfiniteTalk template is primarily designed for **Engui Studio**, a comprehensive AI model management platform. While it can be used via API, Engui Studio provides enhanced features and broader model support.

**Engui Studio Benefits:**
- **Expanded Model Support**: Access to a wider variety of AI models beyond what's available through API
- **Enhanced User Interface**: Intuitive workflow management and model selection
- **Advanced Features**: Additional tools and capabilities for AI model deployment
- **Seamless Integration**: Optimized for Engui Studio's ecosystem

> **Note**: While this template works perfectly with API calls, Engui Studio users will have access to additional models and features that are planned for future releases.

## ✨ Key Features

*   **Video Upscaling**: High-quality video upscaling for resolution enhancement
*   **Frame Interpolation**: Natural frame interpolation using RIFE model
*   **ComfyUI Integration**: Flexible workflow management based on ComfyUI
*   **VHS Support**: Efficient video processing using Video Helper Suite
*   **Multiple Input Formats**: Support for Base64, URL, and file path inputs

## 🚀 RunPod Serverless Template

This template includes all necessary components to run video upscaling and frame interpolation as a RunPod Serverless Worker.

*   **Dockerfile**: Environment configuration and installation of all dependencies required for model execution
*   **handler.py**: Handler function that processes requests for RunPod Serverless
*   **entrypoint.sh**: Performs initialization tasks when the worker starts
*   **upscale.json**: Video upscaling only workflow configuration
*   **upscale_and_interpolation.json**: Upscaling + frame interpolation workflow configuration

### Input

The `input` object must contain the following fields. Videos can be input using **path, URL, or Base64** - one method for each.

#### Workflow Selection Parameters
| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `task_type` | `string` | No | `"upscale"` | Task type: `"upscale"` (upscaling only) or `"upscale_and_interpolation"` (upscaling + frame interpolation) |

#### Video Input (use only one)
| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `video_path` | `string` | No | `/example_video.mp4` | Local path to the input video file |
| `video_url` | `string` | No | `/example_video.mp4` | URL to the input video file |
| `video_base64` | `string` | No | `/example_video.mp4` | Base64 encoded string of the input video file |

**Request Examples:**

#### 1. Upscaling Only (using URL)
```json
{
  "input": {
    "task_type": "upscale",
    "video_url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"
  }
}
```

#### 2. Upscaling + Frame Interpolation (using file path)
```json
{
  "input": {
    "task_type": "upscale_and_interpolation",
    "video_path": "/my_volume/input_video.mp4"
  }
}
```

#### 3. Using Base64 (Upscaling Only)
```json
{
  "input": {
    "task_type": "upscale",
    "video_base64": "data:video/mp4;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
  }
}
```

### Output

#### Success

If the job is successful, it returns a JSON object with the generated video Base64 encoded.

| Parameter | Type | Description |
| --- | --- | --- |
| `video` | `string` | Base64 encoded video file data |

**Success Response Example:**

```json
{
  "video": "data:video/mp4;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
}
```

#### Error

If the job fails, it returns a JSON object containing an error message.

| Parameter | Type | Description |
| --- | --- | --- |
| `error` | `string` | Description of the error that occurred |

**Error Response Example:**

```json
{
  "error": "비디오를 찾을 수 없습니다."
}
```

## 🛠️ Usage and API Reference

1.  Create a Serverless Endpoint on RunPod based on this repository.
2.  Once the build is complete and the endpoint is active, submit jobs via HTTP POST requests according to the API Reference below.

### 📁 Using Network Volumes

Instead of directly transmitting Base64 encoded files, you can use RunPod's Network Volumes to handle large files. This is especially useful when dealing with large video files.

1.  **Create and Connect Network Volume**: Create a Network Volume (e.g., S3-based volume) from the RunPod dashboard and connect it to your Serverless Endpoint settings.
2.  **Upload Files**: Upload the video files you want to use to the created Network Volume.
3.  **Specify Paths**: When making an API request, specify the file paths within the Network Volume for `video_path`. For example, if the volume is mounted at `/my_volume` and you use `input_video.mp4`, the path would be `"/my_volume/input_video.mp4"`.

## 🔧 Workflow Configuration

This template includes two workflow configurations that are automatically selected based on your input parameters:

*   **upscale.json**: Video upscaling only workflow
*   **upscale_and_interpolation.json**: Upscaling + frame interpolation workflow

### Workflow Selection Logic

The handler automatically selects the appropriate workflow based on your input parameters:

| task_type | Selected Workflow |
|-----------|-------------------|
| `"upscale"` | upscale.json |
| `"upscale_and_interpolation"` | upscale_and_interpolation.json |

The workflows are based on ComfyUI and include all necessary nodes for video upscaling and frame interpolation processing. Each workflow is optimized for its specific use case and includes the appropriate model configurations.

## 🙏 Original Project

This project is based on the following original repositories. All rights to the models and core logic belong to the original authors.

*   **ComfyUI:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
*   **ComfyUI-Frame-Interpolation:** [https://github.com/Fannovel16/ComfyUI-Frame-Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation)
*   **VHS (Video Helper Suite):** [https://github.com/wlsdml1114/ComfyUI-VideoHelperSuite](https://github.com/wlsdml1114/ComfyUI-VideoHelperSuite)

## 📄 License

This project follows the Apache 2.0 License.