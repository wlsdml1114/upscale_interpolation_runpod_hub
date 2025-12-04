import runpod
from runpod.serverless.utils import rp_upload
import os
import websocket
import base64
import json
import uuid
import logging
import urllib.request
import urllib.parse
import binascii # Base64 에러 처리를 위해 import
import time
from PIL import Image
import cv2

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CUDA 검사 및 설정
def check_cuda_availability():
    """CUDA 사용 가능 여부를 확인하고 환경 변수를 설정합니다."""
    try:
        import torch
        if torch.cuda.is_available():
            logger.info("✅ CUDA is available and working")
            os.environ['CUDA_VISIBLE_DEVICES'] = '0'
            return True
        else:
            logger.error("❌ CUDA is not available")
            raise RuntimeError("CUDA is required but not available")
    except Exception as e:
        logger.error(f"❌ CUDA check failed: {e}")
        raise RuntimeError(f"CUDA initialization failed: {e}")

# CUDA 검사 실행
try:
    cuda_available = check_cuda_availability()
    if not cuda_available:
        raise RuntimeError("CUDA is not available")
except Exception as e:
    logger.error(f"Fatal error: {e}")
    logger.error("Exiting due to CUDA requirements not met")
    exit(1)


server_address = os.getenv('SERVER_ADDRESS', '127.0.0.1')
client_id = str(uuid.uuid4())
    
def queue_prompt(prompt):
    url = f"http://{server_address}:8188/prompt"
    logger.info(f"Queueing prompt to: {url}")
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    url = f"http://{server_address}:8188/view"
    logger.info(f"Getting image from: {url}")
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"{url}?{url_values}") as response:
        return response.read()

def get_history(prompt_id):
    url = f"http://{server_address}:8188/history/{prompt_id}"
    logger.info(f"Getting history from: {url}")
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read())

def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_images = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break
        else:
            continue

    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        images_output = []
        if 'images' in node_output:
            for image in node_output['images']:
                image_data = get_image(image['filename'], image['subfolder'], image['type'])
                # bytes 객체를 base64로 인코딩하여 JSON 직렬화 가능하게 변환
                if isinstance(image_data, bytes):
                    import base64
                    image_data = base64.b64encode(image_data).decode('utf-8')
                images_output.append(image_data)
        output_images[node_id] = images_output

    return output_images

    
def get_video_path(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break
        else:
            continue

    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        if 'gifs' in node_output:
            for video in node_output['gifs']:
                # 첫 번째 비디오 파일 경로 반환
                return video['fullpath']
    
    return None

def get_image_path(ws, prompt):
    """이미지 결과의 파일 경로를 가져옵니다."""
    prompt_id = queue_prompt(prompt)['prompt_id']
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break
        else:
            continue

    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        if 'images' in node_output:
            for image in node_output['images']:
                # 전체 경로 구성
                filename = image['filename']
                subfolder = image.get('subfolder', '')
                if subfolder:
                    full_path = os.path.join('/ComfyUI/output', subfolder, filename)
                else:
                    full_path = os.path.join('/ComfyUI/output', filename)
                # 첫 번째 이미지 파일 경로 반환
                return full_path
    
    return None

def get_image_dimensions(image_path):
    """이미지의 크기를 측정합니다."""
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            return width, height
    except Exception as e:
        logger.error(f"이미지 크기 측정 실패: {e}")
        raise

def get_video_dimensions(video_path):
    """비디오의 크기를 측정합니다."""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"비디오를 열 수 없습니다: {video_path}")
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        return width, height
    except Exception as e:
        logger.error(f"비디오 크기 측정 실패: {e}")
        raise

def get_video_fps(video_path):
    """비디오의 FPS를 측정합니다."""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"비디오를 열 수 없습니다: {video_path}")
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        return fps
    except Exception as e:
        logger.error(f"비디오 FPS 측정 실패: {e}")
        raise

def calculate_resolution(width, height):
    """가장 짧은 곳의 2배를 resolution으로 계산합니다."""
    min_dimension = min(width, height)
    resolution = min_dimension * 2
    logger.info(f"입력 크기: {width}x{height}, 최소 차원: {min_dimension}, 계산된 resolution: {resolution}")
    return resolution

def load_workflow(workflow_path):
    with open(workflow_path, 'r') as file:
        return json.load(file)


