import * as T from './assets/vendor/three.module.js';

// Every object state is calculated from absolute timeline time. No simulation
// history, wall-clock time, remote assets, or free-running animation loops.
const W=3840,H=2160,TAU=Math.PI*2;
const V=(x=0,y=0,z=0)=>new T.Vector3(x,y,z);
const sat=x=>Math.max(0,Math.min(1,x));
const smooth=x=>{x=sat(x);return x*x*(3-2*x)};
const mix=(a,b,t)=>a+(b-a)*t;
const hash=n=>{const x=Math.sin(n*127.1+311.7)*43758.5453123;return x-Math.floor(x)};
const palettes={dark:{bg:0x07121d,floor:0x10202b,fog:0x07121d,key:0xffdfba,rim:0x71ccdb,exp:1.25},light:{bg:0xe3edf0,floor:0xcbdde1,fog:0xe3edf0,key:0xfff0d6,rim:0x3c96ac,exp:1.1},blue:{bg:0x09204e,floor:0x122d59,fog:0x09204e,key:0xbfeaff,rim:0x58b1ff,exp:1.25},copper:{bg:0x261b18,floor:0x392824,fog:0x261b18,key:0xffd3a0,rim:0x78c9d3,exp:1.15},final:{bg:0x0b2635,floor:0x183948,fog:0x0b2635,key:0xffecb7,rim:0x8cdbdd,exp:1.25}};
let renderer,scene,camera,content,floor,key,rim,fill,ambient,shadows,worlds={},features,shots,sky;
let active='',posterTexture;
const tmp=new T.Object3D();
const MAT={};
function environment(){
 const c=document.createElement('canvas');c.width=1024;c.height=512;const x=c.getContext('2d');
 x.fillStyle='#142734';x.fillRect(0,0,1024,512);
 const g=x.createLinearGradient(0,0,0,512);g.addColorStop(0,'#dae7e9');g.addColorStop(.3,'#91a8ad');g.addColorStop(.48,'#102330');g.addColorStop(.56,'#09131d');g.addColorStop(1,'#536771');x.fillStyle=g;x.fillRect(0,0,1024,512);
 for(const [p,w,col] of [[90,100,'#fff6dd'],[400,45,'#d4f6ff'],[700,160,'#e2f4f3'],[950,20,'#c79e77']]){const glow=x.createLinearGradient(p-w,0,p+w,0);glow.addColorStop(0,'rgba(255,255,255,0)');glow.addColorStop(.5,col);glow.addColorStop(1,'rgba(255,255,255,0)');x.fillStyle=glow;x.fillRect(p-w,60,w*2,300)}
 const tex=new T.CanvasTexture(c);tex.mapping=T.EquirectangularReflectionMapping;tex.colorSpace=T.SRGBColorSpace;
 const pm=new T.PMREMGenerator(renderer);const env=pm.fromEquirectangular(tex).texture;tex.dispose();pm.dispose();return env;
}
function bevelBox(w,h,d,r=.06){
 const s=new T.Shape(),a=-w/2,b=-h/2;
 s.moveTo(a+r,b);s.lineTo(a+w-r,b);s.quadraticCurveTo(a+w,b,a+w,b+r);s.lineTo(a+w,b+h-r);s.quadraticCurveTo(a+w,b+h,a+w-r,b+h);s.lineTo(a+r,b+h);s.quadraticCurveTo(a,b+h,a,b+h-r);s.lineTo(a,b+r);s.quadraticCurveTo(a,b,a+r,b);
 const g=new T.ExtrudeGeometry(s,{depth:Math.max(.01,d-2*r),bevelEnabled:true,bevelSegments:2,steps:1,bevelSize:r/2,bevelThickness:r,curveSegments:3});g.center();return g;
}
function mesh(g,m,x=0,y=0,z=0){const o=new T.Mesh(g,m);o.position.set(x,y,z);return o}
function group(){return new T.Group()}
function ring(r=.8,t=.025,mat=MAT.gold){return mesh(new T.TorusGeometry(r,t,8,96),mat)}
function line(points,color=0x4fa8ba,opacity=.5){return new T.Line(new T.BufferGeometry().setFromPoints(points),new T.LineBasicMaterial({color,transparent:true,opacity}))}
function shadow(x,z,r,opacity=.4){
 const c=document.createElement('canvas');c.width=c.height=128;const q=c.getContext('2d');const g=q.createRadialGradient(64,64,0,64,64,64);g.addColorStop(0,`rgba(0,0,0,${opacity})`);g.addColorStop(1,'rgba(0,0,0,0)');q.fillStyle=g;q.fillRect(0,0,128,128);
 const s=mesh(new T.PlaneGeometry(r*2,r*2),new T.MeshBasicMaterial({map:new T.CanvasTexture(c),transparent:true,depthWrite:false}),x,-2.015,z);s.rotation.x=-Math.PI/2;return s;
}
function core(){
 const g=group();g.userData.rings=[];g.userData.panels=[];
 const center=mesh(new T.IcosahedronGeometry(.85,1),MAT.glass);g.add(center);g.userData.center=center;
 const wire=new T.LineSegments(new T.EdgesGeometry(new T.IcosahedronGeometry(.87,1)),new T.LineBasicMaterial({color:0xa6e9e9,transparent:true,opacity:.7}));g.add(wire);
 for(let i=0;i<7;i++){const r=ring(1.05+i*.105,.025,i%2?MAT.gold:MAT.darkMetal);r.rotation.set(i*.39,i*.3,i*.18);g.add(r);g.userData.rings.push(r)}
 const geo=bevelBox(.3,.65,.10,.035);
 for(let i=0;i<36;i++){const p=mesh(geo,i%3?MAT.copper:MAT.ceramic);g.add(p);g.userData.panels.push(p)}
 return g;
}
function animateCore(g,t,open=0){
 g.rotation.set(.15*Math.sin(t*.13),t*.12,.08*Math.sin(t*.21));
 g.userData.center.rotation.set(t*.08,t*.09,0);
 for(let i=0;i<g.userData.rings.length;i++){const r=g.userData.rings[i];r.rotation.set(i*.39+t*.12,i*.3-t*.09,i*.18+t*.04);r.scale.setScalar(1+open*.3)}
 for(let i=0;i<g.userData.panels.length;i++){const a=i/36*TAU,r=1.65+open*(.9+hash(i)*1.2),p=g.userData.panels[i];p.position.set(Math.cos(a)*r,Math.sin(a*3)*(.3+open*.5),Math.sin(a)*r);p.rotation.set(Math.sin(a)*.4,a,Math.cos(a)*.4);}
}
function makeCoreWorld(){const g=group(),c=core();c.position.set(1.8,.25,0);g.add(c);g.userData.core=c;
 const platform=mesh(new T.CylinderGeometry(3,3.05,.17,96),MAT.darkMetal,1.8,-1.9,0);g.add(platform);
 for(let i=0;i<5;i++){const r=ring(3.2+i*.75,.012,MAT.silver);r.rotation.x=Math.PI/2;r.position.set(1.8,-1.98,0);g.add(r)}
 g.add(shadow(1.8,0,3));return g}
