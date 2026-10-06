"""Inspect the real IndexedDB adapter; no test-only application globals."""
READ_STATE = '''async()=>{
 const root=new URL('.',document.baseURI),id=document.documentElement.dataset.qualification||'ap';
 const {createLocalStore}=await import(new URL('src/storage/local.js',root));
 const store=createLocalStore({qualificationId:id,rootPath:root.pathname});
 try{return JSON.parse(await store.snapshot());}finally{await store.close();}
}'''
WRITE_STATE = '''async state=>{
 const root=new URL('.',document.baseURI),id=document.documentElement.dataset.qualification||'ap';
 const {createLocalStore}=await import(new URL('src/storage/local.js',root));
 const store=createLocalStore({qualificationId:id,rootPath:root.pathname});
 try{await store.write(state,{replace:true});}finally{await store.close();}
}'''

def state(page):
    page.wait_for_function('document.querySelector("#main").getAttribute("aria-busy")!=="true" && document.querySelector("#save-state").textContent!=="保存中…"')
    return page.evaluate(READ_STATE)

def write_state(page, value):
    state(page)
    page.evaluate(WRITE_STATE, value)
