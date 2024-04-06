from trainer.models import load_models, pretrained_models
from trainer.utils.lora import patch_pipe_with_lora
from trainer.utils.val_prompts import val_prompts
from trainer.utils.io import make_validation_img_grid
from trainer.dataset_and_utils import pick_best_gpu_id
from trainer.utils.seed import seed_everything
from diffusers import EulerDiscreteScheduler
from trainer.utils.inference import encode_prompt_advanced

import numpy as np
import torch
from huggingface_hub import hf_hub_download
import os, json, random, time

if __name__ == "__main__":

    pretrained_model = pretrained_models['sdxl']
    lora_path      = 'lora_models/plantoid_best--05_21-39-46-sdxl_object_dora/checkpoints/checkpoint-400'
    lora_scale     = 0.5
    render_size    = (1024+1024, 1024)  # H,W
    n_imgs         = 30
    n_steps        = 25
    guidance_scale = 8
    seed           = 1
    use_lightning  = False

    #####################################################################################

    output_dir = f'test_images4/{lora_path.split("/")[-1]}'
    os.makedirs(output_dir, exist_ok=True)

    seed_everything(seed)
    pick_best_gpu_id()

    (pipe,
        tokenizer_one,
        tokenizer_two,
        noise_scheduler,
        text_encoder_one,
        text_encoder_two,
        vae,
        unet) = load_models(pretrained_model, 'cuda', torch.float16)

    if use_lightning:
        repo = "ByteDance/SDXL-Lightning"
        ckpt = "sdxl_lightning_8step_lora.safetensors" # Use the correct ckpt for your step setting!
        pipe.load_lora_weights(hf_hub_download(repo, ckpt))
        pipe.fuse_lora()
        n_steps = 8
        guidance_scale=1.5

    with open(os.path.join(lora_path, "training_args.json"), "r") as f:
        training_args = json.load(f)
        concept_mode = training_args["concept_mode"]

    if concept_mode == "style":
        validation_prompts_raw = random.choices(val_prompts['style'], k=n_imgs)
    elif concept_mode == "face":
        validation_prompts_raw = random.choices(val_prompts['face'], k=n_imgs)
    else:
        validation_prompts_raw = random.choices(val_prompts['object'], k=n_imgs)

    pipe = patch_pipe_with_lora(pipe, lora_path, lora_scale=lora_scale)
    pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config) #, timestep_spacing="trailing")
    generator = torch.Generator(device='cuda').manual_seed(seed)
    negative_prompt = "nude, naked, poorly drawn face, ugly, tiling, out of frame, extra limbs, disfigured, deformed body, blurry, blurred, watermark, text, grainy, signature, cut off, draft"
    pipeline_args = {
                "num_inference_steps": n_steps,
                "guidance_scale": guidance_scale,
                "height": render_size[0],
                "width": render_size[1],
                }

    for i in range(len(validation_prompts_raw)):
        c, uc, pc, puc = encode_prompt_advanced(pipe, lora_path, validation_prompts_raw[i], negative_prompt, lora_scale, guidance_scale)

        pipeline_args['prompt_embeds'] = c
        pipeline_args['negative_prompt_embeds'] = uc
        if pretrained_model['version'] == 'sdxl':
            pipeline_args['pooled_prompt_embeds'] = pc
            pipeline_args['negative_pooled_prompt_embeds'] = puc

        image = pipe(**pipeline_args, generator=generator).images[0]
        image.save(os.path.join(output_dir, f"{validation_prompts_raw[i][:40]}_seed_{seed}_{i}_lora_scale_{lora_scale:.2f}_{int(time.time())}.jpg"), format="JPEG", quality=95)