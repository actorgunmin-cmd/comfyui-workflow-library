# Comfy Cloud에 가져올 모델

2026-11-09에 라이브러리가 쓰는 모델 이름을 현재 Comfy Cloud 계정의 모델 목록과 대조했습니다. 공개 저장소의 워크플로에 필요한데 목록에 없는 모델은 아래 10개입니다. 직접 가져온 모델은 다른 계정으로 따라오지 않으므로, 새 계정에서는 한 번씩 가져와야 합니다.

12_NSFW 전용 성인 카테고리 모델 8개는 공개 저장소에 없는 파일이 쓰는 것이라 이 목록에서 뺐습니다.

## 가져오는 방법

1. Comfy Cloud에서 아래 표의 워크플로 JSON을 엽니다.
2. 없는 모델이 **문제** 패널에 나타나면 **가져오기**를 누릅니다. 워크플로에 저장된 Hugging Face 주소로 받습니다.
3. 주소를 직접 넣어야 하면 아래 표의 `/resolve/` 링크를 그대로 붙여 넣습니다. Cloud 모델 가져오기는 Hugging Face와 Civitai 주소만 받습니다.
4. 가져온 뒤 모델 이름이 표의 **Cloud 이름**과 같은지 확인합니다. 워크플로에는 이 이름이 이미 저장되어 있어서 고칠 필요가 없습니다.

Cloud 이름은 `소유자__저장소__파일명` 형식입니다. 저장소 이름의 점은 빠지고(`Qwen-Image-2.1` → `Qwen-Image-21`), 저장소 안 하위 폴더는 이름에 들어가지 않습니다.

## 목록

아래 10개 링크는 2026-11-09에 모두 HTTP 302(다운로드로 연결)로 응답했습니다. 가져오기와 실행은 시험하지 않았습니다.