function makeSignal(){
 const g=group(),N=1000;const tiles=new T.InstancedMesh(bevelBox(.10,.20,.07,.015),MAT.copper,N);tiles.instanceMatrix.setUsage(T.DynamicDrawUsage);g.add(tiles);g.userData.tiles=tiles;
 const hoop=ring(2.1,.055,MAT.silver);hoop.position.set(2,0,0);g.add(hoop);g.userData.hoop=hoop;return g;
}
function makeArchive(){const g=group();g.userData.ribs=[];
 for(let i=0;i<28;i++){const r=ring(4.1,.10,i%4?MAT.darkMetal:MAT.gold);r.position.set(2,.5,-i*2);r.scale.x=.8;g.add(r);g.userData.ribs.push(r);for(let j=0;j<3;j++){const slab=mesh(bevelBox(1.15,1.5,.10),i%3===j?MAT.ceramic:MAT.darkMetal);const a=j/3*TAU+.5;slab.position.set(2+3.1*Math.cos(a),.5+3.1*Math.sin(a),-i*2);slab.rotation.z=a-Math.PI/2;g.add(slab)}}
 const c=core();c.scale.setScalar(.7);c.position.set(2,0,-7);g.add(c);g.userData.core=c;return g;
}
function makeClock(){const g=group();g.userData.rings=[];for(let i=0;i<13;i++){const r=ring(.9+i*.18,.038,i%3?MAT.copper:MAT.silver);r.position.set(2.6,0,0);g.add(r);g.userData.rings.push(r)}
 const c=mesh(new T.OctahedronGeometry(.65,0),MAT.glass,2.6,0,0);g.add(c);g.userData.core=c;
 for(let i=0;i<60;i++){const p=mesh(new T.BoxGeometry(.035,i%5?.12:.28,.07),MAT.gold);const a=i/60*TAU;p.position.set(2.6+3.4*Math.cos(a),3.4*Math.sin(a),0);p.rotation.z=a-Math.PI/2;g.add(p)}return g;
}
function makePayload(){const g=group();g.userData.sheets=[];const geo=bevelBox(4.3,.14,3.2,.05);
 for(let i=0;i<9;i++){const s=mesh(geo,i%3===0?MAT.copper:MAT.ceramic,2,.12+i*.13,0);g.add(s);g.userData.sheets.push(s)}
 const plate=mesh(new T.CylinderGeometry(3.3,3.4,.16,96),MAT.whiteMetal,2,-1.93,0);g.add(plate);g.add(shadow(2,0,4));
 const grid=new T.GridHelper(40,40,0x94b8c2,0xc2d5d9);grid.position.y=-2;g.add(grid);return g;
}
function makeEncode(){const g=group(),N=384;const pieces=new T.InstancedMesh(bevelBox(.27,.13,.35,.025),MAT.ceramic,N);pieces.instanceMatrix.setUsage(T.DynamicDrawUsage);
 for(let i=0;i<N;i++)pieces.setColorAt(i,new T.Color(i%9===0?0xbb7446:i%4===0?0x4c9ba5:0xe0edf0));g.add(pieces);g.userData.pieces=pieces;
 const platform=mesh(new T.CylinderGeometry(4.3,4.4,.13,96),MAT.whiteMetal,2,-1.94,0);g.add(platform);g.add(shadow(2,0,4));return g;
}
const nodePositions=Array.from({length:24},(_,i)=>{const a=i/24*TAU,r=2.2+(i%3)*1.25;return V(2+Math.cos(a)*r,-.6+hash(i+4)*.7,Math.sin(a)*r)});
function makeNetwork(){const g=group();g.userData.nodes=[];g.userData.links=[];
 const ng=bevelBox(.40,.85,.40,.045);
 nodePositions.forEach((v,i)=>{const n=group();n.position.copy(v);for(let j=0;j<3;j++){const q=mesh(ng,j===1?MAT.copper:MAT.ceramic,0,j*.19,0);n.add(q)}const eye=mesh(new T.SphereGeometry(.065,10,6),MAT.light,0,.65,.22);n.add(eye);g.add(n);g.userData.nodes.push(n);
 const curve=new T.QuadraticBezierCurve3(V(2,-.1,0),V(mix(2,v.x,.5),2+hash(i)*1.3,v.z*.5),v.clone().add(V(0,.7,0)));const l=line(curve.getPoints(48),0x3b8b9c,.35);g.add(l);g.userData.links.push(l);});
 const center=core();center.scale.setScalar(.5);center.position.set(2,0,0);g.add(center);g.userData.core=center;
 const platform=mesh(new T.CylinderGeometry(7.5,7.6,.12,96),MAT.whiteMetal,2,-1.96,0);g.add(platform);g.add(shadow(2,0,5));return g;
}
function makeCertificate(){const g=group();g.userData.seals=[];
 const pedestal=mesh(new T.CylinderGeometry(2.8,3.1,.28,96),MAT.whiteMetal,2,-1.8,0);g.add(pedestal);
 for(let i=0;i<9;i++){const p=mesh(bevelBox(3.6,.09,2.5,.045),i===8?MAT.copper:MAT.ceramic,2,-.8+i*.25,0);g.add(p);g.userData.seals.push(p)}
 const seal=ring(1.1,.15,MAT.gold);seal.position.set(2,1.95,0);seal.rotation.x=-Math.PI/2;g.add(seal);g.userData.seal=seal;g.add(shadow(2,0,4));return g;
}
function makeSui(){const g=group();g.userData.blocks=[];
 for(let i=0;i<12;i++){const o=mesh(bevelBox(1.0,.32,1.0,.06),i%3?MAT.silver:MAT.copper,2,-1.5+i*.32,0);g.add(o);g.userData.blocks.push(o)}
 for(let i=0;i<7;i++){const l=ring(1.9+i*.22,.016,MAT.light);l.position.set(2,-1.7+i*.52,0);l.rotation.x=-Math.PI/2;g.add(l)}
 const lines=line([V(-5,-1,0),V(2,-1,0),V(2,2.5,0),V(7,2.5,0)],0x98e7ff,.8);g.add(lines);return g;
}
function makeLifetime(){const g=group();g.userData.bars=[];
 for(let i=0;i<32;i++){const a=i/32*TAU,r=2.8;const b=mesh(bevelBox(.18,.8,.35,.03),i%4===0?MAT.copper:MAT.silver,2+r*Math.cos(a),0,r*Math.sin(a));b.rotation.y=-a;g.add(b);g.userData.bars.push(b)}
 const r=ring(2.8,.04,MAT.light);r.position.set(2,-.85,0);r.rotation.x=-Math.PI/2;g.add(r);g.userData.ring=r;
 const c=core();c.scale.setScalar(.5);c.position.set(2,.1,0);g.add(c);g.userData.core=c;return g;
}
function makeMeaning(){const g=group();g.userData.pages=[];for(let i=0;i<18;i++){const p=mesh(bevelBox(1.4,1.8,.05,.045),i%4?MAT.silver:MAT.copper);g.add(p);g.userData.pages.push(p)}
 const c=core();c.position.set(2,0,0);c.scale.setScalar(.5);g.add(c);g.userData.core=c;return g;
}
function makeAccess(){const g=group();g.userData.gates=[];
 for(let i=0;i<8;i++){const a=ring(2.4,.15,i%2?MAT.copper:MAT.darkMetal);a.position.set(2,0,-i*1.1);g.add(a);g.userData.gates.push(a);for(let j=0;j<12;j++){const m=mesh(bevelBox(.18,.55,.30,.035),MAT.silver);const ang=j/12*TAU;m.position.set(2+2.4*Math.cos(ang),2.4*Math.sin(ang),-i*1.1);m.rotation.z=ang;g.add(m)}}
 const c=core();c.position.set(2,0,-3);g.add(c);g.userData.core=c;return g;
}
function makeMechanism(){const g=group();g.userData.rings=[];g.userData.teeth=[];
 for(let i=0;i<6;i++){const r=ring(1.6+i*.18,.065,i%2?MAT.copper:MAT.silver);r.position.set(2,0,(i-2.5)*.48);g.add(r);g.userData.rings.push(r);for(let j=0;j<32;j++){const tooth=mesh(bevelBox(.08,.24,.12,.018),MAT.gold);g.add(tooth);g.userData.teeth.push({o:tooth,layer:i,index:j})}}
 const c=mesh(new T.IcosahedronGeometry(.8,1),MAT.glass,2,0,0);g.add(c);g.userData.core=c;return g;
}
function makeSound(){const g=group(),N=240;const bars=new T.InstancedMesh(bevelBox(.10,.10,.10,.018),MAT.copper,N);bars.instanceMatrix.setUsage(T.DynamicDrawUsage);for(let i=0;i<N;i++)bars.setColorAt(i,new T.Color().setHSL(.46+i/N*.13,.38,.48));g.add(bars);g.userData.bars=bars;
 const count=240,bands=6,positions=new Float32Array(count*bands*2*3),uvs=new Float32Array(count*bands*2*2),indices=[];
 for(let b=0;b<bands;b++)for(let i=0;i<count;i++){const n=(b*count+i)*2;uvs[n*2]=i/(count-1);uvs[n*2+1]=0;uvs[(n+1)*2]=i/(count-1);uvs[(n+1)*2+1]=1;if(i<count-1)indices.push(n,n+1,n+2,n+1,n+3,n+2)}
 const geo=new T.BufferGeometry();geo.setAttribute('position',new T.BufferAttribute(positions,3));geo.setAttribute('uv',new T.BufferAttribute(uvs,2));geo.setIndex(indices);const ribbon=mesh(geo,new T.MeshStandardMaterial({color:0x8dd0d3,metalness:.78,roughness:.28,side:T.DoubleSide}));g.add(ribbon);g.userData.ribbon=ribbon;
 const c=ring(2.8,.025,MAT.gold);c.position.set(2,0,0);g.add(c);g.userData.ring=c;return g;
}
function makeEvidence(){const g=group();g.userData.frames=[];
 for(let i=0;i<10;i++){const m=mesh(bevelBox(2.5,3.2,.1,.07),i%3===0?MAT.copper:MAT.ceramic,3.8+i*1.1,.2,-i*2.7);m.rotation.y=-.3;g.add(m);g.userData.frames.push(m)}
 const c=core();c.scale.setScalar(.48);c.position.set(4.9,-.5,1);g.add(c);g.userData.core=c;g.add(shadow(3.6,0,4));
 const frame=mesh(bevelBox(4.5,2.65,.14,.05),MAT.copper,4.4,.9,1);frame.rotation.y=-.28;g.add(frame);
 const picture=mesh(new T.PlaneGeometry(4.28,2.4),new T.MeshBasicMaterial({map:posterTexture}),4.4,.9,1.1);picture.rotation.y=-.28;g.add(picture);return g;
}
function makeContinuity(){const g=group();g.userData.cores=[];
 for(let i=0;i<5;i++){const c=core();c.scale.setScalar(.38);const a=i/5*TAU;c.position.set(2+3.2*Math.cos(a),Math.sin(a*2)*.3,3.2*Math.sin(a));g.add(c);g.userData.cores.push(c)}
 const path=[];for(let i=0;i<=200;i++){const a=i/200*TAU;path.push(V(2+3.2*Math.cos(a),.2*Math.sin(a*2),3.2*Math.sin(a)))}g.add(line(path,0x418b9b,.8));return g;
}
function makeCanopy(){const g=group();g.userData.strips=[];const geo=bevelBox(.14,.14,1.05,.03);
 const N=1600;const lattice=new T.InstancedMesh(geo,MAT.silver,N);lattice.instanceMatrix.setUsage(T.DynamicDrawUsage);
 for(let i=0;i<N;i++)lattice.setColorAt(i,new T.Color(i%11===0?0xd4a56b:i%5===0?0x70b6c0:0xc3dce0));g.add(lattice);g.userData.lattice=lattice;
 for(let i=0;i<36;i++){const a=i/36*TAU;const cr=new T.CubicBezierCurve3(V(2+8.1*Math.cos(a),-2,8.1*Math.sin(a)),V(2+8*Math.cos(a+.16),4.7,8*Math.sin(a+.16)),V(2+2.4*Math.cos(a+.45),7.6,2.4*Math.sin(a+.45)),V(2+.8*Math.cos(a+.7),3.1,.8*Math.sin(a+.7)));const rib=mesh(new T.TubeGeometry(cr,56,.035,6,false),i%3?MAT.gold:MAT.silver);g.add(rib);g.userData.strips.push(rib)}
 const c=core();c.position.set(2,0,0);c.scale.setScalar(.55);g.add(c);g.userData.core=c;return g;
}
function pose(pos,target,fov=38){camera.position.copy(pos);camera.lookAt(target);camera.fov=fov;camera.updateProjectionMatrix()}
function audio(t,k){if(!features)return .3;const a=features[k]||[],x=t*(features.feature_rate||20),i=Math.floor(x);return mix(a[Math.min(i,a.length-1)]||0,a[Math.min(i+1,a.length-1)]||0,x-i)}
function setPalette(tone){const p=palettes[tone];scene.background.setHex(p.bg);scene.fog.color.setHex(p.fog);floor.material.color.setHex(p.floor);key.color.setHex(p.key);rim.color.setHex(p.rim);renderer.toneMappingExposure=p.exp;sky.material.uniforms.uBase.value.setHex(p.bg);sky.material.uniforms.uLight.value.setHex(tone==='light'?0xb2d0d6:0x316371);}

