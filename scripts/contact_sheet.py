from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import sys
root=Path(__file__).resolve().parents[1]
source=root/'evidence'/(sys.argv[1] if len(sys.argv)>1 else 'source-frames')
files=sorted(source.glob('*.png'))
w,h=640,360;gap=24;label=42;cols=4;rows=(len(files)+cols-1)//cols
sheet=Image.new('RGB',(cols*w+(cols+1)*gap,rows*(h+label)+(rows+1)*gap),'#0b1721')
draw=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',22)
for i,file in enumerate(files):
    image=Image.open(file).convert('RGB');image.thumbnail((w,h),Image.Resampling.LANCZOS);x=gap+(i%cols)*(w+gap);y=gap+(i//cols)*(h+label+gap)
    sheet.paste(image,(x,y));draw.text((x,y+h+8),file.stem,fill='#dceaf0',font=font)
dest=root/'evidence'/('CONTACT-SHEET.png' if source.name=='source-frames' else 'EXPORT-CONTACT-SHEET.png');sheet.save(dest);print(dest)
