import os, cv2, numpy as np, sys
WORK = os.environ.get('WORK', '/home/claude/work_edit')
def strip(clip, t0, t1, step, out, crop=(23,95,1058,1935), cols=14, w=96):
    cap=cv2.VideoCapture(f'{WORK}/clips/{clip}.mp4')
    h=int(w*(crop[3]-crop[1])/(crop[2]-crop[0]))
    ims=[]; t=t0
    while t<=t1+1e-6:
        cap.set(cv2.CAP_PROP_POS_MSEC,t*1000); ok,fr=cap.read()
        if not ok: break
        c=fr[crop[1]:crop[3],crop[0]:crop[2]]
        im=cv2.resize(c,(w,h),interpolation=cv2.INTER_AREA)
        cv2.putText(im,f'{t:.2f}',(2,11),cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,255,255),1)
        ims.append(im); t+=step
    while len(ims)%cols: ims.append(np.zeros_like(ims[0]))
    rows=[np.hstack(ims[i:i+cols]) for i in range(0,len(ims),cols)]
    cv2.imwrite(out,np.vstack(rows))
if __name__=='__main__':
    a=sys.argv; strip(a[1],float(a[2]),float(a[3]),float(a[4]),a[5])
