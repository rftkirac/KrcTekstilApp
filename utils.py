import yaml
import os


def load_config():
    # Dosya yolunu belirle
    base_path = os.path.dirname(__file__)
    config_path = os.path.join(base_path, 'config.yaml')

    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config


# Proje genelinde kullanılacak config objesi
cfg = load_config()