export async function initialize(){
 window.filmBoot='loading local assets';
 const result=await Promise.all([fetch('shots.json').then(r=>r.json()),fetch('assets/audio/motion-features.json').then(r=>r.ok?r.json():null).catch(()=>null),document.fonts.ready,new T.TextureLoader().loadAsync('assets/images/previous-film.jpg')]);shots=result[0];features=result[1];posterTexture=result[3];posterTexture.colorSpace=T.SRGBColorSpace;window.filmShots=shots;
 window.filmBoot='initializing WebGL';renderer=new T.WebGLRenderer({canvas:document.getElementById('world'),antialias:true,alpha:false,powerPreference:'high-performance',preserveDrawingBuffer:true});renderer.setPixelRatio(1);renderer.setSize(W,H,false);renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.ACESFilmicToneMapping;
 scene=new T.Scene();scene.background=new T.Color(0x07121d);scene.fog=new T.Fog(0x07121d,20,95);scene.environment=environment();scene.environmentIntensity=.65;
 camera=new T.PerspectiveCamera(38,W/H,.06,200);
 MAT.copper=new T.MeshStandardMaterial({color:0xc88855,metalness:.86,roughness:.29});MAT.gold=new T.MeshStandardMaterial({color:0xe5c292,metalness:.78,roughness:.32});MAT.silver=new T.MeshStandardMaterial({color:0x88b6be,metalness:.74,roughness:.32});MAT.ceramic=new T.MeshStandardMaterial({color:0xe7f0ef,metalness:.18,roughness:.32});MAT.whiteMetal=new T.MeshStandardMaterial({color:0xd3e4e5,metalness:.42,roughness:.42});MAT.darkMetal=new T.MeshStandardMaterial({color:0x233a46,metalness:.85,roughness:.32});MAT.glass=new T.MeshPhysicalMaterial({color:0x59aeb8,metalness:.35,roughness:.14,clearcoat:1,clearcoatRoughness:.12,iridescence:.55,iridescenceIOR:1.4});MAT.light=new T.MeshBasicMaterial({color:0xb8f2fa});
 key=new T.DirectionalLight(0xffdfba,3.7);key.position.set(-4,8,6);rim=new T.DirectionalLight(0x71ccdb,3);rim.position.set(8,4,-7);fill=new T.DirectionalLight(0xd5e8ef,1.2);fill.position.set(-7,1,-3);ambient=new T.HemisphereLight(0xb4d5e6,0x10202d,1.6);scene.add(key,rim,fill,ambient);
 floor=mesh(new T.PlaneGeometry(300,300),new T.MeshStandardMaterial({color:0x10202b,roughness:.43,metalness:.38}),0,-2.04,0);floor.rotation.x=-Math.PI/2;scene.add(floor);
 const skyMat=new T.ShaderMaterial({side:T.BackSide,depthWrite:false,uniforms:{uTime:{value:0},uBase:{value:new T.Color(0x07121d)},uLight:{value:new T.Color(0x316371)}},vertexShader:'varying vec3 vP;void main(){vP=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',fragmentShader:'varying vec3 vP;uniform float uTime;uniform vec3 uBase,uLight;void main(){vec3 p=normalize(vP);float h=exp(-abs(p.y+.04)*7.);float ray=pow(max(0.,sin(p.x*4.+p.z*2.+uTime*.015)),10.)*.15;vec3 c=mix(uBase,uLight,h*.42+ray);gl_FragColor=vec4(c,1.);}'});sky=mesh(new T.SphereGeometry(100,32,16),skyMat);scene.add(sky);
 content=group();scene.add(content);
 window.filmBoot='building scene geometry';worlds={core:makeCoreWorld(),signal:makeSignal(),archive:makeArchive(),clock:makeClock(),payload:makePayload(),encode:makeEncode(),network:makeNetwork(),repair:makeNetwork(),certificate:makeCertificate(),sui:makeSui(),lifetime:makeLifetime(),meaning:makeMeaning(),access:makeAccess(),mechanism:makeMechanism(),sound:makeSound(),evidence:makeEvidence(),continuity:makeContinuity(),canopy:makeCanopy(),cathedral:makeCanopy(),return:makeCoreWorld()};
 for(const g of Object.values(worlds)){g.visible=false;content.add(g)}
 window.renderFilmAt=draw;window.getFilmState=()=>{const objects=[];worlds[active]?.traverse(o=>{objects.push({matrix:Array.from(o.matrixWorld.elements),instances:o.isInstancedMesh?Array.from(o.instanceMatrix.array):null})});return {world:active,camera:Array.from(camera.matrixWorld.elements),projection:Array.from(camera.projectionMatrix.elements),environment:scene.environmentRotation.toArray(),objects}};window.filmReady=true;window.filmBoot='ready';draw(0);
}

