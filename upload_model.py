from huggingface_hub import HfApi
api = HfApi()
api.upload_file(
    path_or_fileobj="kynto.pt",
    path_in_repo="kynto.pt",
    repo_id="mehtabdevelops/kynto",
    repo_type="model"
)
print("uploaded!")
