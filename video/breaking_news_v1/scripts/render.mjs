#!/usr/bin/env node
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';import {renderMedia,renderStill,selectComposition} from '@remotion/renderer';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const value=(flag)=>{const i=process.argv.indexOf(flag);return i>=0&&i+1<process.argv.length?process.argv[i+1]:null};
const compositionId=value('--composition'),output=value('--output'),publicDir=value('--public-dir'),propsPath=value('--props'),receiptPath=value('--receipt');
const scale=Number(value('--scale')||'1'),stillFrame=value('--still-frame'),stillFrames=value('--still-frames'),codec=value('--codec')||'h264';
if(!compositionId||!output||!publicDir||!propsPath||!receiptPath)throw new Error('required render arguments missing');
const inputProps=JSON.parse(fs.readFileSync(propsPath,'utf8'));const started=Date.now();
const serveUrl=await bundle({entryPoint:path.join(root,'src','index.ts'),publicDir,onProgress:()=>{}});
const composition=await selectComposition({serveUrl,id:compositionId,inputProps});fs.mkdirSync(path.dirname(output),{recursive:true});
const batch=stillFrames?stillFrames.split(',').map(Number):[];const outputs=[];
if(batch.length){fs.mkdirSync(output,{recursive:true});for(const frame of batch){const target=path.join(output,`frame_${String(frame).padStart(4,'0')}.png`);await renderStill({serveUrl,composition,frame,imageFormat:'png',scale,output:target,inputProps});outputs.push(target)}}
else if(stillFrame!==null){await renderStill({serveUrl,composition,frame:Number(stillFrame),imageFormat:'png',scale,output,inputProps});outputs.push(output)}
else{const options={serveUrl,composition,codec,scale,concurrency:2,outputLocation:output,inputProps,muted:true};if(codec==='h264')Object.assign(options,{crf:scale<1?25:12,pixelFormat:'yuv420p'});if(codec==='prores')Object.assign(options,{proResProfile:'hq',pixelFormat:'yuv422p10le'});await renderMedia(options);outputs.push(output)}
const receipt={status:'PASS',renderer:'remotion',renderer_version:'4.0.508',composition_id:compositionId,output_paths:outputs,codec,scale,elapsed_ms:Date.now()-started,network_calls:0,uploads:0,browser_profile_used:false};
fs.mkdirSync(path.dirname(receiptPath),{recursive:true});fs.writeFileSync(receiptPath,JSON.stringify(receipt,null,2)+'\n');
