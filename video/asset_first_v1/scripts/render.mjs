#!/usr/bin/env node
import fs from 'node:fs'; import path from 'node:path'; import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler'; import {renderMedia,renderStill,selectComposition} from '@remotion/renderer';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const value=(flag)=>{const i=process.argv.indexOf(flag);return i>=0&&i+1<process.argv.length?process.argv[i+1]:null};
const compositionId=value('--composition'),output=value('--output'),publicDir=value('--public-dir'),propsPath=value('--props'),receiptPath=value('--receipt');
const scale=Number(value('--scale')||'1'),stillFrame=value('--still-frame'),stillFrames=value('--still-frames');
if(!compositionId||!output||!publicDir||!propsPath||!receiptPath) throw new Error('required render arguments missing');
const inputProps=JSON.parse(fs.readFileSync(propsPath,'utf8'));const started=Date.now();
const serveUrl=await bundle({entryPoint:path.join(root,'src','index.ts'),publicDir,onProgress:()=>{}});
const composition=await selectComposition({serveUrl,id:compositionId,inputProps});fs.mkdirSync(path.dirname(output),{recursive:true});
const batch=stillFrames?stillFrames.split(',').map(Number):[];
const outputPaths=[];
if(batch.length){fs.mkdirSync(output,{recursive:true});for(const frame of batch){const target=path.join(output,`frame_${String(frame).padStart(4,'0')}.png`);await renderStill({serveUrl,composition,frame,imageFormat:'png',scale,output:target,inputProps});outputPaths.push(target)}}
else if(stillFrame!==null){await renderStill({serveUrl,composition,frame:Number(stillFrame),imageFormat:'png',scale,output,inputProps});outputPaths.push(output)}
else{await renderMedia({serveUrl,composition,codec:'h264',crf:scale<1?25:18,scale,concurrency:2,outputLocation:output,inputProps,muted:true});outputPaths.push(output)}
const receipt={status:'PASS',renderer:'remotion',renderer_version:'4.0.508',composition_id:compositionId,output_path:output,output_paths:outputPaths,creative_source_sha256:inputProps.creativeSourceSha256,proof_id:inputProps.proofId,captions_visible:inputProps.captionsVisible,scale,still_frame:stillFrame===null?null:Number(stillFrame),still_frames:batch,elapsed_ms:Date.now()-started,network_calls:0,uploads:0,browser_profile_used:false};
fs.mkdirSync(path.dirname(receiptPath),{recursive:true});fs.writeFileSync(receiptPath,JSON.stringify(receipt,null,2)+'\n');
