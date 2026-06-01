# CelebA-Spoof: train 4 FAS models on 10k images (GPU) + eval all 5 vs pretrained AENet.
# Runs as a Kaggle "Save & Run All" notebook with the dataset mounted and a GPU enabled.
# Outputs: /kaggle/working/results.json + /kaggle/working/weights/*.pth
import os, json, math, random, time, urllib.request
import numpy as np
import torch, torch.nn as nn, torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import torchvision, timm
from torchvision import transforms

# ----------------------------- config -----------------------------
SEED = 0
N_TRAIN = 10000           # balanced training images (5k live + 5k spoof)
N_TEST  = 4000            # balanced eval images   (2k live + 2k spoof)
EPOCHS  = 3
BATCH   = 64
LR      = 1e-4
WORKERS = 4
AENET_URL = "https://raw.githubusercontent.com/ZhangYuanhan-AI/CelebA-Spoof/master/intra_dataset_code/ckpt_iter.pth.tar"

ROOT = "/kaggle/input/celeba-spoof-for-face-antispoofing/CelebA_Spoof_/CelebA_Spoof"
OUT  = "/kaggle/working"; os.makedirs(f"{OUT}/weights", exist_ok=True)
DEV  = "cuda" if torch.cuda.is_available() else "cpu"
random.seed(SEED); torch.manual_seed(SEED); np.random.seed(SEED)
print("device:", DEV, "| torch:", torch.__version__)

IMAGENET_MEAN=(0.485,0.456,0.406); IMAGENET_STD=(0.229,0.224,0.225)
LIVE_SPOOF=43

# ------------------------- data utilities --------------------------
def load_bbox(img_path):
    bb = img_path[:-4] + "_BB.txt"
    if not os.path.exists(bb): return None
    try:
        x,y,w,h,_ = open(bb).read().strip().split(" ")[:5]
        return int(float(x)),int(float(y)),int(float(w)),int(float(h))
    except Exception:
        return None

def read_rgb_crop(img_path):
    import cv2
    img = cv2.imread(img_path)
    if img is None:
        return np.zeros((224,224,3), np.uint8)
    h,w = img.shape[:2]; bb = load_bbox(img_path)
    if bb:
        sx,sy = w/224.0, h/224.0
        x,y,bw,bh = int(bb[0]*sx),int(bb[1]*sy),int(bb[2]*sx),int(bb[3]*sy)
        x1,y1 = max(0,x),max(0,y); x2,y2 = min(w,x+bw),min(h,y+bh)
        if x2>x1 and y2>y1: img = img[y1:y2, x1:x2]
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

class DS(Dataset):
    def __init__(self, keys, labels, size, normalize):
        self.keys=keys; self.labels=labels
        t=[transforms.Resize((size,size)), transforms.ToTensor()]
        if normalize: t.append(transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD))
        self.tf=transforms.Compose(t)
    def __len__(self): return len(self.keys)
    def __getitem__(self, i):
        k=self.keys[i]
        img=read_rgb_crop(os.path.join(ROOT,k))
        return self.tf(Image.fromarray(img)), int(self.labels[k][LIVE_SPOOF])

def balanced(labels, n, seed):
    rng=random.Random(seed)
    live=[k for k,v in labels.items() if v[LIVE_SPOOF]==0]
    spoof=[k for k,v in labels.items() if v[LIVE_SPOOF]==1]
    half=n//2
    pick=rng.sample(live,min(half,len(live)))+rng.sample(spoof,min(n-half,len(spoof)))
    rng.shuffle(pick); return pick

# ----------------------------- models ------------------------------
def conv3x3(i,o,s=1): return nn.Conv2d(i,o,3,s,1,bias=False)
class Basic(nn.Module):
    expansion=1
    def __init__(s,inp,p,st=1,ds=None):
        super().__init__(); s.c1=conv3x3(inp,p,st); s.b1=nn.BatchNorm2d(p); s.r=nn.ReLU(True)
        s.c2=conv3x3(p,p); s.b2=nn.BatchNorm2d(p); s.ds=ds
    def forward(s,x):
        r=x; o=s.r(s.b1(s.c1(x))); o=s.b2(s.c2(o))
        if s.ds is not None: r=s.ds(x)
        return s.r(o+r)