export function draw(time){if(!renderer)return;const t=Math.max(0,Math.min(299.999,time));const idx=shots.findIndex(s=>t>=s.start&&t<s.end);const s=shots[Math.max(0,idx)],u=(t-s.start)/(s.end-s.start),v=smooth(u),local=t-s.start;
 if(active!==s.world){for(const g of Object.values(worlds))g.visible=false;document.querySelectorAll('.shot').forEach((el,i)=>{el.style.opacity=i===idx?'1':'0'});active=s.world;worlds[active].visible=true;setPalette(s.tone)}
 const g=worlds[active];g.position.set(0,0,0);g.rotation.set(0,0,0);g.scale.setScalar(1);const low=audio(t,'low'),mid=audio(t,'mid'),high=audio(t,'high');sky.material.uniforms.uTime.value=t;scene.environmentRotation.y=t*.012;
 // Each branch is absolute-time; no state leaks when the renderer seeks backwards.
 if(active==='core'||active==='return'){
  const c=g.userData.core;animateCore(c,t,active==='return'?.15:smooth((u-.25)/.7));
  if(active==='core')pose(V(mix(5.7,7.7,v),mix(2.6,1.3,v),mix(6.8,10.5,v)),V(1.1,.1,0),mix(31,37,v));else{pose(V(6.8-v*1.5,2.4,10),V(.3,0,0),38);c.scale.setScalar(.9);}
 }else if(active==='signal'){
  const tiles=g.userData.tiles;
  for(let i=0;i<tiles.count;i++){const a=i*.2399632297,r=.8+hash(i)*1.5,spread=smooth((u-.1)/.75);tmp.position.set(2+Math.cos(a)*r*(1-spread)+Math.sin(i*.1+t*.23)*4*spread,Math.sin(a)*r*(1-spread)+(hash(i+10)-.5)*5*spread,Math.sin(i*.67)*r*(1-spread)+(hash(i+4)-.5)*12*spread);tmp.rotation.set(i*.1+t*.1,i*.2,t*.12+i*.3);tmp.scale.setScalar(.6+hash(i+5)*.8);tmp.updateMatrix();tiles.setMatrixAt(i,tmp.matrix)}tiles.instanceMatrix.needsUpdate=true;g.userData.hoop.rotation.set(t*.1,t*.12,0);pose(V(5-v*2,2-v,11-v*2),V(.1,0,-.5),40);
 }else if(active==='archive'){
  animateCore(g.userData.core,t,.4);pose(V(.6,1.0,-1-v*17),V(2,0,-15-v*15),44);g.userData.core.position.z=-7-v*17;
 }else if(active==='clock'){
  g.userData.rings.forEach((r,i)=>{r.rotation.set(.25*Math.sin(i*.4+t*.1),i*.17+local*.06*(i%2?1:-1),i*.12);r.position.z=(i-6)*.06+Math.sin(local*.2+i*.3)*.12});g.userData.core.rotation.set(t*.2,t*.14,0);pose(V(6-v*2,2,11-v*1.6),V(.4,0,0),40);
 }else if(active==='payload'){
  g.userData.sheets.forEach((p,i)=>{p.position.set(2+Math.sin(local*.13+i*.15)*.12,-.9+i*(.18+.08*v),0);p.rotation.set(.01*Math.sin(i),local*.018+i*.012,0)});pose(V(7-v*2.2,6-v*2,10.5-v),V(.2,-.1,0),39);
 }else if(active==='encode'){
  const p=g.userData.pieces,a=smooth((u-.05)/.7);
  for(let i=0;i<p.count;i++){const col=i%16,row=Math.floor(i/16)%12,layer=Math.floor(i/192);const x0=(col-7.5)*.29,y0=-.3+layer*.2,z0=(row-5.5)*.37;const ang=col/16*TAU+layer*.3;tmp.position.set(2+mix(x0,Math.cos(ang)*(2.3+row*.11),a),mix(y0,(row-5.5)*.25,a),mix(z0,Math.sin(ang)*(2.3+row*.11),a));tmp.rotation.set(0,a*(-ang),a*.05*Math.sin(t*.2+row));tmp.scale.setScalar(1);tmp.updateMatrix();p.setMatrixAt(i,tmp.matrix)}p.instanceMatrix.needsUpdate=true;pose(V(7-v*3,4.5-v*1.5,10.4),V(.25,.1,0),40);
 }else if(active==='network'||active==='repair'){
  animateCore(g.userData.core,t,active==='repair'?smooth((u-.45)/.3):.1);
  g.userData.nodes.forEach((n,i)=>{const base=nodePositions[i];n.position.copy(base);let k=1;if(active==='repair'&&i%4===0){const disappear=smooth((u-.12)/.12)*(1-smooth((u-.65)/.22));k=1-disappear*.98;n.position.y-=disappear*1.6;}n.scale.setScalar(k);n.rotation.y=t*.03+i*.1;g.userData.links[i].material.opacity=.18+.35*(.5+.5*Math.sin(t*1.4-i*.4))*k;});
  pose(V(7.8-v*2.0,8.7-v*1.5,12-v*2),V(.2,-.5,0),42);
 }else if(active==='certificate'){
  g.userData.seals.forEach((p,i)=>{p.position.y=-1.2+i*(.24+.035*Math.sin(local*.1));p.rotation.y=.15+local*.025+i*.025});g.userData.seal.rotation.set(-Math.PI/2+.2*Math.sin(local*.16),0,t*.14);pose(V(6.5-v,4.2-v,10-v),V(.15,0,0),39);
 }else if(active==='sui'){
  g.userData.blocks.forEach((p,i)=>{p.rotation.y=local*.05+i*.19;p.position.x=2+Math.sin(i*.4+local*.2)*.1});pose(V(7-v*2,3.5-v,10),V(.15,0,0),38);
 }else if(active==='lifetime'){
  g.userData.bars.forEach((b,i)=>{const h=.3+1.8*(.5+.5*Math.sin(i/32*TAU+local*.3));b.scale.y=h;b.position.y=-.8+h*.4});animateCore(g.userData.core,t,.2);pose(V(6.5-v*1.5,5.5-v,9.5),V(.1,0,0),40);
 }else if(active==='meaning'){
  g.userData.pages.forEach((p,i)=>{const a=i/18*TAU+local*.09;const r=2.8+.3*Math.sin(i*.5);p.position.set(2+r*Math.cos(a),.3*Math.sin(a*2),r*Math.sin(a));p.rotation.set(.15*Math.sin(a),-a+Math.PI/2,.15*Math.cos(a));});animateCore(g.userData.core,t,.25);pose(V(7-v*2.5,4.6-v*1.5,11-v),V(.1,0,0),42);
 }else if(active==='access'){
  g.userData.gates.forEach((r,i)=>{r.rotation.z=local*.06*(i%2?-1:1);r.scale.setScalar(1+Math.sin(local*.25-i*.5)*.03)});animateCore(g.userData.core,t,.2);pose(V(5-v*2,2-v*.5,10-v*3),V(.2,0,-2-v),40);
 }else if(active==='mechanism'){
  g.userData.rings.forEach((r,i)=>{r.rotation.set(.12*Math.sin(t*.1+i),.12*Math.cos(t*.09+i),local*.2*(i%2?-1:1))});g.userData.teeth.forEach(({o,layer,index})=>{const a=index/32*TAU+local*.2*(layer%2?-1:1),r=1.6+layer*.18;o.position.set(2+r*Math.cos(a),r*Math.sin(a),(layer-2.5)*.48);o.rotation.set(0,0,a-Math.PI/2)});g.userData.core.rotation.set(local*.2,local*.3,0);pose(V(7-v*3,1.8-v,10-v*1.2),V(.2,0,0),39);
 }else if(active==='sound'){
  const bars=g.userData.bars;for(let i=0;i<bars.count;i++){const a=i/bars.count*TAU,r=2.6+.18*Math.sin(a*7+t*.4);const amp=.3+(.5+.5*Math.sin(a*13-t*2))*(.35+low*.8)+mid*.25;tmp.position.set(2+Math.cos(a)*r,Math.sin(a)*r,Math.sin(a*5+t*.4)*.65);tmp.rotation.set(0,0,a);tmp.scale.set(.8,amp*12,1+high*3);tmp.updateMatrix();bars.setMatrixAt(i,tmp.matrix)}bars.instanceMatrix.needsUpdate=true;
  const geo=g.userData.ribbon.geometry,p=geo.attributes.position;for(let b=0;b<6;b++)for(let i=0;i<240;i++)for(let side=0;side<2;side++){const a=i/239*TAU,phase=b/6*TAU;const r=2.15+.24*Math.sin(a*4+phase+t*.5)+mid*.20*Math.sin(a*9-phase);const z=Math.sin(a*3+phase+t*.24)*(.55+low*.5)+(side-.5)*(.16+high*.1);const n=(b*240+i)*2+side;p.setXYZ(n,2+Math.cos(a)*r,Math.sin(a)*r,z)}p.needsUpdate=true;geo.computeVertexNormals();g.userData.ribbon.rotation.set(.1*Math.sin(t*.1),.25*Math.sin(local*.12),0);g.userData.ring.rotation.set(.15,.2*Math.sin(local*.1),0);pose(V(5.5-v*2,1.8-v,11),V(.15,0,0),39);
 }else if(active==='evidence'){
  animateCore(g.userData.core,t,.2);g.userData.frames.forEach((p,i)=>{p.rotation.y=-.35+Math.sin(t*.08+i)*.05});pose(V(5-v*2,2.8-v*.5,12-v*2),V(.3,.2,-1),40);
 }else if(active==='continuity'){
  g.userData.cores.forEach((c,i)=>{animateCore(c,t+i,.3);const a=i/5*TAU+local*.055;c.position.set(2+3.2*Math.cos(a),.3*Math.sin(a*2),3.2*Math.sin(a));});pose(V(6.5-v*2,6.5-v,11),V(.2,0,0),41);
 }else if(active==='canopy'||active==='cathedral'){
  const l=g.userData.lattice,climax=active==='cathedral',reveal=climax?1:smooth((u-.05)/.9);
  for(let i=0;i<l.count;i++){const col=i%80,row=Math.floor(i/80),a=col/80*TAU;const rr=4.4+row*.20;const arch=Math.sin(row/19*Math.PI);const r=rr*(.35+.65*reveal);tmp.position.set(2+Math.cos(a)*r,(climax?-.6:-1)+arch*3.6+Math.sin(a*6+row*.4+t*.12)*(.12+low*.12),Math.sin(a)*r);tmp.rotation.set(Math.sin(a)*.4,-a+Math.PI/2,Math.cos(a)*.4);tmp.scale.set(1,1,1);tmp.updateMatrix();l.setMatrixAt(i,tmp.matrix)}l.instanceMatrix.needsUpdate=true;animateCore(g.userData.core,t,.6);g.userData.core.position.y=.4;
  g.userData.strips.forEach((r,i)=>{r.scale.y=.85+.15*reveal;r.rotation.y=.01*Math.sin(t*.06+i*.1)});
  if(climax)pose(V(13-v*10,9-v*5.8,22-v*16),V(1.5+v*.5,2.1,0),44);else pose(V(10-v*2,8-v*1.5,18-v*2),V(.2,1.5,0),43);
 }
 renderer.render(scene,camera);
}
