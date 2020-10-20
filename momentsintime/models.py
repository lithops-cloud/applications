import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.models import resnet50
from torchvision import transforms


def modify_resnets(model):
    # Modify attributs
    model.last_linear, model.fc = model.fc, None

    def features(self, input):
        x = self.conv1(input)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        return x

    def logits(self, features):
        x = self.avgpool(features)
        x = x.view(x.size(0), -1)
        x = self.last_linear(x)
        return x

    def forward(self, input):
        x = self.features(input)
        x = self.logits(x)
        return x

    # Modify methods
    setattr(model.__class__, 'features', features)
    setattr(model.__class__, 'logits', logits)
    setattr(model.__class__, 'forward', forward)
    return model


weight_url = 'http://moments.csail.mit.edu/moments_models/moments_RGB_resnet50_imagenetpretrained.pth.tar'


def load_model(weight_file=None):
    """Load pretrained resnet50 model."""

    model = resnet50(num_classes=339)

    # Load checkpoint
    checkpoint = torch.load(weight_file, map_location=lambda storage, loc: storage)  # Load on cpu
    state_dict = {str.replace(str(k), 'module.', ''): v for k, v in checkpoint['state_dict'].items()}
    model.load_state_dict(state_dict)
    model = modify_resnets(model)
    model.eval()

    return model


def load_transform():
    """Load the image transformer."""
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225])])


def load_categories():
    """Load categories."""
    with open('category_momentsv1.txt') as f:
        return [line.rstrip() for line in f.readlines()]