class AENet(nn.Module):
    def __init__(s, layers=(2,2,2,2), num_classes=2):
        super().__init__(); s.inp=64
        s.conv1=nn.Conv2d(3,64,7,2,3,bias=False); s.bn1=nn.BatchNorm2d(64); s.relu=nn.ReLU(True)
        s.maxpool=nn.MaxPool2d(3,2,1)
        s.layer1=s._ml(64,layers[0]); s.layer2=s._ml(128,layers[1],2)
        s.layer3=s._ml(256,layers[2],2); s.layer4=s._ml(512,layers[3],2)
        s.avgpool=nn.AvgPool2d(7,1)
        s.fc_live_attribute=nn.Linear(512,40); s.fc_attack=nn.Linear(512,11)
        s.fc_light=nn.Linear(512,5); s.fc_live=nn.Linear(512,num_classes)
        s.upsample14=nn.Upsample((14,14),mode="bilinear",align_corners=False)
        s.depth_final=nn.Conv2d(512,1,3,1,1,bias=False); s.reflect_final=nn.Conv2d(512,3,3,1,1,bias=False)
        s.sigmoid=nn.Sigmoid()
    def _ml(s,p,n,st=1):
        ds=None
        if st!=1 or s.inp!=p: ds=nn.Sequential(nn.Conv2d(s.inp,p,1,st,bias=False), nn.BatchNorm2d(p))
        L=[Basic(s.inp,p,st,ds)]; s.inp=p
        for _ in range(1,n): L.append(Basic(s.inp,p))
        return nn.Sequential(*L)
    def forward(s,x):
        x=s.relu(s.bn1(s.conv1(x))); x=s.maxpool(x)
        x=s.layer1(x); x=s.layer2(x); x=s.layer3(x); x=s.layer4(x)
        x=s.avgpool(x).flatten(1); return s.fc_live(x)

class CDCConv2d(nn.Module):
    def __init__(s,i,o,k=3,st=1,p=1,theta=0.7):
        super().__init__(); s.conv=nn.Conv2d(i,o,k,st,p,bias=False); s.theta=theta
    def forward(s,x):
        out=s.conv(x)
        if s.theta==0: return out
        kd=s.conv.weight.sum(dim=(2,3),keepdim=True)
        return out - s.theta*F.conv2d(x,kd,stride=s.conv.stride,padding=0)
def cdc_blk(i,o,t): return nn.Sequential(CDCConv2d(i,o,theta=t), nn.BatchNorm2d(o), nn.ReLU(True))
class CDCN(nn.Module):
    def __init__(s,theta=0.7,num_classes=2):
        super().__init__()
        s.stem=cdc_blk(3,64,theta)
        s.b1=nn.Sequential(cdc_blk(64,128,theta),cdc_blk(128,128,theta),nn.MaxPool2d(2))
        s.b2=nn.Sequential(cdc_blk(128,128,theta),cdc_blk(128,128,theta),nn.MaxPool2d(2))
        s.b3=nn.Sequential(cdc_blk(128,128,theta),cdc_blk(128,128,theta),nn.MaxPool2d(2))
        s.cls=nn.Sequential(nn.AdaptiveAvgPool2d(1),nn.Flatten(),nn.Linear(128,num_classes))
    def forward(s,x): return s.cls(s.b3(s.b2(s.b1(s.stem(x)))))
class DeepPixBiS(nn.Module):
    def __init__(s,num_classes=2):
        super().__init__()
        d=torchvision.models.densenet121(weights=torchvision.models.DenseNet121_Weights.IMAGENET1K_V1)
        s.enc=nn.Sequential(*list(d.features.children())[:10])
        with torch.no_grad(): c=s.enc(torch.zeros(1,3,224,224)).shape[1]
        s.cls=nn.Linear(c,num_classes); s.pool=nn.AdaptiveAvgPool2d(1)
    def forward(s,x): return s.cls(s.pool(s.enc(x)).flatten(1))

def build(name):
    if name=="aenet": return AENet(), 224, False
    if name=="cdcn": return CDCN(), 256, True
    if name=="deeppixbis": return DeepPixBiS(), 224, True
    if name=="efficientnet": return timm.create_model("efficientnet_b0",pretrained=True,num_classes=2), 224, True
    if name=="vit": return timm.create_model("vit_base_patch16_224",pretrained=True,num_classes=2), 224, True

def load_aenet_pretrained(model):
    path="/kaggle/working/ckpt_iter.pth.tar"
    urllib.request.urlretrieve(AENET_URL, path)
    ckpt=torch.load(path, map_location="cpu", weights_only=False)
    state=ckpt.get("state_dict",ckpt); own=model.state_dict(); n=0
    for k,p in state.items():
        kk=k.replace("module.","")
        if kk in own and own[kk].shape==getattr(p,"shape",own[kk].shape):
            own[kk].copy_(p.data if hasattr(p,"data") else p); n+=1
    print("  AENet params loaded:", n); return model

