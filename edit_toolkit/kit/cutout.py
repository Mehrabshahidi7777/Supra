import os, cv2, numpy as np
WORK = os.environ.get('WORK', '/home/claude/work_edit')
BOX=(23,95,1058,1935)
def grab(clip,t,box=BOX):
    cap=cv2.VideoCapture(f'{WORK}/clips/{clip}.mp4'); cap.set(cv2.CAP_PROP_POS_MSEC,t*1000); ok,fr=cap.read()
    return fr[box[1]:box[3],box[0]:box[2]]
def segment(im, rect_frac, iters=8):
    h,w=im.shape[:2]; s=0.5
    sm=cv2.resize(im,(int(w*s),int(h*s)),interpolation=cv2.INTER_AREA); H,W=sm.shape[:2]
    x0,y0,x1,y1=rect_frac
    rect=(int(W*x0),int(H*y0),int(W*(x1-x0)),int(H*(y1-y0)))
    mask=np.zeros((H,W),np.uint8); bgd=np.zeros((1,65),np.float64); fgd=np.zeros((1,65),np.float64)
    cv2.grabCut(sm,mask,rect,bgd,fgd,iters,cv2.GC_INIT_WITH_RECT)
    m=((mask==1)|(mask==3)).astype(np.uint8)
    # largest component + fill holes
    n,lab,st,_=cv2.connectedComponentsWithStats(m,8)
    if n>1:
        k=1+np.argmax(st[1:,cv2.CC_STAT_AREA]); m=(lab==k).astype(np.uint8)
    inv=(1-m).astype(np.uint8); n2,lab2,st2,_=cv2.connectedComponentsWithStats(inv,4)
    for j in range(1,n2):
        x,y,ww,hh,a=st2[j]
        if x>0 and y>0 and x+ww<W and y+hh<H and a< 0.02*W*H: m[lab2==j]=1
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    m=cv2.resize(m.astype(np.float32),(w,h),interpolation=cv2.INTER_LINEAR)
    m=cv2.GaussianBlur(m,(0,0),1.2)
    return np.clip((m-0.5)*3+0.5,0,1)
def sprite(im, m, pad=60):
    ys,xs=np.where(m>0.5); y0,y1,x0,x1=ys.min(),ys.max(),xs.min(),xs.max()
    y0=max(0,y0-pad); x0=max(0,x0-pad); y1=min(im.shape[0],y1+pad); x1=min(im.shape[1],x1+pad)
    return im[y0:y1,x0:x1].copy(), m[y0:y1,x0:x1].copy()
