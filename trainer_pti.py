from trainer import TrainerConfig, Trainer
from preprocess import preprocess
import os
from io_utils import MODEL_DICT

out_root_dir = "./lora_models"
run_name     = "face_01"
concept_mode = "face"

output_dir = os.path.join(out_root_dir, run_name)

input_dir, n_imgs, trigger_text, segmentation_prompt, captions = preprocess(
    output_dir,
    concept_mode = concept_mode,
    input_zip_path = "https://storage.googleapis.com/public-assets-xander/A_workbox/lora_training_sets/xander_5.zip",
    #caption_text="in the style of TOK, ",
    caption_text="",
    mask_target_prompts=None,
    target_size=1024,
    crop_based_on_salience=True,
    use_face_detection_instead=False,
    temp=0.7,
    left_right_flip_augmentation=False,
    augment_imgs_up_to_n = 20,
    seed = 0,
    caption_model = "blip"
)

print('-------------------------------------------')
print(f"Trigger text: {trigger_text}")
print(f'n_imgs: {n_imgs}')
print(f'concept_mode: {concept_mode}')
print('-------------------------------------------')


config = TrainerConfig(
    pretrained_model = MODEL_DICT['sdxl'],
    name='unnamed',
    concept_mode=concept_mode,
    trigger_text=trigger_text,
    instance_data_dir = os.path.join(input_dir, "captions.csv"),
    output_dir = output_dir,
    resolution= 1024,
    train_batch_size = 4,
    max_train_steps = 600,
    checkpointing_steps = 200,
    num_train_epochs = 10000,
    gradient_accumulation_steps = 1,
    textual_inversion_lr = 5e-4,
    textual_inversion_weight_decay = 3e-4,
    lora_weight_decay = 0.00,
    prodigy_d_coef = 1.0,
    l1_penalty = 0.0,
    snr_gamma = 5.0,
    precision = "bf16",
    token_dict = {"TOK": "<s0><s1>"},
    inserting_list_tokens = ["<s0>","<s1>"],
    is_lora = True,
    lora_rank = 12,
    lora_alpha = 12,
    hard_pivot = False,
    off_ratio_power = 0.1,
    args_dict = {},
    debug = True,
    seed = 0
)

trainer = Trainer(config)
trainer.train()
print("DONE")