# ----------------------------- metrics -----------------------------
def roc(s,y):
    s=np.asarray(s,float); y=np.asarray(y,int); o=np.argsort(-s,kind="mergesort"); s,y=s[o],y[o]
    d=np.where(np.diff(s))[0]; idx=np.r_[d,s.size-1]
    tp=np.cumsum(y)[idx]; fp=np.cumsum(1-y)[idx]
    tpr=tp/tp[-1]; fpr=fp/fp[-1]
    return np.r_[0,fpr], np.r_[0,tpr]
def metrics(s,y,thr=0.5):
    s=np.asarray(s,float); y=np.asarray(y,int); fpr,tpr=roc(s,y)
    auc=float(np.trapz(tpr,fpr)); fnr=1-tpr; i=int(np.nanargmin(np.abs(fpr-fnr)))
    eer=float((fpr[i]+fnr[i])/2)
    pred=(s>=thr); atk=y==1; bona=y==0
    apcer=float((atk&~pred).sum()/max(1,atk.sum())); bpcer=float((bona&pred).sum()/max(1,bona.sum()))
    t={f"{f:g}":float(np.interp(f,fpr,tpr)) for f in (1e-2,5e-3,1e-3)}
    return {"auc":round(auc,4),"eer":round(eer,4),"acer":round((apcer+bpcer)/2,4),
            "apcer":round(apcer,4),"bpcer":round(bpcer,4),"tpr_at_fpr":t,
            "n":int(s.size),"acc":round(float((pred==y).mean()),4)}

# ------------------------------ run --------------------------------
def train_model(name, train_keys, labels):
    model,size,norm=build(name); model=model.to(DEV).train()
    dl=DataLoader(DS(train_keys,labels,size,norm),batch_size=BATCH,shuffle=True,num_workers=WORKERS,pin_memory=True)
    opt=torch.optim.AdamW(model.parameters(),lr=LR); crit=nn.CrossEntropyLoss()
    for ep in range(EPOCHS):
        tot=0; seen=0; t0=time.time()
        for x,yb in dl:
            x,yb=x.to(DEV),yb.to(DEV); opt.zero_grad()
            out=model(x); out=out[0] if isinstance(out,(tuple,list)) else out
            loss=crit(out,yb); loss.backward(); opt.step()
            tot+=loss.item()*x.size(0); seen+=x.size(0)
        print(f"  [{name}] epoch {ep+1}/{EPOCHS} loss={tot/seen:.4f} ({time.time()-t0:.0f}s)")
    torch.save({"state_dict":model.state_dict(),"model":name}, f"{OUT}/weights/{name}.pth")
    return model,size,norm

@torch.no_grad()
def evaluate(model,size,norm,test_keys,labels):
    model.eval(); dl=DataLoader(DS(test_keys,labels,size,norm),batch_size=128,num_workers=WORKERS,pin_memory=True)
    S=[]; Y=[]
    for x,yb in dl:
        out=model(x.to(DEV)); out=out[0] if isinstance(out,(tuple,list)) else out
        S+=F.softmax(out,1)[:,1].cpu().numpy().tolist(); Y+=yb.numpy().tolist()
    return metrics(S,Y)

def main():
    tr=json.load(open(f"{ROOT}/metas/intra_test/train_label.json"))
    te=json.load(open(f"{ROOT}/metas/intra_test/test_label.json"))
    train_keys=balanced(tr,N_TRAIN,SEED); test_keys=balanced(te,N_TEST,SEED+1)
    print(f"train={len(train_keys)} test={len(test_keys)}")
    results={}; cache={}
    for name in ["efficientnet","vit","deeppixbis","cdcn"]:
        print("TRAIN", name)
        m,size,norm=train_model(name,train_keys,tr); cache[name]=(m,size,norm)
    print("LOAD pretrained AENet")
    am,asize,anorm=build("aenet"); am=load_aenet_pretrained(am).to(DEV); cache["aenet"]=(am,asize,anorm)
    for name,(m,size,norm) in cache.items():
        results[name]=evaluate(m,size,norm,test_keys,tr if False else te)
        print("EVAL", name, results[name])
    json.dump({"config":{"n_train":N_TRAIN,"n_test":N_TEST,"epochs":EPOCHS,"batch":BATCH,"lr":LR},
               "results":results}, open(f"{OUT}/results.json","w"), indent=2)
    print("DONE -> results.json")

main()