def handler(job):
    job_input = job.get("input", {})
    logger.info(f"Received job input: {job_input}")
    task_id = f"task_{uuid.uuid4()}"
    os.makedirs(task_id, exist_ok=True)

    # 출력 형식 확인
    output_format = job_input.get("output", "file_path")  # 기본값: file_path
    
    # 입력 타입 감지 (이미지 또는 비디오)
    image_path_input = job_input.get("image_path")
    image_url_input = job_input.get("image_url")
    image_base64_input = job_input.get("image_base64")
    
    video_path_input = job_input.get("video_path")
    video_url_input = job_input.get("video_url")
    video_base64_input = job_input.get("video_base64")
    
    input_path = None
    input_type = None  # "image" or "video"
    task_type = None  # "image_upscale", "video_upscale", "video_upscale_and_interpolation"
    
    # 이미지 입력 처리
    if image_path_input or image_url_input or image_base64_input:
        input_type = "image"
        task_type = "image_upscale"
        
        if image_path_input:
            input_path = image_path_input
        elif image_url_input:
            try:
                # URL에서 확장자 추출 시도
                parsed_url = urllib.parse.urlparse(image_url_input)
                path = parsed_url.path
                ext = os.path.splitext(path)[1] or '.png'
                input_path = os.path.join(task_id, f"input_image{ext}")
                urllib.request.urlretrieve(image_url_input, input_path)
                logger.info(f"이미지 URL에서 다운로드 완료: {image_url_input}")
            except Exception as e:
                return {"error": f"이미지 URL 다운로드 실패: {e}"}
        elif image_base64_input:
            try:
                # Base64에서 이미지 형식 감지 시도 (PIL 사용)
                decoded_data = base64.b64decode(image_base64_input)
                # BytesIO를 사용하여 PIL로 형식 감지
                from io import BytesIO
                img = Image.open(BytesIO(decoded_data))
                img_format = img.format.lower() if img.format else 'png'
                ext = f'.{img_format}'
                input_path = os.path.join(task_id, f"input_image{ext}")
                with open(input_path, 'wb') as f:
                    f.write(decoded_data)
                logger.info(f"Base64 이미지를 '{input_path}' 파일로 저장했습니다.")
            except Exception as e:
                # 실패 시 기본값으로 .png 사용
                input_path = os.path.join(task_id, "input_image.png")
                with open(input_path, 'wb') as f:
                    f.write(base64.b64decode(image_base64_input))
                logger.info(f"Base64 이미지를 '{input_path}' 파일로 저장했습니다 (기본 형식).")
    
    # 비디오 입력 처리
    elif video_path_input or video_url_input or video_base64_input:
        input_type = "video"
        
        # 작업 타입 확인 (기본값: upscale)
        task_type_input = job_input.get("task_type", "upscale")
        if task_type_input == "upscale_and_interpolation":
            task_type = "video_upscale_and_interpolation"
        else:
            task_type = "video_upscale"
        
        if video_path_input:
            input_path = video_path_input
        elif video_url_input:
            try:
                input_path = os.path.join(task_id, "input_video.mp4")
                urllib.request.urlretrieve(video_url_input, input_path)
                logger.info(f"비디오 URL에서 다운로드 완료: {video_url_input}")
            except Exception as e:
                return {"error": f"비디오 URL 다운로드 실패: {e}"}
        elif video_base64_input:
            try:
                input_path = os.path.join(task_id, "input_video.mp4")
                decoded_data = base64.b64decode(video_base64_input)
                with open(input_path, 'wb') as f:
                    f.write(decoded_data)
                logger.info(f"Base64 비디오를 '{input_path}' 파일로 저장했습니다.")
            except Exception as e:
                return {"error": f"Base64 비디오 디코딩 실패: {e}"}
    else:
        return {"error": "입력이 필요합니다. (image_path/image_url/image_base64 또는 video_path/video_url/video_base64 중 하나)"}
    
    # 입력 파일 크기 측정 및 resolution 계산
    video_fps = None
    try:
        if input_type == "image":
            width, height = get_image_dimensions(input_path)
        else:  # video
            width, height = get_video_dimensions(input_path)
            # interpolation을 사용하는 경우 FPS도 측정
            if task_type == "video_upscale_and_interpolation":
                video_fps = get_video_fps(input_path)
                logger.info(f"원본 비디오 FPS: {video_fps}")
        
        resolution = calculate_resolution(width, height)
    except Exception as e:
        return {"error": f"입력 파일 크기 측정 실패: {e}"}
    
    # 워크플로우 로드 및 설정
    workflow_dir = os.path.join(os.path.dirname(__file__), "workflow")
    
    if task_type == "image_upscale":
        workflow_path = os.path.join(workflow_dir, "image_upscale.json")
        prompt = load_workflow(workflow_path)
        # 노드 16: LoadImage에 이미지 경로 설정
        prompt["16"]["inputs"]["image"] = os.path.basename(input_path)
        # 노드 10: SeedVR2VideoUpscaler에 resolution 설정
        prompt["10"]["inputs"]["resolution"] = resolution
    elif task_type == "video_upscale":
        workflow_path = os.path.join(workflow_dir, "video_upscale_api.json")
        prompt = load_workflow(workflow_path)
        # 노드 21: LoadVideo에 비디오 경로 설정
        prompt["21"]["inputs"]["file"] = os.path.basename(input_path)
        # 노드 10: SeedVR2VideoUpscaler에 resolution 설정
        prompt["10"]["inputs"]["resolution"] = resolution
    elif task_type == "video_upscale_and_interpolation":
        workflow_path = os.path.join(workflow_dir, "video_upscale_interpolation_api.json")
        prompt = load_workflow(workflow_path)
        # 노드 21: LoadVideo에 비디오 경로 설정
        prompt["21"]["inputs"]["file"] = os.path.basename(input_path)
        # 노드 10: SeedVR2VideoUpscaler에 resolution 설정
        prompt["10"]["inputs"]["resolution"] = resolution
        # 노드 25: VHS_VideoCombine에 원본 FPS의 2배 설정
        if video_fps is not None:
            doubled_fps = video_fps * 2
            prompt["25"]["inputs"]["frame_rate"] = doubled_fps
            logger.info(f"Video Combine에 FPS 설정: {doubled_fps} (원본 FPS {video_fps}의 2배)")
        else:
            logger.warning("FPS를 측정할 수 없어 기본값을 사용합니다.")
    else:
        return {"error": f"지원하지 않는 작업 타입입니다: {task_type}"}

    # 입력 파일을 ComfyUI의 입력 디렉토리로 복사
    comfyui_input_dir = "/ComfyUI/input"
    os.makedirs(comfyui_input_dir, exist_ok=True)
    import shutil
    input_filename = os.path.basename(input_path)
    comfyui_input_path = os.path.join(comfyui_input_dir, input_filename)
    shutil.copy2(input_path, comfyui_input_path)
    logger.info(f"입력 파일을 ComfyUI 입력 디렉토리로 복사: {comfyui_input_path}")
    
    # ComfyUI 서버 연결 및 처리
    ws_url = f"ws://{server_address}:8188/ws?clientId={client_id}"
    logger.info(f"Connecting to WebSocket: {ws_url}")
    
    # 먼저 HTTP 연결이 가능한지 확인
    http_url = f"http://{server_address}:8188/"
    logger.info(f"Checking HTTP connection to: {http_url}")
    
    # HTTP 연결 확인 (최대 1분)
    max_http_attempts = 180
    for http_attempt in range(max_http_attempts):
        try:
            response = urllib.request.urlopen(http_url, timeout=5)
            logger.info(f"HTTP 연결 성공 (시도 {http_attempt+1})")
            break
        except Exception as e:
            logger.warning(f"HTTP 연결 실패 (시도 {http_attempt+1}/{max_http_attempts}): {e}")
            if http_attempt == max_http_attempts - 1:
                raise Exception("ComfyUI 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
            time.sleep(1)
    
    ws = websocket.WebSocket()
    # 웹소켓 연결 시도 (최대 3분)
    max_attempts = int(180/5)  # 3분 (5초에 한 번씩 시도)
    for attempt in range(max_attempts):
        try:
            ws.connect(ws_url)
            logger.info(f"웹소켓 연결 성공 (시도 {attempt+1})")
            break
        except Exception as e:
            logger.warning(f"웹소켓 연결 실패 (시도 {attempt+1}/{max_attempts}): {e}")
            if attempt == max_attempts - 1:
                raise Exception("웹소켓 연결 시간 초과 (3분)")
            time.sleep(5)
    
    # 입력 타입에 따라 결과 가져오기
    if input_type == "image":
        result_path = get_image_path(ws, prompt)
        result_key = "image_path"
        result_base64_key = "image"
    else:  # video
        result_path = get_video_path(ws, prompt)
        result_key = "video_path"
        result_base64_key = "video"
    
    ws.close()

    # 결과가 없는 경우 처리
    if not result_path:
        return {"error": f"{input_type}를 생성할 수 없습니다."}
    
    # 출력 형식에 따라 처리
    if output_format == "base64":
        # Base64 인코딩하여 반환
        try:
            with open(result_path, 'rb') as f:
                result_data = base64.b64encode(f.read()).decode('utf-8')
            
            logger.info(f"{input_type}를 Base64로 인코딩하여 반환했습니다.")
            return {result_base64_key: result_data}
            
        except Exception as e:
            logger.error(f"{input_type} Base64 인코딩 실패: {e}")
            return {"error": f"{input_type} 인코딩 실패: {e}"}
    else:
        # 기본값: 파일 경로 반환
        logger.info(f"결과 {input_type} 경로: {result_path}")
        return {result_key: result_path}

runpod.serverless.start({"handler": handler})