| Cloud 이름 | 폴더 | 쓰는 워크플로 | 링크 |
|---|---|---|---|
| `Alissonerdx__Minimax-H3-ComfyUI__minimax_h3_head_swap_v1.0_r32.safetensors` | loras | `02_인물·얼굴_교체/01_H3_HeadSwap` | https://huggingface.co/Alissonerdx/Minimax-H3-ComfyUI/resolve/main/loras/minimax_h3_head_swap_v1.0_r32.safetensors |
| `akatz-ai__MiniMax-H3-Character-Swap-LoRA__h3_character_swap_pro4500_1000.safetensors` | loras | `02_인물·얼굴_교체/02_H3_CharacterSwap` | https://huggingface.co/akatz-ai/MiniMax-H3-Character-Swap-LoRA/resolve/a665bb7e3bb9804e487d2925f67744f554c8ad49/h3_character_swap_pro4500_1000.safetensors |
| `Kijai__WanVideo_comfy__Wan21_CausVid_14B_T2V_lora_rank32_v2.safetensors` | loras | `01_영상편집_VFX/04_마스크로_영역지정_원본보존/03_WAN2.1_VACE14B` | https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan21_CausVid_14B_T2V_lora_rank32_v2.safetensors |
| `Kijai__WanVideo_comfy__Wan22_A14B_T2V_HIGH_Lightning_4steps_lora_250928_rank128_fp16.safetensors` | loras | `01_영상편집_VFX/04_마스크로_영역지정_원본보존/02_WAN2.2_FunVACE` | https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/LoRAs/Wan22-Lightning/Wan22_A14B_T2V_HIGH_Lightning_4steps_lora_250928_rank128_fp16.safetensors |
| `Kijai__WanVideo_comfy__Wan22_A14B_T2V_LOW_Lightning_4steps_lora_250928_rank64_fp16.safetensors` | loras | `01_영상편집_VFX/04_마스크로_영역지정_원본보존/02_WAN2.2_FunVACE` | https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/LoRAs/Wan22-Lightning/Wan22_A14B_T2V_LOW_Lightning_4steps_lora_250928_rank64_fp16.safetensors |
| `lightx2v__Minimax-h3-Turbo__minimax_h3_fl2v_turbo_8step_v1.1_768p_comfyui_bf16.safetensors` | loras | `05_영상_뒤로_연장/01_H3_영상연장_Turbo8`, `11_스타일·모션FX/01_H3_모션FX` | https://huggingface.co/lightx2v/Minimax-h3-Turbo/resolve/main/minimax_h3_fl2v_turbo_8step_v1.1_768p_comfyui_bf16.safetensors |
| `pablodawson__MiniMax-H3-360-Orbit-LoRA__minimax_h3_flf2v_lora_v1.safetensors` | loras | `11_스타일·모션FX/01_H3_모션FX` | https://huggingface.co/pablodawson/MiniMax-H3-360-Orbit-LoRA/resolve/5ddbc2dbbe95edbbdaf5017c3e934b1d01791697/minimax_h3_flf2v_lora_v1.safetensors |
| `ausboss__Qwen-Image-21-Consistency-LoRA__qwen-image-2.1-consistency.safetensors` | loras | `11_스타일·모션FX/02_AnimateLCM`, `11_스타일·모션FX/03_AnimateDiff`, `90_유료API·스토리보드_미실행/H3_스토리보드A·B` | https://huggingface.co/ausboss/Qwen-Image-2.1-Consistency-LoRA/resolve/main/qwen-image-2.1-consistency.safetensors |
| `Stableyogi__Realism-Checkpoints__realismByStableYogi_sd15V9LCM.safetensors` | checkpoints | `11_스타일·모션FX/02_AnimateLCM` | https://huggingface.co/Stableyogi/Realism-Checkpoints/resolve/main/realismByStableYogi_sd15V9LCM.safetensors |
| `WarmBloodAban__Minimax-h3_Singularity__Minimax-h3_Singularity_ref2va_v2_int8.safetensors` | diffusion_models | `90_유료API·스토리보드_미실행/H3_스토리보드A·B`, `90_유료API·스토리보드_미실행/LTX2.5+H3_액션시퀀스` | https://huggingface.co/WarmBloodAban/Minimax-h3_Singularity/resolve/main/Minimax-h3_Singularity_ref2va_v2_int8.safetensors |

## 참고

- 위 LoRA 중 WAN 3개는 터보를 꺼도 필요합니다. 스위치가 끈 쪽도 Cloud의 실행 전 검사를 통과해야 하기 때문입니다.
- 모델 라이선스와 A/B 후보는 `2026-11-09_모델_최신확인.md`에 있습니다.
- 이 목록을 다시 만들려면 `skills/comfyui-workflow/references/클라우드_사실.md`의 2절과 3절을 참고하세요.

## WAN 모델 교체로 추가된 항목 (2026-11-10)

| Cloud 이름 | 다운로드 링크 | 폴더 |
|---|---|---|
| `rzgar__Bernini-v2-ComfyUI__wan2.2_bernini_v2_srcFP32_high_noise_int8_convrot.safetensors` | https://huggingface.co/rzgar/Bernini-v2-ComfyUI/resolve/main/Bernini_v2_int8_convrot_src_FP32/wan2.2_bernini_v2_srcFP32_high_noise_int8_convrot.safetensors | diffusion_models |
| `rzgar__Bernini-v2-ComfyUI__wan2.2_bernini_v2_srcFP32_low_noise_int8_convrot.safetensors` | https://huggingface.co/rzgar/Bernini-v2-ComfyUI/resolve/main/Bernini_v2_int8_convrot_src_FP32/wan2.2_bernini_v2_srcFP32_low_noise_int8_convrot.safetensors | diffusion_models |
| `lightx2v__Wan21-Distill-Loras__wan2.1_t2v_14b_lora_rank64_lightx2v_4step.safetensors` | https://huggingface.co/lightx2v/Wan2.1-Distill-Loras/resolve/main/wan2.1_t2v_14b_lora_rank64_lightx2v_4step.safetensors | loras |
