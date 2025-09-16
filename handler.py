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

def load_workflow(workflow_path):
    with open(workflow_path, 'r') as file:
        return json.load(file)


def handler(job):
    job_input = job.get("input", {})
    logger.info(f"Received job input: {job_input}")
    task_id = f"task_{uuid.uuid4()}"

    # 작업 타입 확인
    task_type = job_input.get("task_type", "upscale")
    
    # 비디오 입력 처리 (video_path, video_url, video_base64 중 하나)
    video_path_input = job_input.get("video_path")
    video_url_input = job_input.get("video_url")
    video_base64_input = job_input.get("video_base64")
    
    if not (video_path_input or video_url_input or video_base64_input):
        return {"error": "비디오 입력이 필요합니다. (video_path, video_url, video_base64 중 하나)"}
    
    # 비디오 파일 경로 확보
    if video_path_input:
        # 파일 경로인 경우
        if video_path_input == "/example_video.mp4":
            video_path = "/example_video.mp4"
            return {"video": "test"}
        else:
            video_path = video_path_input
    elif video_url_input:
        # URL인 경우 다운로드
        try:
            import urllib.request
            video_path = os.path.join(task_id, "input_video.mp4")
            os.makedirs(task_id, exist_ok=True)
            urllib.request.urlretrieve(video_url_input, video_path)
            logger.info(f"비디오 URL에서 다운로드 완료: {video_url_input}")
        except Exception as e:
            return {"error": f"비디오 URL 다운로드 실패: {e}"}
    elif video_base64_input:
        # Base64인 경우 디코딩하여 저장
        try:
            os.makedirs(task_id, exist_ok=True)
            video_path = os.path.join(task_id, "input_video.mp4")
            decoded_data = base64.b64decode(video_base64_input)
            with open(video_path, 'wb') as f:
                f.write(decoded_data)
            logger.info(f"Base64 비디오를 '{video_path}' 파일로 저장했습니다.")
        except Exception as e:
            return {"error": f"Base64 비디오 디코딩 실패: {e}"}
    
    # workflow 로드 및 설정
    if task_type == "upscale":
        # 업스케일링만 하는 경우
        prompt = load_workflow("/upscale.json")
        prompt["8"]["inputs"]["video"] = video_path
    elif task_type == "upscale_and_interpolation":
        # 업스케일링 + 프레임 보간
        prompt = load_workflow("/upscale_and_interpolation.json")
        prompt["8"]["inputs"]["video"] = video_path
    else:
        return {"error": f"지원하지 않는 작업 타입입니다: {task_type}"}

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
            import urllib.request
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
    max_attempts = int(180/5)  # 3분 (1초에 한 번씩 시도)
    for attempt in range(max_attempts):
        import time
        try:
            ws.connect(ws_url)
            logger.info(f"웹소켓 연결 성공 (시도 {attempt+1})")
            break
        except Exception as e:
            logger.warning(f"웹소켓 연결 실패 (시도 {attempt+1}/{max_attempts}): {e}")
            if attempt == max_attempts - 1:
                raise Exception("웹소켓 연결 시간 초과 (3분)")
            time.sleep(5)
    
    video_path = get_video_path(ws, prompt)
    ws.close()

    # 비디오가 없는 경우 처리
    if not video_path:
        return {"error": "비디오를 생성할 수 없습니다."}
    
    # network_volume 파라미터 확인
    use_network_volume = job_input.get("network_volume", False)
    
    if use_network_volume:
        # 네트워크 볼륨 사용: 파일 경로 반환
        try:
            # 결과 비디오 파일 경로 생성
            output_filename = f"{task_type}_{task_id}.mp4"
            output_path = f"/runpod-volume/{output_filename}"
            
            # 원본 파일을 결과 경로로 복사
            import shutil
            shutil.copy2(video_path, output_path)
            
            logger.info(f"결과 비디오를 '{output_path}'에 저장했습니다.")
            return {"video_path": output_path}
            
        except Exception as e:
            logger.error(f"비디오 저장 실패: {e}")
            return {"error": f"비디오 저장 실패: {e}"}
    else:
        # 네트워크 볼륨 미사용: Base64 인코딩하여 반환
        try:
            with open(video_path, 'rb') as f:
                video_data = base64.b64encode(f.read()).decode('utf-8')
            
            logger.info("비디오를 Base64로 인코딩하여 반환했습니다.")
            return {"video": video_data}
            
        except Exception as e:
            logger.error(f"비디오 Base64 인코딩 실패: {e}")
            return {"error": f"비디오 인코딩 실패: {e}"}

runpod.serverless.start({"handler": handler})