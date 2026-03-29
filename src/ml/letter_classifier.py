import torch
from torchvision import transforms
from .model import CustomCNN

import json
from pathlib import Path
from PIL import Image
import numpy as np

class LetterClassifier:
    def __init__(self, device):
        # root_path
        self.root_path = Path.cwd()

        # config
        self.device = device 
        model_path = self.root_path / "ml" / "best_custom_cnn.pth"
        self.IMAGE_RESIZE= 32

        # Class Names Setup
        self.class_names = []
        self.class_names_path = self.root_path / "ml" / "class_names.json"
        with open(self.class_names_path) as f:
            self.class_names = json.load(f)

        # Load Model
        self.model = CustomCNN(len(self.class_names))
        checkpoint = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model"])
        self.model.eval()

        # Transform
        self.transform = transforms.Compose([
            transforms.Resize((self.IMAGE_RESIZE, self.IMAGE_RESIZE)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406],
                                 [0.229, 0.224, 0.225])
        ])

    @torch.no_grad()
    def read_letter(self, letter_img):
        # convert numpy to image
        if isinstance(letter_img, np.ndarray):
            letter_img = Image.fromarray(letter_img)

        x = self.transform(letter_img) # Augment image
        x = x.unsqueeze(0) # add batch size to the image for the model
        x = x.to(self.device) # load sample image to the device

        logits = self.model(x)
        probs = torch.softmax(logits, dim=1)
        
        confidence, pred = torch.max(probs, dim=1)
        letter = self.class_names[pred.item()] 
        return letter, confidence.item()
