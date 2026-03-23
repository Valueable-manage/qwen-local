"""模型加载与推理逻辑，供 CLI 和 Web 共用"""

import os
import re
from threading import Thread

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TextIteratorStreamer,
    StoppingCriteria,
    StoppingCriteriaList,
)

# 修复 Windows 路径校验问题 (huggingface_hub#2004)
import huggingface_hub.utils._validators as _validators

_orig = _validators.validate_repo_id


def _validate_repo_id(repo_id):
    if isinstance(repo_id, str) and (os.path.isdir(repo_id) or os.path.isfile(repo_id)):
        return
    _orig(repo_id)


_validators.validate_repo_id = _validate_repo_id

_MODEL_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "qwen", "Qwen3___5-4B"
)
MODEL_PATH = os.environ.get("MODEL_PATH", _MODEL_DIR)

SYSTEM_PROMPT = (
    "你是一个简洁的中文助手。" "只输出最终答案，不重复用户的问题，不输出分析过程。"
)

_tokenizer = None
_model = None


def load_model():
    global _tokenizer, _model
    if _model is not None:
        return _tokenizer, _model

    use_cuda = torch.cuda.is_available()
    _tokenizer = AutoTokenizer.from_pretrained(
        MODEL_PATH, local_files_only=True, trust_remote_code=True
    )

    if use_cuda:
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"\n>>> GPU: {gpu_name}  显存: {vram_gb:.1f} GB")

        loaded = False
        try:
            from transformers import BitsAndBytesConfig

            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )
            print(">>> 尝试 4-bit 量化加载...")
            _model = AutoModelForCausalLM.from_pretrained(
                MODEL_PATH,
                quantization_config=quantization_config,
                device_map="auto",
                local_files_only=True,
                trust_remote_code=True,
            )
            print(">>> 4-bit 量化加载成功！")
            loaded = True
        except Exception as e:
            print(f">>> 4-bit 量化失败（{e}），回退 float16...")

        if not loaded:
            _model = AutoModelForCausalLM.from_pretrained(
                MODEL_PATH,
                torch_dtype=torch.float16,
                device_map="auto",
                local_files_only=True,
                trust_remote_code=True,
            )
            print(">>> float16 加载成功")
    else:
        print("\n>>> 使用设备: CPU")
        _model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch.float32,
            device_map="cpu",
            local_files_only=True,
            trust_remote_code=True,
        )

    return _tokenizer, _model


def _build_text(messages: list[dict]) -> str:
    """构建输入文本，使用 Qwen3 官方的 enable_thinking=False 彻底关闭思维链"""
    msgs = []
    if not messages or messages[0].get("role") != "system":
        msgs.append({"role": "system", "content": SYSTEM_PROMPT})
    msgs.extend(messages)

    tokenizer, _ = load_model()

    # Qwen3 官方参数：enable_thinking=False 彻底禁止思维模式
    # 这比手动加 <think></think> 更可靠
    try:
        text = tokenizer.apply_chat_template(
            msgs,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,  # ← Qwen3 官方关闭思维链的正确方式
        )
    except TypeError:
        # 旧版 transformers 不支持 enable_thinking 参数，回退兼容
        text = tokenizer.apply_chat_template(
            msgs,
            tokenize=False,
            add_generation_prompt=True,
        )
    return text


def chat(messages: list[dict], max_new_tokens: int = 512) -> str:
    tokenizer, model = load_model()
    text = _build_text(messages)
    inputs = tokenizer([text], return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=None,
            top_p=None,
            pad_token_id=tokenizer.eos_token_id,
        )

    response = tokenizer.decode(
        outputs[0][len(inputs.input_ids[0]) :], skip_special_tokens=True
    )
    # 保留简单清理作为兜底
    response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
    return response


class _StopFlagCriteria(StoppingCriteria):
    """检查外部 stop_flag，为 True 时停止生成"""

    def __init__(self, stop_flag: list):
        self.stop_flag = stop_flag

    def __call__(self, input_ids, scores, **kwargs) -> bool:
        return bool(self.stop_flag and self.stop_flag[0])


def chat_stream(
    messages: list[dict],
    max_new_tokens: int = 512,
    stop_flag: list | None = None,
):
    """流式生成，stop_flag 为 [False] 时可通过设为 [True] 中断"""
    tokenizer, model = load_model()
    text = _build_text(messages)
    inputs = tokenizer([text], return_tensors="pt").to(model.device)

    streamer = TextIteratorStreamer(
        tokenizer, skip_special_tokens=True, skip_prompt=True
    )
    gen_kwargs = dict(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        temperature=None,
        top_p=None,
        pad_token_id=tokenizer.eos_token_id,
        streamer=streamer,
    )
    if stop_flag is not None:
        gen_kwargs["stopping_criteria"] = StoppingCriteriaList(
            [_StopFlagCriteria(stop_flag)]
        )

    def _generate():
        with torch.no_grad():
            model.generate(**gen_kwargs)

    thread = Thread(target=_generate)
    thread.start()

    for chunk in streamer:
        yield chunk

    thread.join()
