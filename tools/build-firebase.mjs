import {build} from 'esbuild';
import {mkdirSync} from 'node:fs';
const directory=new URL('../assets/vendor/',import.meta.url);mkdirSync(directory,{recursive:true});
await build({entryPoints:[new URL('firebase-entry.js',import.meta.url).pathname],outfile:new URL('firebase.js',directory).pathname,bundle:true,format:'esm',minify:true,target:'es2022',legalComments:'eof'});
console.log('Built pinned Firebase Auth/Firestore SDK; Analytics is excluded.');
